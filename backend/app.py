"""
app_enhanced.py — Enhanced Bharat Scheme Mitra with Conversational AI

NEW FEATURES:
✅ Multi-turn conversational AI with context awareness
✅ User profile management for personalized recommendations
✅ Step-by-step application guidance
✅ Interactive document processing with guidance
✅ Application status tracking
✅ Intelligent intent detection and routing
✅ Enhanced multilingual support (15 languages)
✅ Sentiment analysis for user satisfaction
"""

import base64
import boto3
import json
import uuid
import time
import io
import os
import urllib.request
import requests as http_requests
import re
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv

# Import our new services
from conversation_engine import ConversationEngine, ConversationState
from user_profile_service import UserProfileService
from conversation_state_manager import ConversationFlowController
from aws_services_integration import AWSServicesOrchestrator

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "rkss-r6710-bucket")
DATA_REGION = os.getenv("DATA_REGION", "").strip() or None

SESSIONS_TABLE_NAME = os.getenv("SESSIONS_TABLE", "user-sessions")
USERS_TABLE_NAME = os.getenv("USERS_TABLE", "user-profiles")
SCHEMES_CACHE_TABLE_NAME = os.getenv("SCHEMES_CACHE_TABLE", "schemeuser")
INDICTRANS2_URL = os.getenv("INDICTRANS2_URL", "http://localhost:5001")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

# Use Amazon Nova Lite (AWS Free Tier - Safe for hackathon)
MODEL_ID = "amazon.nova-lite-v1:0"

# ─────────────────────────────────────────────────────────────
# LANGUAGE MAPS
# ─────────────────────────────────────────────────────────────
LANG_NAME = {
    "hi": "Hindi",
    "en": "English",
    "ta": "Tamil",
    "te": "Telugu",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
}

TRANSCRIBE_LANG_MAP = {
    "hi": "hi-IN",  # Hindi - SUPPORTED by AWS Transcribe
    "en": "en-IN",  # English - SUPPORTED
    "ta": "ta-IN",  # Tamil - SUPPORTED
    "te": "te-IN",  # Telugu - SUPPORTED
    "mr": "mr-IN",  # Marathi - SUPPORTED
    # Languages below may have limited or no support - will fallback to en-IN
    "bn": "en-IN",  # Bengali - Fallback to English (limited support)
    "gu": "en-IN",  # Gujarati - Fallback to English (limited support)
    "kn": "en-IN",  # Kannada - Fallback to English (limited support)
    "ml": "en-IN",  # Malayalam - Fallback to English (limited support)
    "pa": "en-IN",  # Punjabi - Fallback to English (limited support)
    "or": "en-IN",  # Odia - Fallback to English (not supported)
    "as": "en-IN",  # Assamese - Fallback to English (not supported)
    "ur": "en-IN",  # Urdu - Fallback to English (not supported)
}

# Languages with full AWS Transcribe support
TRANSCRIBE_SUPPORTED = ["hi", "en", "ta", "te", "mr"]

POLLY_VOICES = {
    "hi": ("Kajal", "hi-IN", "neural"),
    "en": ("Raveena", "en-IN", "neural"),
}

# ─────────────────────────────────────────────────────────────
# AWS CLIENTS
# ─────────────────────────────────────────────────────────────
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
comprehend = boto3.client("comprehend", region_name=BEDROCK_REGION)
sns_client = boto3.client("sns", region_name=BEDROCK_REGION)

s3_client = None
dynamodb = None
transcribe_cl = None
polly = None
textract = None
sessions_table = None
users_table = None
schemes_cache_table = None


def detect_bucket_region(bucket: str) -> str:
    tmp = boto3.client("s3")
    resp = tmp.get_bucket_location(Bucket=bucket)
    return resp.get("LocationConstraint") or "us-east-1"


def init_data_clients():
    global DATA_REGION, s3_client, dynamodb, transcribe_cl
    global polly, textract, sessions_table, users_table, schemes_cache_table

    if DATA_REGION is None:
        DATA_REGION = detect_bucket_region(S3_BUCKET)

    s3_client = boto3.client("s3", region_name=DATA_REGION)
    dynamodb = boto3.resource("dynamodb", region_name=DATA_REGION)
    transcribe_cl = boto3.client("transcribe", region_name=DATA_REGION)
    polly = boto3.client("polly", region_name=DATA_REGION)
    textract = boto3.client("textract", region_name=DATA_REGION)

    try:
        sessions_table = dynamodb.Table(SESSIONS_TABLE_NAME)
        users_table = dynamodb.Table(USERS_TABLE_NAME)
        schemes_cache_table = dynamodb.Table(SCHEMES_CACHE_TABLE_NAME)
        print(
            f"✅ DynamoDB tables initialized: {SESSIONS_TABLE_NAME}, {USERS_TABLE_NAME}, {SCHEMES_CACHE_TABLE_NAME}"
        )
    except Exception as e:
        print(f"⚠️  DynamoDB initialization warning: {e}")
        sessions_table = None
        users_table = None
        schemes_cache_table = None


init_data_clients()

# ─────────────────────────────────────────────────────────────
# SCHEME CACHING FUNCTIONS
# ─────────────────────────────────────────────────────────────


def get_cached_schemes(occupation: str):
    """Get schemes from cache for given occupation"""
    if not schemes_cache_table:
        return None

    try:
        response = schemes_cache_table.get_item(Key={"occupation": occupation.lower()})
        if "Item" in response:
            print(f"✅ Cache hit for occupation: {occupation}")
            return response["Item"].get("schemes", [])
        return None
    except Exception as e:
        print(f"⚠️  Cache read error: {e}")
        return None


