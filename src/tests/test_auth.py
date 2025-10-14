from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.routes.auth import get_db
from src.api.utils.jwt import create_access_token


class FakeCollection:
    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}
    
    def find_one(self, query: Dict[str, Any]) -> Dict[str, Any] | None:
        if "_id" in query:
            return self.data.get(query["_id"])
        if "email" in query:
            return self.data.get(query["email"])
        return None
    
    def insert_one(self, document: Dict[str, Any]) -> None:
        self.data[document["_id"]] = document
    
    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> None:
        key = query.get("_id") or query.get("email")
        if key and key in self.data:
            if "$set" in update:
                self.data[key].update(update["$set"])
    
    def find_one_and_update(self, query: Dict[str, Any], update: Dict[str, Any], **kwargs) -> Dict[str, Any] | None:
        key = query.get("_id") or query.get("email")
        if key and key in self.data:
            if "$set" in update:
                self.data[key].update(update["$set"])
            return self.data[key]
        return None
    
    def delete_one(self, query: Dict[str, Any]) -> MagicMock:
        key = query.get("_id") or query.get("email")
        result = MagicMock()
        if key and key in self.data:
            del self.data[key]
            result.deleted_count = 1
        else:
            result.deleted_count = 0
        return result


class FakeDB:
    def __init__(self):
        self.collections: Dict[str, FakeCollection] = {}
    
    def get_collection(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]


@pytest.fixture
def fake_db():
    return FakeDB()


