from flask import abort


def _register_failing_routes(app):
    # Helper routes are not named test_* so pytest doesn't collect them as tests.
    @app.get("/boom/400")
    def raise_400():
        abort(400)

    @app.get("/boom/409")
    def raise_409():
        abort(409)

    @app.get("/boom/500")
    def raise_500():
        abort(500)


def test_error_handlers_return_json(app):
    _register_failing_routes(app)
    client = app.test_client()

    for url, status, code in [
        ("/boom/400", 400, "bad_request"),
        ("/api/does-not-exist", 404, "not_found"),
        ("/boom/409", 409, "conflict"),
        ("/boom/500", 500, "internal_server_error"),
    ]:
        response = client.get(url)
        assert response.status_code == status
        assert response.is_json
        assert response.get_json()["error"]["code"] == code


def test_cors_allows_only_frontend_origin(app):
    client = app.test_client()

    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"

    blocked = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "Access-Control-Allow-Origin" not in blocked.headers