def cache_schemes_for_occupation(occupation: str, schemes: list):
    """Cache schemes for given occupation"""
    if not schemes_cache_table:
        return False

    try:
        schemes_cache_table.put_item(
            Item={
                "occupation": occupation.lower(),
                "schemes": schemes,
                "lastUpdated": datetime.now().isoformat(),
                "count": len(schemes),
            }
        )
        print(f"✅ Cached {len(schemes)} schemes for occupation: {occupation}")
        return True
    except Exception as e:
        print(f"⚠️  Cache write error: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# SMS NOTIFICATION FUNCTIONS
# ─────────────────────────────────────────────────────────────
def send_sms_notification(phone_number: str, message: str):
    """Send SMS notification via SNS"""
    if not SNS_TOPIC_ARN or not phone_number:
        print("⚠️  SNS not configured or phone number missing")
        return False

    try:
        # Format phone number (must start with +91 for India)
        if not phone_number.startswith("+"):
            phone_number = "+91" + phone_number.replace(" ", "").replace("-", "")

        response = sns_client.publish(
            PhoneNumber=phone_number,
            Message=message,
            MessageAttributes={
                "AWS.SNS.SMS.SMSType": {
                    "DataType": "String",
                    "StringValue": "Transactional",
                }
            },
        )
        print(f"📱 SMS sent to {phone_number}: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"❌ SMS error: {e}")
        return False


def send_scheme_notification(phone_number: str, scheme_name: str, language: str = "en"):
    """Send scheme application confirmation SMS"""
    messages = {
        "en": f"✅ Your application for {scheme_name} has been received. You will be notified about the status. - Bharat Scheme Mitra",
        "hi": f"✅ {scheme_name} के लिए आपका आवेदन प्राप्त हो गया है। स्थिति के बारे में सूचित किया जाएगा। - भारत स्कीम मित्र",
        "te": f"✅ {scheme_name} కోసం మీ దరఖాస్తు స్వీకరించబడింది. స్థితి గురించి తెలియజేయబడుతుంది. - భారత్ స్కీమ్ మిత్ర",
    }

    message = messages.get(language, messages["en"])
    return send_sms_notification(phone_number, message)


# ─────────────────────────────────────────────────────────────
# LOAD SCHEMES
# ─────────────────────────────────────────────────────────────
_base = os.path.dirname(os.path.abspath(__file__))
_schemes_path = os.path.join(_base, "..", "data", "schemes.json")

with open(_schemes_path, "r", encoding="utf-8") as f:
    SCHEMES = json.load(f)

SCHEMES_TEXT = "\n\n".join(
    [
        f"SCHEME: {s.get('name', '')}\n"
        f"Category: {s.get('category', '')}\n"
        f"Benefit: {s.get('benefit', '')}\n"
        f"Eligibility: {s.get('who_can_apply', '')}\n"
        f"Documents: {s.get('documents', '')}\n"
        f"How to apply: {s.get('how_to_apply', '')}"
        for s in SCHEMES
    ]
)

# Initialize services
conversation_engine = ConversationEngine(SCHEMES)
profile_service = UserProfileService(USERS_TABLE_NAME, DATA_REGION)
aws_orchestrator = AWSServicesOrchestrator(region=DATA_REGION)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────


def strip_emojis(text: str) -> str:
    """Remove all emojis from text for TTS processing"""
    emoji_pattern = re.compile(
        "["
        "\U0001f300-\U0001f9ff"  # Emoticons
        "\U00002600-\U000027bf"  # Misc symbols
        "\U0001f000-\U0001f02f"  # Mahjong tiles
        "\U0001f0a0-\U0001f0ff"  # Playing cards
        "\U0001f100-\U0001f64f"  # Enclosed characters
        "\U0001f680-\U0001f6ff"  # Transport & map
        "\U0001f900-\U0001f9ff"  # Supplemental symbols
        "\U0001fa00-\U0001fa6f"  # Chess symbols
        "\U0001fa70-\U0001faff"  # Symbols and pictographs
        "\U00002300-\U000023ff"  # Misc technical
        "\U00002b50\U00002b55"  # Stars
        "\U0000231a-\U0000231b"  # Watch
        "\U00002328\U000023cf"  # Keyboard
        "\U000023e9-\U000023fa"  # Media controls
        "\U000024c2\U000025aa-\U000025fe"  # Geometric shapes
        "\U00002600-\U00002604\U0000260e\U00002611"  # Weather
        "\U00002614-\U00002615\U00002618\U0000261d"  # Umbrella, coffee
        "\U00002620\U00002622-\U00002623\U00002626"  # Hazard symbols
        "\U0000262a\U0000262e-\U0000263a"  # Religious symbols
        "\U00002640\U00002642"  # Gender symbols
        "\U00002648-\U00002653"  # Zodiac
        "\U0000265f-\U00002660\U00002663\U00002665-\U00002666"  # Card suits
        "\U00002668\U0000267b\U0000267e-\U0000267f"  # Misc
        "\U00002692-\U00002697\U00002699\U0000269b-\U0000269c"  # Tools
        "\U000026a0-\U000026a1\U000026a7\U000026aa-\U000026ab"  # Warning
        "\U000026b0-\U000026b1\U000026bd-\U000026be\U000026c4-\U000026c5"  # Sports
        "\U000026c8\U000026ce-\U000026cf\U000026d1\U000026d3-\U000026d4"  # Weather
        "\U000026e9-\U000026ea\U000026f0-\U000026f5\U000026f7-\U000026fa\U000026fd"  # Buildings
        "\U00002702\U00002705\U00002708-\U0000270d\U0000270f"  # Scissors, plane
        "\U00002712\U00002714\U00002716\U0000271d\U00002721"  # Check marks
        "\U00002728\U00002733-\U00002734\U00002744\U00002747"  # Sparkles
        "\U0000274c\U0000274e\U00002753-\U00002755\U00002757"  # X marks, question
        "\U00002763-\U00002764\U00002795-\U00002797\U000027a1"  # Hearts, plus
        "\U000027b0\U000027bf\U00002934-\U00002935"  # Curly loop
        "\U00002b05-\U00002b07\U00002b1b-\U00002b1c\U00002b50\U00002b55"  # Arrows
        "\U00003030\U0000303d\U00003297\U00003299"  # Wavy dash
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def contains_devanagari(text: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", text or ""))


def indictrans2_health() -> bool:
    try:
        r = http_requests.get(f"{INDICTRANS2_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# Translation cache to speed up repeated translations
TRANSLATION_CACHE = {}


def translate_text(text: str, source: str, target: str) -> str:
    """Translate using Amazon Translate (AWS Native). Falls back to original on error."""
    if not text or not text.strip() or source == target:
        return text

    # Check cache first
    cache_key = f"{source}:{target}:{text[:100]}"
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]

    # Amazon Translate language codes
    translate_lang_map = {
        "hi": "hi",
        "en": "en",
        "ta": "ta",
        "te": "te",
        "bn": "bn",
        "mr": "mr",
        "gu": "gu",
        "kn": "kn",
        "ml": "ml",
        "pa": "pa",
        "or": "or",
        "as": "as",
        "ur": "ur",
    }

    source_code = translate_lang_map.get(source, "en")
    target_code = translate_lang_map.get(target, "en")

    if source_code == target_code:
        return text

    try:
        # Use Amazon Translate with timeout
        translate_client = boto3.client("translate", region_name=BEDROCK_REGION)
        response = translate_client.translate_text(
            Text=text[:5000],  # Amazon Translate limit
            SourceLanguageCode=source_code,
            TargetLanguageCode=target_code,
        )

        translated = response.get("TranslatedText", text)

        # Cache the result
        TRANSLATION_CACHE[cache_key] = translated

        return translated

    except Exception as e:
        app.logger.error(f"❌ Translation error ({source}→{target}): {e}")
        # Fallback: return original text
        return text


def translate_batch(texts: list, source: str, target: str) -> list:
    """Batch translate multiple texts at once for better performance"""
    if not texts or source == target:
        return texts

    # Filter out empty texts
    texts = [str(t) if t else "" for t in texts]
    if not any(texts):
        return texts

    # Amazon Translate language codes
    translate_lang_map = {
        "hi": "hi",
        "en": "en",
        "ta": "ta",
        "te": "te",
        "bn": "bn",
        "mr": "mr",
        "gu": "gu",
        "kn": "kn",
        "ml": "ml",
        "pa": "pa",
        "or": "or",
        "as": "as",
        "ur": "ur",
    }

    source_code = translate_lang_map.get(source, "en")
    target_code = translate_lang_map.get(target, "en")

    if source_code == target_code:
        return texts

    try:
        # Combine texts with unique separator
        separator = " |||SEP||| "
        combined = separator.join(texts)

        # Limit to AWS Translate max
        if len(combined) > 5000:
            # Fallback to individual translations for very long texts
            return [translate_text(t, source, target) for t in texts]

        translate_client = boto3.client("translate", region_name=BEDROCK_REGION)
        response = translate_client.translate_text(
            Text=combined,
            SourceLanguageCode=source_code,
            TargetLanguageCode=target_code,
        )

        translated = response.get("TranslatedText", combined)
        result = translated.split(separator)

        # Ensure we have the same number of results
        if len(result) != len(texts):
            app.logger.warning(f"⚠️ Batch translation mismatch: {
                    len(texts)} inputs, {
                    len(result)} outputs")
            return texts

        return result

    except Exception as e:
        app.logger.error(f"❌ Batch translation error: {e}")
        # Fallback to individual translations
        return [translate_text(t, source, target) for t in texts]


def detect_language_comprehend(text: str) -> str:
    """Use Amazon Comprehend to auto-detect language."""
    try:
        resp = comprehend.detect_dominant_language(Text=text[:300])
        langs = resp.get("Languages", [])
        if langs:
            code = langs[0]["LanguageCode"]
            return code if code in LANG_NAME else "en"
    except Exception:
        pass
    return "en"


def analyze_sentiment_comprehend(text: str, lang: str = "en") -> str:
    """Use Amazon Comprehend for sentiment analysis."""
    supported = {"en", "hi", "de", "fr", "es", "it", "pt", "ja", "zh", "ko", "ar"}
    lang_code = lang if lang in supported else "en"
    try:
        text_for_analysis = (
            text if lang_code == lang else translate_text(text, lang, "en")
        )
        resp = comprehend.detect_sentiment(
            Text=text_for_analysis[:5000], LanguageCode=lang_code
        )
        return resp.get("Sentiment", "NEUTRAL")
    except Exception:
        return "NEUTRAL"


# ─────────────────────────────────────────────────────────────
# DYNAMO CHAT HISTORY
# ─────────────────────────────────────────────────────────────


def get_session_data(session_id: str) -> dict:
    """Get complete session data including history and state"""
    if not sessions_table:
        return {"history": [], "state": None, "user_profile": {}, "flow_state": {}}
    try:
        resp = sessions_table.get_item(Key={"sessionId": session_id})
        item = resp.get("Item", {})
        return {
            "history": item.get("history", []),
            "state": item.get("conversation_state"),
            "user_profile": item.get("user_profile", {}),
            "context": item.get("context", {}),
            "flow_state": item.get("flow_state", {}),
        }
    except Exception:
        return {
            "history": [],
            "state": None,
            "user_profile": {},
            "context": {},
            "flow_state": {},
        }


def save_session_data(
    session_id: str,
    history: list,
    state: str = None,
    user_profile: dict = None,
    context: dict = None,
    flow_state: dict = None,
):
    """Save complete session data"""
    if not sessions_table:
        return
    ttl = int(datetime.now().timestamp()) + (30 * 24 * 3600)
    try:
        item = {
            "sessionId": session_id,
            "history": history[-20:],
            "updated": datetime.now().isoformat(),
            "ttl": ttl,
        }
        if state:
            item["conversation_state"] = state
        if user_profile:
            item["user_profile"] = user_profile
        if context:
            item["context"] = context
        if flow_state:
            item["flow_state"] = flow_state

        sessions_table.put_item(Item=item)
    except Exception as e:
        app.logger.warning(f"DynamoDB save failed: {e}")


# ─────────────────────────────────────────────────────────────
# BEDROCK — Amazon Nova Lite (AWS Free Tier)
# ─────────────────────────────────────────────────────────────


def call_nova(messages: list, system_text: str) -> str:
    """Call AWS Bedrock - Nova Lite model"""
    converse_messages = [
        {"role": m["role"], "content": [{"text": m["content"]}]} for m in messages
    ]
    resp = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": system_text}],
        messages=converse_messages,
        inferenceConfig={"maxTokens": 2048, "temperature": 0.7},
    )
    return resp["output"]["message"]["content"][0]["text"]


# ─────────────────────────────────────────────────────────────
# ENHANCED CONVERSATIONAL CHAT
# ─────────────────────────────────────────────────────────────


def get_conversational_reply(user_message: str, session_id: str, language: str) -> dict:
    """
    Enhanced conversational reply with intent detection and context management
    NOW WITH: Smart question management to prevent repetition
    """
    app.logger.info(
        f"🔍 Processing message: '{user_message[:100]}...' | Session: {session_id} | Language: {language}"
    )

    # Check for simple greetings - don't show schemes, just greet back
    msg_lower = user_message.lower().strip()
    greeting_keywords = [
        "hello",
        "hi",
        "hey",
        "namaste",
        "namaskar",
        "vanakkam",
        "namaskaram",
        "hola",
        "bonjour",
        "hallo",
        "ciao",
        "ola",
        "salaam",
        "salam",
    ]

    # If it's JUST a greeting (short message with greeting word), respond
    # simply
    if any(msg_lower == kw for kw in greeting_keywords) or (
        len(msg_lower) < 15 and any(kw in msg_lower for kw in greeting_keywords)
    ):
        greetings = {
            "hi": "नमस्ते! 🙏 मैं भारत स्कीम मित्र हूं। मैं आपकी सरकारी योजनाओं के बारे में जानकारी देने में मदद कर सकता हूं। आप मुझसे क्या जानना चाहेंगे?",
            "en": "Hello! 🙏 I am Bharat Scheme Mitra. I can help you learn about government welfare schemes. What would you like to know?",
            "te": "నమస్కారం! 🙏 నేను భారత్ స్కీమ్ మిత్రా. నేను మీకు ప్రభుత్వ సంక్షేమ పథకాల గురించి తెలుసుకోవడంలో సహాయం చేయగలను. మీరు ఏమి తెలుసుకోవాలనుకుంటున్నారు?",
            "ta": "வணக்கம்! 🙏 நான் பாரத் திட்ட மித்ரா. அரசு நல திட்டங்கள் பற்றி அறிய உங்களுக்கு உதவ முடியும். நீங்கள் என்ன தெரிந்து கொள்ள விரும்புகிறீர்கள்?",
            "bn": "নমস্কার! 🙏 আমি ভারত স্কিম মিত্র। আমি আপনাকে সরকারি কল্যাণ প্রকল্প সম্পর্কে জানতে সাহায্য করতে পারি। আপনি কি জানতে চান?",
            "mr": "नमस्कार! 🙏 मी भारत स्कीम मित्र आहे। मी तुम्हाला सरकारी कल्याण योजनांबद्दल माहिती देण्यास मदत करू शकतो। तुम्हाला काय जाणून घ्यायचे आहे?",
        }
        return {
            "reply": greetings.get(language, greetings["en"]),
            "intent": "greeting",
            "user_profile": {},
            "sentiment": "NEUTRAL",
        }

    # Get session data
    session_data = get_session_data(session_id)
    history = session_data["history"]
    user_profile = session_data["user_profile"]
    context = session_data["context"]
    flow_state = session_data.get("flow_state", {})

    app.logger.info(f"📚 Session history: {
            len(history)} messages | Profile: {user_profile}")

    # Initialize or load conversation flow controller
    flow_controller = ConversationFlowController()
    if flow_state:
        flow_controller.load_state(flow_state)

    # Update user profile from message
    updated_profile = profile_service.extract_profile_from_conversation(
        user_message, user_profile
    )

    # Analyze intent
    intent_data = conversation_engine.analyze_intent(user_message, history)
    intent = intent_data["intent"]
    entities = intent_data["entities"]

    app.logger.info(f"🎯 Intent detected: {
            intent.value} | Entities: {entities}")

    # Check sentiment
    sentiment = analyze_sentiment_comprehend(user_message, language)

    # Process message through flow controller to check for repetitive questions
    flow_decision = flow_controller.process_user_message(
        user_message, updated_profile, intent.value, language
    )

    # Build context-aware system prompt
    system_prompt = build_enhanced_system_prompt(
        intent, entities, language, updated_profile, sentiment, flow_decision
    )

    # Translate to English for reasoning if needed
    reasoning_input = user_message
    if language != "en":
        reasoning_input = translate_text(user_message, language, "en")

    # Prepare conversation history
    history.append({"role": "user", "content": user_message})
    short_history = history[-6:]
    short_history[-1] = {"role": "user", "content": reasoning_input}

    # CRITICAL FIX: Ensure conversation starts with user message
    # AWS Bedrock requires first message to be from user, not assistant
    while short_history and short_history[0]["role"] != "user":
        short_history.pop(0)

    # If history is empty or has no user message, create one
    if not short_history:
        short_history = [{"role": "user", "content": reasoning_input}]

    app.logger.info(f"🤖 Calling AI with {
            len(short_history)} messages | Intent: {
            intent.value}")
    app.logger.info(f"📋 First message role: {
            short_history[0]['role']}")  # Debug log

    # Get AI response
    try:
        raw_response = call_nova(short_history, system_prompt)
        app.logger.info(
            f"✅ AI response received: {len(raw_response)} chars | First 100: {raw_response[:100]}..."
        )
    except Exception as e:
        app.logger.error(f"❌ AI call failed: {e}", exc_info=True)
        raise

    # Parse response
    response_data = parse_ai_response(raw_response, intent, language, entities)
    app.logger.info(f"📦 Parsed response type: {
            response_data.get('type') if isinstance(
                response_data,
                dict) else type(response_data)}")

    # TRANSLATE RESPONSE TO TARGET LANGUAGE
    if language != "en" and isinstance(response_data, dict):
        app.logger.info(f"🌍 Translating response to {language}")

        # Translate all text fields in the response
        if "intro" in response_data:
            original = response_data["intro"]
            response_data["intro"] = translate_text(
                response_data["intro"], "en", language
            )
            app.logger.info(
                f"📝 Translated intro: {original[:50]}... → {response_data['intro'][:50]}..."
            )

        if "text" in response_data:
            response_data["text"] = translate_text(
                response_data["text"], "en", language
            )

        if "follow_up" in response_data:
            response_data["follow_up"] = translate_text(
                response_data["follow_up"], "en", language
            )

        if "question" in response_data:
            response_data["question"] = translate_text(
                response_data["question"], "en", language
            )

        # Translate steps in application guidance (OPTIMIZED: Batch
        # translation)
        if "steps" in response_data and isinstance(response_data["steps"], list):
            app.logger.info(
                f"📋 Translating {len(response_data['steps'])} steps (batch mode)"
            )

            # Collect all step texts
            step_texts = []
            for step in response_data["steps"]:
                if "title" in step:
                    step_texts.append(step["title"])
                if "description" in step:
                    step_texts.append(step["description"])

            # Batch translate
            if step_texts:
                translated_steps = translate_batch(step_texts, "en", language)

                # Apply back
                idx = 0
                for step in response_data["steps"]:
                    if "title" in step and idx < len(translated_steps):
                        step["title"] = translated_steps[idx]
                        idx += 1
                    if "description" in step and idx < len(translated_steps):
                        step["description"] = translated_steps[idx]
                        idx += 1

        # Translate scheme descriptions (OPTIMIZED: Batch translation)
        if "schemes" in response_data and isinstance(response_data["schemes"], list):
            app.logger.info(
                f"🎯 Translating {len(response_data['schemes'])} schemes (batch mode)"
            )

            # Collect all texts to translate
            texts_to_translate = []
            for scheme in response_data["schemes"]:
                if "benefit" in scheme:
                    texts_to_translate.append(scheme["benefit"])
                if "who_can_apply" in scheme:
                    texts_to_translate.append(scheme["who_can_apply"])
                if "eligibility" in scheme and isinstance(scheme["eligibility"], str):
                    texts_to_translate.append(scheme["eligibility"])

            # Batch translate all at once
            if texts_to_translate:
                translated_texts = translate_batch(texts_to_translate, "en", language)

                # Apply translations back
                idx = 0
                for scheme in response_data["schemes"]:
                    if "benefit" in scheme and idx < len(translated_texts):
                        scheme["benefit"] = translated_texts[idx]
                        idx += 1
                    if "who_can_apply" in scheme and idx < len(translated_texts):
                        scheme["who_can_apply"] = translated_texts[idx]
                        idx += 1
                    if (
                        "eligibility" in scheme
                        and isinstance(scheme["eligibility"], str)
                        and idx < len(translated_texts)
                    ):
                        scheme["eligibility"] = translated_texts[idx]
                        idx += 1

    # IMPORTANT: Remove follow-up question if flow controller says not to ask
    if not flow_decision["should_ask_question"]:
        if isinstance(response_data, dict):
            response_data.pop("follow_up", None)
            response_data.pop("question", None)
    else:
        # Use the smart question from flow controller
        if flow_decision["question"]:
            if isinstance(response_data, dict):
                response_data["follow_up"] = flow_decision["question"]

    # Save session with flow state
    history.append(
        {"role": "assistant", "content": json.dumps(response_data, ensure_ascii=False)}
    )
    save_session_data(
        session_id,
        history,
        state=intent.value,
        user_profile=updated_profile,
        context={"last_intent": intent.value, "sentiment": sentiment},
        flow_state=flow_controller.get_state(),
    )

    return {
        "reply": response_data,
        "intent": intent.value,
        "user_profile": updated_profile,
        "sentiment": sentiment,
        "flow_info": {
            "should_ask_question": flow_decision["should_ask_question"],
            "reason": flow_decision["reason"],
        },
    }


def build_enhanced_system_prompt(
    intent: ConversationState,
    entities: dict,
    language: str,
    user_profile: dict,
    sentiment: str,
    flow_decision: dict = None,
) -> str:
    """Build context-aware system prompt based on conversation state"""

    base_prompt = f"""You are Bharat Scheme Mitra (भारत स्कीम मित्र), a friendly AI assistant helping
Indian citizens with government welfare schemes.

CRITICAL CONVERSATIONAL BEHAVIOR:
1) Act like a REAL HUMAN - have natural conversations
2) When user shares basic info (like "I am a farmer"), ACKNOWLEDGE and ASK if they want schemes
3) When user provides DETAILED info (document upload, multiple details), SHOW SCHEMES IMMEDIATELY
4) When user explicitly asks for schemes, SHOW THEM IMMEDIATELY

CONVERSATION FLOW:
- User says "hello" → Respond: "Hello! How can I help you today?"
- User says "I am a farmer" → Ask: "Would you like me to show you schemes for farmers?"
- User says "yes" or "show schemes" → SHOW SCHEMES IMMEDIATELY
- User uploads document with details → SHOW SCHEMES IMMEDIATELY (they're ready!)
- User provides multiple details (age, occupation, location) → SHOW SCHEMES IMMEDIATELY

USER PROFILE:
{json.dumps(user_profile, ensure_ascii=False)}

CONVERSATION STATE: {intent.value}
USER SENTIMENT: {sentiment}
LANGUAGE: {LANG_NAME.get(language, 'English')}

SCHEMES DATABASE:
{SCHEMES_TEXT}

RULES FOR SHOWING SCHEMES:
1) SHOW schemes when user:
   - Says "yes", "show", "tell me", "what schemes", "help me find", "i need schemes"
   - Uploads document with personal details
   - Provides detailed information (age, occupation, location, etc.)
   - Explicitly requests schemes
2) ASK permission only for simple statements like "I am a farmer"
3) If user has uploaded document or given details → SHOW SCHEMES NOW!

CRITICAL RULES FOR QUESTIONS:
1) DO NOT ask questions that are already answered in the user profile above
2) DO NOT repeat questions you've already asked
3) If user has provided details or uploaded document → SHOW SCHEMES, don't ask more questions
4) Only ask ONE question at a time, not multiple
5) If user seems frustrated (NEGATIVE sentiment), SHOW SCHEMES immediately

"""

    # Add flow decision context
    if flow_decision:
        if not flow_decision["should_ask_question"]:
            base_prompt += f"""
IMPORTANT: DO NOT ask any clarifying questions in your response.
Reason: {flow_decision["reason"]}
Provide helpful information based on what you already know.
"""
        else:
            base_prompt += f"""
You MAY ask ONE clarifying question if absolutely necessary.
Suggested question: {flow_decision.get("question", "")}
But ONLY if it's truly needed for the current request.
"""

    base_prompt += f"""
GENERAL RULES:
1) Always respond in {LANG_NAME.get(language, 'English')}
2) Be warm, friendly, and conversational like a real human
3) Keep official scheme names in English
4) Provide actionable guidance
5) Be concise and to the point
6) For simple greetings, just greet back - DON'T show schemes
7) Only show schemes when user asks: "show me schemes", "what schemes", "help me find", etc.

"""

    # Add intent-specific instructions
    if intent == ConversationState.APPLICATION_GUIDANCE:
        # Extract scheme information if available
        scheme_info = ""
        if entities.get("scheme"):
            scheme = entities["scheme"]
            scheme_info = f"""
SCHEME INFORMATION (USE THIS DATA):
Name: {scheme.get('name', '')}
Benefit: {scheme.get('benefit', '')}
Eligibility: {scheme.get('who_can_apply', '')}
Documents Required: {scheme.get('documents', '')}
How to Apply: {scheme.get('how_to_apply', '')}
Apply URL: {scheme.get('apply_url', '')}
Category: {scheme.get('category', '')}

IMPORTANT: Use the above ACTUAL scheme data to create step-by-step instructions!
"""

        base_prompt += f"""
TASK: Provide DETAILED step-by-step application guidance using ACTUAL SCHEME DATA

{scheme_info}

⚠️ CRITICAL REQUIREMENTS - MUST FOLLOW:
1. Use the ACTUAL scheme data provided above (documents, apply URL, how to apply)
2. EVERY step MUST have a "description" field with AT LEAST 2-3 COMPLETE SENTENCES
3. Descriptions must explain EXACTLY what to do - NOT just repeat the title!
4. Include SPECIFIC details from the scheme: website URLs, document names, eligibility criteria
5. Write like you're personally guiding someone through the process
6. Be encouraging, patient, and detailed
7. DO NOT ask profile questions - ONLY provide application steps
8. Use the "apply_url" field for portal links
9. Use the "documents" field for required documents
10. Use the "how_to_apply" field as guidance for creating steps

MANDATORY OUTPUT FORMAT (JSON) - FOLLOW EXACTLY:
{{
  "type": "application_guidance",
  "intro": "I'll guide you through applying for [Scheme Name]. Here are the detailed steps:",
  "scheme_name": "{entities.get('scheme', {}).get('name', 'the scheme')}",
  "steps": [
    {{
      "step": 1,
      "title": "Visit the Official Portal",
      "description": "Go to the official website at [use apply_url from scheme data] and look for the application or registration section. Click on the 'Apply Now' or 'Register' button. Make sure you have a stable internet connection and keep all required documents ready before starting.",
      "tips": ["Bookmark the website for future reference", "Use Chrome or Firefox browser for best experience"]
    }},
    {{
      "step": 2,
      "title": "Register/Login",
      "description": "If you're a new user, click on 'New Registration' and enter your mobile number and Aadhaar number. You will receive an OTP on your mobile for verification. If you already have an account, simply login with your credentials.",
      "tips": ["Keep your Aadhaar card ready", "Use a valid mobile number that you have access to"]
    }},
    {{
      "step": 3,
      "title": "Fill Application Form",
      "description": "Enter all required personal details including name, father's name, date of birth, address, and bank account details. Make sure all information matches your Aadhaar card and other documents exactly. Fill in the scheme-specific details as required.",
      "tips": ["Double-check all spellings", "Keep your bank passbook ready for account details"]
    }},
    {{
      "step": 4,
      "title": "Upload Required Documents",
      "description": "Scan and upload all required documents: [list documents from scheme data]. Each document should be clear, readable, and in PDF or JPG format with maximum size of 2MB. Make sure all four corners of the document are visible in the scan.",
      "tips": ["Use a scanner or clear mobile camera", "Ensure documents are not blurry"]
    }},
    {{
      "step": 5,
      "title": "Submit Application",
      "description": "Review all entered information carefully on the preview page. Once you're sure everything is correct, click the 'Submit' button. You will receive an application reference number via SMS and email. Save this number for tracking your application status.",
      "tips": ["Take a screenshot of the confirmation page", "Note down your application reference number"]
    }}
  ],
  "documents_needed": [list from scheme's "documents" field],
  "estimated_time": "15-30 minutes",
  "follow_up": "Would you like me to explain any specific step in more detail?"
}}

⚠️ REMEMBER:
- Use ACTUAL scheme data (apply_url, documents, how_to_apply)
- Each "description" field MUST be 2-3 COMPLETE SENTENCES with SPECIFIC DETAILS
- Include the actual website URL from apply_url field
- List actual documents from documents field
"""

    elif intent == ConversationState.ELIGIBILITY_CHECK:
        base_prompt += """
TASK: Check eligibility based on EXISTING profile information
- Review user profile above
- Match against scheme criteria
- Explain why they are or aren't eligible
- DO NOT ask for information that's already in the profile
- Only ask for missing CRITICAL information (max 1 question)

OUTPUT FORMAT (JSON):
{
  "type": "eligibility_check",
  "intro": "friendly message",
  "eligible_schemes": [{"name": "...", "reason": "..."}],
  "need_more_info": false,
  "question": "",
  "follow_up": "what they should do next"
}
"""

    elif intent == ConversationState.DOCUMENT_HELP:
        base_prompt += """
TASK: Help with document preparation
- Explain what each document is
- Where to get it
- Format requirements
- Common mistakes to avoid
- Offer to verify uploaded documents
- DO NOT ask profile questions

OUTPUT FORMAT (JSON):
{
  "type": "document_help",
  "intro": "...",
  "documents": [
    {"name": "...", "description": "...", "where_to_get": "...", "tips": ["..."]}
  ],
  "follow_up": "offer to help upload or move forward"
}
"""

    elif intent == ConversationState.PROFILE_COLLECTION:
        base_prompt += """
TASK: Acknowledge user's profile information and ASK if they want schemes
- Thank them for sharing information
- Acknowledge what they told you (e.g., "Great! I see you're a farmer")
- ASK if they would like to see relevant schemes
- DO NOT show schemes yet - wait for confirmation
- Be conversational and friendly

EXAMPLES:
User: "I am a farmer"
Response: "Great! I can help you find government schemes for farmers. Would you like me to show you some relevant schemes?"

User: "I am 65 years old"
Response: "Thank you for sharing that! There are several schemes for senior citizens. Would you like me to show you the ones you might be eligible for?"

OUTPUT FORMAT (JSON):
{
  "type": "profile_acknowledgment",
  "text": "friendly acknowledgment + question asking if they want to see schemes",
  "follow_up": "Would you like me to show you relevant schemes?"
}
"""

    else:  # SCHEME_DISCOVERY
        base_prompt += """
TASK: Show relevant government schemes based on user's request

CRITICAL: UNDERSTAND FLEXIBLE USER QUERIES!
Users may ask in MANY different ways. You MUST understand and respond with schemes for ALL these types of questions:

1. Direct scheme requests:
   - "show me schemes"
   - "what schemes are available"
   - "i need schemes"
   - "give me schemes"

2. Asking about specific schemes:
   - "i need the documents required for Stand Up India"
   - "provide me the direct link for Stand Up India portal"
   - "tell me about PM-KISAN scheme"
   - "how to apply for Ayushman Bharat"

3. Asking about scheme categories:
   - "pension schemes"
   - "farmer schemes"
   - "women schemes"
   - "education schemes"

4. Asking with profile info:
   - "i am a farmer, show schemes"
   - "schemes for senior citizens"
   - "i need pension related schemes"

FOR ALL THESE CASES: SHOW SCHEMES IN JSON FORMAT!

INTELLIGENT MATCHING:
- If user mentions a scheme name (like "Stand Up India", "PM-KISAN"), find that scheme in the database
- If user asks about documents/links for a scheme, show that specific scheme
- If user mentions a category (pension, farmer, women), show schemes from that category
- If user provides profile info, show personalized schemes
- ALWAYS show at least 3 relevant schemes

USE EXISTING USER PROFILE FOR PERSONALIZATION:
{json.dumps(user_profile, ensure_ascii=False)}

SEARCH THE SCHEMES DATABASE INTELLIGENTLY:
{SCHEMES_TEXT}

CRITICAL: YOU MUST RETURN SCHEMES IN THIS EXACT JSON FORMAT:

OUTPUT FORMAT (JSON) - MANDATORY:
{{
  "language": "{language}",
  "intro": "Based on your request, here are the relevant schemes:",
  "schemes": [
    {{
      "name": "Scheme Name (keep in English)",
      "category": "category",
      "benefit": "Benefit description",
      "why_relevant": "Why this scheme matches the user's request",
      "eligibility": "Who can apply",
      "documents": ["Document 1", "Document 2", "Document 3"],
      "apply_steps": ["Step 1", "Step 2", "Step 3"],
      "apply_url": "https://official-website.gov.in",
      "official_link": "https://official-website.gov.in"
    }},
    {{
      "name": "Second Scheme Name",
      "category": "category",
      "benefit": "Benefit description",
      "why_relevant": "Why this scheme is relevant",
      "eligibility": "Who can apply",
      "documents": ["Document 1", "Document 2"],
      "apply_steps": ["Step 1", "Step 2"],
      "apply_url": "https://official-website.gov.in",
      "official_link": "https://official-website.gov.in"
    }},
    {{
      "name": "Third Scheme Name",
      "category": "category",
      "benefit": "Benefit description",
      "why_relevant": "Why this scheme is relevant",
      "eligibility": "Who can apply",
      "documents": ["Document 1", "Document 2"],
      "apply_steps": ["Step 1", "Step 2"],
      "apply_url": "https://official-website.gov.in",
      "official_link": "https://official-website.gov.in"
    }}
  ],
  "follow_up": "Would you like detailed application guidance for any of these schemes?"
}}

MANDATORY RULES:
1. ALWAYS include "schemes" array with at least 3 schemes
2. Each scheme MUST have ALL fields: name, category, benefit, why_relevant, eligibility, documents, apply_steps, apply_url, official_link
3. Make "why_relevant" specific to the user's request
4. Include REAL government scheme URLs in apply_url and official_link
5. DO NOT return plain text - ONLY JSON with schemes array
6. If user asks about a specific scheme, include that scheme FIRST in the array
7. If user asks about documents/links, include those details in the scheme object
8. NEVER say "I apologize" or "I couldn't format" - ALWAYS return schemes JSON

EXAMPLES OF WHAT TO DO:

User asks: "i need the documents required for Stand Up India"
→ Find "Stand Up India" scheme in database
→ Return JSON with Stand Up India as first scheme
→ Include full documents list in the scheme object

User asks: "provide me the direct link for Stand Up India portal"
→ Find "Stand Up India" scheme in database
→ Return JSON with Stand Up India scheme
→ Include apply_url and official_link fields

User asks: "pension schemes"
→ Find all pension-related schemes in database
→ Return JSON with 3-5 pension schemes

User asks: "i am a farmer"
→ Find all agriculture/farmer schemes
→ Return JSON with 3-5 farmer schemes

REMEMBER: ALWAYS RETURN JSON WITH SCHEMES ARRAY. NEVER RETURN PLAIN TEXT APOLOGIES!
"""

    return base_prompt


def parse_ai_response(
    raw_response: str, intent: ConversationState, language: str, entities: dict
) -> dict:
    """Parse AI response and ensure proper format"""
    app.logger.info(f"🔍 Parsing AI response: {raw_response[:200]}...")

    # CRITICAL FIX: Check if response is already a dict (shouldn't happen but
    # defensive)
    if isinstance(raw_response, dict):
        app.logger.info("✅ Response is already a dict, returning as-is")
        return raw_response

    # Try to parse as JSON
    cleaned = raw_response.strip()

    # AGGRESSIVE JSON EXTRACTION: Find JSON object in the response
    # Sometimes AI wraps JSON in extra text or quotes
    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}") + 1

    if json_start != -1 and json_end > json_start:
        # Extract just the JSON part
        cleaned = cleaned[json_start:json_end]
        app.logger.info(f"📦 Extracted JSON from position {json_start} to {json_end}")

    # Remove markdown code blocks
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Remove any leading/trailing backticks
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])

    # Remove single backticks
    cleaned = cleaned.strip("`").strip()

    # Remove any leading/trailing quotes that might wrap the JSON
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]
        app.logger.info("🔧 Removed wrapping quotes from JSON")

    # Unescape any escaped quotes
    if '\\"' in cleaned:
        cleaned = cleaned.replace('\\"', '"')
        app.logger.info("🔧 Unescaped quotes in JSON")

    try:
        data = json.loads(cleaned)
        app.logger.info("✅ Successfully parsed JSON response")

        # Validate that it's a dict
        if not isinstance(data, dict):
            app.logger.warning(f"⚠️ Parsed data is not a dict: {type(data)}")
            return {
                "type": "text_response",
                "language": language,
                "text": "I apologize, but I encountered an error formatting the response. Please try again.",
                "intent": intent.value,
            }

        # If it's a scheme response, ensure it has schemes array
        if intent == ConversationState.SCHEME_DISCOVERY:
            if (
                "schemes" not in data
                or not isinstance(data.get("schemes"), list)
                or len(data.get("schemes", [])) == 0
            ):
                app.logger.warning(
                    "⚠️ Scheme response missing 'schemes' array or empty"
                )
                app.logger.warning(f"⚠️ Response data keys: {data.keys()}")

                # Try to extract schemes from the response if it's nested
                if (
                    "reply" in data
                    and isinstance(data["reply"], dict)
                    and "schemes" in data["reply"]
                ):
                    app.logger.info("✅ Found schemes in nested 'reply' field")
                    return data["reply"]

                # Last resort: return error message
                return {
                    "type": "text_response",
                    "language": language,
                    "text": "I apologize, but I couldn't find relevant schemes. Please provide more details about your profile (age, occupation, location).",
                    "intent": intent.value,
                }

        return data

    except json.JSONDecodeError as e:
        app.logger.error(f"❌ JSON parsing failed: {e}")
        app.logger.error(f"❌ Cleaned response: {cleaned[:500]}")

        # Check if the response looks like JSON but has syntax errors
        if cleaned.startswith("{") or cleaned.startswith("["):
            app.logger.error("❌ Response looks like JSON but has syntax errors")
            # Try to fix common JSON errors
            try:
                # Remove trailing commas
                fixed = cleaned.replace(",]", "]").replace(",}", "}")
                data = json.loads(fixed)
                app.logger.info("✅ Fixed JSON syntax errors and parsed successfully")
                return data
            except BaseException:
                pass

        # Fallback: create structured response with the text
        return {
            "type": "text_response",
            "language": language,
            "text": (
                raw_response
                if len(raw_response) < 500
                else "I apologize, but I encountered an error. Please try asking in a different way."
            ),
            "intent": intent.value,
        }
    except Exception as e:
        app.logger.error(f"❌ Unexpected error parsing response: {e}", exc_info=True)
        return {
            "type": "text_response",
            "language": language,
            "text": "I apologize, but I encountered an error processing your request. Please try again.",
            "intent": intent.value,
        }


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "status": "ok",
            "message": "🇮🇳 Bharat Scheme Mitra — Enhanced Conversational AI",
            "version": "4.0",
            "features": [
                "Multi-turn conversations",
                "User profile management",
                "Application guidance",
                "Document assistance",
                "15 Indian languages",
                "Sentiment analysis",
            ],
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "Bharat Scheme Mitra Enhanced",
            "version": "4.0",
            "ai_engine": f"Amazon Bedrock — Nova Lite ({MODEL_ID})",
            "bedrock_region": BEDROCK_REGION,
            "data_region": DATA_REGION,
            "s3_bucket": S3_BUCKET,
            "schemes_loaded": len(SCHEMES),
            "translation": "Amazon Translate (AWS Native)",
            "features": [
                "Conversational AI",
                "Profile Management",
                "Intent Detection",
                "SMS Notifications",
            ],
            "sms_configured": bool(SNS_TOPIC_ARN),
            "aws_services": [
                "Bedrock",
                "S3",
                "Transcribe",
                "Polly",
                "Comprehend",
                "DynamoDB",
                "SNS",
                "Textract",
                "Translate",
            ],
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/send-sms", methods=["POST"])
def send_sms_route():
    """Send SMS with scheme details to user"""
    data = request.json or {}
    phone_number = data.get("phone")
    scheme_name = data.get("schemeName", "")
    language = data.get("language", "en")

    if not phone_number:
        return jsonify({"error": "Phone number required"}), 400

    success = send_scheme_notification(phone_number, scheme_name, language)

    if success:
        return jsonify(
            {"success": True, "message": "SMS sent successfully", "phone": phone_number}
        )
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Failed to send SMS. Please check SNS configuration.",
                }
            ),
            500,
        )


