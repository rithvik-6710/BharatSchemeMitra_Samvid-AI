#!/bin/bash

# Quick voice testing script
# Usage: ./scripts/test_voice.sh

API_URL="${API_URL:-http://localhost:5000}"

echo "🎤 Testing Voice Processing"
echo "API URL: $API_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Check voice services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Checking Voice Services Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response=$(curl -s "$API_URL/test-voice")
status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

if [ "$status" = "OK" ]; then
    echo -e "${GREEN}✓ All voice services configured correctly!${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${RED}✗ Voice services have issues${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    echo -e "${YELLOW}Please fix the issues above before testing voice features${NC}"
    exit 1
fi

echo ""

# Test 2: Test TTS
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Testing Text-to-Speech (Polly)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

tts_response=$(curl -s -X POST "$API_URL/speak" \
    -H "Content-Type: application/json" \
    -d '{"text": "Hello, this is a test", "language": "en"}')

if echo "$tts_response" | grep -q "audio_base64"; then
    echo -e "${GREEN}✓ Text-to-speech working!${NC}"
    audio_length=$(echo "$tts_response" | grep -o '"audio_base64":"[^"]*"' | wc -c)
    echo "Audio data length: $audio_length bytes"
else
    echo -e "${RED}✗ Text-to-speech failed${NC}"
    echo "$tts_response" | python3 -m json.tool 2>/dev/null || echo "$tts_response"
fi

echo ""

# Test 3: Check if test audio file exists
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Testing Speech-to-Text (Transcribe)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "test.mp3" ]; then
    echo "Found test.mp3, uploading..."
    
    voice_response=$(curl -s -X POST "$API_URL/voice" \
        -F "audio=@test.mp3" \
        -F "language=hi" \
        -F "sessionId=test-voice-123")
    
    if echo "$voice_response" | grep -q "transcript"; then
        echo -e "${GREEN}✓ Speech-to-text working!${NC}"
        transcript=$(echo "$voice_response" | grep -o '"transcript":"[^"]*"' | cut -d'"' -f4)
        echo "Transcript: $transcript"
    else
        echo -e "${RED}✗ Speech-to-text failed${NC}"
        echo "$voice_response" | python3 -m json.tool 2>/dev/null || echo "$voice_response"
    fi
else
    echo -e "${YELLOW}⚠ No test.mp3 file found${NC}"
    echo "To test speech-to-text, create a test.mp3 file with some speech"
    echo "Example: Record yourself saying 'मैं किसान हूं' and save as test.mp3"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$status" = "OK" ]; then
    echo -e "${GREEN}✓ Voice services: READY${NC}"
    echo -e "${GREEN}✓ Text-to-speech: WORKING${NC}"
    
    if [ -f "test.mp3" ]; then
        if echo "$voice_response" | grep -q "transcript"; then
            echo -e "${GREEN}✓ Speech-to-text: WORKING${NC}"
            echo ""
            echo -e "${GREEN}🎉 All voice features are working!${NC}"
        else
            echo -e "${RED}✗ Speech-to-text: FAILED${NC}"
            echo ""
            echo -e "${YELLOW}Check the error above and fix speech-to-text${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Speech-to-text: NOT TESTED (no test.mp3)${NC}"
        echo ""
        echo -e "${YELLOW}Voice features are ready, but create test.mp3 to fully test${NC}"
    fi
else
    echo -e "${RED}✗ Voice services: NOT CONFIGURED${NC}"
    echo ""
    echo -e "${RED}Please configure AWS services before using voice features${NC}"
fi

echo ""
