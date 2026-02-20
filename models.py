"""Simple data-access helpers returning dicts."""
from datetime import date
from db import get_conn


# ── Classes ────────────────────────────────────────────────────────────────

def add_class(name: str, description: str = "", color: str = "cyan") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO classes (name, description, color) VALUES (?, ?, ?)",
            (name, description, color),
        )
        return cur.lastrowid


def list_classes() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM classes ORDER BY name")]


def get_class(class_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM classes WHERE id=?", (class_id,)).fetchone()
        return dict(row) if row else None


def delete_class(class_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM classes WHERE id=?", (class_id,))


# ── Assignment Types ───────────────────────────────────────────────────────

def add_assignment_type(name: str, weight: float = 1.0) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO assignment_types (name, weight) VALUES (?, ?)", (name, weight)
        )
        return cur.lastrowid


def list_assignment_types() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM assignment_types ORDER BY weight")]


def get_assignment_type(type_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM assignment_types WHERE id=?", (type_id,)
        ).fetchone()
        return dict(row) if row else None


# ── Assignments ────────────────────────────────────────────────────────────

def add_assignment(
    title: str,
    class_id: int,
    due_date: str,
    type_id: int | None = None,
    est_hours: float = 1.0,
    priority: int = 2,
    notes: str = "",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO assignments
               (title, class_id, type_id, due_date, est_hours, priority, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, class_id, type_id, due_date, est_hours, priority, notes),
        )
        return cur.lastrowid


def list_assignments(include_completed: bool = False) -> list[dict]:
    with get_conn() as conn:
        query = """
            SELECT a.*, c.name AS class_name, t.name AS type_name
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            LEFT JOIN assignment_types t ON a.type_id = t.id
            {where}
            ORDER BY a.due_date, a.priority DESC
        """
        where = "" if include_completed else "WHERE a.completed = 0"
        return [dict(r) for r in conn.execute(query.format(where=where))]


def complete_assignment(assignment_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE assignments SET completed=1 WHERE id=?", (assignment_id,)
        )


def delete_assignment(assignment_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))


# ── Tests ──────────────────────────────────────────────────────────────────

def add_test(
    title: str,
    class_id: int,
    date: str,
    topics: str = "",
    est_hours: float = 2.0,
    importance: int = 2,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO tests (title, class_id, date, topics, est_hours, importance)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, class_id, date, topics, est_hours, importance),
        )
        return cur.lastrowid


def list_tests(upcoming_only: bool = True) -> list[dict]:
    with get_conn() as conn:
        query = """
            SELECT t.*, c.name AS class_name
            FROM tests t
            JOIN classes c ON t.class_id = c.id
            {where}
            ORDER BY t.date, t.importance DESC
        """
        today = date.today().isoformat()
        where = f"WHERE t.date >= '{today}'" if upcoming_only else ""
        return [dict(r) for r in conn.execute(query.format(where=where))]


def delete_test(test_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM tests WHERE id=?", (test_id,))


# ── Study Plans ────────────────────────────────────────────────────────────

def save_study_plan(plan_text: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO study_plans (plan_text) VALUES (?)", (plan_text,)
        )
        return cur.lastrowid


def list_study_plans(limit: int = 5) -> list[dict]:
    with get_conn() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT id, created_at, substr(plan_text,1,100) AS preview "
                "FROM study_plans ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        ]


def get_study_plan(plan_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM study_plans WHERE id=?", (plan_id,)
        ).fetchone()
        return dict(row) if row else None
