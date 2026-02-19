import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base, get_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={"email": "test@example.com", "password": "pass123"})
    res = client.post("/auth/login", json={"email": "test@example.com", "password": "pass123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_register(client):
    res = client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
    assert res.status_code == 201
    assert res.json()["email"] == "a@b.com"


def test_duplicate_register(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
    res = client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
    assert res.status_code == 400


def test_login(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass"})
    res = client.post("/auth/login", json={"email": "a@b.com", "password": "pass"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "correct"})
    res = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert res.status_code == 401


def test_list_files_empty(client, auth_headers):
    res = client.get("/files/", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_upload_invalid_file_type(client, auth_headers):
    res = client.post(
        "/files/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
        headers=auth_headers
    )
    assert res.status_code == 400


def test_protected_route_without_token(client):
    res = client.get("/files/")
    assert res.status_code == 403
