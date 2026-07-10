"""End-to-end smoke test: create a dashboard, view it, verify cache.

Usage:
    python scripts/test-e2e.py [--base-url http://localhost:8000]

Requires: running server + redis + postgres + rustfs (make up).
"""

import argparse
import json
import sys

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print(f"E2E smoke test against {base}")
    print("=" * 50)

    # 1. Health check
    print("[1/6] Health check...", end=" ")
    resp = httpx.get(f"{base}/api/health", timeout=5)
    assert resp.status_code == 200, f"FAIL: {resp.status_code}"
    assert resp.json() == {"status": "ok"}
    print("OK")

    # 2. Upload dashboard directly to S3
    print("[2/6] Upload dashboard to S3...", end=" ")
    import asyncio
    from snapbami_server.ids import generate_public_id
    from snapbami_server.storage.s3 import upload_dashboard
    from snapbami_server.storage.html_loader import generate_html_loader

    public_id = generate_public_id()
    spec = {
        "title": "E2E Test Dashboard",
        "layout": [
            {
                "widget": "KpiCard",
                "width": "col-span-1",
                "props": {"label": "Revenue", "value": "$4.2k", "change": "+15%"},
            }
        ],
    }
    html = generate_html_loader(public_id)
    asyncio.run(upload_dashboard(public_id, json.dumps(spec), html))
    print(f"OK (id={public_id})")

    # 3. Fetch HTML via /d/{id}
    print("[3/6] GET /d/{id} (HTML)...", end=" ")
    resp = httpx.get(f"{base}/d/{public_id}", timeout=5)
    assert resp.status_code == 200, f"FAIL: {resp.status_code}"
    assert "text/html" in resp.headers.get("content-type", "")
    assert "dashboard-root" in resp.text
    print("OK")

    # 4. Fetch JSON via /d/{id}.json
    print("[4/6] GET /d/{id}.json...", end=" ")
    resp = httpx.get(f"{base}/d/{public_id}.json", timeout=5)
    assert resp.status_code == 200, f"FAIL: {resp.status_code}"
    body = resp.json()
    assert body["title"] == "E2E Test Dashboard"
    print("OK")

    # 5. Second fetch should be Redis cache hit (same data)
    print("[5/6] GET /d/{id}.json (cache hit)...", end=" ")
    resp2 = httpx.get(f"{base}/d/{public_id}.json", timeout=5)
    assert resp2.status_code == 200
    assert resp2.json() == body
    print("OK")

    # 6. 404 for nonexistent
    print("[6/6] GET /d/nonexistent (404)...", end=" ")
    resp = httpx.get(f"{base}/d/nonexistent", timeout=5)
    assert resp.status_code == 404, f"FAIL: {resp.status_code}"
    print("OK")

    print("=" * 50)
    print(f"ALL PASSED (dashboard: {base}/d/{public_id})")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
