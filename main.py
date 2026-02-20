#!/usr/bin/env python3
"""
Productivity CLI — manage classes, assignments & tests, then generate AI study plans.

Usage:
    python main.py --help
    python main.py class add "Calculus II"
    python main.py assignment add "Problem Set 3" --class 1 --due 2026-03-01 --hours 3
    python main.py test add "Midterm" --class 1 --date 2026-03-10 --hours 6
    python main.py plan generate
"""
import sys
from datetime import date

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.markdown import Markdown

import db
import models as m
from ai_planner import generate_study_plan

console = Console()

PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}
PRIORITY_LABEL = {1: "[dim]Low[/dim]", 2: "[yellow]Medium[/yellow]", 3: "[red]High[/red]"}
IMPORTANCE_LABEL = {1: "[dim]Low[/dim]", 2: "[yellow]Medium[/yellow]", 3: "[red]High[/red]"}
COLORS = ["cyan", "magenta", "green", "yellow", "blue", "red"]


def _init():
    db.init_db()


# ── Root ───────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """AI-powered productivity & study planner."""
    _init()


# ── Class commands ─────────────────────────────────────────────────────────

@cli.group("class")
def class_group():
    """Manage classes/courses."""


@class_group.command("add")
@click.argument("name")
@click.option("--desc", default="", help="Short description")
@click.option(
    "--color",
    default="cyan",
    type=click.Choice(COLORS, case_sensitive=False),
    help="Display color",
)
def class_add(name, desc, color):
    """Add a new class."""
    try:
        cid = m.add_class(name, desc, color)
        console.print(f"[green]✓[/green] Added class [bold]{name}[/bold] (ID: {cid})")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@class_group.command("list")
def class_list():
    """List all classes."""
    classes = m.list_classes()
    if not classes:
        console.print("[dim]No classes yet. Add one with: class add <name>[/dim]")
        return
    table = Table(title="Classes", show_lines=True)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    for c in classes:
        table.add_row(str(c["id"]), f"[{c['color']}]{c['name']}[/{c['color']}]", c["description"])
    console.print(table)


@class_group.command("delete")
@click.argument("class_id", type=int)
def class_delete(class_id):
    """Delete a class (and all its assignments/tests)."""
    cls = m.get_class(class_id)
    if not cls:
        console.print(f"[red]No class with ID {class_id}[/red]")
        sys.exit(1)
    if not click.confirm(f"Delete '{cls['name']}' and all related data?"):
        return
    m.delete_class(class_id)
    console.print(f"[green]✓[/green] Deleted class '{cls['name']}'")


# ── Assignment-Type commands ───────────────────────────────────────────────

@cli.group("type")
def type_group():
    """Manage assignment types (e.g. Homework, Quiz)."""


@type_group.command("list")
def type_list():
    """List assignment types."""
    types = m.list_assignment_types()
    table = Table(title="Assignment Types")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name")
    table.add_column("Weight", justify="right")
    for t in types:
        table.add_row(str(t["id"]), t["name"], f"{t['weight']:.2f}")
    console.print(table)


@type_group.command("add")
@click.argument("name")
@click.option("--weight", default=1.0, type=float, help="Relative weight (default 1.0)")
def type_add(name, weight):
    """Add a custom assignment type."""
    tid = m.add_assignment_type(name, weight)
    console.print(f"[green]✓[/green] Added type '{name}' with weight {weight} (ID: {tid})")


# ── Assignment commands ────────────────────────────────────────────────────

@cli.group("assignment")
def assignment_group():
    """Manage assignments."""


@assignment_group.command("add")
@click.argument("title")
@click.option("--class", "class_id", required=True, type=int, help="Class ID")
@click.option(
    "--due",
    required=True,
    help="Due date (YYYY-MM-DD)",
    metavar="DATE",
)
@click.option("--type", "type_id", type=int, default=None, help="Assignment type ID")
@click.option("--hours", default=1.0, type=float, help="Estimated hours to complete")
@click.option(
    "--priority",
    default="medium",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
)
@click.option("--notes", default="", help="Any extra notes")
def assignment_add(title, class_id, due, type_id, hours, priority, notes):
    """Add an assignment."""
    if not m.get_class(class_id):
        console.print(f"[red]No class with ID {class_id}. Use 'class list' to see classes.[/red]")
        sys.exit(1)
    try:
        date.fromisoformat(due)
    except ValueError:
        console.print("[red]Date must be in YYYY-MM-DD format.[/red]")
        sys.exit(1)
    aid = m.add_assignment(
        title, class_id, due, type_id, hours, PRIORITY_MAP[priority.lower()], notes
    )
    console.print(f"[green]✓[/green] Added assignment '{title}' due {due} (ID: {aid})")


