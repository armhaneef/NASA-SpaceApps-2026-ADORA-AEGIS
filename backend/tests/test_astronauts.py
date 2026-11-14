"""Astronaut API behavior and validation."""

import pytest

PROFILE = {"astronaut_id": "AST-001", "name": "Mira Sen (fictional)",
           "mission_id": "MARS-SIM-01", "mission_role": "Engineer",
           "profile_metadata": {"fictional": True}}


def test_crud(client):
    assert client.get("/astronauts").json() == []
    response = client.post("/astronauts", json=PROFILE)
    assert response.status_code == 201
    assert "created_at" in response.json()
    assert client.post("/astronauts", json=PROFILE).status_code == 409
    assert client.get("/astronauts/AST-001").json()["profile_metadata"] == {"fictional": True}
    assert len(client.get("/astronauts").json()) == 1
    assert client.get("/astronauts?offset=1").json() == []
    response = client.patch("/astronauts/AST-001", json={"mission_role": "Commander"})
    assert response.status_code == 200
    assert response.json()["mission_role"] == "Commander"
    assert response.json()["name"] == PROFILE["name"]
    assert client.delete("/astronauts/AST-001").status_code == 204
    assert client.get("/astronauts/AST-001").status_code == 404


@pytest.mark.parametrize("method,payload", [("get", None), ("patch", {"name": "Test"}),
                                           ("delete", None)])
def test_missing_astronaut(client, method, payload):
    kwargs = {"json": payload} if payload else {}
    assert client.request(method, "/astronauts/missing", **kwargs).status_code == 404


@pytest.mark.parametrize("changes", [{"name": " "}, {"astronaut_id": "bad/id"},
                                     {"mission_id": ""}, {"unexpected": 1}])
def test_invalid_create(client, changes):
    assert client.post("/astronauts", json=PROFILE | changes).status_code == 422


@pytest.mark.parametrize("changes", [{}, {"name": None}, {"astronaut_id": "new"},
                                     {"profile_metadata": None}])
def test_invalid_update(client, changes):
    client.post("/astronauts", json=PROFILE)
    assert client.patch("/astronauts/AST-001", json=changes).status_code == 422
