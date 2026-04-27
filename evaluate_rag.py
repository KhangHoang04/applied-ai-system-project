"""
Evaluation Harness for PawPal+ RAG System

Tests the RAG system's ability to provide accurate, evidence-based pet care recommendations.
"""

import os
from rag_system import PetCareRAG, get_rag_system
from datetime import date


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def run_test_case(test_name: str, rag: PetCareRAG, pet_info: dict, tasks: list, expected_keywords: list) -> dict:
    """
    Run a single RAG test case.

    Returns:
        dict with 'passed', 'score', 'recommendations', 'warnings'
    """
    print(f"📝 Test: {test_name}")
    print(f"   Pet: {pet_info['name']} ({pet_info['species']}, {pet_info['age']} years)")
    print(f"   Special needs: {pet_info['special_needs'] or 'None'}")
    print(f"   Tasks: {len(tasks)}")

    # Get recommendations
    result = rag.get_schedule_recommendations(
        pet_name=pet_info['name'],
        species=pet_info['species'],
        age=pet_info['age'],
        special_needs=pet_info['special_needs'],
        tasks=tasks,
        available_minutes=pet_info['available_minutes']
    )

    recommendations = result['recommendations'].lower()
    warnings = result.get('warnings', [])
    confidence = result.get('confidence', 0.0)

    # Check if expected keywords appear in recommendations
    matches = [kw for kw in expected_keywords if kw.lower() in recommendations]
    score = len(matches) / len(expected_keywords) if expected_keywords else 0.0
    passed = score >= 0.5  # At least 50% of expected keywords present

    print(f"   ✅ PASSED" if passed else f"   ❌ FAILED")
    print(f"   Score: {score:.1%} ({len(matches)}/{len(expected_keywords)} expected keywords found)")
    print(f"   Confidence: {confidence:.2f}")
    if warnings:
        print(f"   ⚠️  Warnings: {len(warnings)}")

    return {
        'test_name': test_name,
        'passed': passed,
        'score': score,
        'confidence': confidence,
        'recommendations': result['recommendations'],
        'warnings': warnings,
        'matches': matches
    }


