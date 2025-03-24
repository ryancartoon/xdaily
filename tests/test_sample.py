import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_generate_reports():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/generate-reports")
        
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "Reports generated successfully" in response.json()["message"]