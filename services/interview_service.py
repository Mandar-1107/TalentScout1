# services/interview_service.py
from services.llama_service import LlamaService
from services.candidate_service import CandidateService
from models.interview import InterviewSession, ConversationMessage
from models.common import ProficiencyLevel
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import traceback

class InterviewService:
    def __init__(self, db, llama_service: LlamaService, candidate_service: CandidateService):
        self.db = db
        self.collection = db.interview_sessions
        self.llama_service = llama_service
        self.candidate_service = candidate_service

    def start_interview(self, candidate_id: str) -> str:
        """Start interview and generate first question"""
        try:
            print(f"[DEBUG] Starting interview for candidate: {candidate_id}")
            session_id = uuid.uuid4().hex
            
            candidate = self.candidate_service.get_candidate(candidate_id)
            if not candidate or not candidate.tech_stack:
                return "Error: No candidate tech stack found."
            
            tech_plan = self._build_tech_plan(candidate.tech_stack)
            
            if not tech_plan:
                return "Error: No technologies found."
            
            print(f"[DEBUG] Tech plan created: {[t['name'] for t in tech_plan]}")
            
            # Clear any existing cache for this session
            self.llama_service.clear_session_cache(session_id)
            
            # Create session
            session_data = {
                "session_id": session_id,
                "candidate_id": candidate_id,
                "status": "active",
                "tech_plan": tech_plan,
                "current_tech_index": 0,
                "conversation_history": [],
                "started_at": datetime.utcnow(),
                "total_points": 0.0,
                "max_possible_points": 0.0,
                "answer_ratings": [],
                "tech_ratings": {}
            }
            
            session = InterviewSession(**session_data)
            self.collection.insert_one(session.model_dump())
            
            # Generate first question
            current_tech = tech_plan[0]
            print(f"[DEBUG] Generating first question for {current_tech['name']}")
            
            first_question = self.generate_question(
                technology=current_tech["name"], 
                proficiency=current_tech["proficiency"], 
                session_id=session_id
            )
            
            # Update question count - start with 0, will increment to 1 after first answer
            tech_plan[0]["questions_asked"] = 0
            self.collection.update_one(
                {"session_id": session_id},
                {"$set": {"tech_plan": tech_plan}}
            )
            
            welcome_content = f"""🎯 **Technical Interview Started**

Hello {candidate.full_name}! We'll cover **{len(tech_plan)} technologies**: {', '.join([t['name'] for t in tech_plan])}

**Starting with {current_tech['name']}** (Level: {current_tech['proficiency']})

**Question 1/3:** {first_question}"""
            
            self.add_message(session_id, ConversationMessage(
                role="assistant",
                content=welcome_content,
                timestamp=datetime.utcnow(),
                technology=current_tech["name"]
            ))
            
            print(f"[DEBUG] Interview started successfully: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"[ERROR] Error in start_interview: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return f"Error starting interview: {str(e)}"

    def _build_tech_plan(self, tech_stack) -> List[Dict]:
        """Build technology plan from candidate's tech stack"""
        try:
            print(f"[DEBUG] Building tech plan from stack: {tech_stack}")
            tech_plan = []
            
            for category in tech_stack:
                print(f"[DEBUG] Processing category: {category.category if hasattr(category, 'category') else category.get('category')}")
                technologies = category.technologies if hasattr(category, 'technologies') else category.get('technologies', [])
                
                for tech in technologies:
                    name = tech.name if hasattr(tech, 'name') else tech.get('name')
                    proficiency = tech.proficiency if hasattr(tech, 'proficiency') else tech.get('proficiency')
                    
                    if name and proficiency:
                        tech_plan.append({
                            "name": name,
                            "proficiency": proficiency,
                            "questions_asked": 0,
                            "completed": False
                        })
                        print(f"[DEBUG] Added tech: {name} ({proficiency})")
            
            return tech_plan
            
        except Exception as e:
            print(f"[ERROR] Error building tech plan: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return []

    def process_user_input(self, session_id: str, user_input: str) -> str:
        try:
            print(f"[DEBUG] Processing user input for session: {session_id}")
            print(f"[DEBUG] User input: {user_input[:100]}...")
            
            # Validate session
            session_doc = self.collection.find_one({"session_id": session_id})
            if not session_doc:
                raise ValueError("Session not found")

            # Get current tech and question count
            current_tech_index = session_doc.get("current_tech_index", 0)
            tech_plan = session_doc.get("tech_plan", [])
            
            print(f"[DEBUG] Current tech index: {current_tech_index}")
            print(f"[DEBUG] Tech plan length: {len(tech_plan)}")
            
            if current_tech_index >= len(tech_plan):
                return self._complete_interview(session_id)

            current_tech = tech_plan[current_tech_index]
            questions_asked = current_tech.get("questions_asked", 0)
            
            print(f"[DEBUG] Current tech: {current_tech['name']}")
            print(f"[DEBUG] Questions asked BEFORE increment: {questions_asked}")

            # Rate answer
            answer_rating = self._rate_answer(user_input, current_tech["name"], current_tech["proficiency"])
            print(f"[DEBUG] Answer rating: {answer_rating}")
            
            # Calculate totals
            current_total = float(session_doc.get('total_points', 0))
            current_max = float(session_doc.get('max_possible_points', 0))
            new_total = current_total + answer_rating
            new_max = current_max + 10

            # Add user message
            user_message = ConversationMessage(
                role="user",
                content=user_input,
                timestamp=datetime.utcnow(),
                technology=current_tech["name"]
            )
            
            # Atomic update for message, ratings, and totals
            update_result = self.collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {
                        "conversation_history": user_message.model_dump(),
                        "answer_ratings": {
                            "technology": current_tech["name"],
                            "question_number": questions_asked + 1,  # This is the question they just answered
                            "rating": answer_rating,
                            "timestamp": datetime.utcnow()
                        }
                    },
                    "$set": {
                        "total_points": float(new_total),
                        "max_possible_points": float(new_max),
                        "total_rating_display": f"{round(new_total)}/{round(new_max)}",
                        "average_rating": float((new_total / new_max) * 10) if new_max > 0 else 0
                    }
                }
            )

            if not update_result.modified_count:
                raise ValueError("Failed to update session")

            # Increment questions_asked AFTER processing the answer
            questions_asked += 1
            tech_plan[current_tech_index]["questions_asked"] = questions_asked
            
            print(f"[DEBUG] Questions asked AFTER increment: {questions_asked}")
            
            # Update tech plan in database
            self.collection.update_one(
                {"session_id": session_id},
                {"$set": {"tech_plan": tech_plan}}
            )

            # Determine next action based on question count
            if questions_asked >= 3:
                print(f"[DEBUG] Moving to next technology (3 questions completed)")
                response_text = self._move_to_next_technology(session_id, session_doc, updated_tech_plan=tech_plan)
            else:
                print(f"[DEBUG] Getting next question - we've answered {questions_asked} questions")
                response_text = self._get_next_question(
                    session_id=session_id,
                    current_tech=current_tech,
                    questions_answered=questions_asked,  # FIXED: Pass questions answered, not next question number
                    user_input=user_input
                )

            # Add assistant message
            assistant_message = ConversationMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow(),
                technology=current_tech["name"]
            )
            self.collection.update_one(
                {"session_id": session_id},
                {"$push": {"conversation_history": assistant_message.model_dump()}}
            )

            print(f"[DEBUG] Response generated successfully")
            return response_text

        except Exception as e:
            print(f"[ERROR] Error in process_user_input: {str(e)}")
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return f"Error processing input: {str(e)}"

    def _rate_answer(self, answer: str, technology: str, proficiency: str) -> float:
        """Enhanced answer rating system"""
        try:
            # Base rating
            rating = 5.0
            
            # Length analysis
            if len(answer) < 50:
                rating -= 2
            elif len(answer) > 200:
                rating += 1
            
            # Technical depth indicators
            tech_keywords = {
                "example": 0.5,
                "experience": 0.5,
                "project": 0.5,
                "implementation": 1,
                "architecture": 1,
                "design": 0.5,
                "solution": 0.5,
                "problem": 0.5,
                "optimize": 1,
                "performance": 1,
                "security": 1,
                "testing": 1,
                "debug": 0.5,
                "framework": 0.5,
                "library": 0.5,
                "database": 0.5,
                "api": 0.5,
                "interface": 0.5,
                "component": 0.5,
                "system": 0.5
            }
            
            # Code indicators
            code_patterns = [
                "return ", "if ", "for ", "while ", "try:",
                "{", "}", "()", "[]"
            ]
            
            answer_lower = answer.lower()
            
            # Add points for technical keywords
            for keyword, points in tech_keywords.items():
                if keyword in answer_lower:
                    rating += points
            
            # Add points for code examples
            for pattern in code_patterns:
                if pattern in answer:
                    rating += 0.5
                    
            # Proficiency-based adjustment
            if proficiency == "Advanced":
                rating *= 1.2
            elif proficiency == "Beginner":
                rating *= 0.8
                
            # Cap rating between 0-10
            return min(max(rating, 0), 10)
            
        except Exception as e:
            print(f"[ERROR] Error in _rate_answer: {e}")
            return 5.0  # Default rating on error

    def _get_next_question(self, session_id: str, current_tech: dict, questions_answered: int, user_input: str) -> str:
        """Get next question with proper progression logic - FIXED parameter name"""
        print(f"[DEBUG] === GETTING NEXT QUESTION ===")
        print(f"[DEBUG] Questions answered so far: {questions_answered}")
        
        try:
            tech_name = current_tech["name"]
            proficiency = current_tech["proficiency"]
            
            # Now the logic is: 
            # - questions_answered = 1: Generate follow-up (question 2)
            # - questions_answered = 2: Generate final question (question 3)
            
            if questions_answered == 1:  # After 1st answer, give follow-up
                print(f"[DEBUG] Generating follow-up question (2/3)...")
                followup = self.generate_followup(
                    technology=tech_name, 
                    user_input=user_input,
                    session_id=session_id
                )
                return f"**Follow-up Question (2/3):**\n\n{followup}"
            
            elif questions_answered == 2:  # After 2nd answer, give final question
                print(f"[DEBUG] Generating final question (3/3)...")
                final_question = self.generate_question(
                    technology=tech_name, 
                    proficiency=proficiency, 
                    session_id=session_id,
                    question_type="final"
                )
                return f"**Final Question (3/3):**\n\n{final_question}"
            
            else:  # This shouldn't happen, but fallback
                print(f"[DEBUG] Unexpected questions_answered count: {questions_answered}")
                question = self.generate_question(
                    technology=tech_name, 
                    proficiency=proficiency, 
                    session_id=session_id
                )
                return f"**Question:**\n\n{question}"
                
        except Exception as e:
            print(f"[ERROR] Error in _get_next_question: {e}")
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return self.get_fallback_question(current_tech["name"], current_tech["proficiency"])

    def _move_to_next_technology(self, session_id: str, session_doc: dict, updated_tech_plan: List[Dict] = None) -> str:
        """Move to next technology"""
        print(f"[DEBUG] === MOVING TO NEXT TECHNOLOGY ===")
        try:
            current_tech_index = session_doc.get("current_tech_index", 0)
            tech_plan = updated_tech_plan or session_doc.get("tech_plan", [])
            
            print(f"[DEBUG] Current tech index: {current_tech_index}")
            
            # Mark current tech as completed
            if current_tech_index < len(tech_plan):
                tech_plan[current_tech_index]["completed"] = True
                print(f"[DEBUG] Marked {tech_plan[current_tech_index]['name']} as completed")
            
            # Move to next tech
            next_tech_index = current_tech_index + 1
            
            if next_tech_index >= len(tech_plan):
                print(f"[DEBUG] No more technologies, completing interview")
                return self._complete_interview(session_id)
            
            next_tech = tech_plan[next_tech_index]
            print(f"[DEBUG] Next technology: {next_tech['name']}")
            
            # Update session with next tech - start with 0 questions asked
            next_tech["questions_asked"] = 0  # Reset to 0 for next tech
            self.collection.update_one(
                {"session_id": session_id},
                {"$set": {
                    "current_tech_index": next_tech_index,
                    "tech_plan": tech_plan
                }}
            )
            
            # Generate first question for next tech
            print(f"[DEBUG] Generating first question for {next_tech['name']}")
            first_question = self.generate_question(
                technology=next_tech["name"], 
                proficiency=next_tech["proficiency"], 
                session_id=session_id
            )
            
            completed = sum(1 for t in tech_plan if t.get("completed", False))
            total = len(tech_plan)
            
            return f"""✅ **{tech_plan[current_tech_index]['name']} Complete!**

📊 **Progress:** {completed}/{total} technologies completed

🎯 **Now discussing {next_tech['name']}** (Level: {next_tech['proficiency']})

**Question 1/3:** {first_question}"""

        except Exception as e:
            print(f"[ERROR] Error in _move_to_next_technology: {e}")
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return f"Error moving to next technology: {str(e)}"

    def generate_question(self, technology: str, proficiency: str, session_id: str, question_type: str = "regular") -> str:
        """Generate question with comprehensive error handling and variety"""
        print(f"[DEBUG] === GENERATING QUESTION ===")
        print(f"[DEBUG] Technology: {technology}")
        print(f"[DEBUG] Proficiency: {proficiency}")
        print(f"[DEBUG] Question type: {question_type}")
        
        try:
            questions = self.llama_service.generate_questions(
                technology=technology,
                proficiency=ProficiencyLevel(proficiency),
                count=1,
                session_id=session_id
            )
            
            print(f"[DEBUG] LlamaService returned: {len(questions) if questions else 0} questions")
            
            if questions and questions.get("question_text"):
                question = questions["question_text"]
                if len(question) > 20 and question.endswith('?'):
                    print(f"[DEBUG] Using LlamaService question")
                    return question
            
            print(f"[DEBUG] Using fallback question")
            return self.get_fallback_question(technology, proficiency)
                
        except Exception as e:
            print(f"[ERROR] Error in generate_question: {e}")
            print(f"[ERROR] Full traceback: {traceback.format_exc()}")
            return self.get_fallback_question(technology, proficiency)

    def generate_followup(self, technology: str, user_input: str, session_id: str) -> str:
        """Generate follow-up question based on user's answer"""
        print(f"[DEBUG] === GENERATING FOLLOWUP ===")
        print(f"[DEBUG] Technology: {technology}")
        
        try:
            followup = self.llama_service.generate_followup(
                original_question="Previous question",
                candidate_answer=user_input,
                technology=technology,
                session_id=session_id
            )
            
            if followup and len(followup) > 15 and followup.endswith('?'):
                print(f"[DEBUG] Using LlamaService followup")
                return followup
            else:
                print(f"[DEBUG] Using fallback followup")
                return self.get_fallback_followup(technology, user_input)
                
        except Exception as e:
            print(f"[ERROR] Error in generate_followup: {e}")
            return self.get_fallback_followup(technology, user_input)

    def get_fallback_question(self, technology: str, proficiency: str) -> str:
        """Guaranteed fallback questions with variety"""
        import random
        
        questions = {
            ("Python", "Beginner"): [
                "What are the main data types in Python and when do you use each one?",
                "Explain the difference between lists and tuples in Python.",
                "How do you handle user input and basic error checking in Python?"
            ],
            ("Python", "Intermediate"): [
                "How do you handle exceptions in Python? Can you give an example?",
                "Explain Python's memory management and garbage collection.",
                "What are Python decorators and how would you create one?",
                "How do you work with files in Python? Give an example.",
                "What's the difference between shallow and deep copy in Python?"
            ],
            ("Python", "Advanced"): [
                "How would you optimize a slow Python application?",
                "Explain Python's Global Interpreter Lock (GIL) and its implications.",
                "How would you implement a metaclass in Python?",
                "Describe how Python's import system works.",
                "How do you implement proper logging in a Python application?"
            ],
            ("JavaScript", "Beginner"): [
                "What's the difference between var, let, and const?",
                "Explain how JavaScript handles data types.",
                "What is the DOM and how do you manipulate it?"
            ],
            ("JavaScript", "Intermediate"): [
                "How do you handle asynchronous operations in JavaScript?",
                "Explain closures in JavaScript with an example.",
                "What are JavaScript promises and how do they work?"
            ],
            ("JavaScript", "Advanced"): [
                "How would you implement a custom state management system?",
                "Explain event delegation and when you would use it.",
                "How would you optimize JavaScript performance in a large application?"
            ]
        }
        
        tech_questions = questions.get((technology, proficiency), [
            f"Tell me about a challenging {technology} project and how you solved the technical problems.",
            f"What are the best practices you follow when working with {technology}?",
            f"How do you debug and troubleshoot issues in {technology}?"
        ])
        
        return random.choice(tech_questions)

    def get_fallback_followup(self, technology: str, user_input: str) -> str:
        """Fallback follow-up questions"""
        answer_lower = user_input.lower()
        
        if "project" in answer_lower:
            return f"What was the biggest technical challenge in that {technology} project and how did you overcome it?"
        elif "error" in answer_lower or "bug" in answer_lower:
            return f"How do you typically debug {technology} applications when you encounter issues?"
        elif "performance" in answer_lower:
            return f"What specific techniques do you use to improve {technology} performance?"
        elif "code" in answer_lower or "implementation" in answer_lower:
            return f"Can you walk me through the code structure and explain your design decisions?"
        else:
            return f"Can you give a specific example of how you used {technology} to solve a complex problem?"

    def get_current_tech(self, session_doc: dict) -> Optional[dict]:
        """Get current technology"""
        current_tech_index = session_doc.get("current_tech_index", 0)
        tech_plan = session_doc.get("tech_plan", [])
        
        if current_tech_index < len(tech_plan):
            return tech_plan[current_tech_index]
        return None

    def _complete_interview(self, session_id: str) -> str:
        """Complete interview and clear caches"""
        try:
            # Clear LLM cache for this session
            self.llama_service.clear_session_cache(session_id)
            
            # Update session status
            self.collection.update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                }}
            )
            
            return """🎉 **Interview Complete!**

**Excellent work!** You've successfully completed the technical interview.

**What's Next:**
✅ Technical team review (2-3 business days)
📧 Detailed feedback via email
📞 Potential follow-up discussion

**Thank you for your time!**"""

        except Exception as e:
            print(f"[ERROR] Error in _complete_interview: {e}")
            return "Interview completed with some technical issues. Please contact support."

    def add_message(self, session_id: str, message: ConversationMessage):
        """Add message to conversation"""
        try:
            self.collection.update_one(
                {"session_id": session_id},
                {"$push": {"conversation_history": message.model_dump()}}
            )
        except Exception as e:
            print(f"[ERROR] Error adding message: {e}")

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Get session"""
        try:
            session_doc = self.collection.find_one({"session_id": session_id})
            return InterviewSession(**session_doc) if session_doc else None
        except Exception as e:
            print(f"[ERROR] Error getting session: {e}")
            return None