@app.route("/chat", methods=["POST"])
def chat():
    """Enhanced conversational chat endpoint"""
    data = request.json or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("sessionId") or str(uuid.uuid4())
    language = data.get("language", "hi")

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    try:
        # Auto-detect language if not specified
        if not data.get("language"):
            language = detect_language_comprehend(user_message)

        app.logger.info(
            f"📨 Chat request: session={session_id}, lang={language}, msg={user_message[:50]}..."
        )

        result = get_conversational_reply(user_message, session_id, language)

        app.logger.info(f"✅ Chat response: intent={
                result.get('intent')}, reply_type={
                type(
                    result.get('reply'))}")

        return jsonify({"sessionId": session_id, **result})

    except Exception as e:
        app.logger.error(f"❌ /chat ERROR: {e}", exc_info=True)

        # Return user-friendly error message
        error_messages = {
            "hi": "⚠️ कनेक्शन में समस्या है। कृपया दोबारा कोशिश करें।",
            "en": "⚠️ Connection error. Please try again.",
            "te": "⚠️ కనెక్షన్ లోపం. దయచేసి మళ్లీ ప్రయత్నించండి.",
            "ta": "⚠️ இணைப்பு பிழை. மீண்டும் முயற்சிக்கவும்.",
        }

        return (
            jsonify(
                {
                    "error": error_messages.get(language, error_messages["en"]),
                    "details": str(e)[:200],
                    "sessionId": session_id,
                }
            ),
            500,
        )