@pytest.fixture
def client(fake_db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: fake_db
    return TestClient(app)


@pytest.fixture
def admin_user(fake_db):
    """Create an admin user for testing"""
    users = fake_db.get_collection("users")
    user = {
        "_id": "admin@test.com",
        "email": "admin@test.com",
        "full_name": "Admin User",
        "role": "Admin",
        "password_hash": "$2b$12$7utAbcmhDd6V7m.tjwplYeTJXj7ZkM6QIG8gzFR6q/Arn79s1SJVC",  # password: "adminpass123"
        "is_active": True,
        "failed_attempts": 0,
    }
    users.insert_one(user)
    return user


@pytest.fixture
def regular_user(fake_db):
    """Create a regular user for testing"""
    users = fake_db.get_collection("users")
    user = {
        "_id": "user@test.com",
        "email": "user@test.com",
        "full_name": "Regular User",
        "role": "User",
        "password_hash": "$2b$12$7raGbA.DySA7MZLVHe7L1u.QYGO7KKW7J6qzfkTFLpifj2lwsBiTS",  # password: "userpass123"
        "is_active": True,
        "failed_attempts": 0,
    }
    users.insert_one(user)
    return user


def test_register_success(client):
    """Test successful user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "newpass123",
            "full_name": "New User",
            "role": "User",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "User"
    assert data["is_active"] is True
    assert "password_hash" not in data


def test_register_duplicate_email(client, regular_user):
    """Test registration with duplicate email"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "user@test.com",
            "password": "anotherpass123",
            "full_name": "Another User",
            "role": "User",
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_password_too_short(client):
    """Test registration with password too short"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "shortpass@test.com",
            "password": "short",
            "full_name": "Short Pass User",
            "role": "User",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_success(client, regular_user):
    """Test successful login"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "user@test.com",
            "password": "userpass123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, regular_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "user@test.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid credentials" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent user"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "somepassword",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_lockout_after_failed_attempts(client, regular_user):
    """Test account lockout after multiple failed login attempts"""
    # Make 5 failed login attempts
    for i in range(5):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "user@test.com",
                "password": "wrongpassword",
            },
        )
        if i < 4:
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        else:
            # 5th attempt should lock the account
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "locked" in response.json()["detail"].lower()
    
    # Try to login with correct password - should still be locked
    response = client.post(
        "/api/auth/login",
        json={
            "email": "user@test.com",
            "password": "userpass123",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "locked" in response.json()["detail"].lower()


def test_login_reset_failed_attempts_on_success(client, fake_db):
    """Test that failed attempts are reset after successful login"""
    users = fake_db.get_collection("users")
    # Create user with some failed attempts
    user = {
        "_id": "resetuser@test.com",
        "email": "resetuser@test.com",
        "full_name": "Reset User",
        "role": "User",
        "password_hash": "$2b$12$7raGbA.DySA7MZLVHe7L1u.QYGO7KKW7J6qzfkTFLpifj2lwsBiTS",  # password: "userpass123"
        "is_active": True,
        "failed_attempts": 3,
    }
    users.insert_one(user)
    
    # Successful login should reset failed_attempts
    response = client.post(
        "/api/auth/login",
        json={
            "email": "resetuser@test.com",
            "password": "userpass123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Check that failed_attempts was reset
    updated_user = users.find_one({"email": "resetuser@test.com"})
    assert updated_user["failed_attempts"] == 0
    assert updated_user.get("lockout_until") is None


def test_me_endpoint_success(client, regular_user):
    """Test /me endpoint with valid token"""
    token = create_access_token({"sub": regular_user["_id"], "role": regular_user["role"]})
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == regular_user["email"]
    assert data["full_name"] == regular_user["full_name"]
    assert data["role"] == regular_user["role"]


def test_me_endpoint_missing_token(client):
    """Test /me endpoint without token"""
    response = client.get("/api/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "missing bearer token" in response.json()["detail"].lower()


def test_me_endpoint_invalid_token(client):
    """Test /me endpoint with invalid token"""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token_xyz"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_endpoint_inactive_user(client, fake_db):
    """Test /me endpoint with inactive user"""
    users = fake_db.get_collection("users")
    user = {
        "_id": "inactive@test.com",
        "email": "inactive@test.com",
        "full_name": "Inactive User",
        "role": "User",
        "password_hash": "$2b$12$7raGbA.DySA7MZLVHe7L1u.QYGO7KKW7J6qzfkTFLpifj2lwsBiTS",
        "is_active": False,
    }
    users.insert_one(user)
    
    token = create_access_token({"sub": user["_id"], "role": user["role"]})
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "inactive" in response.json()["detail"].lower()


def test_deactivate_user_as_admin(client, admin_user, regular_user):
    """Test admin can deactivate a user"""
    admin_token = create_access_token({"sub": admin_user["_id"], "role": admin_user["role"]})
    response = client.patch(
        f"/api/auth/users/{regular_user['email']}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is False


def test_deactivate_user_as_regular_user(client, regular_user):
    """Test regular user cannot deactivate another user"""
    user_token = create_access_token({"sub": regular_user["_id"], "role": regular_user["role"]})
    response = client.patch(
        "/api/auth/users/someother@test.com/deactivate",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "admin" in response.json()["detail"].lower()


def test_deactivate_nonexistent_user(client, admin_user):
    """Test deactivating a non-existent user"""
    admin_token = create_access_token({"sub": admin_user["_id"], "role": admin_user["role"]})
    response = client.patch(
        "/api/auth/users/nonexistent@test.com/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_activate_user_as_admin(client, admin_user, fake_db):
    """Test admin can activate a user"""
    users = fake_db.get_collection("users")
    inactive_user = {
        "_id": "inactive2@test.com",
        "email": "inactive2@test.com",
        "full_name": "Inactive User 2",
        "role": "User",
        "password_hash": "$2b$12$7raGbA.DySA7MZLVHe7L1u.QYGO7KKW7J6qzfkTFLpifj2lwsBiTS",
        "is_active": False,
    }
    users.insert_one(inactive_user)
    
    admin_token = create_access_token({"sub": admin_user["_id"], "role": admin_user["role"]})
    response = client.patch(
        f"/api/auth/users/{inactive_user['email']}/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is True


def test_activate_user_as_regular_user(client, regular_user):
    """Test regular user cannot activate another user"""
    user_token = create_access_token({"sub": regular_user["_id"], "role": regular_user["role"]})
    response = client.patch(
        "/api/auth/users/someother@test.com/activate",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_user_as_admin(client, admin_user, regular_user):
    """Test admin can delete a user"""
    admin_token = create_access_token({"sub": admin_user["_id"], "role": admin_user["role"]})
    response = client.delete(
        f"/api/auth/users/{regular_user['email']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_user_as_regular_user(client, regular_user):
    """Test regular user cannot delete another user"""
    user_token = create_access_token({"sub": regular_user["_id"], "role": regular_user["role"]})
    response = client.delete(
        "/api/auth/users/someother@test.com",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_nonexistent_user(client, admin_user):
    """Test deleting a non-existent user"""
    admin_token = create_access_token({"sub": admin_user["_id"], "role": admin_user["role"]})
    response = client.delete(
        "/api/auth/users/nonexistent@test.com",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
