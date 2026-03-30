"""PawPal+ system logic — core classes for pet care scheduling."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = Path("data.json")

PRIORITY_EMOJI = {"high": "\U0001f534", "medium": "\U0001f7e1", "low": "\U0001f7e2"}
CATEGORY_EMOJI = {
    "walk": "\U0001f6b6",
    "feed": "\U0001f356",
    "medicine": "\U0001f48a",
    "grooming": "\u2702\ufe0f",
    "enrichment": "\U0001f9f8",
    "other": "\U0001f4cb",
}


@dataclass
class Task:
    """A single pet care activity with priority, duration, and optional scheduling."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    category: str = "other"
    pet_name: str = ""
    completed: bool = False
    scheduled_time: str = ""        # "HH:MM" format, e.g. "08:30"
    frequency: str = "once"         # "once", "daily", or "weekly"
    due_date: date | None = None

    def mark_complete(self) -> Task | None:
        """Mark this task as completed. Returns a new Task for the next occurrence if recurring."""
        self.completed = True
        if self.frequency == "daily" and self.due_date:
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                pet_name=self.pet_name,
                scheduled_time=self.scheduled_time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly" and self.due_date:
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                category=self.category,
                pet_name=self.pet_name,
                scheduled_time=self.scheduled_time,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None

    def priority_value(self) -> int:
        """Map priority string to a numeric value (higher = more urgent)."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 0)

    def end_time_minutes(self) -> int | None:
        """Return the end time in minutes from midnight, or None if unscheduled."""
        start = self._start_minutes()
        if start is None:
            return None
        return start + self.duration_minutes

    def _start_minutes(self) -> int | None:
        """Parse scheduled_time 'HH:MM' into minutes from midnight."""
        if not self.scheduled_time:
            return None
        h, m = self.scheduled_time.split(":")
        return int(h) * 60 + int(m)

    def display_priority(self) -> str:
        """Return priority with emoji prefix."""
        emoji = PRIORITY_EMOJI.get(self.priority, "")
        return f"{emoji} {self.priority.upper()}"

    def display_category(self) -> str:
        """Return category with emoji prefix."""
        emoji = CATEGORY_EMOJI.get(self.category, CATEGORY_EMOJI["other"])
        return f"{emoji} {self.category}"

    def to_dict(self) -> dict:
        """Serialize task to a plain dictionary for JSON storage."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "pet_name": self.pet_name,
            "completed": self.completed,
            "scheduled_time": self.scheduled_time,
            "frequency": self.frequency,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        """Deserialize a task from a dictionary."""
        due = data.get("due_date")
        return cls(
            title=data["title"],
            duration_minutes=data["duration_minutes"],
            priority=data.get("priority", "medium"),
            category=data.get("category", "other"),
            pet_name=data.get("pet_name", ""),
            completed=data.get("completed", False),
            scheduled_time=data.get("scheduled_time", ""),
            frequency=data.get("frequency", "once"),
            due_date=date.fromisoformat(due) if due else None,
        )


@dataclass
class Pet:
    """A pet with profile info and its own task list."""

    name: str
    species: str
    age: int = 0
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def summary(self) -> str:
        """Return a one-line description of this pet."""
        needs = f" (needs: {', '.join(self.special_needs)})" if self.special_needs else ""
        return f"{self.name} the {self.species}, age {self.age}{needs}"

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def to_dict(self) -> dict:
        """Serialize pet to a plain dictionary for JSON storage."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "special_needs": self.special_needs,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pet:
        """Deserialize a pet from a dictionary."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            age=data.get("age", 0),
            special_needs=data.get("special_needs", []),
        )
        for td in data.get("tasks", []):
            task = Task.from_dict(td)
            task.pet_name = pet.name
            pet.tasks.append(task)
        return pet


