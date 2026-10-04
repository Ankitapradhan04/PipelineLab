from datetime import UTC, datetime
from threading import Lock

from app.models import Priority, Stats, Task, TaskCreate, TaskUpdate


class TaskStore:
    """In-memory task storage. Thread-safe, and deliberately simple.

    Swapping this for a real database is the obvious next step, but the point of this
    project is the pipeline around the code, not the persistence layer.
    """

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        self._lock = Lock()

    def create(self, data: TaskCreate) -> Task:
        with self._lock:
            task = Task(
                id=self._next_id,
                title=data.title,
                priority=data.priority,
                created_at=datetime.now(UTC),
            )
            self._tasks[task.id] = task
            self._next_id += 1
            return task

    def list_tasks(self, done: bool | None = None) -> list[Task]:
        with self._lock:
            tasks = list(self._tasks.values())
        if done is not None:
            tasks = [t for t in tasks if t.done == done]
        return tasks

    def get(self, task_id: int) -> Task | None:
        with self._lock:
            return self._tasks.get(task_id)

    def update(self, task_id: int, data: TaskUpdate) -> Task | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            changes = data.model_dump(exclude_unset=True, exclude_none=True)
            updated = task.model_copy(update=changes)
            self._tasks[task_id] = updated
            return updated

    def delete(self, task_id: int) -> bool:
        with self._lock:
            return self._tasks.pop(task_id, None) is not None

    def stats(self) -> Stats:
        with self._lock:
            tasks = list(self._tasks.values())
        done = sum(1 for t in tasks if t.done)
        return Stats(
            total=len(tasks),
            done=done,
            open=len(tasks) - done,
            by_priority={p.value: sum(1 for t in tasks if t.priority == p) for p in Priority},
        )
