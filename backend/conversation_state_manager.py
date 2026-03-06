"""
conversation_state_manager.py — Advanced Conversation State Management

Prevents repetitive questions and manages conversation flow intelligently.
"""

import json
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum


class QuestionType(Enum):
    """Types of questions that can be asked"""
    OCCUPATION = "occupation"
    STATE = "state"
    AGE_GROUP = "age_group"
    INCOME = "income_bracket"
    LAND_SIZE = "land_acres"
    GENDER = "gender"
    CATEGORY = "category"
    EDUCATION = "education_level"
    FAMILY_SIZE = "family_size"


class ConversationStateManager:
    """
    Manages conversation state to prevent repetitive questions
    and ensure smooth conversation flow
    """
    
    def __init__(self):
        self.asked_questions: Set[str] = set()
        self.answered_questions: Set[str] = set()
        self.failed_attempts: Dict[str, int] = {}
        self.conversation_stage = "greeting"
        self.last_question_time = None
        self.question_history: List[Dict] = []
        
    def has_asked_question(self, question_type: str) -> bool:
        """Check if we've already asked this question"""
        return question_type in self.asked_questions
    
    def has_answer_for(self, question_type: str, user_profile: Dict) -> bool:
        """Check if we already have an answer for this question"""
        field_map = {
            QuestionType.OCCUPATION.value: "occupation",
            QuestionType.STATE.value: "state",
            QuestionType.AGE_GROUP.value: "age_group",
            QuestionType.INCOME.value: "income_bracket",
            QuestionType.LAND_SIZE.value: "land_acres",
            QuestionType.GENDER.value: "gender",
            QuestionType.CATEGORY.value: "category",
            QuestionType.EDUCATION.value: "education_level",
            QuestionType.FAMILY_SIZE.value: "family_size",
        }
        
        field = field_map.get(question_type)
        if not field:
            return False
        
        return bool(user_profile.get(field))
    
    def mark_question_asked(self, question_type: str, question_text: str):
        """Mark that we've asked this question"""
        self.asked_questions.add(question_type)
        self.last_question_time = datetime.now()
        self.question_history.append({
            "type": question_type,
            "text": question_text,
            "timestamp": datetime.now().isoformat()
        })
    
    def mark_question_answered(self, question_type: str):
        """Mark that user has answered this question"""
        self.answered_questions.add(question_type)
        if question_type in self.failed_attempts:
            del self.failed_attempts[question_type]
    
    def record_failed_attempt(self, question_type: str):
        """Record that user didn't answer the question"""
        if question_type not in self.failed_attempts:
            self.failed_attempts[question_type] = 0
        self.failed_attempts[question_type] += 1
    
    def should_skip_question(self, question_type: str) -> bool:
        """
        Determine if we should skip asking this question
        (e.g., asked too many times, user ignored it)
        """
        # Skip if asked more than 2 times
        if self.failed_attempts.get(question_type, 0) >= 2:
            return True
        
        # Skip if already asked in last 3 questions
        recent_questions = [q["type"] for q in self.question_history[-3:]]
        if question_type in recent_questions:
            return True
        
        return False
    
    def get_next_question_priority(self, user_profile: Dict, 
                                   intent: str) -> Optional[str]:
        """
        Intelligently determine what question to ask next based on:
        - Current intent
        - Missing profile fields
        - Question history
        - Failed attempts
        """
        # Priority questions based on intent
        intent_priorities = {
            "scheme_discovery": [
                QuestionType.OCCUPATION,
                QuestionType.STATE,
                QuestionType.INCOME,
            ],
            "eligibility_check": [
                QuestionType.OCCUPATION,
                QuestionType.STATE,
                QuestionType.AGE_GROUP,
                QuestionType.INCOME,
            ],
            "application_guidance": [
                QuestionType.STATE,
                QuestionType.OCCUPATION,
            ],
        }
        
        priority_list = intent_priorities.get(intent, [
            QuestionType.OCCUPATION,
            QuestionType.STATE,
        ])
        
        # Find first missing field that we haven't asked too many times
        for question_type in priority_list:
            q_type = question_type.value
            
            # Skip if we already have the answer
            if self.has_answer_for(q_type, user_profile):
                continue
            
            # Skip if we should avoid asking
            if self.should_skip_question(q_type):
                continue
            
            return q_type
        
        return None
    
    def should_ask_clarifying_question(self, user_profile: Dict, 
                                      intent: str) -> bool:
        """
        Determine if we should ask a clarifying question
        
        Rules:
        - Don't ask if we just asked one
        - Don't ask if user is in middle of something
        - Don't ask if we have enough info
        """
        # Don't ask if we just asked something
        if self.last_question_time:
            time_since_last = (datetime.now() - self.last_question_time).seconds
            if time_since_last < 30:  # Wait at least 30 seconds
                return False
        
        # Don't ask if we've asked too many questions
        if len(self.asked_questions) >= 5:
            return False
        
        # Don't ask if user is asking for specific help
        if intent in ["application_guidance", "document_help", "status_tracking"]:
            return False
        
        # Check if we have minimum required info
        required_fields = ["occupation", "state"]
        has_required = all(user_profile.get(field) for field in required_fields)
        
        if has_required:
            return False  # We have enough info
        
        return True
    
    def generate_smart_question(self, question_type: str, 
                               language: str, 
                               user_profile: Dict) -> Optional[str]:
        """
        Generate a contextual, non-repetitive question
        """
        # Check if we should skip
        if self.should_skip_question(question_type):
            return None
        
        # Generate question based on context
        questions = self._get_contextual_questions(
            question_type, language, user_profile
        )
        
        # Pick a question we haven't asked before
        for question in questions:
            if not any(q["text"] == question for q in self.question_history):
                self.mark_question_asked(question_type, question)
                return question
        
        return None
    
    def _get_contextual_questions(self, question_type: str, 
                                 language: str, 
                                 user_profile: Dict) -> List[str]:
        """
        Get contextual question variations based on what we already know
        """
        # Get what we already know
        occupation = user_profile.get("occupation")
        state = user_profile.get("state")
        
        questions_map = {
            "occupation": {
                "hi": [
                    "आप क्या काम करते हैं?",
                    "आपका व्यवसाय क्या है?",
                    "आप किस क्षेत्र में काम करते हैं?",
                ],
                "en": [
                    "What do you do for a living?",
                    "What is your occupation?",
                    "What field do you work in?",
                ]
            },
            "state": {
                "hi": [
                    "आप किस राज्य में रहते हैं?",
                    "आपका राज्य कौन सा है?",
                    f"{'बढ़िया! ' if occupation else ''}आप कहाँ रहते हैं?",
                ],
                "en": [
                    "Which state do you live in?",
                    "What is your state?",
                    f"{'Great! ' if occupation else ''}Where are you located?",
                ]
            },
            "income_bracket": {
                "hi": [
                    "आपकी वार्षिक आय कितनी है?",
                    "आपकी परिवार की सालाना आय क्या है?",
                    "आप किस आय वर्ग में आते हैं?",
                ],
                "en": [
                    "What is your annual income?",
                    "What is your family's yearly income?",
                    "Which income bracket do you fall under?",
                ]
            },
            "land_acres": {
                "hi": [
                    "आपके पास कितनी जमीन है?",
                    "आपकी कृषि भूमि कितनी है?",
                    "आपके पास कितने एकड़ जमीन है?",
                ],
                "en": [
                    "How much land do you own?",
                    "What is your agricultural land size?",
                    "How many acres of land do you have?",
                ]
            },
            "age_group": {
                "hi": [
                    "आपकी उम्र कितनी है?",
                    "आप किस आयु वर्ग में हैं?",
                ],
                "en": [
                    "What is your age?",
                    "Which age group do you belong to?",
                ]
            },
        }
        
        return questions_map.get(question_type, {}).get(language, [])
    
    def to_dict(self) -> Dict:
        """Serialize state for storage"""
        return {
            "asked_questions": list(self.asked_questions),
            "answered_questions": list(self.answered_questions),
            "failed_attempts": self.failed_attempts,
            "conversation_stage": self.conversation_stage,
            "last_question_time": self.last_question_time.isoformat() if self.last_question_time else None,
            "question_history": self.question_history,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationStateManager':
        """Deserialize state from storage"""
        manager = cls()
        manager.asked_questions = set(data.get("asked_questions", []))
        manager.answered_questions = set(data.get("answered_questions", []))
        manager.failed_attempts = data.get("failed_attempts", {})
        manager.conversation_stage = data.get("conversation_stage", "greeting")
        
        last_q_time = data.get("last_question_time")
        if last_q_time:
            manager.last_question_time = datetime.fromisoformat(last_q_time)
        
        manager.question_history = data.get("question_history", [])
        return manager


class ConversationFlowController:
    """
    Controls the overall conversation flow to ensure natural progression
    """
    
    def __init__(self):
        self.state_manager = ConversationStateManager()
    
    def process_user_message(self, message: str, user_profile: Dict, 
                            intent: str, language: str) -> Dict:
        """
        Process user message and determine next action
        
        Returns:
            {
                "should_ask_question": bool,
                "question": str or None,
                "question_type": str or None,
                "reason": str
            }
        """
        # Check if user answered a previous question
        self._check_for_answers(message, user_profile)
        
        # Determine if we should ask a clarifying question
        should_ask = self.state_manager.should_ask_clarifying_question(
            user_profile, intent
        )
        
        if not should_ask:
            return {
                "should_ask_question": False,
                "question": None,
                "question_type": None,
                "reason": "Have enough information or inappropriate timing"
            }
        
        # Get next question priority
        next_question_type = self.state_manager.get_next_question_priority(
            user_profile, intent
        )
        
        if not next_question_type:
            return {
                "should_ask_question": False,
                "question": None,
                "question_type": None,
                "reason": "No more questions needed"
            }
        
        # Generate smart question
        question = self.state_manager.generate_smart_question(
            next_question_type, language, user_profile
        )
        
        if not question:
            return {
                "should_ask_question": False,
                "question": None,
                "question_type": None,
                "reason": "Question already asked or should be skipped"
            }
        
        return {
            "should_ask_question": True,
            "question": question,
            "question_type": next_question_type,
            "reason": "Need this information for better recommendations"
        }
    
    def _check_for_answers(self, message: str, user_profile: Dict):
        """Check if user's message answered any pending questions"""
        # Check each asked but not answered question
        pending = self.state_manager.asked_questions - self.state_manager.answered_questions
        
        for question_type in pending:
            if self.state_manager.has_answer_for(question_type, user_profile):
                self.state_manager.mark_question_answered(question_type)
            else:
                # User didn't answer, record failed attempt
                self.state_manager.record_failed_attempt(question_type)
    
    def get_state(self) -> Dict:
        """Get current state for storage"""
        return self.state_manager.to_dict()
    
    def load_state(self, state_data: Dict):
        """Load state from storage"""
        self.state_manager = ConversationStateManager.from_dict(state_data)
