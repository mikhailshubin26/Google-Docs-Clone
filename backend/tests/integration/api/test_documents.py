from httpx import AsyncClient


class TestCreateDocument:

    async def test_create_document_returns_201(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/v1/documents",
            json={"title": "My first doc"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "My first doc"
        assert body["revision"] == 0

    async def test_create_document_without_auth_returns_401(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/v1/documents", json={"title": "No auth"})
        assert response.status_code == 401

    async def test_creat_document_rejects_empty_file(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/v1/documents", json={"title": ""}, headers=auth_headers)
        assert response.status_code == 422

class TestListDocuments:

    async def test_list_returns_only_own_documents(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/v1/documents", json={"title": "Doc1"}, headers=auth_headers)
        await client.post("/api/v1/documents", json={"title": "Doc2"}, headers=auth_headers)

        response = await client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()

        assert len(body["items"]) == 2

    async def test_list_respects_pagination_params(self, client: AsyncClient, auth_headers: dict):
        for i in range(3):
            await client.post("/api/v1/documents", json={"title": f"Doc{i}"}, headers=auth_headers)

        response = await client.get("/api/v1/documents?limit=2&offset=0", headers=auth_headers)
        body = response.json()
        assert len(body["items"]) == 2
        assert body["limit"] == 2

class TestGetDocument:

    async def test_owner_can_get_document(self, client: AsyncClient, auth_headers: dict):
        create_response = await client.post(
            "/api/v1/documents",
            json={"title": "Readable doc"},
            headers=auth_headers,
        )
        document_id = create_response.json()["id"]
        response = await client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["content"] == ""

    async def test_get_nonexistent_document_returns_403(self, client: AsyncClient, auth_headers: dict):
        import uuid
        response = await client.get(f"/api/v1/documents/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 403

    async def test_stranger_cannot_get_document(self, client: AsyncClient, auth_headers: dict):
        create_response = await client.post(
            "/api/v1/documents",
            json={"title": "Private doc"},
            headers=auth_headers,
        )
        document_id = create_response.json()["id"]

        second_user_register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "stranger@example.com",
                "password": "password123",
                "display_name": "Stranger"},
        )

        stranger_headers = {"Authorization": f"Bearer {second_user_register.json()['access_token']}"}
        response = await client.get(f"/api/v1/documents/{document_id}", headers=stranger_headers)
        assert response.status_code == 403

class TestRenameDocument:
    async def test_owner_can_rename(self, client: AsyncClient, auth_headers: dict):
        create_response = await client.post(
            "/api/v1/documents", json={"title": "Old title"}, headers=auth_headers,
        )
        document_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/documents/{document_id}",
            json={"title": "New title"},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["title"] == "New title"

class TestDeleteDocument:

    async def test_owner_can_delete(self, client: AsyncClient, auth_headers: dict):
        create_response = await client.post(
            "/api/v1/documents", json={"title": "To be deleteed"}, headers=auth_headers,
        )
        document_id = create_response.json()["id"]
        response = await client.delete(f"/api/v1/documents/{document_id}", headers=auth_headers)
        assert response.status_code == 204

        get_response = await client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
        assert get_response.status_code == 404