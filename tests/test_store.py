from app.models import Priority, TaskCreate, TaskUpdate
from app.store import TaskStore


def test_create_assigns_incrementing_ids():
    store = TaskStore()
    first = store.create(TaskCreate(title="one"))
    second = store.create(TaskCreate(title="two"))
    assert (first.id, second.id) == (1, 2)


def test_update_only_changes_given_fields():
    store = TaskStore()
    task = store.create(TaskCreate(title="write docs", priority=Priority.low))
    updated = store.update(task.id, TaskUpdate(done=True))
    assert updated.done is True
    assert updated.title == "write docs"
    assert updated.priority == Priority.low


def test_update_missing_task_returns_none():
    assert TaskStore().update(99, TaskUpdate(done=True)) is None


def test_delete_reports_whether_anything_was_removed():
    store = TaskStore()
    task = store.create(TaskCreate(title="temp"))
    assert store.delete(task.id) is True
    assert store.delete(task.id) is False


def test_list_filters_by_done():
    store = TaskStore()
    a = store.create(TaskCreate(title="a"))
    store.create(TaskCreate(title="b"))
    store.update(a.id, TaskUpdate(done=True))
    assert [t.title for t in store.list_tasks(done=True)] == ["a"]
    assert [t.title for t in store.list_tasks(done=False)] == ["b"]
    assert len(store.list_tasks()) == 2


def test_stats_counts_by_status_and_priority():
    store = TaskStore()
    store.create(TaskCreate(title="a", priority=Priority.high))
    b = store.create(TaskCreate(title="b", priority=Priority.high))
    store.update(b.id, TaskUpdate(done=True))
    stats = store.stats()
    assert (stats.total, stats.done, stats.open) == (2, 1, 1)
    assert stats.by_priority == {"low": 0, "medium": 0, "high": 2}
