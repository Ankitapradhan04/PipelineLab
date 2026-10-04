def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_uses_git_sha_env(client, monkeypatch):
    monkeypatch.setenv("GIT_SHA", "abc1234")
    body = client.get("/version").json()
    assert body["commit"] == "abc1234"
    assert body["version"]


def test_version_defaults_to_local(client, monkeypatch):
    monkeypatch.delenv("GIT_SHA", raising=False)
    assert client.get("/version").json()["commit"] == "local"


def test_create_and_fetch_task(client):
    created = client.post("/tasks", json={"title": "  ship it  ", "priority": "high"})
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "ship it"
    assert body["done"] is False

    fetched = client.get(f"/tasks/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["priority"] == "high"


def test_create_rejects_empty_title(client):
    assert client.post("/tasks", json={"title": "   "}).status_code == 422


def test_create_rejects_unknown_priority(client):
    assert client.post("/tasks", json={"title": "x", "priority": "urgent"}).status_code == 422


def test_list_with_done_filter(client):
    first = client.post("/tasks", json={"title": "a"}).json()
    client.post("/tasks", json={"title": "b"})
    client.patch(f"/tasks/{first['id']}", json={"done": True})

    assert len(client.get("/tasks").json()) == 2
    assert [t["title"] for t in client.get("/tasks?done=true").json()] == ["a"]
    assert [t["title"] for t in client.get("/tasks?done=false").json()] == ["b"]


def test_update_task(client):
    task = client.post("/tasks", json={"title": "draft"}).json()
    response = client.patch(f"/tasks/{task['id']}", json={"title": "final", "done": True})
    assert response.status_code == 200
    assert response.json()["title"] == "final"
    assert response.json()["done"] is True


def test_delete_task(client):
    task = client.post("/tasks", json={"title": "temp"}).json()
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_missing_task_returns_404_everywhere(client):
    assert client.get("/tasks/42").status_code == 404
    assert client.patch("/tasks/42", json={"done": True}).status_code == 404
    assert client.delete("/tasks/42").status_code == 404


def test_stats_route_is_not_shadowed_by_task_id(client):
    client.post("/tasks", json={"title": "a", "priority": "low"})
    response = client.get("/tasks/stats")
    assert response.status_code == 200
    assert response.json()["total"] == 1
