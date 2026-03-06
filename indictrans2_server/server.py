"""
indictrans2_server/server.py
IndicTrans2 Translation Server — runs on AWS EC2 (g4dn.xlarge or t3.large)
Model: ai4bharat/indictrans2-en-indic-1B  (supports 22 Indian languages)

Setup: see scripts/setup_indictrans2_ec2.sh
Run:   uvicorn server:app --host 0.0.0.0 --port 5001
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Flores-200 language codes used by IndicTrans2 ────────────
LANG_CODE_MAP = {
    "hi":  "hin_Deva",   # Hindi
    "ta":  "tam_Taml",   # Tamil
    "te":  "tel_Telu",   # Telugu
    "bn":  "ben_Beng",   # Bengali
    "mr":  "mar_Deva",   # Marathi
    "gu":  "guj_Gujr",   # Gujarati
    "kn":  "kan_Knda",   # Kannada
    "ml":  "mal_Mlym",   # Malayalam
    "pa":  "pan_Guru",   # Punjabi
    "or":  "ory_Orya",   # Odia
    "as":  "asm_Beng",   # Assamese
    "ur":  "urd_Arab",   # Urdu
    "en":  "eng_Latn",   # English
    "sa":  "san_Deva",   # Sanskrit
    "ne":  "npi_Deva",   # Nepali
    "mai": "mai_Deva",   # Maithili
    "kok": "kok_Deva",   # Konkani
    "doi": "doi_Deva",   # Dogri
    "ks":  "kas_Arab",   # Kashmiri
    "sat": "sat_Olck",   # Santali
    "mni": "mni_Mtei",   # Manipuri (Meitei)
    "brx": "brx_Deva",   # Bodo
}

# Global model references
_model = None
_tokenizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, release on shutdown."""
    global _model, _tokenizer
    logger.info("Loading IndicTrans2 model — ai4bharat/indictrans2-en-indic-1B ...")
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        model_name = "ai4bharat/indictrans2-en-indic-1B"

        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        _model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = _model.to(device)
        _model.eval()
        logger.info(f"✅ IndicTrans2 loaded on {device.upper()}")
    except Exception as e:
        logger.error(f"❌ Model load failed: {e}")
        logger.warning("Running in MOCK mode — install model dependencies and try again")

    yield  # App is running

    # Cleanup on shutdown
    _model = None
    _tokenizer = None
    logger.info("IndicTrans2 model released")


app = FastAPI(
    title="IndicTrans2 Translation Server",
    description="AI4Bharat IndicTrans2 — 22 Indian language translation (no BHASHINI needed)",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Pydantic models ───────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str
    source: str = "en"
    target: str = "hi"


class TranslateResponse(BaseModel):
    translated: str
    source: str
    target: str
    engine: str = "IndicTrans2"
    model: str = "ai4bharat/indictrans2-en-indic-1B"


# ── Translation helper ────────────────────────────────────────

def run_translation(text: str, src_flores: str, tgt_flores: str) -> str:
    """
    Run IndicTrans2 translation.
    Uses the correct tokenizer API for ai4bharat/indictrans2-en-indic-1B.
    """
    if _model is None or _tokenizer is None:
        raise RuntimeError("Model not loaded")

    # IndicTrans2 tokenizer accepts src_lang as a parameter
    inputs = _tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256,
    ).to(_model.device)

    # Get the forced BOS token ID for the target language
    try:
        forced_bos_id = _tokenizer.convert_tokens_to_ids(tgt_flores)
    except Exception:
        # Fallback: use lang_code_to_id if available
        forced_bos_id = _tokenizer.lang_code_to_id.get(tgt_flores)

    if forced_bos_id is None or forced_bos_id == _tokenizer.unk_token_id:
        raise ValueError(f"Target language token not found for: {tgt_flores}")

    with torch.no_grad():
        output_tokens = _model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_id,
            max_new_tokens=256,
            num_beams=4,
            early_stopping=True,
        )

    translated = _tokenizer.batch_decode(
        output_tokens,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]
    return translated


# ── Routes ────────────────────────────────────────────────────

@app.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if req.source not in LANG_CODE_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported source language: '{req.source}'. Supported: {list(LANG_CODE_MAP.keys())}")

    if req.target not in LANG_CODE_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: '{req.target}'. Supported: {list(LANG_CODE_MAP.keys())}")

    # Same language — return as-is immediately
    if req.source == req.target:
        return TranslateResponse(
            translated=req.text,
            source=req.source,
            target=req.target,
        )

    # Mock mode (model not loaded yet)
    if _model is None:
        logger.warning("Model not loaded — returning mock translation")
        return TranslateResponse(
            translated=f"[{req.target.upper()}] {req.text}",
            source=req.source,
            target=req.target,
            engine="IndicTrans2-MOCK",
        )

    try:
        src_flores = LANG_CODE_MAP[req.source]
        tgt_flores = LANG_CODE_MAP[req.target]
        translated = run_translation(req.text, src_flores, tgt_flores)
        return TranslateResponse(
            translated=translated,
            source=req.source,
            target=req.target,
        )
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


@app.post("/translate/batch")
async def translate_batch(texts: list[str], source: str = "en", target: str = "hi"):
    """Translate multiple strings in one call (more efficient than looping)."""
    results = []
    for text in texts:
        try:
            req = TranslateRequest(text=text, source=source, target=target)
            result = await translate(req)
            results.append(result.translated)
        except Exception:
            results.append(text)  # On error, return original
    return {"translations": results, "count": len(results)}


@app.get("/health")
async def health():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return {
        "status":              "ok",
        "model":               "ai4bharat/indictrans2-en-indic-1B",
        "model_loaded":        _model is not None,
        "device":              device,
        "supported_languages": list(LANG_CODE_MAP.keys()),
        "language_count":      len(LANG_CODE_MAP),
    }


@app.get("/languages")
async def list_languages():
    return {
        "languages": LANG_CODE_MAP,
        "total":     len(LANG_CODE_MAP),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