@app.route("/profile", methods=["GET", "POST"])
def user_profile():
    """Get or update user profile"""
    if request.method == "GET":
        user_id = request.args.get("userId")
        if not user_id:
            return jsonify({"error": "userId required"}), 400

        profile = profile_service.get_profile(user_id)
        return jsonify({"profile": profile or {}})

    else:  # POST
        data = request.json or {}
        user_id = data.get("userId")
        profile_data = data.get("profile", {})

        if not user_id:
            return jsonify({"error": "userId required"}), 400

        updated = profile_service.create_or_update_profile(user_id, profile_data)
        return jsonify({"profile": updated})


@app.route("/schemes/personalized", methods=["POST"])
def personalized_schemes():
    """Get personalized scheme recommendations"""
    data = request.json or {}
    user_profile = data.get("profile", {})
    language = data.get("language", "en")

    scored_schemes = profile_service.get_personalized_schemes(user_profile, SCHEMES)

    return jsonify(
        {"schemes": scored_schemes, "total": len(scored_schemes), "language": language}
    )


# Keep all existing routes from original app.py
@app.route("/test-voice", methods=["GET"])
def test_voice():
    """
    Test endpoint to check if voice processing is configured correctly
    """
    checks = {
        "s3_client": s3_client is not None,
        "transcribe_client": transcribe_cl is not None,
        "polly_client": polly is not None,
        "s3_bucket": S3_BUCKET,
        "data_region": DATA_REGION,
        "transcribe_languages": list(TRANSCRIBE_LANG_MAP.keys()),
        "polly_voices": list(POLLY_VOICES.keys()),
    }

    # Test S3 access
    if s3_client and S3_BUCKET:
        try:
            s3_client.head_bucket(Bucket=S3_BUCKET)
            checks["s3_access"] = "OK"
        except Exception as e:
            checks["s3_access"] = f"FAILED: {str(e)}"
    else:
        checks["s3_access"] = "NOT CONFIGURED"

    # Test Transcribe access
    if transcribe_cl:
        try:
            transcribe_cl.list_transcription_jobs(MaxResults=1)
            checks["transcribe_access"] = "OK"
        except Exception as e:
            checks["transcribe_access"] = f"FAILED: {str(e)}"
    else:
        checks["transcribe_access"] = "NOT CONFIGURED"

    # Test Polly access
    if polly:
        try:
            polly.describe_voices(LanguageCode="en-IN")
            checks["polly_access"] = "OK"
        except Exception as e:
            checks["polly_access"] = f"FAILED: {str(e)}"
    else:
        checks["polly_access"] = "NOT CONFIGURED"

    all_ok = all(
        [
            checks["s3_client"],
            checks["transcribe_client"],
            checks["polly_client"],
            checks["s3_access"] == "OK",
            checks["transcribe_access"] == "OK",
            checks["polly_access"] == "OK",
        ]
    )

    return jsonify(
        {
            "status": "OK" if all_ok else "ISSUES FOUND",
            "checks": checks,
            "recommendation": (
                "All voice services are working!"
                if all_ok
                else "Please check the failed services above"
            ),
        }
    )


