"""
conversation_engine.py — Enhanced Conversational AI Engine

Handles multi-turn conversations, context management, and intelligent routing
for scheme discovery, application guidance, and document processing.
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class ConversationState(Enum):
    """Conversation states for tracking user journey"""
    GREETING = "greeting"
    PROFILE_COLLECTION = "profile_collection"
    SCHEME_DISCOVERY = "scheme_discovery"
    SCHEME_DETAILS = "scheme_details"
    ELIGIBILITY_CHECK = "eligibility_check"
    APPLICATION_GUIDANCE = "application_guidance"
    DOCUMENT_HELP = "document_help"
    STATUS_TRACKING = "status_tracking"
    GENERAL_QUERY = "general_query"


class ConversationEngine:
    """
    Manages conversation flow, context, and intelligent routing
    """
    
    def __init__(self, schemes_data: List[Dict]):
        self.schemes = schemes_data
        self.scheme_map = {s.get("name", "").lower(): s for s in schemes_data}
        
    def analyze_intent(self, message: str, history: List[Dict]) -> Dict:
        """
        Analyze user message to determine intent and extract entities
        
        Returns:
            {
                "intent": ConversationState,
                "entities": {...},
                "confidence": float,
                "context": {...}
            }
        """
        msg_lower = message.lower()
        
        # Application guidance keywords - HIGHEST PRIORITY for "steps" requests
        application_keywords = [
            "how to apply", "apply", "application", "steps", "step by step",
            "guidance", "guide me", "help me apply", "process", "instructions",
            "instruction", "how do i apply", "tell me how", "procedure",
            "कैसे आवेदन", "आवेदन", "चरण", "प्रक्रिया", "निर्देश",
            "దరఖాస్తు", "దశలు", "విధానం", "సూచనలు",
            "விண்ணப்பம்", "படிகள்", "வழிகாட்டி", "வழிமுறைகள்",
            "আবেদন", "ধাপ", "প্রক্রিয়া", "নির্দেশ",
            "अर्ज", "पायऱ्या", "सूचना"
        ]
        
        # Check if user is asking for application steps
        if any(kw in msg_lower for kw in application_keywords):
            # Extract scheme name from message or history
            scheme_entity = self._extract_scheme_name(message)
            if not scheme_entity:
                # Check if there's a scheme mentioned in recent history
                scheme_entity = self._extract_scheme_from_history(history)
            
            # Check if user is referring to a scheme with context words like "this", "these", "that"
            context_words = ["this", "these", "that", "the", "इस", "यह", "ఈ", "இந்த", "এই", "या"]
            has_context_word = any(word in msg_lower for word in context_words)
            
            # If user says "instructions for this scheme" but no scheme found in message,
            # definitely look in history
            if has_context_word and not scheme_entity:
                scheme_entity = self._extract_scheme_from_history(history)
            
            return {
                "intent": ConversationState.APPLICATION_GUIDANCE,
                "entities": scheme_entity,
                "confidence": 0.95,
                "context": {"needs_scheme_selection": not scheme_entity}
            }
        
        # Scheme request keywords - HIGH PRIORITY
        scheme_request_keywords = [
            "show", "schemes", "योजना", "పథకాలు", "திட்டம்", "প্রকল্প",
            "need schemes", "i need", "eligible", "help me find",
            "what schemes", "which schemes", "tell me", "give me"
        ]
        
        # Check if user is explicitly requesting schemes
        if any(kw in msg_lower for kw in scheme_request_keywords):
            return {
                "intent": ConversationState.SCHEME_DISCOVERY,
                "entities": self._extract_user_profile(message),
                "confidence": 0.95,
                "context": {"explicit_request": True}
            }
        
        # Check if message contains detailed information (document upload scenario)
        has_details = self._has_detailed_info(message)
        if has_details:
            return {
                "intent": ConversationState.SCHEME_DISCOVERY,
                "entities": self._extract_user_profile(message),
                "confidence": 0.9,
                "context": {"has_details": True}
            }
        
        # Profile collection keywords
        profile_keywords = ["i am", "मैं हूं", "నేను", "நான்", "আমি", "मी आहे"]
        
        # Document help keywords
        document_keywords = [
            "document", "documents", "दस्तावेज़", "పత్రాలు", "ஆவணங்கள்",
            "নথি", "कागदपत्रे", "upload", "अपलोड"
        ]
        
        # Status tracking keywords
        status_keywords = [
            "status", "track", "check status", "स्थिति", "స్థితి",
            "நிலை", "অবস্থা", "स्थिती"
        ]
        
        # Eligibility check keywords
        eligibility_keywords = [
            "eligible", "qualify", "पात्र", "అర్హత", "தகுதி",
            "যোগ্য", "पात्रता"
        ]
        
        # Determine intent
        if any(kw in msg_lower for kw in document_keywords):
            return {
                "intent": ConversationState.DOCUMENT_HELP,
                "entities": self._extract_document_type(message),
                "confidence": 0.85,
                "context": {}
            }
        
        elif any(kw in msg_lower for kw in status_keywords):
            return {
                "intent": ConversationState.STATUS_TRACKING,
                "entities": {},
                "confidence": 0.8,
                "context": {}
            }
        
        elif any(kw in msg_lower for kw in eligibility_keywords):
            return {
                "intent": ConversationState.ELIGIBILITY_CHECK,
                "entities": self._extract_user_profile(message),
                "confidence": 0.85,
                "context": {}
            }
        
        elif any(kw in msg_lower for kw in profile_keywords):
            return {
                "intent": ConversationState.PROFILE_COLLECTION,
                "entities": self._extract_user_profile(message),
                "confidence": 0.9,
                "context": {}
            }
        
        else:
            return {
                "intent": ConversationState.SCHEME_DISCOVERY,
                "entities": self._extract_categories(message),
                "confidence": 0.7,
                "context": {}
            }
    
    def _extract_scheme_name(self, message: str) -> Dict:
        """Extract scheme name from message"""
        msg_lower = message.lower()
        
        # Common scheme name patterns (expanded)
        scheme_patterns = [
            "pm kisan", "pm-kisan", "pradhan mantri kisan", "kisan samman",
            "fasal bima", "pmfby", "crop insurance", "pradhan mantri fasal",
            "kisan credit", "kcc", "credit card",
            "soil health", "soil card", "health card",
            "pm kusum", "kusum",
            "ayushman", "pmjay", "ayushman bharat",
            "ujjwala", "pmuy", "pradhan mantri ujjwala"
        ]
        
        for pattern in scheme_patterns:
            if pattern in msg_lower:
                # Find matching scheme in database
                for scheme_name, scheme_data in self.scheme_map.items():
                    if pattern in scheme_name.lower():
                        return {"scheme": scheme_data}
        
        # Try partial match with scheme names
        for scheme_name, scheme_data in self.scheme_map.items():
            # Check if any word from the scheme name is in the message
            scheme_words = scheme_name.lower().split()
            if len(scheme_words) >= 2:
                # Check if at least 2 words match
                matches = sum(1 for word in scheme_words if word in msg_lower and len(word) > 3)
                if matches >= 2:
                    return {"scheme": scheme_data}
        
        # Try exact match
        for scheme_name, scheme_data in self.scheme_map.items():
            if scheme_name.lower() in msg_lower:
                return {"scheme": scheme_data}
        
        return {}
    
    def _extract_scheme_from_history(self, history: List[Dict]) -> Dict:
        """Extract scheme name from recent conversation history"""
        # Look at last 5 messages for scheme mentions
        recent_messages = history[-5:] if len(history) > 5 else history
        
        for msg in reversed(recent_messages):
            content = msg.get("content", "")
            
            # Check if content is a string (user message)
            if isinstance(content, str):
                scheme_entity = self._extract_scheme_name(content)
                if scheme_entity:
                    return scheme_entity
            
            # Check if content is a dict (bot response with schemes)
            elif isinstance(content, dict):
                # If previous message had schemes array, use the first one
                if content.get("schemes") and isinstance(content.get("schemes"), list):
                    schemes = content.get("schemes", [])
                    if schemes and len(schemes) > 0:
                        return {"scheme": schemes[0]}
                
                # If previous message was application_guidance, extract scheme_name
                if content.get("type") == "application_guidance" and content.get("scheme_name"):
                    scheme_name = content.get("scheme_name")
                    # Find this scheme in database
                    for db_scheme_name, db_scheme_data in self.scheme_map.items():
                        if scheme_name.lower() in db_scheme_name.lower() or db_scheme_name.lower() in scheme_name.lower():
                            return {"scheme": db_scheme_data}
            
            # Check if content is a JSON string
            elif isinstance(content, str):
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and parsed.get("schemes"):
                        schemes = parsed.get("schemes", [])
                        if schemes and len(schemes) > 0:
                            return {"scheme": schemes[0]}
                except:
                    pass
        
        return {}
    
    def _has_detailed_info(self, message: str) -> bool:
        """Check if message contains detailed information (like document upload)"""
        msg_lower = message.lower()
        
        # Check for multiple pieces of information
        detail_indicators = [
            "uploaded", "document", "details", "dob", "date of birth",
            "id number", "account number", "permanent", "card",
            "name:", "age:", "occupation:", "location:",
            len(message) > 100,  # Long messages usually have details
        ]
        
        # Count how many indicators are present
        indicator_count = sum(1 for indicator in detail_indicators if 
                            (isinstance(indicator, str) and indicator in msg_lower) or
                            (isinstance(indicator, bool) and indicator))
        
        # If 2 or more indicators, consider it detailed info
        return indicator_count >= 2
    
    def _extract_document_type(self, message: str) -> Dict:
        """Extract document type from message"""
        msg_lower = message.lower()
        doc_types = {
            "aadhaar": ["aadhaar", "आधार", "ఆధార్", "ஆதார்"],
            "pan": ["pan", "पैन"],
            "income": ["income", "आय", "ఆదాయం", "வருமானம்"],
            "caste": ["caste", "जाति", "కులం", "சாதி"],
            "ration": ["ration", "राशन", "రేషన్", "ரேஷன்"],
        }
        
        for doc_type, keywords in doc_types.items():
            if any(kw in msg_lower for kw in keywords):
                return {"document_type": doc_type}
        return {}
    
    def _extract_user_profile(self, message: str) -> Dict:
        """Extract user profile information from message"""
        profile = {}
        msg_lower = message.lower()
        
        # Occupation
        occupations = {
            "farmer": ["farmer", "किसान", "రైతు", "விவசாயி", "কৃষক", "शेतकरी"],
            "student": ["student", "छात्र", "విద్యార్థి", "மாணவர்", "ছাত্র"],
            "woman": ["woman", "महिला", "మహిళ", "பெண்", "মহিলা"],
            "senior": ["senior", "elderly", "बुजुर्ग", "వృద్ధ", "முதியவர்"],
            "disabled": ["disabled", "दिव्यांग", "వికలాంగ", "மாற்றுத்திறனாளி"],
            "business": ["business", "व्यवसाय", "వ్యాపారం", "வணிகம்"],
        }
        
        for occ, keywords in occupations.items():
            if any(kw in msg_lower for kw in keywords):
                profile["occupation"] = occ
                break
        
        return profile
    
    def _extract_categories(self, message: str) -> Dict:
        """Extract scheme categories from message"""
        msg_lower = message.lower()
        categories = {
            "agriculture": ["farm", "agriculture", "खेती", "వ్యవసాయం", "விவசாயம்", "কৃষি"],
            "health": ["health", "स्वास्थ्य", "ఆరోగ్యం", "சுகாதாரம்", "স্বাস্থ্য"],
            "housing": ["house", "housing", "आवास", "గృహం", "வீடு", "বাসস্থান"],
            "education": ["education", "study", "शिक्षा", "విద్య", "கல்வி", "শিক্ষা"],
            "women": ["woman", "women", "महिला", "మహిళ", "பெண்", "মহিলা"],
        }
        
        for cat, keywords in categories.items():
            if any(kw in msg_lower for kw in keywords):
                return {"category": cat}
        return {}
    
    def build_application_guidance(self, scheme: Dict, language: str) -> Dict:
        """
        Build step-by-step application guidance for a scheme
        """
        return {
            "type": "application_guidance",
            "scheme_name": scheme.get("name", ""),
            "steps": [
                {
                    "step": 1,
                    "title": "Prepare Documents",
                    "description": f"Gather these documents: {scheme.get('documents', 'Required documents')}",
                    "completed": False
                },
                {
                    "step": 2,
                    "title": "Visit Portal",
                    "description": f"Go to: {scheme.get('how_to_apply', 'Official portal')}",
                    "completed": False
                },
                {
                    "step": 3,
                    "title": "Fill Application",
                    "description": "Complete the online application form with your details",
                    "completed": False
                },
                {
                    "step": 4,
                    "title": "Upload Documents",
                    "description": "Upload scanned copies of required documents",
                    "completed": False
                },
                {
                    "step": 5,
                    "title": "Submit & Track",
                    "description": "Submit application and note your reference number",
                    "completed": False
                }
            ],
            "estimated_time": "15-30 minutes",
            "tips": [
                "Keep all documents ready before starting",
                "Use a good internet connection",
                "Save your application ID for tracking"
            ]
        }
    
    def build_document_checklist(self, scheme: Dict, user_profile: Dict) -> Dict:
        """
        Build personalized document checklist
        """
        base_docs = ["Aadhaar Card", "Bank Account Details", "Passport Photo"]
        scheme_docs = scheme.get("documents", "").split(",") if scheme.get("documents") else []
        
        all_docs = base_docs + [d.strip() for d in scheme_docs if d.strip()]
        
        return {
            "type": "document_checklist",
            "scheme_name": scheme.get("name", ""),
            "documents": [
                {
                    "name": doc,
                    "required": True,
                    "uploaded": False,
                    "help": self._get_document_help(doc)
                }
                for doc in all_docs
            ]
        }
    
    def _get_document_help(self, doc_name: str) -> str:
        """Get help text for document"""
        help_map = {
            "Aadhaar Card": "12-digit unique ID issued by UIDAI. Upload clear photo of both sides.",
            "PAN Card": "10-character alphanumeric ID for tax purposes.",
            "Income Certificate": "Issued by Tehsildar/Revenue Officer showing annual income.",
            "Caste Certificate": "Issued by competent authority for SC/ST/OBC categories.",
            "Bank Account Details": "Passbook first page or cancelled cheque.",
            "Passport Photo": "Recent color photo with white background.",
        }
        return help_map.get(doc_name, "Upload clear, readable copy of this document.")
    
    def get_conversation_prompt(self, intent: ConversationState, entities: Dict, 
                                language: str, user_profile: Dict = None) -> str:
        """
        Build specialized prompt based on conversation state
        """
        prompts = {
            ConversationState.APPLICATION_GUIDANCE: f"""
You are helping the user apply for a government scheme. Provide clear, step-by-step guidance.
Be encouraging and patient. Break down complex processes into simple steps.
Language: {language}
Entities: {json.dumps(entities, ensure_ascii=False)}
""",
            ConversationState.DOCUMENT_HELP: f"""
You are helping the user understand and prepare documents for scheme application.
Explain what each document is, where to get it, and how to upload it properly.
Language: {language}
""",
            ConversationState.ELIGIBILITY_CHECK: f"""
You are checking if the user is eligible for schemes. Ask clarifying questions about:
- Age, income, location, occupation, family size
Be conversational and friendly. Don't ask all questions at once.
Language: {language}
User Profile: {json.dumps(user_profile or {}, ensure_ascii=False)}
""",
            ConversationState.PROFILE_COLLECTION: f"""
You are collecting user profile information to provide personalized recommendations.
Ask one question at a time. Be friendly and explain why you need this information.
Language: {language}
""",
        }
        
        return prompts.get(intent, "")
