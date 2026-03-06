"""
user_profile_service.py — User Profile Management

Handles user profile creation, updates, and personalized recommendations
"""

import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os


class UserProfileService:
    """
    Manages user profiles for personalized scheme recommendations
    """
    
    def __init__(self, table_name: str = None, region: str = None):
        self.region = region or os.getenv("DATA_REGION", "us-east-1")
        self.table_name = table_name or os.getenv("USERS_TABLE", "welfare-users")
        
        try:
            dynamodb = boto3.resource("dynamodb", region_name=self.region)
            self.table = dynamodb.Table(self.table_name)
        except Exception:
            self.table = None
    
    def create_or_update_profile(self, user_id: str, profile_data: Dict) -> Dict:
        """
        Create or update user profile
        
        Args:
            user_id: Unique user identifier
            profile_data: Dictionary containing profile information
        
        Returns:
            Updated profile dictionary
        """
        if not self.table:
            return profile_data
        
        profile = {
            "userId": user_id,
            "updated": datetime.now().isoformat(),
            **profile_data
        }
        
        try:
            self.table.put_item(Item=profile)
            return profile
        except Exception as e:
            print(f"Error saving profile: {e}")
            return profile_data
    
    def get_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile by ID"""
        if not self.table:
            return None
        
        try:
            response = self.table.get_item(Key={"userId": user_id})
            return response.get("Item")
        except Exception:
            return None
    
    def extract_profile_from_conversation(self, message: str, 
                                         current_profile: Dict = None) -> Dict:
        """
        Extract profile information from user message
        
        Args:
            message: User's message
            current_profile: Existing profile data
        
        Returns:
            Updated profile dictionary
        """
        profile = current_profile or {}
        msg_lower = message.lower()
        
        # Extract occupation
        occupation_map = {
            "farmer": ["farmer", "किसान", "రైతు", "விவசாயி", "কৃষক", "शेतकरी"],
            "student": ["student", "छात्र", "విద్యార్థి", "மாணவர்", "ছাত্র", "विद्यार्थी"],
            "teacher": ["teacher", "शिक्षक", "ఉపాధ్యాయుడు", "ஆசிரியர்", "শিক্ষক"],
            "business_owner": ["business", "व्यवसाय", "వ్యాపారం", "வணிகம்", "ব্যবসা"],
            "daily_wage": ["labor", "मजदूर", "కూలీ", "கூலி", "শ্রমিক"],
            "unemployed": ["unemployed", "बेरोजगार", "నిరుద్యోగి", "வேலையில்லாத"],
        }
        
        for occ, keywords in occupation_map.items():
            if any(kw in msg_lower for kw in keywords):
                profile["occupation"] = occ
                break
        
        # Extract state/location
        states = {
            "UP": ["uttar pradesh", "up", "यूपी", "उत्तर प्रदेश"],
            "Maharashtra": ["maharashtra", "महाराष्ट्र", "మహారాష్ట్ర"],
            "Tamil Nadu": ["tamil nadu", "तमिलनाडु", "తమిళనాడు", "தமிழ்நாடு"],
            "Karnataka": ["karnataka", "कर्नाटक", "కర్ణాటక", "ಕರ್ನಾಟಕ"],
            "West Bengal": ["west bengal", "bengal", "পশ্চিমবঙ্গ"],
            "Gujarat": ["gujarat", "गुजरात", "ગુજરાત"],
            "Rajasthan": ["rajasthan", "राजस्थान"],
            "Andhra Pradesh": ["andhra", "ఆంధ్రప్రదేశ్"],
            "Telangana": ["telangana", "తెలంగాణ"],
            "Kerala": ["kerala", "കേരളം"],
        }
        
        for state, keywords in states.items():
            if any(kw in msg_lower for kw in keywords):
                profile["state"] = state
                break
        
        # Extract income (rough estimation from keywords)
        if any(word in msg_lower for word in ["poor", "गरीब", "పేద", "ஏழை", "দরিদ্র"]):
            profile["income_bracket"] = "below_poverty_line"
        elif any(word in msg_lower for word in ["middle", "मध्यम", "మధ్యతరగతి"]):
            profile["income_bracket"] = "middle_class"
        
        # Extract land ownership (for farmers)
        if "acre" in msg_lower or "एकड़" in msg_lower or "ఎకరం" in msg_lower:
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                profile["land_acres"] = int(numbers[0])
        
        # Extract age group
        if any(word in msg_lower for word in ["old", "senior", "बुजुर्ग", "వృద్ధ", "முதியவர்"]):
            profile["age_group"] = "senior_citizen"
        elif any(word in msg_lower for word in ["young", "youth", "युवा", "యువత", "இளைஞர்"]):
            profile["age_group"] = "youth"
        
        # Extract gender
        if any(word in msg_lower for word in ["woman", "female", "महिला", "మహిళ", "பெண்", "মহিলা"]):
            profile["gender"] = "female"
        elif any(word in msg_lower for word in ["man", "male", "पुरुष", "పురుషుడు", "ஆண்"]):
            profile["gender"] = "male"
        
        # Extract category
        if any(word in msg_lower for word in ["sc", "st", "obc", "अनुसूचित"]):
            profile["category"] = "reserved"
        
        return profile
    
    def get_personalized_schemes(self, profile: Dict, all_schemes: List[Dict]) -> List[Dict]:
        """
        Filter and rank schemes based on user profile
        
        Args:
            profile: User profile dictionary
            all_schemes: List of all available schemes
        
        Returns:
            Sorted list of relevant schemes
        """
        scored_schemes = []
        
        for scheme in all_schemes:
            score = 0
            reasons = []
            
            # Match occupation
            occupation = profile.get("occupation", "").lower()
            category = scheme.get("category", "").lower()
            
            if occupation == "farmer" and category == "agriculture":
                score += 10
                reasons.append("Matches your occupation")
            
            if occupation == "student" and category == "education":
                score += 10
                reasons.append("Education scheme for students")
            
            if profile.get("gender") == "female" and category == "women":
                score += 10
                reasons.append("Women-specific scheme")
            
            if profile.get("age_group") == "senior_citizen" and category == "elderly":
                score += 10
                reasons.append("For senior citizens")
            
            # Match state
            state = profile.get("state", "")
            scheme_states = scheme.get("states", "ALL")
            if state and (state in scheme_states or scheme_states == "ALL"):
                score += 5
                if scheme_states != "ALL":
                    reasons.append(f"Available in {state}")
            
            # Income-based schemes
            if profile.get("income_bracket") == "below_poverty_line":
                if any(word in scheme.get("who_can_apply", "").lower() 
                       for word in ["bpl", "poor", "low income"]):
                    score += 8
                    reasons.append("For low-income families")
            
            if score > 0:
                scored_schemes.append({
                    "scheme": scheme,
                    "score": score,
                    "reasons": reasons
                })
        
        # Sort by score
        scored_schemes.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_schemes[:5]  # Top 5 schemes
    
    def get_missing_profile_fields(self, profile: Dict) -> List[str]:
        """
        Identify missing profile fields for better recommendations
        
        Returns:
            List of missing field names
        """
        important_fields = [
            "occupation",
            "state",
            "age_group",
            "income_bracket",
            "gender"
        ]
        
        missing = [field for field in important_fields if not profile.get(field)]
        return missing
    
    def generate_profile_question(self, missing_field: str, language: str) -> str:
        """
        Generate a friendly question to collect missing profile information
        """
        questions = {
            "occupation": {
                "hi": "आप क्या काम करते हैं? (किसान, छात्र, व्यवसाय, आदि)",
                "en": "What is your occupation? (farmer, student, business, etc.)",
                "ta": "உங்கள் தொழில் என்ன? (விவசாயி, மாணவர், வணிகம், போன்றவை)",
                "te": "మీ వృత్తి ఏమిటి? (రైతు, విద్యార్థి, వ్యాపారం, మొదలైనవి)",
            },
            "state": {
                "hi": "आप किस राज्य में रहते हैं?",
                "en": "Which state do you live in?",
                "ta": "நீங்கள் எந்த மாநிலத்தில் வசிக்கிறீர்கள்?",
                "te": "మీరు ఏ రాష్ట్రంలో నివసిస్తున్నారు?",
            },
            "age_group": {
                "hi": "आपकी उम्र कितनी है? (युवा, मध्यम आयु, वरिष्ठ नागरिक)",
                "en": "What is your age group? (youth, middle-aged, senior citizen)",
                "ta": "உங்கள் வயது என்ன? (இளைஞர், நடுத்தர வயது, மூத்த குடிமகன்)",
                "te": "మీ వయస్సు ఎంత? (యువత, మధ్య వయస్సు, సీనియర్ సిటిజన్)",
            },
            "income_bracket": {
                "hi": "आपकी वार्षिक आय कितनी है? (गरीबी रेखा से नीचे, मध्यम वर्ग, उच्च)",
                "en": "What is your annual income? (below poverty line, middle class, high)",
                "ta": "உங்கள் ஆண்டு வருமானம் என்ன?",
                "te": "మీ వార్షిక ఆదాయం ఎంత?",
            },
            "gender": {
                "hi": "आपका लिंग क्या है?",
                "en": "What is your gender?",
                "ta": "உங்கள் பாலினம் என்ன?",
                "te": "మీ లింగం ఏమిటి?",
            }
        }
        
        return questions.get(missing_field, {}).get(language, 
                                                    questions.get(missing_field, {}).get("en", ""))
