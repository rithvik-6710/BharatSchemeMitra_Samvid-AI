# 📡 Bharat Scheme Mitra API Reference

**Base URL (local dev):** `http://localhost:5000`  
**Base URL (deployed):** `https://your-eb-url.ap-south-1.elasticbeanstalk.com`  
**Translation engine:** IndicTrans2 (AI4Bharat) on AWS EC2  

---

## `GET /health`
Check all services are running.

**Response:**
```json
{
  "status": "ok",
  "service": "Bharat Scheme Mitra AI",
  "version": "2.0.0",
  "region": "ap-south-1",
  "translation": "IndicTrans2 @ http://EC2_IP:5001 [ok]",
  "schemes_loaded": 15,
  "timestamp": "2026-02-27T10:00:00Z"
}
```

---

## `GET /schemes`
List all government schemes, with optional filters.

**Query params:**
- `category` — `agriculture` | `health` | `housing` | `women` | `education` | `elderly` | `disability` | `business` | `employment`
- `state` — e.g. `UP`, `MH` (optional)

**Response:**
```json
{
  "schemes": [
    {
      "id": "pmkisan",
      "name": "PM Kisan Samman Nidhi",
      "benefit": "Rs 6000 per year...",
      "who_can_apply": "Small farmers...",
      "documents": "Aadhaar, Land records...",
      "how_to_apply": "Visit pmkisan.gov.in...",
      "category": "agriculture",
      "apply_url": "https://pmkisan.gov.in"
    }
  ],
  "total": 15
}
```

---

## `POST /chat`
Text conversation — accepts any Indian language.

**Request:**
```json
{
  "message": "मैं किसान हूं, UP में रहता हूं",
  "sessionId": "sess-abc123"
}
```

**Response:**
```json
{
  "reply": "आपके लिए PM-KISAN, Fasal Bima और KCC योजनाएं हैं...",
  "sessionId": "sess-abc123"
}
```

**Flow:** Load session history (DynamoDB) → Claude 3 Sonnet (Bedrock) with scheme RAG context → Save history → Return reply

---

## `POST /voice`
Voice message → text → Claude reply.

**Request:** `multipart/form-data`
```
audio     : <audio/webm file>
language  : "hi"    (hi, en, ta, te, bn, mr, gu, kn, ml, pa)
sessionId : "sess-abc123"
```

**Response:**
```json
{
  "transcript": "मुझे किसान योजना बताओ",
  "reply": "PM-KISAN के लिए ₹6000 प्रति वर्ष मिलता है...",
  "sessionId": "sess-abc123",
  "language": "hi"
}
```

**Flow:** Audio → S3 → Amazon Transcribe (hi-IN) → Claude 3 → Response

---

## `POST /speak`
Convert text to speech (MP3 audio).

**Request:**
```json
{
  "text": "आप PM-KISAN के लिए पात्र हैं",
  "language": "hi"
}
```

**Response:** `audio/mpeg` binary (MP3)

| Language | Voice | Engine |
|----------|-------|--------|
| `hi` | Kajal | Polly Neural |
| `en` | Raveena | Polly Neural |
| Others | Kajal (translated to hi first) | Polly Neural |

---

## `POST /upload-doc`
Document OCR + AI field extraction.

**Request:** `multipart/form-data`
```
document : <image or PDF, max 5MB>
type     : "aadhaar" | "pan" | "income_cert" | "ration_card" | "caste_cert" | "general"
userId   : "user-xyz"  (optional, saves to DynamoDB profile)
```

**Response:**
```json
{
  "extracted": {
    "name": "राज कुमार",
    "dob": "15/08/1985",
    "id_number": "XXXX-XXXX-1234",
    "address": "Village Rampur, UP",
    "gender": "Male",
    "document_type": "aadhaar"
  },
  "raw_text": "Government of India...",
  "doc_type": "aadhaar",
  "s3_key": "docs/anon/aadhaar/abc123.jpg"
}
```

**Flow:** S3 upload → Amazon Textract OCR → Claude 3 parse → DynamoDB profile update

---

## `POST /translate`
Translate between Indian languages via IndicTrans2 on EC2.

**Request:**
```json
{
  "text": "You are eligible for PM-KISAN scheme",
  "source": "en",
  "target": "hi"
}
```

**Response:**
```json
{
  "original": "You are eligible for PM-KISAN scheme",
  "translated": "आप PM-KISAN योजना के लिए पात्र हैं",
  "source": "en",
  "target": "hi",
  "engine": "IndicTrans2 (AI4Bharat)"
}
```

**Supported languages:** hi, ta, te, bn, mr, gu, kn, ml, pa, or, as, ur, sa, ne, mai, kok, doi, ks, sat, mni, bo, en

**Why IndicTrans2 instead of BHASHINI?**  
BHASHINI requires institutional paperwork. IndicTrans2 is the same underlying model, open-source, runs on your own EC2 instance with AWS credits — no approval needed.

---

## Error Responses

```json
{ "error": "Message cannot be empty" }
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request (missing or empty required field) |
| `413` | File too large (> 5MB) |
| `500` | Server error — check CloudWatch logs |
| `503` | IndicTrans2 EC2 unreachable — check EC2 status |
