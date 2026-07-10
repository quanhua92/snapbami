from snapbami_server.storage.html_loader import generate_html_loader


def test_returns_html_string():
    html = generate_html_loader("abc12345")
    assert isinstance(html, str)
    assert "<html" in html.lower()


def test_contains_dashboard_root():
    html = generate_html_loader("abc12345")
    assert 'id="dashboard-root"' in html


def test_contains_fetch_logic():
    html = generate_html_loader("abc12345")
    assert "fetch(" in html
    assert ".json" in html


def test_injects_public_id():
    html = generate_html_loader("abc12345")
    assert "abc12345" in html


def test_different_ids_produce_different_html():
    html1 = generate_html_loader("abc12345")
    html2 = generate_html_loader("xyz99999")
    assert html1 != html2


def test_custom_title():
    html = generate_html_loader("abc12345", title="My Dashboard")
    assert "<title>My Dashboard</title>" in html