@assignment_group.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include completed assignments")
def assignment_list(show_all):
    """List assignments."""
    assignments = m.list_assignments(include_completed=show_all)
    if not assignments:
        console.print("[dim]No assignments found.[/dim]")
        return
    table = Table(title="Assignments", show_lines=True)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Class", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Due Date")
    table.add_column("Hours", justify="right")
    table.add_column("Priority")
    table.add_column("Done", justify="center")
    for a in assignments:
        done_str = "[green]✓[/green]" if a["completed"] else ""
        due_style = ""
        try:
            days_left = (date.fromisoformat(a["due_date"]) - date.today()).days
            if days_left < 0:
                due_style = "[red]"
            elif days_left <= 2:
                due_style = "[yellow]"
        except ValueError:
            pass
        table.add_row(
            str(a["id"]),
            a["class_name"],
            a["title"],
            a.get("type_name") or "—",
            f"{due_style}{a['due_date']}",
            str(a["est_hours"]),
            PRIORITY_LABEL[a["priority"]],
            done_str,
        )
    console.print(table)


@assignment_group.command("done")
@click.argument("assignment_id", type=int)
def assignment_done(assignment_id):
    """Mark an assignment as complete."""
    m.complete_assignment(assignment_id)
    console.print(f"[green]✓[/green] Marked assignment {assignment_id} as complete.")


@assignment_group.command("delete")
@click.argument("assignment_id", type=int)
def assignment_delete(assignment_id):
    """Delete an assignment."""
    m.delete_assignment(assignment_id)
    console.print(f"[green]✓[/green] Deleted assignment {assignment_id}.")


# ── Test commands ──────────────────────────────────────────────────────────

@cli.group("test")
def test_group():
    """Manage tests and exams."""


@test_group.command("add")
@click.argument("title")
@click.option("--class", "class_id", required=True, type=int, help="Class ID")
@click.option("--date", "test_date", required=True, help="Test date (YYYY-MM-DD)", metavar="DATE")
@click.option("--topics", default="", help="Comma-separated list of topics")
@click.option("--hours", default=2.0, type=float, help="Estimated study hours needed")
@click.option(
    "--importance",
    default="medium",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
)
def test_add(title, class_id, test_date, topics, hours, importance):
    """Add a test or exam."""
    if not m.get_class(class_id):
        console.print(f"[red]No class with ID {class_id}.[/red]")
        sys.exit(1)
    try:
        date.fromisoformat(test_date)
    except ValueError:
        console.print("[red]Date must be in YYYY-MM-DD format.[/red]")
        sys.exit(1)
    tid = m.add_test(title, class_id, test_date, topics, hours, PRIORITY_MAP[importance.lower()])
    console.print(f"[green]✓[/green] Added test '{title}' on {test_date} (ID: {tid})")


@test_group.command("list")
@click.option("--all", "show_all", is_flag=True, help="Include past tests")
def test_list(show_all):
    """List upcoming tests."""
    tests = m.list_tests(upcoming_only=not show_all)
    if not tests:
        console.print("[dim]No upcoming tests.[/dim]")
        return
    table = Table(title="Tests / Exams", show_lines=True)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Class", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Date")
    table.add_column("Study Hrs", justify="right")
    table.add_column("Importance")
    table.add_column("Topics")
    for t in tests:
        table.add_row(
            str(t["id"]),
            t["class_name"],
            t["title"],
            t["date"],
            str(t["est_hours"]),
            IMPORTANCE_LABEL[t["importance"]],
            t["topics"] or "—",
        )
    console.print(table)


@test_group.command("delete")
@click.argument("test_id", type=int)
def test_delete(test_id):
    """Delete a test."""
    m.delete_test(test_id)
    console.print(f"[green]✓[/green] Deleted test {test_id}.")


# ── Plan commands ──────────────────────────────────────────────────────────

@cli.group("plan")
def plan_group():
    """Generate and view AI study plans."""


