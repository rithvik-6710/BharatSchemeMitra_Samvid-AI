"""
backend/tests/test_chat.py
Full test suite for Bharat Scheme Mitra v3.0
Run: cd backend && pytest tests/ -v
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["TESTING"]            = "true"
os.environ["S3_BUCKET"]          = "test-bucket"
os.environ["INDICTRANS2_URL"]    = "http://localhost:5001"
os.environ["BEDROCK_REGION"]     = "us-east-1"
os.environ["DATA_REGION"]        = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


# ── Mock nova converse response ──────────────────────────────
NOVA_RESPONSE = json.dumps({
    "language": "en",
    "intro": "Here are schemes for you.",
    "schemes": [{
        "name": "PM-KISAN",
        "category": "agriculture",
        "benefit": "Rs 6000 per year",
        "eligibility": "Small farmers with up to 2 hectares of land",
        "documents": ["Aadhaar", "Land records"],
        "apply_steps": ["Visit PM-KISAN portal", "Register with Aadhaar", "Submit land records"],
        "apply_url": "https://pmkisan.gov.in",
    }],
    "follow_up": "Do you own agricultural land?",
})


@pytest.fixture(autouse=True)
def mock_aws():
    with patch("boto3.client") as mock_client_fn, \
         patch("boto3.resource") as mock_resource_fn:

        # Bedrock mock — converse API
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": NOVA_RESPONSE}]
                }
            }
        }

        # Comprehend mock
        mock_comprehend = MagicMock()
        mock_comprehend.detect_dominant_language.return_value = {
            "Languages": [{"LanguageCode": "en", "Score": 0.99}]
        }
        mock_comprehend.detect_sentiment.return_value = {
            "Sentiment": "NEUTRAL",
            "SentimentScore": {"Positive": 0.1, "Negative": 0.1, "Neutral": 0.8, "Mixed": 0.0}
        }

        # DynamoDB
        mock_table = MagicMock()
        mock_table.get_item.return_value  = {"Item": {"sessionId": "t1", "history": []}}
        mock_table.put_item.return_value  = {}
        mock_resource = MagicMock()
        mock_resource.Table.return_value  = mock_table

        # S3
        mock_s3 = MagicMock()
        mock_s3.get_bucket_location.return_value = {"LocationConstraint": "us-east-1"}

        def client_factory(service, **kwargs):
            return {
                "bedrock-runtime": mock_bedrock,
                "comprehend":      mock_comprehend,
                "s3":              mock_s3,
                "transcribe":      MagicMock(),
                "polly":           MagicMock(),
                "textract":        MagicMock(),
            }.get(service, MagicMock())

        mock_client_fn.side_effect    = client_factory
        mock_resource_fn.return_value = mock_resource

        yield {"bedrock": mock_bedrock, "table": mock_table, "comprehend": mock_comprehend}


@pytest.fixture
def client(mock_aws):
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── /health ──────────────────────────────────────────────────

class TestHealth:

    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_status_ok(self, client):
        d = json.loads(client.get("/health").data)
        assert d["status"] == "ok"

    def test_shows_scheme_count(self, client):
        d = json.loads(client.get("/health").data)
        assert d["schemes_loaded"] >= 15

    def test_shows_indictrans2_in_translation(self, client):
        d = json.loads(client.get("/health").data)
        assert "IndicTrans2" in d["translation"]

    def test_shows_aws_services(self, client):
        d = json.loads(client.get("/health").data)
        assert "Bedrock" in d["aws_services"]
        assert "Comprehend" in d["aws_services"]

    def test_shows_ai_engine(self, client):
        d = json.loads(client.get("/health").data)
        assert "Nova" in d["ai_engine"] or "nova" in d["ai_engine"]


# ── /chat ────────────────────────────────────────────────────

class TestChat:

    def test_basic_success(self, client):
        r = client.post("/chat", json={"message": "What schemes for farmers?", "sessionId": "s1"})
        assert r.status_code == 200

    def test_returns_reply_object(self, client):
        d = json.loads(client.post("/chat", json={"message": "Tell me about PM-KISAN"}).data)
        assert "reply" in d

    def test_reply_has_schemes(self, client):
        d = json.loads(client.post("/chat", json={"message": "I am a farmer"}).data)
        assert "schemes" in d["reply"]

    def test_returns_session_id(self, client):
        d = json.loads(client.post("/chat", json={"message": "Hello"}).data)
        assert "sessionId" in d and d["sessionId"]

    def test_preserves_given_session_id(self, client):
        d = json.loads(client.post("/chat", json={
            "message": "Hello", "sessionId": "my-session-999"
        }).data)
        assert d["sessionId"] == "my-session-999"

    def test_auto_generates_session_if_missing(self, client):
        d = json.loads(client.post("/chat", json={"message": "Hello"}).data)
        assert d["sessionId"]

    def test_empty_message_returns_400(self, client):
        assert client.post("/chat", json={"message": ""}).status_code == 400

    def test_missing_message_returns_400(self, client):
        assert client.post("/chat", json={}).status_code == 400

    def test_hindi_message(self, client):
        r = client.post("/chat", json={
            "message": "मुझे किसान योजना के बारे में बताओ",
            "sessionId": "hindi-s1",
            "language": "hi"
        })
        assert r.status_code == 200

    def test_tamil_message(self, client):
        r = client.post("/chat", json={
            "message": "நான் விவசாயி. என்ன திட்டம் கிடைக்கும்?",
            "sessionId": "tamil-s1",
            "language": "ta"
        })
        assert r.status_code == 200


# ── /schemes ─────────────────────────────────────────────────

class TestSchemes:

    def test_returns_list(self, client):
        d = json.loads(client.get("/schemes").data)
        assert "schemes" in d and "total" in d

    def test_has_at_least_15_schemes(self, client):
        d = json.loads(client.get("/schemes").data)
        assert d["total"] >= 15

    def test_category_filter_agriculture(self, client):
        d = json.loads(client.get("/schemes?category=agriculture").data)
        for s in d["schemes"]:
            assert s["category"] == "agriculture"

    def test_category_filter_health(self, client):
        d = json.loads(client.get("/schemes?category=health").data)
        for s in d["schemes"]:
            assert s["category"] == "health"


# ── /detect-language ─────────────────────────────────────────

class TestDetectLanguage:

    def test_detects_english(self, client):
        d = json.loads(client.post("/detect-language", json={"text": "Hello I am a farmer"}).data)
        assert d["detected_language"] == "en"
        assert d["engine"] == "Amazon Comprehend"

    def test_empty_text_returns_400(self, client):
        assert client.post("/detect-language", json={"text": ""}).status_code == 400

    def test_returns_language_name(self, client):
        d = json.loads(client.post("/detect-language", json={"text": "Hello"}).data)
        assert "language_name" in d


# ── /sentiment ───────────────────────────────────────────────

class TestSentiment:

    def test_returns_sentiment(self, client):
        d = json.loads(client.post("/sentiment", json={"text": "This is great!", "language": "en"}).data)
        assert d["sentiment"] in {"POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED"}
        assert d["engine"] == "Amazon Comprehend"

    def test_empty_text_returns_400(self, client):
        assert client.post("/sentiment", json={"text": ""}).status_code == 400


# ── /translate ───────────────────────────────────────────────

class TestTranslate:

    def test_same_language_returns_original(self, client):
        d = json.loads(client.post("/translate", json={
            "text": "Hello", "source": "en", "target": "en"
        }).data)
        assert d["translated"] == "Hello"

    def test_empty_text_returns_400(self, client):
        assert client.post("/translate", json={
            "text": "", "source": "en", "target": "hi"
        }).status_code == 400

    def test_returns_engine_info(self, client):
        with patch("app.http_requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"translated": "नमस्ते"}
            d = json.loads(client.post("/translate", json={
                "text": "Hello", "source": "en", "target": "hi"
            }).data)
            assert "IndicTrans2" in d["engine"]

    def test_fallback_on_ec2_down(self, client):
        import requests
        with patch("app.http_requests.post", side_effect=requests.exceptions.ConnectionError):
            d = json.loads(client.post("/translate", json={
                "text": "Hello", "source": "en", "target": "hi"
            }).data)
            assert d["translated"] == "Hello"


# ── Data Integrity ────────────────────────────────────────────

class TestSchemesData:

    def _load(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes.json")
        with open(os.path.abspath(path)) as f:
            return json.load(f)

    def test_file_exists(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "schemes.json")
        assert os.path.exists(os.path.abspath(path))

    def test_valid_json(self):
        assert isinstance(self._load(), list)

    def test_at_least_15_schemes(self):
        assert len(self._load()) >= 15

    def test_all_required_fields_present(self):
        required = ["id", "name", "benefit", "who_can_apply", "documents",
                    "how_to_apply", "category", "apply_url"]
        for s in self._load():
            for field in required:
                assert field in s, f"Scheme '{s.get('id')}' missing field: '{field}'"

    def test_no_duplicate_ids(self):
        ids = [s["id"] for s in self._load()]
        assert len(ids) == len(set(ids))

    def test_valid_categories(self):
        valid = {"agriculture", "health", "housing", "women", "education",
                 "elderly", "disability", "business", "employment"}
        for s in self._load():
            assert s["category"] in valid, \
                f"'{s['id']}' has invalid category: '{s['category']}'"


# ── Constants ─────────────────────────────────────────────────

class TestConstants:

    def test_system_prompt_has_scheme_data(self):
        from app import SYSTEM_PROMPT
        assert "SCHEME:" in SYSTEM_PROMPT

    def test_transcribe_map_has_hindi(self):
        from app import TRANSCRIBE_LANG_MAP
        assert TRANSCRIBE_LANG_MAP.get("hi") == "hi-IN"

    def test_transcribe_map_has_enough_languages(self):
        from app import TRANSCRIBE_LANG_MAP
        assert len(TRANSCRIBE_LANG_MAP) >= 8

    def test_polly_voices_kajal(self):
        from app import POLLY_VOICES
        assert POLLY_VOICES["hi"][0] == "Kajal"

    def test_schemes_loaded(self):
        from app import SCHEMES
        assert len(SCHEMES) >= 15

    def test_translate_returns_original_on_connection_error(self):
        from app import translate_text
        import requests
        with patch("app.http_requests.post", side_effect=requests.exceptions.ConnectionError):
            result = translate_text("Hello world", "en", "hi")
            assert result == "Hello world"

    def test_nova_model_id(self):
        from app import NOVA_MODEL
        assert "nova" in NOVA_MODEL.lower()