# 🏗️ Bharat Scheme Mitra System Architecture

## Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                        │
│        React PWA (Mobile-First)  |  WhatsApp (roadmap)       │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌──────────────────────────────────────────────────────────────┐
│              API Gateway  +  AWS WAF  +  Cognito OTP         │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                   Flask Backend (EC2 / EB)                    │
│                                                               │
│  /chat        →  Bedrock (Claude 3 Sonnet)                   │
│  /voice       →  S3 → Amazon Transcribe → Claude             │
│  /speak       →  Amazon Polly (Kajal Neural, Hindi)          │
│  /upload-doc  →  S3 → Textract → Claude (parse fields)       │
│  /translate   →  IndicTrans2 EC2 server                      │
└────┬─────────────────┬────────────────────┬──────────────────┘
     │                 │                    │
     ▼                 ▼                    ▼
┌─────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│ AWS AI  │  │   DATA LAYER     │  │  IndicTrans2 EC2 Server  │
│         │  │                  │  │                          │
│ Bedrock │  │ DynamoDB         │  │ AI4Bharat open-source    │
│ Claude3 │  │  - sessions      │  │ model — 22 Indian langs  │
│         │  │  - users         │  │ No BHASHINI paperwork    │
│Transcribe  │  - schemes      │  │                          │
│  Polly  │  │                  │  │ g4dn.xlarge (GPU) or     │
│ Textract│  │ S3               │  │ t3.large (CPU)           │
└─────────┘  │  - docs/         │  └──────────────────────────┘
             │  - audio/        │
             └──────────────────┘
```

## Why IndicTrans2 vs BHASHINI

| | BHASHINI | IndicTrans2 (our choice) |
|--|---------|--------------------------|
| Approval | Institutional paperwork (weeks) | None — open source |
| Cost | Free (but gatekept) | EC2 instance ($0.50/hr g4dn.xlarge) |
| Languages | 22 | 22 (same model underneath) |
| Control | External API dependency | Full control on our EC2 |
| Offline | No | Yes (once downloaded) |
| Setup time | Weeks | Hours |

## AWS Services Used

| Service | Purpose |
|---------|---------|
| Amazon Bedrock (Claude 3 Sonnet) | Core AI conversation |
| Amazon Bedrock (Titan Embeddings) | Scheme vector embeddings for RAG |
| Amazon Transcribe | Speech-to-text (10 Indian languages) |
| Amazon Polly | Text-to-speech (Kajal Neural - Hindi) |
| Amazon Textract | Document OCR (Aadhaar, income cert) |
| Amazon DynamoDB | Sessions, users, scheme data |
| Amazon S3 | Document and audio storage |
| AWS EC2 | Hosts IndicTrans2 translation server |
| Amazon Cognito | OTP authentication |
| AWS IAM | Least-privilege access control |

## Data Flow: Voice Query

```
User speaks Hindi
      ↓
Browser MediaRecorder (audio/webm)
      ↓
POST /voice (multipart)
      ↓
Upload to S3 (audio/job123.webm)
      ↓
Amazon Transcribe (hi-IN)
      ↓
Transcript: "मुझे किसान योजना बताओ"
      ↓
Load session history (DynamoDB)
      ↓
Bedrock — Claude 3 Sonnet
  System: [schemes database + instructions]
  Messages: [history + transcript]
      ↓
AI reply in Hindi (same language as input)
      ↓
Save history (DynamoDB, 30-day TTL)
      ↓
Return {transcript, reply, sessionId}
      ↓
Frontend plays TTS via /speak (Polly)
```

## Scheme RAG Pipeline

```
data/schemes.json (15 schemes)
      ↓
seed_schemes.py
      ↓
DynamoDB (keyword search, instant)
      ↓  (optional)
Titan Embeddings (1536-dim vectors)
      ↓
OpenSearch k-NN (semantic search)
      ↓
Claude 3 assembles personalised answer
```