@app.route("/schemes", methods=["GET"])
def list_schemes():
    category = request.args.get("category")
    state = request.args.get("state")
    filtered = [
        s
        for s in SCHEMES
        if (not category or s.get("category") == category)
        and (not state or state.upper() in s.get("states", "ALL").upper())
    ]
    return jsonify({"schemes": filtered, "total": len(filtered)})


@app.route("/detect-language", methods=["POST"])
def detect_language_route():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    lang = detect_language_comprehend(text)
    return jsonify(
        {
            "detected_language": lang,
            "language_name": LANG_NAME.get(lang, "Unknown"),
            "engine": "Amazon Comprehend",
        }
    )


@app.route("/sentiment", methods=["POST"])
def sentiment_route():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    lang = data.get("language", "en")
    if not text:
        return jsonify({"error": "text is required"}), 400
    sentiment = analyze_sentiment_comprehend(text, lang)
    return jsonify(
        {
            "sentiment": sentiment,
            "engine": "Amazon Comprehend",
        }
    )


@app.route("/voice", methods=["POST"])
def voice_chat():
    """
    Voice pipeline with enhanced conversational response

    FIXED ISSUES:
    - Added AWS client checks with detailed error messages
    - Better error handling with user-friendly tips
    - Support for multiple audio formats
    - Improved timeout handling
    - Detailed error messages
    - Strip emojis from responses
    """
    try:
        # Check if audio file is provided
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]

        # Check if file is empty
        if audio_file.filename == "":
            return jsonify({"error": "Empty audio file"}), 400

        language = request.form.get("language", "hi")
        session_id = request.form.get("sessionId") or str(uuid.uuid4())
        transcribe_lang = TRANSCRIBE_LANG_MAP.get(language, "en-IN")

        # Check if language is fully supported or using fallback
        is_fallback = language not in TRANSCRIBE_SUPPORTED
        if is_fallback:
            app.logger.info(
                f"⚠️ Language '{language}' using English transcription fallback"
            )

        # Check if AWS clients are initialized
        if not s3_client:
            app.logger.error("S3 client not initialized")
            return (
                jsonify(
                    {
                        "error": "Voice service not configured",
                        "tip": "AWS S3 is not configured. Please check S3_BUCKET environment variable.",
                    }
                ),
                500,
            )

        if not transcribe_cl:
            app.logger.error("Transcribe client not initialized")
            return (
                jsonify(
                    {
                        "error": "Voice service not configured",
                        "tip": "AWS Transcribe is not configured. Please check DATA_REGION environment variable.",
                    }
                ),
                500,
            )

        # Generate unique job name
        job_name = f"bsm-{uuid.uuid4().hex[:10]}"

        # Detect audio format from filename or default to webm
        file_ext = (
            audio_file.filename.rsplit(".", 1)[-1].lower()
            if "." in audio_file.filename
            else "webm"
        )

        # Map file extensions to Transcribe formats
        format_map = {
            "webm": "webm",
            "mp3": "mp3",
            "mp4": "mp4",
            "m4a": "mp4",
            "wav": "wav",
            "flac": "flac",
            "ogg": "ogg",
            "amr": "amr",
        }

        media_format = format_map.get(file_ext, "webm")
        s3_key = f"audio/{job_name}.{file_ext}"

        # Upload to S3 with error handling
        try:
            audio_file.seek(0)  # Reset file pointer
            file_size = len(audio_file.read())
            audio_file.seek(0)  # Reset again after reading
            app.logger.info(
                f"📤 Uploading audio: {file_size} bytes, format: {media_format}"
            )
            s3_client.upload_fileobj(audio_file, S3_BUCKET, s3_key)
            app.logger.info(f"✅ Uploaded audio to s3://{S3_BUCKET}/{s3_key}")
        except Exception as e:
            app.logger.error(f"S3 upload failed: {e}")
            return (
                jsonify(
                    {
                        "error": "Failed to upload audio",
                        "tip": f"Check if S3 bucket '{S3_BUCKET}' exists and you have write permissions.",
                    }
                ),
                500,
            )

        # Start transcription job with error handling
        try:
            transcribe_cl.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": f"s3://{S3_BUCKET}/{s3_key}"},
                MediaFormat=media_format,
                LanguageCode=transcribe_lang,
            )
            app.logger.info(f"Started transcription job: {job_name}")
        except Exception as e:
            app.logger.error(f"Transcribe job start failed: {e}")
            error_msg = str(e)
            if "AccessDenied" in error_msg:
                tip = "AWS credentials don't have permission for Transcribe. Check IAM permissions."
            elif "InvalidParameter" in error_msg:
                tip = f"Audio format '{media_format}' or language '{transcribe_lang}' not supported."
            else:
                tip = "Check if AWS Transcribe is enabled in your region."
            return (
                jsonify({"error": "Failed to start voice transcription", "tip": tip}),
                500,
            )

        # Poll for completion with language-aware timeout
        # Fully supported Indic languages may take longer to transcribe
        max_attempts = 30 if language in TRANSCRIBE_SUPPORTED else 20
        app.logger.info(
            f"🎯 Transcribing in {language} ({transcribe_lang}) - max wait: {
                max_attempts * 2}s | Fallback: {is_fallback}"
        )

        for attempt in range(max_attempts):
            time.sleep(2)

            try:
                job = transcribe_cl.get_transcription_job(TranscriptionJobName=job_name)
                status = job["TranscriptionJob"]["TranscriptionJobStatus"]

                app.logger.info(
                    f"📊 Transcription status (attempt {
                        attempt + 1}/{max_attempts}): {status} | Language: {transcribe_lang}"
                )

                if status == "COMPLETED":
                    # Get transcript
                    uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                    result = json.loads(urllib.request.urlopen(uri).read())

                    # Extract transcript text
                    transcripts = result.get("results", {}).get("transcripts", [])
                    app.logger.info(f"📝 Transcription result: {transcripts}")
                    app.logger.info(f"🔍 Full transcription response: {
                            json.dumps(
                                result,
                                ensure_ascii=False)[
                                :500]}")

                    if not transcripts or not transcripts[0].get("transcript"):
                        app.logger.warning(
                            f"⚠️ No speech detected in audio. Full result: {result}"
                        )
                        return (
                            jsonify(
                                {
                                    "error": "No speech detected in audio",
                                    "tip": f"Please speak louder and closer to the microphone. Make sure you're speaking for at least 2-3 seconds. Language: {LANG_NAME.get(language, language)}",
                                }
                            ),
                            400,
                        )

                    transcript = transcripts[0]["transcript"]
                    app.logger.info(f"✅ Transcript ({language}): {transcript}")

                    # If using fallback, add a note for the user
                    if is_fallback:
                        app.logger.info(
                            f"ℹ️ Using English transcription for {
                                LANG_NAME.get(
                                    language,
                                    language)} - user should speak in English or use text input"
                        )

                    # Use enhanced conversational reply
                    reply_result = get_conversational_reply(
                        transcript, session_id, language
                    )

                    # Clean up S3 file (optional)
                    try:
                        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
                    except BaseException:
                        pass  # Ignore cleanup errors

                    # Add fallback notice if applicable
                    response_data = {
                        "sessionId": session_id,
                        "language": language,
                        "transcript": transcript,
                        **reply_result,
                    }

                    # Inform user if fallback was used
                    if is_fallback:
                        fallback_messages = {
                            "bn": "দ্রষ্টব্য: বাংলা ভয়েস সীমিত সমর্থন আছে। ইংরেজিতে বলুন বা টেক্সট ব্যবহার করুন।",
                            "gu": "નોંધ: ગુજરાતી વૉઇસ મર્યાદિત સપોર્ટ છે। અંગ્રેજીમાં બોલો અથવા ટેક્સ્ટ વાપરો।",
                            "kn": "ಗಮನಿಸಿ: ಕನ್ನಡ ವಾಯ್ಸ್ ಸೀಮಿತ ಬೆಂಬಲ ಇದೆ। ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಿ ಅಥವಾ ಪಠ್ಯ ಬಳಸಿ।",
                            "ml": "ശ്രദ്ധിക്കുക: മലയാളം വോയ്‌സിന് പരിമിത പിന്തുണയുണ്ട്. ഇംഗ്ലീഷിൽ സംസാരിക്കുക അല്ലെങ്കിൽ ടെക്‌സ്റ്റ് ഉപയോഗിക്കുക।",
                            "pa": "ਨੋਟ: ਪੰਜਾਬੀ ਵੌਇਸ ਸੀਮਤ ਸਹਾਇਤਾ ਹੈ। ਅੰਗਰੇਜ਼ੀ ਵਿੱਚ ਬੋਲੋ ਜਾਂ ਟੈਕਸਟ ਵਰਤੋ।",
                            "or": "ଧ୍ୟାନ ଦିଅନ୍ତୁ: ଓଡ଼ିଆ ଭଏସ୍ ସୀମିତ ସମର୍ଥନ ଅଛି। ଇଂରାଜୀରେ କୁହନ୍ତୁ କିମ୍ବା ଟେକ୍ସଟ୍ ବ୍ୟବହାର କରନ୍ତୁ।",
                            "as": "মন কৰক: অসমীয়া ভইচ সীমিত সমৰ্থন আছে। ইংৰাজীত কওক বা টেক্সট ব্যৱহাৰ কৰক।",
                            "ur": "نوٹ: اردو وائس محدود سپورٹ ہے۔ انگریزی میں بولیں یا ٹیکسٹ استعمال کریں۔",
                        }
                        response_data["fallback_notice"] = fallback_messages.get(
                            language,
                            "Note: Voice support for this language is limited. Please speak in English or use text input.",
                        )

                    return jsonify(response_data)

                elif status == "FAILED":
                    reason = job["TranscriptionJob"].get("FailureReason", "Unknown")
                    app.logger.error(f"Transcription failed: {reason}")
                    return (
                        jsonify(
                            {
                                "error": f"Transcription failed: {reason}",
                                "tip": "Try using a different audio format (mp3, wav) or check audio quality",
                            }
                        ),
                        500,
                    )

            except Exception as e:
                app.logger.error(f"Error checking transcription status: {e}")
                # Continue polling unless it's the last attempt
                if attempt == max_attempts - 1:
                    return (
                        jsonify(
                            {
                                "error": "Error checking transcription status",
                                "details": str(e),
                            }
                        ),
                        500,
                    )

        # Timeout
        app.logger.error(f"⏱️ Transcription timed out after {
                max_attempts *
                2} seconds | Language: {transcribe_lang} | Job: {job_name}")
        return (
            jsonify(
                {
                    "error": "Voice processing timed out",
                    "tip": f"Audio transcription is taking longer than expected for {
                    LANG_NAME.get(
                        language, language)}. Try: 1) Speaking for 2-5 seconds, 2) Speaking clearly and slowly, 3) Using text input instead.",
                }
            ),
            500,
        )

    except Exception as e:
        app.logger.error(f"Voice processing error: {e}")
        return jsonify({"error": "Voice processing failed", "details": str(e)}), 500


