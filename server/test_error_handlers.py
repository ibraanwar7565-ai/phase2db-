from app import create_app
from config import TestConfig
from flask import abort


app = create_app(TestConfig)


@app.get("/test/400")
def test_bad_request():
    abort(400)


@app.get("/test/409")
def test_conflict():
    abort(409)


@app.get("/test/500")
def test_internal_server_error():
    abort(500)


def test_error_handlers():
    with app.test_client() as client:

        # Test 400
        response = client.get("/test/400")
        assert response.status_code == 400
        assert response.is_json
        assert response.get_json()["error"]["code"] == "bad_request"
        print("400 handler: PASS")

        # Test 404
        response = client.get("/api/does-not-exist")
        assert response.status_code == 404
        assert response.is_json
        assert response.get_json()["error"]["code"] == "not_found"
        print("404 handler: PASS")

        # Test 409
        response = client.get("/test/409")
        assert response.status_code == 409
        assert response.is_json
        assert response.get_json()["error"]["code"] == "conflict"
        print("409 handler: PASS")

        # Test 500
        response = client.get("/test/500")
        assert response.status_code == 500
        assert response.is_json
        assert (
            response.get_json()["error"]["code"]
            == "internal_server_error"
        )
        print("500 handler: PASS")


if __name__ == "__main__":
    test_error_handlers()