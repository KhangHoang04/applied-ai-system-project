"""
PawPal+ RAG Demo - End-to-End Demonstration

Shows how the RAG system provides AI-powered pet care recommendations.
"""

import os
from rag_system import get_rag_system
from pawpal_system import Owner, Pet, Task, Scheduler
from datetime import date, timedelta


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_tasks(tasks: list, title: str = "Tasks"):
    """Print formatted task list."""
    print(f"\n{title}:")
    print(f"{'-'*80}")
    for i, task in enumerate(tasks, 1):
        time_str = task.scheduled_time if task.scheduled_time else "flexible"
        print(f"{i}. {task.title:<25} | {time_str:<10} | {task.display_priority():<15} | {task.duration_minutes}min | {task.display_category()}")
    print(f"{'-'*80}\n")


def demo_scenario_1():
    """Scenario 1: Diabetic Dog - Critical Medication Timing"""
    print_header("Scenario 1: Diabetic Dog with Insulin Requirements")

    # Create owner and pet
    owner = Owner(name="Sarah", available_minutes=240)
    max_dog = Pet(
        name="Max",
        species="dog",
        age=8,
        special_needs="diabetic, requires insulin twice daily"
    )

    # Add tasks
    tasks = [
        Task("Morning insulin", 5, "high", "medicine", "Max", scheduled_time="08:00", frequency="daily", due_date=date.today()),
        Task("Morning feeding", 10, "high", "feed", "Max", scheduled_time="07:55", frequency="daily", due_date=date.today()),
        Task("Walk", 30, "medium", "walk", "Max", scheduled_time="09:00"),
        Task("Evening feeding", 10, "high", "feed", "Max", scheduled_time="19:55", frequency="daily", due_date=date.today()),
        Task("Evening insulin", 5, "high", "medicine", "Max", scheduled_time="20:00", frequency="daily", due_date=date.today()),
        Task("Playtime", 20, "medium", "enrichment", "Max"),
    ]

    max_dog.tasks = tasks
    owner.add_pet(max_dog)

    print(f"👤 Owner: {owner.name}")
    print(f"   Available time: {owner.available_minutes} minutes/day")
    print(f"\n🐕 Pet: {max_dog.name}")
    print(f"   Species: {max_dog.species.capitalize()}")
    print(f"   Age: {max_dog.age} years")
    print(f"   Special needs: {max_dog.special_needs}")

    print_tasks(tasks, "Scheduled Tasks")

    # Get AI recommendations
    print("🤖 Getting AI-powered recommendations...")
    rag = get_rag_system()

    task_dicts = [
        {
            'title': t.title,
            'category': t.category,
            'priority': t.priority,
            'duration_minutes': t.duration_minutes,
            'scheduled_time': t.scheduled_time
        }
        for t in tasks
    ]

    result = rag.get_schedule_recommendations(
        pet_name=max_dog.name,
        species=max_dog.species,
        age=max_dog.age,
        special_needs=max_dog.special_needs,
        tasks=task_dicts,
        available_minutes=owner.available_minutes
    )

    print("\n📋 AI RECOMMENDATIONS:")
    print("-" * 80)
    print(result['recommendations'])
    print("-" * 80)

    if result.get('warnings'):
        print("\n⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"   • {warning}")

    print(f"\n🎯 Confidence Score: {result.get('confidence', 0.0):.2f}/1.00")

    # Evaluate schedule quality
    evaluation = rag.evaluate_schedule_quality(task_dicts, max_dog.species)
    print(f"\n📊 Schedule Quality: {evaluation['grade']}")
    print(f"   Completeness: {evaluation['scores']['completeness']:.1%}")
    print(f"   Timing: {evaluation['scores']['timing']:.1%}")
    print(f"   Priority Alignment: {evaluation['scores']['priority_alignment']:.1%}")

    if evaluation['suggestions']:
        print("\n💡 Suggestions:")
        for suggestion in evaluation['suggestions']:
            print(f"   • {suggestion}")


def demo_scenario_2():
    """Scenario 2: Indoor Cat - Mental Enrichment Focus"""
    print_header("Scenario 2: Indoor Cat Needing Mental Stimulation")

    owner = Owner(name="Alex", available_minutes=120)
    shadow = Pet(
        name="Shadow",
        species="cat",
        age=3,
        special_needs="indoor only, prone to boredom"
    )

    tasks = [
        Task("Morning play session", 15, "high", "enrichment", "Shadow", scheduled_time="08:00"),
        Task("Breakfast", 5, "high", "feed", "Shadow", scheduled_time="07:30"),
        Task("Puzzle feeder", 10, "medium", "enrichment", "Shadow"),
        Task("Litter box cleaning", 5, "high", "other", "Shadow", scheduled_time="09:00"),
        Task("Evening play", 15, "high", "enrichment", "Shadow", scheduled_time="19:00"),
        Task("Dinner", 5, "high", "feed", "Shadow", scheduled_time="18:30"),
        Task("Grooming", 10, "low", "grooming", "Shadow"),
    ]

    shadow.tasks = tasks
    owner.add_pet(shadow)

    print(f"👤 Owner: {owner.name}")
    print(f"   Available time: {owner.available_minutes} minutes/day")
    print(f"\n🐱 Pet: {shadow.name}")
    print(f"   Species: {shadow.species.capitalize()}")
    print(f"   Age: {shadow.age} years")
    print(f"   Special needs: {shadow.special_needs}")

    print_tasks(tasks, "Scheduled Tasks")

    # Get AI recommendations
    print("🤖 Getting AI-powered recommendations...")
    rag = get_rag_system()

    task_dicts = [
        {
            'title': t.title,
            'category': t.category,
            'priority': t.priority,
            'duration_minutes': t.duration_minutes,
            'scheduled_time': t.scheduled_time
        }
        for t in tasks
    ]

    result = rag.get_schedule_recommendations(
        pet_name=shadow.name,
        species=shadow.species,
        age=shadow.age,
        special_needs=shadow.special_needs,
        tasks=task_dicts,
        available_minutes=owner.available_minutes
    )

    print("\n📋 AI RECOMMENDATIONS:")
    print("-" * 80)
    print(result['recommendations'])
    print("-" * 80)

    if result.get('warnings'):
        print("\n⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"   • {warning}")

    print(f"\n🎯 Confidence Score: {result.get('confidence', 0.0):.2f}/1.00")

    # Evaluate schedule quality
    evaluation = rag.evaluate_schedule_quality(task_dicts, shadow.species)
    print(f"\n📊 Schedule Quality: {evaluation['grade']}")
    print(f"   Overall Score: {evaluation['scores']['overall']:.1%}")


def demo_scenario_3():
    """Scenario 3: High-Energy Puppy - Exercise Limits"""
    print_header("Scenario 3: Young Puppy - Age-Appropriate Exercise")

    owner = Owner(name="Mike", available_minutes=200)
    buddy = Pet(
        name="Buddy",
        species="dog",
        age=0.5,  # 6 months
        special_needs="puppy, Golden Retriever, still growing"
    )

    tasks = [
        Task("Morning walk", 25, "high", "walk", "Buddy", scheduled_time="07:00"),
        Task("Breakfast", 10, "high", "feed", "Buddy", scheduled_time="07:30"),
        Task("Training session", 10, "high", "enrichment", "Buddy", scheduled_time="10:00"),
        Task("Midday feeding", 10, "high", "feed", "Buddy", scheduled_time="13:00"),
        Task("Afternoon walk", 25, "high", "walk", "Buddy", scheduled_time="16:00"),
        Task("Socialization time", 30, "medium", "enrichment", "Buddy"),
        Task("Dinner", 10, "high", "feed", "Buddy", scheduled_time="18:30"),
        Task("Evening play", 15, "medium", "enrichment", "Buddy"),
    ]

    buddy.tasks = tasks
    owner.add_pet(buddy)

    print(f"👤 Owner: {owner.name}")
    print(f"   Available time: {owner.available_minutes} minutes/day")
    print(f"\n🐕 Pet: {buddy.name}")
    print(f"   Species: {buddy.species.capitalize()}")
    print(f"   Age: {buddy.age * 12:.0f} months")
    print(f"   Special needs: {buddy.special_needs}")

    print_tasks(tasks, "Scheduled Tasks")

    # Get AI recommendations
    print("🤖 Getting AI-powered recommendations...")
    rag = get_rag_system()

    task_dicts = [
        {
            'title': t.title,
            'category': t.category,
            'priority': t.priority,
            'duration_minutes': t.duration_minutes,
            'scheduled_time': t.scheduled_time
        }
        for t in tasks
    ]

    result = rag.get_schedule_recommendations(
        pet_name=buddy.name,
        species=buddy.species,
        age=buddy.age,
        special_needs=buddy.special_needs,
        tasks=task_dicts,
        available_minutes=owner.available_minutes
    )

    print("\n📋 AI RECOMMENDATIONS:")
    print("-" * 80)
    print(result['recommendations'])
    print("-" * 80)

    if result.get('warnings'):
        print("\n⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"   • {warning}")

    print(f"\n🎯 Confidence Score: {result.get('confidence', 0.0):.2f}/1.00")

    # Evaluate schedule quality
    evaluation = rag.evaluate_schedule_quality(task_dicts, buddy.species)
    print(f"\n📊 Schedule Quality: {evaluation['grade']}")


def main():
    """Run all demo scenarios."""
    print("\n" + "="*80)
    print("  PawPal+ RAG System - End-to-End Demonstration")
    print("  Evidence-Based Pet Care Recommendations")
    print("="*80)

    api_key_available = bool(os.getenv("ANTHROPIC_API_KEY"))
    print(f"\n🔑 API Status: {'✅ Available' if api_key_available else '⚠️  Not set (using fallback mode)'}")

    if not api_key_available:
        print("\nℹ️  To see AI-powered recommendations, set your API key:")
        print("   export ANTHROPIC_API_KEY='your-key-here'\n")
        print("   Without the API key, you'll see basic rule-based recommendations.\n")

    # Run scenarios
    demo_scenario_1()
    input("\n\nPress Enter to continue to Scenario 2...")

    demo_scenario_2()
    input("\n\nPress Enter to continue to Scenario 3...")

    demo_scenario_3()

    print("\n" + "="*80)
    print("  Demo Complete!")
    print("="*80)
    print("\n✨ The RAG system successfully:")
    print("   1. Retrieved relevant pet care knowledge from the knowledge base")
    print("   2. Generated evidence-based recommendations using AI")
    print("   3. Provided schedule quality evaluation with actionable feedback")
    print("   4. Identified critical warnings for pet health and safety")
    print("\n💡 Next steps:")
    print("   - Run 'python evaluate_rag.py' for comprehensive testing")
    print("   - Run 'streamlit run app.py' to try the interactive UI")
    print("   - Check out the knowledge base in /knowledge/ folder\n")


if __name__ == "__main__":
    main()