@app.route("/speak", methods=["POST"])
def speak():
    """
    Amazon Polly TTS

    FIXED ISSUES:
    - Added AWS client checks
    - Better error handling
    - Support for JSON text extraction
    - Strip emojis before TTS synthesis
    """
    try:
        data = request.json or {}
        text = (data.get("text") or "").strip()
        language = data.get("language", "en")

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Check if Polly is initialized
        if not polly:
            return (
                jsonify(
                    {
                        "error": "AWS Polly not configured",
                        "tip": "Check DATA_REGION environment variable",
                    }
                ),
                500,
            )

        # If text is a dict/object (from scheme cards), extract readable text
        if isinstance(text, dict):
            # Extract intro and scheme names
            parts = []
            if text.get("intro"):
                parts.append(text["intro"])
            if text.get("schemes"):
                for scheme in text["schemes"][:3]:  # Max 3 schemes
                    parts.append(scheme.get("name", ""))
            text = ". ".join(parts)

        # Remove all emojis before TTS synthesis
        text = strip_emojis(text)

        if not text:
            return jsonify({"error": "No text to speak after processing"}), 400

        spoken_language = language
        tts_text = text[:2500]  # Polly limit

        # Translate if language not supported by Polly
        if language not in POLLY_VOICES:
            tts_text = translate_text(text[:2500], language, "en")
            spoken_language = "en"

        voice_id, lang_code, engine = POLLY_VOICES[spoken_language]

        try:
            resp = polly.synthesize_speech(
                Text=tts_text,
                OutputFormat="mp3",
                VoiceId=voice_id,
                LanguageCode=lang_code,
                Engine=engine,
            )
            audio_bytes = resp["AudioStream"].read()

            return jsonify(
                {
                    "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
                    "spoken_language": spoken_language,
                    "text_length": len(tts_text),
                }
            )
        except Exception as e:
            app.logger.error(f"Polly synthesis failed: {e}")
            return (
                jsonify(
                    {
                        "error": "Text-to-speech failed",
                        "details": str(e),
                        "tip": "Check if AWS Polly is enabled in your region",
                    }
                ),
                500,
            )

    except Exception as e:
        app.logger.error(f"TTS error: {e}")
        return (
            jsonify({"error": "Text-to-speech processing failed", "details": str(e)}),
            500,
        )

    if language not in POLLY_VOICES:
        tts_text = translate_text(text, language, "en")
        spoken_language = "en"

    voice_id, lang_code, engine = POLLY_VOICES[spoken_language]
    resp = polly.synthesize_speech(
        Text=tts_text[:2500],
        OutputFormat="mp3",
        VoiceId=voice_id,
        LanguageCode=lang_code,
        Engine=engine,
    )
    audio_bytes = resp["AudioStream"].read()

    return jsonify(
        {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "spoken_language": spoken_language,
        }
    )


