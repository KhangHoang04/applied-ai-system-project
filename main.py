"""CLI demo script — professional formatted output with emojis."""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITY_EMOJI, CATEGORY_EMOJI


def fmt_priority(p: str) -> str:
    return f"{PRIORITY_EMOJI.get(p, '')} {p.upper()}"


def fmt_category(c: str) -> str:
    return f"{CATEGORY_EMOJI.get(c, CATEGORY_EMOJI['other'])} {c}"


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a simple aligned table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep = "  ".join("-" * widths[i] for i in range(len(headers)))
    print(f"  {header_line}")
    print(f"  {sep}")
    for row in rows:
        print("  " + "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    mochi = Pet(name="Mochi", species="dog", age=3, special_needs=["joint supplement"])
    whiskers = Pet(name="Whiskers", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # Tasks added out of order
    mochi.add_task(Task(
        title="Fetch in the yard", duration_minutes=20,
        priority="low", category="enrichment", scheduled_time="10:00",
    ))
    mochi.add_task(Task(
        title="Morning walk", duration_minutes=30,
        priority="high", category="walk", scheduled_time="07:00",
        frequency="daily", due_date=date.today(),
    ))
    mochi.add_task(Task(
        title="Joint supplement", duration_minutes=5,
        priority="high", category="medicine", scheduled_time="07:45",
        frequency="daily", due_date=date.today(),
    ))
    whiskers.add_task(Task(
        title="Laser pointer play", duration_minutes=15,
        priority="low", category="enrichment", scheduled_time="10:00",
    ))
    whiskers.add_task(Task(
        title="Feed breakfast", duration_minutes=10,
        priority="high", category="feed", scheduled_time="08:00",
        frequency="daily", due_date=date.today(),
    ))
    whiskers.add_task(Task(
        title="Brush fur", duration_minutes=15,
        priority="medium", category="grooming",
    ))

    scheduler = Scheduler(owner)

    # --- Pets ---
    print("\U0001f43e Pets")
    for pet in owner.pets:
        print(f"  - {pet.summary()}")

    # --- Sorted by time ---
    print(f"\n\u23f0 Tasks Sorted by Time")
    rows = []
    for t in scheduler.sort_by_time():
        rows.append([
            t.scheduled_time or "flex",
            t.title,
            t.pet_name,
            fmt_priority(t.priority),
            fmt_category(t.category),
        ])
    print_table(["Time", "Task", "Pet", "Priority", "Category"], rows)

    # --- Conflict check ---
    print(f"\n\U0001f50d Conflict Check")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for w in conflicts:
            print(f"  \u26a0\ufe0f  {w}")
    else:
        print("  \u2705 No conflicts found.")

    # --- Generated schedule ---
    schedule = scheduler.generate_schedule()
    total = sum(t.duration_minutes for t in schedule)
    print(f"\n\U0001f4cb Today's Schedule ({total}/{owner.available_minutes} min)")
    rows = []
    for i, t in enumerate(schedule, 1):
        time_str = t.scheduled_time or "flex"
        freq = f" [{t.frequency}]" if t.frequency != "once" else ""
        rows.append([
            str(i),
            time_str,
            f"{t.title}{freq}",
            t.pet_name,
            f"{t.duration_minutes} min",
            fmt_priority(t.priority),
        ])
    print_table(["#", "Time", "Task", "Pet", "Duration", "Priority"], rows)

    skipped = [t for t in scheduler.tasks if not t.completed and t not in schedule]
    if skipped:
        names = ", ".join(t.title for t in skipped)
        print(f"\n  \u26a0\ufe0f  Skipped (not enough time): {names}")

    # --- Next available slot ---
    print(f"\n\U0001f4a1 Next Available Slot")
    slot = scheduler.find_next_slot(duration=15)
    if slot:
        print(f"  Next open 15-min slot starts at {slot}")
    else:
        print("  No open slots today.")

    # --- Recurring task demo ---
    print(f"\n\U0001f504 Recurring Task Demo")
    walk = next(t for t in mochi.tasks if t.title == "Morning walk")
    print(f"  Completing '{walk.title}' (due {walk.due_date}) ...")
    next_walk = scheduler.complete_task(walk)
    if next_walk:
        print(f"  \u2705 Next occurrence auto-created: due {next_walk.due_date}")
    print(f"  Mochi's task count is now {len(mochi.tasks)}")

    # --- Persistence demo ---
    print(f"\n\U0001f4be Persistence Demo")
    owner.save_to_json("data.json")
    print("  Saved owner data to data.json")
    loaded = Owner.load_from_json("data.json")
    if loaded:
        print(f"  Loaded back: {loaded.name} with {len(loaded.pets)} pets, "
              f"{len(loaded.all_tasks())} tasks")


if __name__ == "__main__":
    main()
