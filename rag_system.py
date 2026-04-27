"""RAG System for PawPal+ - Retrieval-Augmented Generation for pet care advice."""

import os
from pathlib import Path
from typing import List, Dict
import anthropic


class PetCareRAG:
    """Retrieval-Augmented Generation system for evidence-based pet care recommendations."""

    def __init__(self, knowledge_dir: str = "knowledge"):
        """Initialize RAG system with knowledge base."""
        self.knowledge_dir = Path(knowledge_dir)
        self.documents = self._load_knowledge_base()
        self.client = None

        # Initialize Anthropic client if API key available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

    def _load_knowledge_base(self) -> Dict[str, str]:
        """Load all markdown files from knowledge directory."""
        documents = {}
        if not self.knowledge_dir.exists():
            return documents

        for file_path in self.knowledge_dir.glob("*.md"):
            with open(file_path, 'r') as f:
                documents[file_path.stem] = f.read()

        return documents

    def _chunk_document(self, doc: str, chunk_size: int = 500) -> List[str]:
        """Split document into overlapping chunks for better retrieval."""
        chunks = []
        lines = doc.split('\n')
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line)
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                # Keep last 2 lines for overlap
                current_chunk = current_chunk[-2:] if len(current_chunk) > 2 else []
                current_size = sum(len(l) for l in current_chunk)

            current_chunk.append(line)
            current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def retrieve_relevant_context(self, query: str, species: str = None) -> str:
        """
        Retrieve relevant pet care information based on query.

        Simple keyword-based retrieval. For production, use embeddings.
        """
        # Filter documents by species if provided
        relevant_docs = {}
        if species:
            species_key = f"{species.lower()}_care_guide"
            if species_key in self.documents:
                relevant_docs[species_key] = self.documents[species_key]
        else:
            relevant_docs = self.documents

        if not relevant_docs:
            return ""

        # Score chunks by keyword overlap
        query_terms = set(query.lower().split())
        scored_chunks = []

        for doc_name, doc_content in relevant_docs.items():
            chunks = self._chunk_document(doc_content)
            for chunk in chunks:
                chunk_terms = set(chunk.lower().split())
                score = len(query_terms & chunk_terms)
                if score > 0:
                    scored_chunks.append((score, chunk))

        # Return top 3 most relevant chunks
        scored_chunks.sort(reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:3]]

        return "\n\n---\n\n".join(top_chunks)

    def get_schedule_recommendations(
        self,
        pet_name: str,
        species: str,
        age: int,
        special_needs: str,
        tasks: List[Dict],
        available_minutes: int,
        use_agent_mode: bool = False
    ) -> Dict[str, any]:
        """
        Get AI-powered scheduling recommendations based on retrieved knowledge.

        Args:
            use_agent_mode: If True, uses agentic workflow with multi-step reasoning

        Returns:
            - recommendations: AI-generated advice
            - relevant_context: Retrieved knowledge chunks
            - warnings: Critical care warnings
            - confidence: Confidence score (0-1)
            - agent_steps: (if use_agent_mode) Observable planning steps
        """
        if not self.client:
            return {
                "recommendations": "⚠️ AI recommendations unavailable (ANTHROPIC_API_KEY not set). Using knowledge base only.",
                "relevant_context": self._get_basic_recommendations(species, special_needs, tasks),
                "warnings": [],
                "confidence": 0.0
            }

        # Use agentic workflow if requested
        if use_agent_mode:
            return self._get_recommendations_with_agent(
                pet_name, species, age, special_needs, tasks, available_minutes
            )

        # Build query from pet profile and tasks
        task_descriptions = [f"{t['title']} ({t['category']}, {t['priority']} priority)" for t in tasks[:10]]
        query = f"{species} age {age} {special_needs} tasks: {', '.join(task_descriptions)}"

        # Retrieve relevant knowledge
        context = self.retrieve_relevant_context(query, species)

        if not context:
            context = self._get_basic_recommendations(species, special_needs, tasks)

        # Generate recommendations using Claude with FEW-SHOT SPECIALIZATION
        try:
            # Few-shot examples to establish specialized veterinarian tone
            few_shot_examples = """
Example 1:
Pet: Bella (diabetic dog, 10 years)
Tasks: Insulin at 8am and 8pm, feeding before each
Response: "I'm concerned about Bella's insulin schedule - timing is absolutely critical for diabetic dogs. Here's what you need to know: insulin must be given exactly 12 hours apart (you've got this right with 8am/8pm), and she MUST eat before each dose. If Bella refuses food, never give insulin - call your vet immediately. This prevents life-threatening hypoglycemia. Your schedule looks excellent! 🎯"

Example 2:
Pet: Charlie (6-month puppy)
Tasks: Two 45-minute walks daily
Response: "I notice Charlie's walks might be too long for his age. The guideline for puppies is 5 minutes per month of age, twice daily. At 6 months, that's 30 minutes total - you're doing 90 minutes, which risks permanent joint damage while his bones are still growing. Let's dial it back to 15-20 minutes per walk. I know it's tempting to tire him out, but patience now means healthy joints for life! 🐾"

Example 3:
Pet: Luna (indoor cat)
Tasks: Feeding, litter box
Response: "Luna's basic needs are covered, but I'm worried about boredom - indoor cats need mental stimulation to thrive. Without it, you'll see destructive behavior. Add 10-15 minutes of interactive play twice daily (wand toys at dawn/dusk match their hunting instinct), plus a puzzle feeder. These aren't optional extras - they're essential for indoor cats' mental health. Trust me, a stimulated cat is a happy cat! 🐱"
"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""You are Dr. Sarah, a warm and knowledgeable veterinarian with 15 years of experience. You give evidence-based advice in a caring but direct tone - you're not afraid to flag dangerous mistakes, but you explain WHY with empathy.

{few_shot_examples}

Now, based on the following pet care guidelines and the owner's situation, provide specific scheduling recommendations in the same warm, knowledgeable veterinarian tone.

**Pet Profile:**
- Name: {pet_name}
- Species: {species}
- Age: {age} years
- Special needs: {special_needs or "None"}
- Owner's available time: {available_minutes} minutes/day

**Scheduled Tasks:**
{chr(10).join(f"• {t['title']} - {t['duration_minutes']}min ({t['category']}, {t['priority']} priority)" for t in tasks[:10])}

**Pet Care Guidelines:**
{context}

Provide:
1. **Priority Recommendations** - Which tasks are most critical for this pet's health
2. **Timing Suggestions** - Optimal times for specific tasks based on guidelines
3. **Warnings** - Any concerning gaps or conflicts with best practices
4. **Confidence Score** - How confident you are (0.0-1.0) based on available info

Format as:
RECOMMENDATIONS: [your advice]
WARNINGS: [any concerns]
CONFIDENCE: [score]"""
                }]
            )

            content = response.content[0].text

            # Parse response
            recommendations = ""
            warnings = []
            confidence = 0.8

            if "RECOMMENDATIONS:" in content:
                rec_part = content.split("RECOMMENDATIONS:")[1]
                if "WARNINGS:" in rec_part:
                    recommendations = rec_part.split("WARNINGS:")[0].strip()
                else:
                    recommendations = rec_part.strip()

            if "WARNINGS:" in content:
                warn_part = content.split("WARNINGS:")[1]
                if "CONFIDENCE:" in warn_part:
                    warn_text = warn_part.split("CONFIDENCE:")[0].strip()
                else:
                    warn_text = warn_part.strip()
                if warn_text and warn_text.lower() not in ["none", "none.", "n/a"]:
                    warnings = [warn_text]

            if "CONFIDENCE:" in content:
                conf_part = content.split("CONFIDENCE:")[1].strip()
                try:
                    confidence = float(conf_part.split()[0])
                except:
                    confidence = 0.8

            return {
                "recommendations": recommendations or content,
                "relevant_context": context,
                "warnings": warnings,
                "confidence": confidence
            }

        except Exception as e:
            return {
                "recommendations": f"⚠️ AI recommendation error: {str(e)}",
                "relevant_context": context,
                "warnings": [],
                "confidence": 0.0
            }

    def _get_recommendations_with_agent(
        self,
        pet_name: str,
        species: str,
        age: int,
        special_needs: str,
        tasks: List[Dict],
        available_minutes: int
    ) -> Dict[str, any]:
        """
        AGENTIC WORKFLOW: Multi-step reasoning with observable intermediate steps.

        Steps:
        1. PLAN: Analyze pet profile and identify key concerns
        2. RETRIEVE: Get relevant knowledge from knowledge base
        3. REASON: Generate initial recommendations
        4. CRITIQUE: Self-check recommendations for safety/completeness
        5. REFINE: Produce final recommendations with confidence score
        """
        agent_steps = []

        # STEP 1: PLAN - Analyze the situation
        task_descriptions = [f"{t['title']} ({t['category']}, {t['priority']} priority)" for t in tasks[:10]]

        planning_prompt = f"""You are a pet care planning expert. Analyze this situation and create a step-by-step plan.

**Pet Profile:**
- Name: {pet_name}
- Species: {species}
- Age: {age} years
- Special needs: {special_needs or "None"}
- Available time: {available_minutes} minutes/day

**Tasks to schedule:**
{chr(10).join(f"• {t['title']} - {t['duration_minutes']}min ({t['category']}, {t['priority']} priority)" for t in tasks[:10])}

Create a 3-step analysis plan:
1. Identify critical health/safety concerns
2. Determine priority order for tasks
3. Spot potential scheduling conflicts or gaps

Respond with: PLAN: [your 3-step analysis]"""

        try:
            plan_response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": planning_prompt}]
            )
            plan = plan_response.content[0].text
            agent_steps.append({"step": "1. PLAN", "output": plan})
        except Exception as e:
            agent_steps.append({"step": "1. PLAN", "output": f"Error: {str(e)}"})
            plan = "Plan generation failed"

        # STEP 2: RETRIEVE - Get relevant knowledge
        query = f"{species} age {age} {special_needs} tasks: {', '.join(task_descriptions)}"
        context = self.retrieve_relevant_context(query, species)

        if not context:
            context = self._get_basic_recommendations(species, special_needs, tasks)

        agent_steps.append({
            "step": "2. RETRIEVE",
            "output": f"Retrieved {len(context)} chars of relevant knowledge from {species} care guide"
        })

        # STEP 3: REASON - Generate initial recommendations
        reasoning_prompt = f"""Based on your analysis plan and the retrieved pet care guidelines, generate specific recommendations.

**Your Plan:**
{plan}

**Pet Care Guidelines:**
{context[:2000]}

Provide specific, actionable recommendations for this pet's daily schedule."""

        try:
            reasoning_response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": reasoning_prompt}]
            )
            initial_recommendations = reasoning_response.content[0].text
            agent_steps.append({"step": "3. REASON", "output": initial_recommendations})
        except Exception as e:
            agent_steps.append({"step": "3. REASON", "output": f"Error: {str(e)}"})
            initial_recommendations = "Reasoning failed"

        # STEP 4: CRITIQUE - Self-check for safety and completeness
        critique_prompt = f"""Review these pet care recommendations for safety issues and completeness.

**Recommendations:**
{initial_recommendations}

**Pet Profile:** {pet_name} ({species}, {age} years, {special_needs or 'no special needs'})

Check for:
- Missing critical tasks (medication, feeding, exercise)
- Unsafe timing (e.g., insulin without food, exercise too soon after meals)
- Age-inappropriate activities
- Conflicts with special needs

Respond with: CRITIQUE: [issues found] or CRITIQUE: No major issues"""

        try:
            critique_response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": critique_prompt}]
            )
            critique = critique_response.content[0].text
            agent_steps.append({"step": "4. CRITIQUE", "output": critique})
        except Exception as e:
            agent_steps.append({"step": "4. CRITIQUE", "output": f"Error: {str(e)}"})
            critique = "Critique failed"

        # STEP 5: REFINE - Produce final recommendations
        refine_prompt = f"""Produce final, refined recommendations based on your critique.

**Initial Recommendations:**
{initial_recommendations}

**Critique:**
{critique}

Provide:
1. FINAL RECOMMENDATIONS: [refined advice]
2. WARNINGS: [critical safety warnings, or "None"]
3. CONFIDENCE: [0.0-1.0 score]

Use few-shot specialized tone (warm, knowledgeable veterinarian)."""

        try:
            final_response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": refine_prompt}]
            )
            final_content = final_response.content[0].text
            agent_steps.append({"step": "5. REFINE", "output": final_content})

            # Parse final response
            recommendations = ""
            warnings = []
            confidence = 0.8

            if "FINAL RECOMMENDATIONS:" in final_content or "RECOMMENDATIONS:" in final_content:
                rec_marker = "FINAL RECOMMENDATIONS:" if "FINAL RECOMMENDATIONS:" in final_content else "RECOMMENDATIONS:"
                rec_part = final_content.split(rec_marker)[1]
                if "WARNINGS:" in rec_part:
                    recommendations = rec_part.split("WARNINGS:")[0].strip()
                else:
                    recommendations = rec_part.strip()

            if "WARNINGS:" in final_content:
                warn_part = final_content.split("WARNINGS:")[1]
                if "CONFIDENCE:" in warn_part:
                    warn_text = warn_part.split("CONFIDENCE:")[0].strip()
                else:
                    warn_text = warn_part.strip()
                if warn_text and warn_text.lower() not in ["none", "none.", "n/a"]:
                    warnings = [warn_text]

            if "CONFIDENCE:" in final_content:
                conf_part = final_content.split("CONFIDENCE:")[1].strip()
                try:
                    confidence = float(conf_part.split()[0])
                except:
                    confidence = 0.8

            return {
                "recommendations": recommendations or final_content,
                "relevant_context": context,
                "warnings": warnings,
                "confidence": confidence,
                "agent_steps": agent_steps  # Observable intermediate steps
            }

        except Exception as e:
            agent_steps.append({"step": "5. REFINE", "output": f"Error: {str(e)}"})
            return {
                "recommendations": f"⚠️ Error in agentic workflow: {str(e)}",
                "relevant_context": context,
                "warnings": [],
                "confidence": 0.0,
                "agent_steps": agent_steps
            }

    def _get_basic_recommendations(self, species: str, special_needs: str, tasks: List[Dict]) -> str:
        """Fallback recommendations when AI is unavailable."""
        basic_recs = []

        if species.lower() == "dog":
            basic_recs.append("Dogs need daily exercise - ensure walks are scheduled")
            basic_recs.append("Feed at consistent times, allow 30-60 min rest before exercise")
        elif species.lower() == "cat":
            basic_recs.append("Cats need 2-3 play sessions daily for mental stimulation")
            basic_recs.append("Scoop litter box at least twice daily")

        if special_needs and "diabetic" in special_needs.lower():
            basic_recs.append("⚠️ CRITICAL: Diabetic pets need meals and insulin at exact same times daily")

        task_categories = [t['category'] for t in tasks]
        if 'medicine' in task_categories:
            basic_recs.append("⚠️ Medication should be time-critical (never skip)")

        return "\n".join(f"• {rec}" for rec in basic_recs)

    def evaluate_schedule_quality(self, schedule: List[Dict], pet_species: str) -> Dict[str, any]:
        """
        Evaluate schedule quality against best practices.

        Returns scores and suggestions.
        """
        scores = {
            "completeness": 0.0,
            "timing": 0.0,
            "priority_alignment": 0.0,
            "overall": 0.0
        }

        suggestions = []

        # Check for essential task categories
        categories = set(t['category'] for t in schedule)
        essential = {'walk', 'feed'} if pet_species.lower() == 'dog' else {'feed', 'enrichment'}
        missing = essential - categories

        if not missing:
            scores["completeness"] = 1.0
        else:
            scores["completeness"] = (len(essential) - len(missing)) / len(essential)
            suggestions.append(f"Consider adding: {', '.join(missing)}")

        # Check timing appropriateness
        has_timed = any(t.get('scheduled_time') for t in schedule)
        if has_timed:
            scores["timing"] = 1.0
        else:
            scores["timing"] = 0.5
            suggestions.append("Add specific times for critical tasks (feeding, medication)")

        # Check priority alignment
        high_priority = [t for t in schedule if t.get('priority') == 'high']
        if high_priority:
            scores["priority_alignment"] = 1.0
        else:
            scores["priority_alignment"] = 0.7

        scores["overall"] = sum(scores.values()) / 3

        return {
            "scores": scores,
            "suggestions": suggestions,
            "grade": "A" if scores["overall"] > 0.9 else "B" if scores["overall"] > 0.7 else "C"
        }


# Singleton instance
_rag_instance = None

def get_rag_system() -> PetCareRAG:
    """Get or create RAG system singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = PetCareRAG()
    return _rag_instance
