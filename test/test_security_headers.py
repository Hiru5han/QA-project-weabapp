def test_security_headers_present(client):
    response = client.get("/")
    assert response.headers.get("Content-Security-Policy") is not None
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert (
        response.headers.get("Permissions-Policy")
        == "camera=(), microphone=(), geolocation=()"
    )
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Embedder-Policy") == "require-corp"