@app.route("/upload-doc", methods=["POST"])
def upload_doc():
    """Document processing with conversational guidance"""
    if "document" not in request.files:
        return jsonify({"error": "No document provided"}), 400

    doc_file = request.files["document"]
    doc_type = request.form.get("type", "general")

    doc_file.seek(0, 2)
    size = doc_file.tell()
    if size > 5 * 1024 * 1024:
        return jsonify({"error": "File too large. Maximum 5MB allowed."}), 413
    doc_file.seek(0)

    s3_key = f"docs/uploads/{doc_type}/{uuid.uuid4().hex}.jpg"
    s3_client.upload_fileobj(doc_file, S3_BUCKET, s3_key)

    try:
        ocr = textract.detect_document_text(
            Document={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}}
        )
        lines = [b["Text"] for b in ocr["Blocks"] if b["BlockType"] == "LINE"]
        raw_text = " | ".join(lines)
    except Exception as e:
        return jsonify({"error": f"Textract OCR failed: {e}"}), 500

    try:
        extraction_prompt = [
            {
                "role": "user",
                "content": f"OCR output from {doc_type} document: {raw_text}\n\n"
                "Return ONLY valid JSON with these fields: "
                '{"name": "", "dob": "", "id_number": "", '
                '"address": "", "gender": "", "document_type": ""}. '
                "Use null for missing fields. No markdown.",
            }
        ]
        raw = call_nova(
            extraction_prompt, "You are a document parser. Return only valid JSON."
        )
        parsed = json.loads(
            raw.strip().replace("```json", "").replace("```", "").strip()
        )
    except Exception:
        parsed = {"raw_ocr": raw_text}

    return jsonify(
        {
            "extracted": parsed,
            "raw_text": raw_text,
            "engine": "Amazon Textract + Nova",
            "guidance": "Document uploaded successfully. I can now use this information to find schemes for you.",
        }
    )


@app.route("/translate", methods=["POST"])
def translate_route():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    source = data.get("source", "en")
    target = data.get("target", "hi")
    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400
    return jsonify(
        {
            "original": text,
            "translated": translate_text(text, source, target),
            "engine": "Amazon Translate (AWS Native)",
        }
    )


if __name__ == "__main__":
    print("\n🇮🇳  Bharat Scheme Mitra v4.0 — Enhanced Conversational AI")
    print(f"   Bedrock (Nova Lite):  {BEDROCK_REGION}")
    print(f"   Data Services:        {DATA_REGION}")
    print(f"   S3 Bucket:            {S3_BUCKET}")
    print(f"   DynamoDB:             {SESSIONS_TABLE_NAME}")
    print(f"   Schemes loaded:       {len(SCHEMES)}")
    print("   Translation:          Amazon Translate (AWS Native)")
    print(
        "   Features:             Conversational AI, Profile Management, Intent Detection"
    )
    print(f"   Languages:            {len(LANG_NAME)} Indian languages")
    print(
        "   AWS Services:         9 services (Bedrock, S3, Transcribe, Polly, Comprehend, DynamoDB, SNS, Textract, Translate)\n"
    )
    app.run(port=5000, debug=True)
