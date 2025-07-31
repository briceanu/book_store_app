import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app



client = TestClient(app)




@pytest.mark.asyncio
async def test_sign_in():
    async with httpx.AsyncClient() as client:
        response = await client.post(
        "http://localhost:8000/api/v1/user/sign-in",
        data={"username": "gigi", "password": "gigi123",'scope':['author']},
    )

    # Ensure it returns a successful status
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_sign_up():
    async with httpx.AsyncClient(base_url="http://localhost:8000/") as client:
        response = await client.post(
            "/api/v1/user/sign-up",
            json={'name': 'paula', 'password': 'paula123', 'scopes': ['user'],'email':'paula@gmail.com'}
        )
        assert response.status_code == 201
        assert response.json() == {"success": "Your account has been created."}