@plan_group.command("generate")
@click.option("--days", default=14, type=int, help="How many days ahead to plan for")
@click.option(
    "--hours",
    default=4.0,
    type=float,
    help="Available study hours per day",
)
@click.option("--save/--no-save", default=True, help="Save plan to history")
def plan_generate(days, hours, save):
    """Generate an AI-powered study plan using Claude."""
    assignments = m.list_assignments(include_completed=False)
    tests = m.list_tests(upcoming_only=True)

    if not assignments and not tests:
        console.print(
            Panel(
                "[yellow]You have no upcoming assignments or tests.\n"
                "Add some first with:[/yellow]\n"
                "  [bold]assignment add[/bold] <title> --class <id> --due YYYY-MM-DD\n"
                "  [bold]test add[/bold] <title> --class <id> --date YYYY-MM-DD",
                title="Nothing to plan",
            )
        )
        return

    console.print(
        Panel(
            f"[cyan]Generating study plan for the next [bold]{days} days[/bold] "
            f"with [bold]{hours}h/day[/bold] available...[/cyan]\n"
            "[dim]Powered by Claude claude-opus-4-6 with adaptive thinking[/dim]",
            title="AI Study Planner",
        )
    )
    console.print()

    plan_chunks = []
    try:
        for chunk in generate_study_plan(days_ahead=days, daily_hours=hours):
            console.print(chunk, end="", markup=False)
            plan_chunks.append(chunk)
        console.print()  # newline after streaming
    except RuntimeError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        sys.exit(1)

    if save and plan_chunks:
        plan_text = "".join(plan_chunks)
        plan_id = m.save_study_plan(plan_text)
        console.print(f"\n[dim]Plan saved (ID: {plan_id}). View with: plan view {plan_id}[/dim]")


@plan_group.command("list")
def plan_list():
    """List recent study plans."""
    plans = m.list_study_plans()
    if not plans:
        console.print("[dim]No saved plans yet.[/dim]")
        return
    table = Table(title="Saved Study Plans")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Created At")
    table.add_column("Preview")
    for p in plans:
        table.add_row(str(p["id"]), p["created_at"], p["preview"] + "…")
    console.print(table)


@plan_group.command("view")
@click.argument("plan_id", type=int)
def plan_view(plan_id):
    """View a saved study plan."""
    plan = m.get_study_plan(plan_id)
    if not plan:
        console.print(f"[red]No plan with ID {plan_id}[/red]")
        sys.exit(1)
    console.print(Panel(Markdown(plan["plan_text"]), title=f"Study Plan #{plan_id} — {plan['created_at']}"))


# ── Status overview ────────────────────────────────────────────────────────

@cli.command("status")
def status():
    """Show a quick overview of your workload."""
    classes = m.list_classes()
    assignments = m.list_assignments(include_completed=False)
    tests = m.list_tests(upcoming_only=True)

    today = date.today()

    overdue = [a for a in assignments if date.fromisoformat(a["due_date"]) < today]
    due_soon = [
        a for a in assignments
        if 0 <= (date.fromisoformat(a["due_date"]) - today).days <= 3
    ]

    console.print(Panel(
        f"[bold]Classes:[/bold] {len(classes)}\n"
        f"[bold]Pending assignments:[/bold] {len(assignments)}"
        + (f"  [red]({len(overdue)} overdue!)[/red]" if overdue else "")
        + (f"  [yellow]({len(due_soon)} due within 3 days)[/yellow]" if due_soon else "")
        + f"\n[bold]Upcoming tests:[/bold] {len(tests)}",
        title="[bold cyan]Productivity Status[/bold cyan]",
    ))

    if overdue:
        console.print("\n[red bold]Overdue Assignments:[/red bold]")
        for a in overdue:
            console.print(f"  ✗ [{a['class_name']}] {a['title']} (was due {a['due_date']})")

    if due_soon:
        console.print("\n[yellow bold]Due Within 3 Days:[/yellow bold]")
        for a in due_soon:
            days = (date.fromisoformat(a["due_date"]) - today).days
            label = "today" if days == 0 else f"in {days}d"
            console.print(f"  ⚡ [{a['class_name']}] {a['title']} ({label})")

    if tests:
        next_test = tests[0]
        days_to_test = (date.fromisoformat(next_test["date"]) - today).days
        console.print(
            f"\n[cyan bold]Next test:[/cyan bold] [{next_test['class_name']}] "
            f"{next_test['title']} on {next_test['date']} "
            f"({'today' if days_to_test == 0 else f'in {days_to_test} days'})"
        )


if __name__ == "__main__":
    cli()
