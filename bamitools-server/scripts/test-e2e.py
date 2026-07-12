"""End-to-end smoke test: create a page, view it, verify cache.

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

    # 2. Upload page directly to S3
    print("[2/6] Upload page to S3...", end=" ")
    import asyncio
    from bamitools_server.ids import generate_public_id
    from bamitools_server.storage.s3 import upload_page
    from bamitools_server.storage.html_loader import generate_page_loader

    public_id = generate_public_id()
    spec = {
        "title": "E2E Test Page",
        "layout": [
            {
                "widget_id": "kpi-card",
                "props": {"label": "Revenue", "value": "$4.2k", "change": "+15%"},
            }
        ],
    }
    html = generate_page_loader(public_id)
    asyncio.run(upload_page(public_id, json.dumps(spec), html))
    print(f"OK (id={public_id})")

    # 3. Fetch HTML via /p/{id}
    print("[3/6] GET /p/{id} (HTML)...", end=" ")
    resp = httpx.get(f"{base}/p/{public_id}", timeout=5)
    assert resp.status_code == 200, f"FAIL: {resp.status_code}"
    assert "text/html" in resp.headers.get("content-type", "")
    assert "page-root" in resp.text
    print("OK")

    # 4. Fetch JSON via /p/{id}.json
    print("[4/6] GET /p/{id}.json...", end=" ")
    resp = httpx.get(f"{base}/p/{public_id}.json", timeout=5)
    assert resp.status_code == 200, f"FAIL: {resp.status_code}"
    body = resp.json()
    assert body["title"] == "E2E Test Page"
    print("OK")

    # 5. Second fetch should be Redis cache hit (same data)
    print("[5/6] GET /p/{id}.json (cache hit)...", end=" ")
    resp2 = httpx.get(f"{base}/p/{public_id}.json", timeout=5)
    assert resp2.status_code == 200
    assert resp2.json() == body
    print("OK")

    # 6. 404 for nonexistent
    print("[6/6] GET /p/nonexistent (404)...", end=" ")
    resp = httpx.get(f"{base}/p/nonexistent", timeout=5)
    assert resp.status_code == 404, f"FAIL: {resp.status_code}"
    print("OK")

    print("=" * 50)
    print(f"ALL PASSED (page: {base}/p/{public_id})")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