def main():
    """Run comprehensive RAG evaluation tests."""

    print_section("PawPal+ RAG System Evaluation")

    # Check if API key is available
    api_key_available = bool(os.getenv("ANTHROPIC_API_KEY"))
    print(f"ANTHROPIC_API_KEY: {'✅ Available' if api_key_available else '❌ Not set (using fallback mode)'}\n")

    if not api_key_available:
        print("⚠️  Note: AI-powered recommendations require ANTHROPIC_API_KEY")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'\n")

    rag = get_rag_system()

    # Test Cases
    test_results = []

    # Test 1: Diabetic Dog (Critical Medication)
    print_section("Test 1: Diabetic Dog - Critical Medication Timing")
    test_results.append(run_test_case(
        test_name="Diabetic Dog Medication",
        rag=rag,
        pet_info={
            'name': 'Max',
            'species': 'dog',
            'age': 8,
            'special_needs': 'diabetic, requires insulin',
            'available_minutes': 180
        },
        tasks=[
            {'title': 'Morning insulin', 'category': 'medicine', 'priority': 'high', 'duration_minutes': 5},
            {'title': 'Morning feeding', 'category': 'feed', 'priority': 'high', 'duration_minutes': 10},
            {'title': 'Evening insulin', 'category': 'medicine', 'priority': 'high', 'duration_minutes': 5},
            {'title': 'Evening feeding', 'category': 'feed', 'priority': 'high', 'duration_minutes': 10},
            {'title': 'Walk', 'category': 'walk', 'priority': 'medium', 'duration_minutes': 30},
        ],
        expected_keywords=['insulin', 'exact', 'food', 'same time', 'critical', '12 hours']
    ))

    # Test 2: High-Energy Adult Dog
    print_section("Test 2: High-Energy Adult Dog - Exercise Requirements")
    test_results.append(run_test_case(
        test_name="High-Energy Dog Exercise",
        rag=rag,
        pet_info={
            'name': 'Luna',
            'species': 'dog',
            'age': 3,
            'special_needs': 'Border Collie, high energy',
            'available_minutes': 240
        },
        tasks=[
            {'title': 'Morning walk', 'category': 'walk', 'priority': 'high', 'duration_minutes': 45},
            {'title': 'Afternoon fetch', 'category': 'enrichment', 'priority': 'medium', 'duration_minutes': 30},
            {'title': 'Evening walk', 'category': 'walk', 'priority': 'high', 'duration_minutes': 45},
            {'title': 'Feeding', 'category': 'feed', 'priority': 'high', 'duration_minutes': 10},
        ],
        expected_keywords=['exercise', '60', 'minutes', 'mental', 'energy']
    ))

    # Test 3: Senior Cat with Arthritis
    print_section("Test 3: Senior Cat - Gentle Exercise & Arthritis Care")
    test_results.append(run_test_case(
        test_name="Senior Cat Arthritis",
        rag=rag,
        pet_info={
            'name': 'Whiskers',
            'species': 'cat',
            'age': 12,
            'special_needs': 'arthritis, limited mobility',
            'available_minutes': 120
        },
        tasks=[
            {'title': 'Gentle play session', 'category': 'enrichment', 'priority': 'medium', 'duration_minutes': 10},
            {'title': 'Feeding', 'category': 'feed', 'priority': 'high', 'duration_minutes': 5},
            {'title': 'Medication', 'category': 'medicine', 'priority': 'high', 'duration_minutes': 5},
            {'title': 'Grooming', 'category': 'grooming', 'priority': 'low', 'duration_minutes': 15},
        ],
        expected_keywords=['gentle', 'senior', 'arthritis', 'medication']
    ))

    # Test 4: Indoor Cat - Mental Stimulation
    print_section("Test 4: Indoor Cat - Mental Enrichment Needs")
    test_results.append(run_test_case(
        test_name="Indoor Cat Enrichment",
        rag=rag,
        pet_info={
            'name': 'Shadow',
            'species': 'cat',
            'age': 2,
            'special_needs': 'indoor only',
            'available_minutes': 90
        },
        tasks=[
            {'title': 'Morning play', 'category': 'enrichment', 'priority': 'high', 'duration_minutes': 15},
            {'title': 'Puzzle feeder', 'category': 'enrichment', 'priority': 'medium', 'duration_minutes': 10},
            {'title': 'Feeding', 'category': 'feed', 'priority': 'high', 'duration_minutes': 5},
            {'title': 'Litter box cleaning', 'category': 'other', 'priority': 'high', 'duration_minutes': 5},
        ],
        expected_keywords=['play', 'mental', 'enrichment', 'indoor']
    ))

    # Test 5: Puppy - Age-Appropriate Exercise
    print_section("Test 5: Puppy - Age-Appropriate Exercise Limits")
    test_results.append(run_test_case(
        test_name="Puppy Exercise Limits",
        rag=rag,
        pet_info={
            'name': 'Buddy',
            'species': 'dog',
            'age': 0.5,  # 6 months
            'special_needs': 'puppy, still growing',
            'available_minutes': 150
        },
        tasks=[
            {'title': 'Short walk', 'category': 'walk', 'priority': 'high', 'duration_minutes': 30},
            {'title': 'Training session', 'category': 'enrichment', 'priority': 'high', 'duration_minutes': 10},
            {'title': 'Feeding (3x daily)', 'category': 'feed', 'priority': 'high', 'duration_minutes': 15},
            {'title': 'Socialization', 'category': 'enrichment', 'priority': 'medium', 'duration_minutes': 20},
        ],
        expected_keywords=['puppy', 'short', 'growing', 'training']
    ))

    # Test 6: Knowledge Retrieval Test
    print_section("Test 6: Knowledge Base Retrieval Quality")
    print("Testing context retrieval for medication query...")
    context = rag.retrieve_relevant_context("diabetic insulin timing medication", species="dog")
    has_context = len(context) > 100
    has_insulin = 'insulin' in context.lower()
    has_timing = 'time' in context.lower() or 'exact' in context.lower()

    retrieval_score = sum([has_context, has_insulin, has_timing]) / 3
    retrieval_passed = retrieval_score >= 0.67

    print(f"   {'✅ PASSED' if retrieval_passed else '❌ FAILED'}")
    print(f"   Context length: {len(context)} chars")
    print(f"   Contains 'insulin': {'✅' if has_insulin else '❌'}")
    print(f"   Contains timing keywords: {'✅' if has_timing else '❌'}")

    test_results.append({
        'test_name': 'Knowledge Retrieval',
        'passed': retrieval_passed,
        'score': retrieval_score,
        'confidence': 1.0 if has_context else 0.0
    })

    # Summary Report
    print_section("Evaluation Summary")

    passed_count = sum(1 for r in test_results if r['passed'])
    total_count = len(test_results)
    avg_score = sum(r['score'] for r in test_results) / total_count
    avg_confidence = sum(r.get('confidence', 0.0) for r in test_results) / total_count

    print(f"📊 Test Results: {passed_count}/{total_count} passed ({passed_count/total_count:.1%})")
    print(f"📈 Average Score: {avg_score:.1%}")
    print(f"🎯 Average Confidence: {avg_confidence:.2f}")
    print(f"\nGrade: ", end="")

    if passed_count == total_count and avg_score >= 0.8:
        print("🏆 A+ (Excellent)")
    elif passed_count >= total_count * 0.8 and avg_score >= 0.7:
        print("✅ A (Very Good)")
    elif passed_count >= total_count * 0.7:
        print("✔️  B (Good)")
    elif passed_count >= total_count * 0.5:
        print("⚠️  C (Needs Improvement)")
    else:
        print("❌ F (Failed)")

    print("\n" + "=" * 80)

    # Detailed Results Table
    print("\nDetailed Results:")
    print("-" * 80)
    print(f"{'Test Name':<35} {'Pass':<6} {'Score':<8} {'Confidence':<12}")
    print("-" * 80)
    for r in test_results:
        status = "✅ PASS" if r['passed'] else "❌ FAIL"
        print(f"{r['test_name']:<35} {status:<6} {r['score']:>6.1%}   {r.get('confidence', 0.0):>6.2f}")
    print("-" * 80)

    print("\n✨ Evaluation complete!\n")

    # Return results for programmatic use
    return {
        'passed': passed_count,
        'total': total_count,
        'avg_score': avg_score,
        'avg_confidence': avg_confidence,
        'results': test_results
    }


if __name__ == "__main__":
    results = main()
