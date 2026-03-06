#!/bin/bash

# Test script for enhanced Bharat Scheme Mitra features
# Usage: ./scripts/test_enhanced_features.sh

set -e

API_URL="${API_URL:-http://localhost:5000}"
SESSION_ID="test-$(date +%s)"

echo "🧪 Testing Enhanced Bharat Scheme Mitra"
echo "API URL: $API_URL"
echo "Session ID: $SESSION_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected="$5"
    
    echo -n "Testing: $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s "$API_URL$endpoint")
    else
        response=$(curl -s -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Response: $response"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. BASIC HEALTH CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint \
    "Health check" \
    "GET" \
    "/health" \
    "" \
    "ok"

test_endpoint \
    "Schemes list" \
    "GET" \
    "/schemes" \
    "" \
    "schemes"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. CONVERSATIONAL AI TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: Profile extraction
echo -e "${YELLOW}Test: Profile extraction from conversation${NC}"
response=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"I am a farmer from Maharashtra with 5 acres\",
        \"sessionId\": \"$SESSION_ID\",
        \"language\": \"en\"
    }")

if echo "$response" | grep -q "user_profile"; then
    echo -e "${GREEN}✓ Profile extraction working${NC}"
    ((TESTS_PASSED++))
    
    # Check if profile contains expected fields
    if echo "$response" | grep -q "farmer" && echo "$response" | grep -q "Maharashtra"; then
        echo -e "${GREEN}✓ Profile contains occupation and state${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ Profile missing expected fields${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}✗ Profile extraction failed${NC}"
    ((TESTS_FAILED++))
fi

# Test 2: Intent detection - Application guidance
echo ""
echo -e "${YELLOW}Test: Intent detection - Application guidance${NC}"
response=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"How do I apply for PM-KISAN?\",
        \"sessionId\": \"$SESSION_ID\",
        \"language\": \"en\"
    }")

if echo "$response" | grep -q "application_guidance"; then
    echo -e "${GREEN}✓ Application guidance intent detected${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Intent detection failed${NC}"
    echo "Response: $response"
    ((TESTS_FAILED++))
fi

# Test 3: Intent detection - Document help
echo ""
echo -e "${YELLOW}Test: Intent detection - Document help${NC}"
response=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"What documents do I need for Aadhaar?\",
        \"sessionId\": \"$SESSION_ID\",
        \"language\": \"en\"
    }")

if echo "$response" | grep -q "document"; then
    echo -e "${GREEN}✓ Document help intent detected${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Document intent detection failed${NC}"
    ((TESTS_FAILED++))
fi

# Test 4: Sentiment analysis
echo ""
echo -e "${YELLOW}Test: Sentiment analysis${NC}"
response=$(curl -s -X POST "$API_URL/sentiment" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"I am very happy with this service!\",
        \"language\": \"en\"
    }")

if echo "$response" | grep -q "POSITIVE"; then
    echo -e "${GREEN}✓ Positive sentiment detected${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Sentiment analysis failed${NC}"
    ((TESTS_FAILED++))
fi

response=$(curl -s -X POST "$API_URL/sentiment" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"I am frustrated with this process!\",
        \"language\": \"en\"
    }")

if echo "$response" | grep -q "NEGATIVE"; then
    echo -e "${GREEN}✓ Negative sentiment detected${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Negative sentiment detection failed${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. PROFILE MANAGEMENT TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

USER_ID="test-user-$(date +%s)"

# Test: Create profile
echo -e "${YELLOW}Test: Create user profile${NC}"
response=$(curl -s -X POST "$API_URL/profile" \
    -H "Content-Type: application/json" \
    -d "{
        \"userId\": \"$USER_ID\",
        \"profile\": {
            \"occupation\": \"farmer\",
            \"state\": \"Maharashtra\",
            \"land_acres\": 5,
            \"income_bracket\": \"middle_class\"
        }
    }")

if echo "$response" | grep -q "farmer"; then
    echo -e "${GREEN}✓ Profile created successfully${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Profile creation failed${NC}"
    ((TESTS_FAILED++))
fi

# Test: Get profile
echo ""
echo -e "${YELLOW}Test: Retrieve user profile${NC}"
response=$(curl -s "$API_URL/profile?userId=$USER_ID")

if echo "$response" | grep -q "farmer" && echo "$response" | grep -q "Maharashtra"; then
    echo -e "${GREEN}✓ Profile retrieved successfully${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Profile retrieval failed${NC}"
    ((TESTS_FAILED++))
fi

