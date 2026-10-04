import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status

from app import __version__
from app.models import Stats, Task, TaskCreate, TaskUpdate
from app.store import TaskStore


def get_store(request: Request) -> TaskStore:
    return request.app.state.store


StoreDep = Annotated[TaskStore, Depends(get_store)]


def create_app() -> FastAPI:
    app = FastAPI(
        title="PipelineLab",
        version=__version__,
        description="A tiny task API, built to be shipped by a GitLab CI/CD pipeline.",
    )
    app.state.store = TaskStore()

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version", tags=["meta"])
    def version() -> dict[str, str]:
        # GIT_SHA is baked into the image by the pipeline at build time.
        return {"version": __version__, "commit": os.getenv("GIT_SHA", "local")}

    @app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["tasks"])
    def create_task(data: TaskCreate, store: StoreDep) -> Task:
        return store.create(data)

    @app.get("/tasks", response_model=list[Task], tags=["tasks"])
    def list_tasks(store: StoreDep, done: bool | None = None) -> list[Task]:
        return store.list_tasks(done)

    @app.get("/tasks/stats", response_model=Stats, tags=["tasks"])
    def task_stats(store: StoreDep) -> Stats:
        return store.stats()

    @app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
    def get_task(task_id: int, store: StoreDep) -> Task:
        task = store.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.patch("/tasks/{task_id}", response_model=Task, tags=["tasks"])
    def update_task(task_id: int, data: TaskUpdate, store: StoreDep) -> Task:
        task = store.update(task_id, data)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
    def delete_task(task_id: int, store: StoreDep) -> Response:
        if not store.delete(task_id):
            raise HTTPException(status_code=404, detail="Task not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
