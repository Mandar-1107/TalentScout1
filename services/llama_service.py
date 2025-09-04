import requests
import json
import random
from typing import List, Dict, Set, Optional

from models.common import ProficiencyLevel

class LlamaService:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2"
        self.asked_questions_cache = {}

    def generate_questions(self, technology: str, proficiency: ProficiencyLevel, count: int = 1, session_id: str = None) -> List[dict]:
        """Generate clean, well-formed questions"""
        
        prompt = f"""Generate 1 specific technical interview question for {technology}.

Level: {proficiency.value}
Requirements:
- Must be answerable by a {proficiency.value} level developer
- Requires detailed explanation with examples
- Tests practical {technology} knowledge
- Must end with a question mark

Question:"""
        
        try:
            response = self._call_llama(prompt)
            question_text = self._extract_clean_question(response)
            
            if question_text and len(question_text) > 15:
                return [{
                    "question_id": f"{technology}_{session_id}_{random.randint(1000,9999)}",
                    "technology": technology,
                    "question_text": question_text,
                    "question_type": "technical",
                    "difficulty_score": self._get_difficulty_score(proficiency)
                }]
            else:
                return [self._get_simple_fallback(technology, proficiency, session_id)]
                
        except Exception as e:
            print(f"Question generation failed: {e}")
            return [self._get_simple_fallback(technology, proficiency, session_id)]

    def generate_followup(self, original_question: str, candidate_answer: str, technology: str, session_id: str = None) -> str:
        """Generate clean follow-up questions"""
        
        prompt = f"""Based on this technical interview answer, ask 1 focused follow-up question.

Technology: {technology}
Previous Answer: {candidate_answer}

Generate a follow-up that:
- Explores {technology} deeper
- Tests practical application
- Asks for specific examples

Follow-up question:"""
        
        try:
            response = self._call_llama(prompt)
            followup = self._extract_clean_question(response)
            
            if followup and len(followup) > 15:
                return followup
            else:
                return self._get_simple_followup_fallback(technology, candidate_answer)
                
        except Exception:
            return self._get_simple_followup_fallback(technology, candidate_answer)

    def _extract_clean_question(self, response: str) -> str:
        """Extract clean question from LLM response"""
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        if not lines:
            return ""
        
        question = lines[0]
        
        # Remove prefixes
        prefixes = ["Question:", "Follow-up:", "1.", "2.", "3.", "-", "*"]
        for prefix in prefixes:
            if question.startswith(prefix):
                question = question[len(prefix):].strip()
        
        # Remove quotes
        if question.startswith('"') and question.endswith('"'):
            question = question[1:-1]
        
        # Ensure question mark
        if question and not question.endswith('?'):
            question += '?'
        
        return question

    def _get_difficulty_score(self, proficiency: ProficiencyLevel) -> int:
        return {
            ProficiencyLevel.BEGINNER: 3,
            ProficiencyLevel.INTERMEDIATE: 5,
            ProficiencyLevel.ADVANCED: 8
        }.get(proficiency, 5)

    def _get_simple_fallback(self, technology: str, proficiency: ProficiencyLevel, session_id: str) -> dict:
        """Simple fallback question"""
        
        templates = {
            ProficiencyLevel.BEGINNER: f"What are the key concepts every {technology} developer should understand?",
            ProficiencyLevel.INTERMEDIATE: f"Describe a challenging {technology} project and how you solved the main technical problems.",
            ProficiencyLevel.ADVANCED: f"How would you architect a scalable system using {technology}?"
        }
        
        return {
            "question_id": f"{technology}_fallback_{random.randint(1000,9999)}",
            "technology": technology,
            "question_text": templates.get(proficiency, templates[ProficiencyLevel.INTERMEDIATE]),
            "question_type": "fallback",
            "difficulty_score": self._get_difficulty_score(proficiency)
        }

    def _get_simple_followup_fallback(self, technology: str, candidate_answer: str) -> str:
        """Simple follow-up fallback"""
        
        answer_lower = candidate_answer.lower()
        
        if "project" in answer_lower:
            return f"What was the biggest technical challenge in that {technology} project?"
        elif "experience" in answer_lower:
            return f"Can you give a specific example of how you used {technology} to solve that problem?"
        elif "used" in answer_lower or "use" in answer_lower:
            return f"What best practices do you follow when working with {technology}?"
        else:
            return f"How would you explain this {technology} concept to a junior developer?"

    def _call_llama(self, prompt: str) -> str:
        """Optimized Llama call"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "top_p": 0.8,
                "num_predict": 100,
                "stop": ["\n\n", "Answer:", "Response:", "Follow-up Question:"]
            }
        }
        
        response = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=25)
        response.raise_for_status()
        return response.json().get("response", "").strip()

    def clear_session_cache(self, session_id: str):
        """Clear cache for session"""
        keys_to_remove = [key for key in self.asked_questions_cache.keys() 
                         if key.startswith(session_id)]
        for key in keys_to_remove:
            del self.asked_questions_cache[key]

    def clear_all_cache(self):
        """Clear all caches"""
        self.asked_questions_cache.clear()