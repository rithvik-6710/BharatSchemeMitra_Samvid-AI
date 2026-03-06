# Contributing to Bharat Scheme Mitra

## Quick contributions

- 📋 **Add more schemes** — edit `data/schemes.json`, follow the existing JSON format
- 🌍 **Add language support** — update `LANGS` array in `frontend/src/App.js`  
- 🐛 **Bug fixes** — check open Issues, submit a PR
- 📖 **Improve docs** — edit files in `docs/`

## Dev setup

```bash
# Backend
cd backend && pip install -r requirements.txt && python app.py

# Frontend
cd frontend && npm install && npm start

# Tests
cd backend && pytest tests/ -v
```

## Pull Request checklist

- [ ] `pytest tests/` passes
- [ ] No credentials or `.env` committed
- [ ] New schemes have all 7 required fields
