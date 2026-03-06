@echo off
REM Test script for enhanced Bharat Scheme Mitra features (Windows)
REM Usage: scripts\test_enhanced_features.bat

setlocal enabledelayedexpansion

if "%API_URL%"=="" set API_URL=http://localhost:5000
set SESSION_ID=test-%RANDOM%

echo Testing Enhanced Bharat Scheme Mitra
echo API URL: %API_URL%
echo Session ID: %SESSION_ID%
echo.

set TESTS_PASSED=0
set TESTS_FAILED=0

echo ================================================
echo 1. BASIC HEALTH CHECKS
echo ================================================

echo Testing: Health check...
curl -s "%API_URL%/health" | findstr "ok" >nul
if %errorlevel%==0 (
    echo [PASS] Health check
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Health check
    set /a TESTS_FAILED+=1
)

echo Testing: Schemes list...
curl -s "%API_URL%/schemes" | findstr "schemes" >nul
if %errorlevel%==0 (
    echo [PASS] Schemes list
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Schemes list
    set /a TESTS_FAILED+=1
)

echo.
echo ================================================
echo 2. CONVERSATIONAL AI TESTS
echo ================================================

echo Testing: Profile extraction...
curl -s -X POST "%API_URL%/chat" -H "Content-Type: application/json" -d "{\"message\": \"I am a farmer from Maharashtra\", \"sessionId\": \"%SESSION_ID%\", \"language\": \"en\"}" | findstr "user_profile" >nul
if %errorlevel%==0 (
    echo [PASS] Profile extraction
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Profile extraction
    set /a TESTS_FAILED+=1
)

echo Testing: Intent detection - Application guidance...
curl -s -X POST "%API_URL%/chat" -H "Content-Type: application/json" -d "{\"message\": \"How do I apply for PM-KISAN?\", \"sessionId\": \"%SESSION_ID%\", \"language\": \"en\"}" | findstr "application_guidance" >nul
if %errorlevel%==0 (
    echo [PASS] Application guidance intent
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Application guidance intent
    set /a TESTS_FAILED+=1
)

echo Testing: Sentiment analysis...
curl -s -X POST "%API_URL%/sentiment" -H "Content-Type: application/json" -d "{\"text\": \"I am very happy!\", \"language\": \"en\"}" | findstr "POSITIVE" >nul
if %errorlevel%==0 (
    echo [PASS] Positive sentiment
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Positive sentiment
    set /a TESTS_FAILED+=1
)

echo.
echo ================================================
echo 3. PROFILE MANAGEMENT TESTS
echo ================================================

set USER_ID=test-user-%RANDOM%

echo Testing: Create profile...
curl -s -X POST "%API_URL%/profile" -H "Content-Type: application/json" -d "{\"userId\": \"%USER_ID%\", \"profile\": {\"occupation\": \"farmer\", \"state\": \"Maharashtra\"}}" | findstr "farmer" >nul
if %errorlevel%==0 (
    echo [PASS] Profile creation
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Profile creation
    set /a TESTS_FAILED+=1
)

echo Testing: Get profile...
curl -s "%API_URL%/profile?userId=%USER_ID%" | findstr "farmer" >nul
if %errorlevel%==0 (
    echo [PASS] Profile retrieval
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Profile retrieval
    set /a TESTS_FAILED+=1
)

echo Testing: Personalized recommendations...
curl -s -X POST "%API_URL%/schemes/personalized" -H "Content-Type: application/json" -d "{\"profile\": {\"occupation\": \"farmer\", \"state\": \"Maharashtra\"}, \"language\": \"en\"}" | findstr "schemes" >nul
if %errorlevel%==0 (
    echo [PASS] Personalized recommendations
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Personalized recommendations
    set /a TESTS_FAILED+=1
)

echo.
echo ================================================
echo 4. MULTILINGUAL TESTS
echo ================================================

echo Testing: Language detection...
curl -s -X POST "%API_URL%/detect-language" -H "Content-Type: application/json" -d "{\"text\": \"मैं किसान हूं\"}" | findstr "hi" >nul
if %errorlevel%==0 (
    echo [PASS] Hindi language detection
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Hindi language detection
    set /a TESTS_FAILED+=1
)

echo Testing: Translation...
curl -s -X POST "%API_URL%/translate" -H "Content-Type: application/json" -d "{\"text\": \"Hello\", \"source\": \"en\", \"target\": \"hi\"}" | findstr "translated" >nul
if %errorlevel%==0 (
    echo [PASS] Translation service
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Translation service
    set /a TESTS_FAILED+=1
)

echo.
echo ================================================
echo TEST SUMMARY
echo ================================================
echo.

set /a TOTAL_TESTS=%TESTS_PASSED%+%TESTS_FAILED%
set /a PASS_RATE=%TESTS_PASSED%*100/%TOTAL_TESTS%

echo Total Tests: %TOTAL_TESTS%
echo Passed: %TESTS_PASSED%
echo Failed: %TESTS_FAILED%
echo Pass Rate: %PASS_RATE%%%
echo.

if %TESTS_FAILED%==0 (
    echo All tests passed! Enhanced features are working correctly.
    exit /b 0
) else (
    echo Some tests failed. Please check the output above.
    exit /b 1
)
