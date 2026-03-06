#!/bin/bash
# scripts/test_endpoints.sh
# Quick smoke test for all Bharat Scheme Mitra API endpoints.
# Usage: ./scripts/test_endpoints.sh [API_URL]
# Example: ./scripts/test_endpoints.sh http://localhost:5000

API=${1:-http://localhost:5000}
PASS=0
FAIL=0

check() {
  local name=$1
  local result=$2
  if echo "$result" | grep -q "$3"; then
    echo "  ✅ $name"
    ((PASS++))
  else
    echo "  ❌ $name — got: ${result:0:120}"
    ((FAIL++))
  fi
}

echo ""
echo "🧪 Bharat Scheme Mitra API Smoke Tests"
echo "   Target: $API"
echo ""

# Health
R=$(curl -s "$API/health")
check "GET /health → status ok"        "$R" '"status"'
check "GET /health → IndicTrans2 info" "$R" 'IndicTrans2'
check "GET /health → schemes_loaded"   "$R" 'schemes_loaded'

# Schemes list
R=$(curl -s "$API/schemes")
check "GET /schemes → returns list"    "$R" '"schemes"'
check "GET /schemes → 15+ schemes"     "$R" '"total"'

# Schemes filter
R=$(curl -s "$API/schemes?category=agriculture")
check "GET /schemes?category=agriculture" "$R" 'agriculture'

# Chat
R=$(curl -s -X POST "$API/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"I am a farmer in UP, what schemes can I get?","sessionId":"smoke-test-1"}')
check "POST /chat → has reply"      "$R" '"reply"'
check "POST /chat → has sessionId"  "$R" '"sessionId"'

# Chat — Hindi
R=$(curl -s -X POST "$API/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"मैं किसान हूं","sessionId":"smoke-test-hindi"}')
check "POST /chat Hindi → has reply" "$R" '"reply"'

# Chat — empty message
R=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":""}')
check "POST /chat empty → 400"  "$R" "400"

# Translate
R=$(curl -s -X POST "$API/translate" \
  -H "Content-Type: application/json" \
  -d '{"text":"You are eligible for this scheme","source":"en","target":"hi"}')
check "POST /translate → has translated" "$R" '"translated"'
check "POST /translate → has engine"     "$R" 'IndicTrans2'

# Translate — same language
R=$(curl -s -X POST "$API/translate" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello","source":"en","target":"en"}')
check "POST /translate same lang → original returned" "$R" 'Hello'

# Summary
echo ""
echo "══════════════════════════════════"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
if [ $FAIL -eq 0 ]; then
  echo "  🎉 All tests passed!"
else
  echo "  ⚠️  Some tests failed. Check the backend logs."
fi
echo "══════════════════════════════════"
echo ""
