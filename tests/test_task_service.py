from sqlalchemy import event

from app.models import Tag, Task
from app.services import task_service


def test_list_tasks_loads_tags_without_n_plus_one(db_session):
    # 이슈 #1 회귀 테스트: 할 일 개수와 상관없이 쿼리가 2회(할 일 1회 + 태그 1회)여야 합니다.
    tags = [Tag(name=f"tag{i}") for i in range(3)]
    for i in range(20):
        db_session.add(Task(title=f"할 일 {i}", tags=tags[: i % 3 + 1]))
    db_session.commit()
    db_session.expire_all()

    statements: list[str] = []

    def count(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count)
    try:
        tasks = task_service.list_tasks(db_session)
        tag_names = [[tag.name for tag in task.tags] for task in tasks]
    finally:
        event.remove(engine, "before_cursor_execute", count)

    assert len(tasks) == 20
    assert all(tag_names)
    assert len(statements) == 2, statements