# Test: Personalized recommendations
echo ""
echo -e "${YELLOW}Test: Personalized scheme recommendations${NC}"
response=$(curl -s -X POST "$API_URL/schemes/personalized" \
    -H "Content-Type: application/json" \
    -d "{
        \"profile\": {
            \"occupation\": \"farmer\",
            \"state\": \"Maharashtra\",
            \"land_acres\": 5
        },
        \"language\": \"en\"
    }")

if echo "$response" | grep -q "schemes"; then
    echo -e "${GREEN}✓ Personalized recommendations working${NC}"
    ((TESTS_PASSED++))
    
    # Check if agriculture schemes are prioritized
    if echo "$response" | grep -q "agriculture"; then
        echo -e "${GREEN}✓ Relevant schemes prioritized${NC}"
        ((TESTS_PASSED++))
    fi
else
    echo -e "${RED}✗ Personalized recommendations failed${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. MULTILINGUAL TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test: Language detection
echo -e "${YELLOW}Test: Automatic language detection${NC}"
response=$(curl -s -X POST "$API_URL/detect-language" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"मैं किसान हूं\"
    }")

if echo "$response" | grep -q "hi"; then
    echo -e "${GREEN}✓ Hindi language detected${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Language detection failed${NC}"
    ((TESTS_FAILED++))
fi

# Test: Hindi conversation
echo ""
echo -e "${YELLOW}Test: Hindi conversation${NC}"
response=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"मैं किसान हूं\",
        \"sessionId\": \"test-hi-$(date +%s)\",
        \"language\": \"hi\"
    }")

if echo "$response" | grep -q "reply"; then
    echo -e "${GREEN}✓ Hindi conversation working${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Hindi conversation failed${NC}"
    ((TESTS_FAILED++))
fi

# Test: Translation
echo ""
echo -e "${YELLOW}Test: Translation service${NC}"
response=$(curl -s -X POST "$API_URL/translate" \
    -H "Content-Type: application/json" \
    -d "{
        \"text\": \"Hello, how are you?\",
        \"source\": \"en\",
        \"target\": \"hi\"
    }")

if echo "$response" | grep -q "translated"; then
    echo -e "${GREEN}✓ Translation service working${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Translation failed${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. CONTEXT RETENTION TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CONTEXT_SESSION="context-test-$(date +%s)"

echo -e "${YELLOW}Test: Multi-turn conversation with context${NC}"

# Turn 1: Introduce self
echo "Turn 1: User introduces themselves"
response1=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"I am a farmer from UP\",
        \"sessionId\": \"$CONTEXT_SESSION\",
        \"language\": \"en\"
    }")

if echo "$response1" | grep -q "user_profile"; then
    echo -e "${GREEN}✓ Turn 1: Profile extracted${NC}"
    ((TESTS_PASSED++))
fi

# Turn 2: Provide more details
echo "Turn 2: User provides more details"
response2=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"I have 2 acres of land\",
        \"sessionId\": \"$CONTEXT_SESSION\",
        \"language\": \"en\"
    }")

if echo "$response2" | grep -q "user_profile"; then
    echo -e "${GREEN}✓ Turn 2: Profile updated with land info${NC}"
    ((TESTS_PASSED++))
fi

# Turn 3: Ask about schemes
echo "Turn 3: User asks about schemes"
response3=$(curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"What schemes are available for me?\",
        \"sessionId\": \"$CONTEXT_SESSION\",
        \"language\": \"en\"
    }")

if echo "$response3" | grep -q "schemes"; then
    echo -e "${GREEN}✓ Turn 3: Personalized schemes provided${NC}"
    ((TESTS_PASSED++))
    
    # Check if context was used (should mention farmer/UP)
    if echo "$response3" | grep -qi "farmer\|agriculture"; then
        echo -e "${GREEN}✓ Context retained across turns${NC}"
        ((TESTS_PASSED++))
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. PERFORMANCE TESTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Test: Response time${NC}"

start_time=$(date +%s%N)
curl -s -X POST "$API_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{
        \"message\": \"test\",
        \"sessionId\": \"perf-test\",
        \"language\": \"en\"
    }" > /dev/null
end_time=$(date +%s%N)

duration=$(( (end_time - start_time) / 1000000 ))

if [ $duration -lt 5000 ]; then
    echo -e "${GREEN}✓ Response time: ${duration}ms (< 5000ms)${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Response time: ${duration}ms (> 5000ms)${NC}"
    echo "  (This is acceptable but could be optimized)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
PASS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo "Pass Rate: $PASS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Enhanced features are working correctly.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please check the output above.${NC}"
    exit 1
fi
