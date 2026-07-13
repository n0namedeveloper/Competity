import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_competitor(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/competitors/",
        json={
            "name": "TestCorp",
            "domain": "testcorp.com",
            "github_org": "testcorp",
            "keywords": ["testcorp"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TestCorp"
    assert data["domain"] == "testcorp.com"
    assert data["id"] is not None
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_get_competitor(async_client: AsyncClient):
    # Setup
    create_response = await async_client.post(
        "/api/v1/competitors/",
        json={"name": "GetTest"}
    )
    comp_id = create_response.json()["id"]

    # Test
    response = await async_client.get(f"/api/v1/competitors/{comp_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "GetTest"

@pytest.mark.asyncio
async def test_get_competitor_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/competitors/9999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_list_competitors(async_client: AsyncClient):
    await async_client.post("/api/v1/competitors/", json={"name": "A"})
    await async_client.post("/api/v1/competitors/", json={"name": "B"})

    response = await async_client.get("/api/v1/competitors/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Ensure order by name
    assert data[0]["name"] == "A"
    assert data[1]["name"] == "B"

@pytest.mark.asyncio
async def test_update_competitor(async_client: AsyncClient):
    # Setup
    create_response = await async_client.post(
        "/api/v1/competitors/",
        json={"name": "OldName"}
    )
    comp_id = create_response.json()["id"]

    # Update
    update_response = await async_client.put(
        f"/api/v1/competitors/{comp_id}",
        json={"name": "NewName", "is_active": False}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "NewName"
    assert data["is_active"] is False

@pytest.mark.asyncio
async def test_delete_competitor(async_client: AsyncClient):
    # Setup
    create_response = await async_client.post(
        "/api/v1/competitors/",
        json={"name": "ToDelete"}
    )
    comp_id = create_response.json()["id"]

    # Delete
    delete_response = await async_client.delete(f"/api/v1/competitors/{comp_id}")
    assert delete_response.status_code == 204

    # Verify
    get_response = await async_client.get(f"/api/v1/competitors/{comp_id}")
    assert get_response.status_code == 404
