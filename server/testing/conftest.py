import pytest

from app import create_app
from config import TestConfig
from extensions import db as _db


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def user(db):
    from models import User

    u = User(name="Wanjiku", email="wanjiku@example.com", phone="+254700000001")
    u.set_password("secret123")
    db.session.add(u)
    db.session.commit()
    return u
