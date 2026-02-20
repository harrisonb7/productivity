"""AI-powered study plan generation via Claude."""
import os
from datetime import date, timedelta
from typing import Generator

import anthropic

from models import list_assignments, list_tests, list_classes


def _build_context(days_ahead: int, daily_hours: float) -> str:
    today = date.today()
    cutoff = (today + timedelta(days=days_ahead)).isoformat()

    assignments = [
        a for a in list_assignments(include_completed=False)
        if a["due_date"] <= cutoff
    ]
    tests = [
        t for t in list_tests(upcoming_only=True)
        if t["date"] <= cutoff
    ]
    classes = list_classes()

    lines = [
        f"Today's date: {today.isoformat()}",
        f"Planning window: {days_ahead} days (until {cutoff})",
        f"Available study hours per day: {daily_hours}",
        "",
        "## Enrolled Classes",
    ]
    if classes:
        for c in classes:
            lines.append(f"  - {c['name']}" + (f": {c['description']}" if c["description"] else ""))
    else:
        lines.append("  (none)")

    lines += ["", "## Upcoming Assignments"]
    if assignments:
        for a in assignments:
            priority_label = {1: "Low", 2: "Medium", 3: "High"}.get(a["priority"], "Medium")
            lines.append(
                f"  - [{a['class_name']}] {a['title']} — due {a['due_date']}, "
                f"~{a['est_hours']}h, priority: {priority_label}"
                + (f", type: {a['type_name']}" if a.get("type_name") else "")
                + (f"\n    Notes: {a['notes']}" if a.get("notes") else "")
            )
    else:
        lines.append("  (none in window)")

    lines += ["", "## Upcoming Tests / Exams"]
    if tests:
        for t in tests:
            importance_label = {1: "Low", 2: "Medium", 3: "High"}.get(t["importance"], "Medium")
            lines.append(
                f"  - [{t['class_name']}] {t['title']} — date {t['date']}, "
                f"~{t['est_hours']}h to study, importance: {importance_label}"
                + (f"\n    Topics: {t['topics']}" if t.get("topics") else "")
            )
    else:
        lines.append("  (none in window)")

    return "\n".join(lines)


SYSTEM_PROMPT = """\
You are an expert academic productivity coach and study planner. Your job is to \
create a realistic, detailed, day-by-day study schedule that optimally prepares a \
student for their upcoming assignments and tests.

Guidelines:
- Spread work across available days; avoid cramming everything at the end.
- Prioritize high-priority assignments and high-importance tests.
- Account for "warm-up" review sessions before tests (start reviewing 3-5 days out for major exams).
- For assignments, allocate study sessions proportional to estimated hours.
- Leave buffer time for unexpected delays.
- Group subjects intelligently to avoid context-switching fatigue.
- Clearly label each day, list sessions in order, and include approximate hours per session.
- End with a brief summary of your scheduling strategy and any warnings (e.g., tight deadlines).
- Format the plan in clean Markdown with a day-by-day table or list.
"""


def generate_study_plan(
    days_ahead: int = 14,
    daily_hours: float = 4.0,
) -> Generator[str, None, None]:
    """Stream a study plan from Claude. Yields text chunks."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "Export it before running: export ANTHROPIC_API_KEY=sk-ant-..."
        )

    context = _build_context(days_ahead, daily_hours)
    user_message = (
        f"Please create a detailed study plan based on my current workload:\n\n{context}"
    )

    client = anthropic.Anthropic(api_key=api_key)

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            yield text
