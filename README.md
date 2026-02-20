# AI Study Planner

A command-line productivity system that tracks classes, assignments, and tests, then uses **Claude claude-opus-4-6** (with adaptive thinking) to generate optimal, day-by-day study schedules.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # required for AI plan generation
```

## Quick Start

```bash
# 1. Add your classes
python main.py class add "Calculus II" --desc "Integrals and series"
python main.py class add "Algorithms"  --desc "CS theory"

# 2. Check class IDs
python main.py class list

# 3. Add assignments
python main.py assignment add "Problem Set 5" --class 1 --due 2026-03-01 --hours 3 --priority high

# 4. Add tests
python main.py test add "Midterm" --class 1 --date 2026-03-10 --hours 8 --importance high \
  --topics "Integration, Series, Limits"

# 5. Check your workload
python main.py status

# 6. Generate an AI study plan
python main.py plan generate --days 14 --hours 4
```

## Commands

| Command | Description |
|---|---|
| `class add <name>` | Add a course |
| `class list` | List all courses |
| `class delete <id>` | Delete a course and all related data |
| `assignment add <title>` | Add an assignment |
| `assignment list` | List pending assignments (add `--all` for completed) |
| `assignment done <id>` | Mark assignment complete |
| `assignment delete <id>` | Delete an assignment |
| `test add <title>` | Add a test/exam |
| `test list` | List upcoming tests |
| `test delete <id>` | Delete a test |
| `type list` | List assignment types (Homework, Quiz, Project, …) |
| `type add <name>` | Add a custom assignment type |
| `plan generate` | Generate AI study plan with Claude |
| `plan list` | List saved plans |
| `plan view <id>` | View a saved plan |
| `status` | Quick workload overview |

## Options for `plan generate`

| Flag | Default | Description |
|---|---|---|
| `--days` | 14 | How many days ahead to plan for |
| `--hours` | 4.0 | Available study hours per day |
| `--no-save` | — | Don't save the plan to history |

## Priority / Importance Levels

- `low` — minor assignments, low-stakes
- `medium` — standard assignments (default)
- `high` — heavily weighted or time-sensitive

## Data Storage

Plans and data are stored in `~/.productivity.db` (SQLite). Override with:

```bash
export PRODUCTIVITY_DB=/path/to/my.db
```