@dataclass
class Owner:
    """A pet owner who manages multiple pets and a daily time budget."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    available_minutes: int = 120

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def all_tasks(self) -> list[Task]:
        """Collect every task across all pets."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    # ---- JSON persistence --------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize owner to a plain dictionary for JSON storage."""
        return {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        """Deserialize an owner from a dictionary."""
        owner = cls(
            name=data["name"],
            available_minutes=data.get("available_minutes", 120),
        )
        for pd in data.get("pets", []):
            owner.pets.append(Pet.from_dict(pd))
        return owner

    def save_to_json(self, path: str | Path = DATA_FILE) -> None:
        """Persist the owner, pets, and all tasks to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, path: str | Path = DATA_FILE) -> Owner | None:
        """Load an owner from a JSON file. Returns None if the file doesn't exist."""
        p = Path(path)
        if not p.exists():
            return None
        with open(p) as f:
            return cls.from_dict(json.load(f))


class Scheduler:
    """The scheduling brain — sorts, filters, detects conflicts, and plans daily tasks."""

    def __init__(self, owner: Owner, tasks: list[Task] | None = None) -> None:
        self.owner = owner
        self.tasks: list[Task] = tasks if tasks is not None else owner.all_tasks()

    # ---- Sorting -----------------------------------------------------------

    def sort_by_time(self) -> list[Task]:
        """Sort tasks by scheduled_time (HH:MM). Unscheduled tasks go to the end."""
        return sorted(
            self.tasks,
            key=lambda t: (t.scheduled_time == "", t.scheduled_time),
        )

    def sort_by_priority(self) -> list[Task]:
        """Sort tasks by priority descending (high first)."""
        return sorted(self.tasks, key=lambda t: t.priority_value(), reverse=True)

    # ---- Filtering ---------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        category: str | None = None,
    ) -> list[Task]:
        """Return tasks matching the given criteria."""
        result = self.tasks
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if category is not None:
            result = [t for t in result if t.category == category]
        return result

    # ---- Recurring tasks ---------------------------------------------------

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task complete and auto-create the next occurrence if recurring."""
        next_task = task.mark_complete()
        if next_task is not None:
            self.tasks.append(next_task)
            for pet in self.owner.pets:
                if pet.name == next_task.pet_name:
                    pet.tasks.append(next_task)
                    break
        return next_task

    # ---- Conflict detection ------------------------------------------------

    def detect_conflicts(self) -> list[str]:
        """Find tasks whose scheduled times overlap and return warning strings."""
        scheduled = [t for t in self.tasks if t.scheduled_time and not t.completed]
        scheduled.sort(key=lambda t: t.scheduled_time)
        warnings: list[str] = []
        for i in range(len(scheduled)):
            for j in range(i + 1, len(scheduled)):
                a, b = scheduled[i], scheduled[j]
                a_start = a._start_minutes()
                a_end = a.end_time_minutes()
                b_start = b._start_minutes()
                if a_start is not None and a_end is not None and b_start is not None:
                    if b_start < a_end:
                        warnings.append(
                            f"Conflict: '{a.title}' ({a.pet_name} {a.scheduled_time}\u2013"
                            f"{a_end // 60:02d}:{a_end % 60:02d}) overlaps with "
                            f"'{b.title}' ({b.pet_name} {b.scheduled_time})"
                        )
        return warnings

    # ---- Next available slot (Challenge 1) ---------------------------------

    def find_next_slot(self, duration: int, day_start: str = "06:00", day_end: str = "22:00") -> str | None:
        """Find the earliest gap in the schedule that fits *duration* minutes.

        Scans from *day_start* to *day_end*, skipping over already-occupied
        time ranges.  Returns an "HH:MM" string for the start of the gap,
        or None if no slot is available.
        """
        start_min = self._parse_time(day_start)
        end_min = self._parse_time(day_end)

        # Collect occupied intervals from pending timed tasks
        occupied: list[tuple[int, int]] = []
        for t in self.tasks:
            if t.completed or not t.scheduled_time:
                continue
            ts = t._start_minutes()
            te = t.end_time_minutes()
            if ts is not None and te is not None:
                occupied.append((ts, te))
        occupied.sort()

        cursor = start_min
        for occ_start, occ_end in occupied:
            if cursor + duration <= occ_start:
                return f"{cursor // 60:02d}:{cursor % 60:02d}"
            cursor = max(cursor, occ_end)

        # Check the remaining window after all occupied slots
        if cursor + duration <= end_min:
            return f"{cursor // 60:02d}:{cursor % 60:02d}"
        return None

    @staticmethod
    def _parse_time(hhmm: str) -> int:
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    # ---- Schedule generation -----------------------------------------------

    def generate_schedule(self) -> list[Task]:
        """Build a schedule: time-slotted tasks first (by time), then remaining by priority."""
        pending = [t for t in self.tasks if not t.completed]

        timed = sorted(
            [t for t in pending if t.scheduled_time],
            key=lambda t: t.scheduled_time,
        )
        untimed = sorted(
            [t for t in pending if not t.scheduled_time],
            key=lambda t: t.priority_value(),
            reverse=True,
        )

        schedule: list[Task] = []
        remaining = self.owner.available_minutes

        for task in timed:
            if task.duration_minutes <= remaining:
                schedule.append(task)
                remaining -= task.duration_minutes

        for task in untimed:
            if task.duration_minutes <= remaining:
                schedule.append(task)
                remaining -= task.duration_minutes

        return schedule

    def explain_plan(self, schedule: list[Task]) -> str:
        """Explain why the schedule is ordered and which tasks were included."""
        if not schedule:
            return "No tasks could be scheduled within the available time."

        total = sum(t.duration_minutes for t in schedule)
        lines = [
            f"Schedule for {self.owner.name} "
            f"({total}/{self.owner.available_minutes} min used):\n"
        ]
        for i, task in enumerate(schedule, 1):
            time_str = task.scheduled_time if task.scheduled_time else "flex"
            freq = f" [{task.frequency}]" if task.frequency != "once" else ""
            lines.append(
                f"  {i}. [{task.priority.upper()}] {task.title} "
                f"({task.pet_name}) \u2014 {task.duration_minutes} min "
                f"@ {time_str}{freq}"
            )

        skipped = [t for t in self.tasks if not t.completed and t not in schedule]
        if skipped:
            names = ", ".join(t.title for t in skipped)
            lines.append(f"\n  Skipped (not enough time): {names}")

        lines.append(
            "\nTime-slotted tasks are placed first (by clock time), "
            "then flexible tasks fill remaining time by priority."
        )
        return "\n".join(lines)
