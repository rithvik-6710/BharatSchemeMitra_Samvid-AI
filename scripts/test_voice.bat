@echo off
REM Quick voice testing script for Windows
REM Usage: scripts\test_voice.bat

setlocal

if "%API_URL%"=="" set API_URL=http://localhost:5000

echo Testing Voice Processing
echo API URL: %API_URL%
echo.

echo ================================================
echo Test 1: Checking Voice Services Configuration
echo ================================================

curl -s "%API_URL%/test-voice" > temp_response.json
findstr "OK" temp_response.json >nul

if %errorlevel%==0 (
    echo [PASS] All voice services configured correctly!
    type temp_response.json
) else (
    echo [FAIL] Voice services have issues
    type temp_response.json
    echo.
    echo Please fix the issues above before testing voice features
    del temp_response.json
    exit /b 1
)

echo.

echo ================================================
echo Test 2: Testing Text-to-Speech (Polly)
echo ================================================

curl -s -X POST "%API_URL%/speak" -H "Content-Type: application/json" -d "{\"text\": \"Hello, this is a test\", \"language\": \"en\"}" > temp_tts.json

findstr "audio_base64" temp_tts.json >nul

if %errorlevel%==0 (
    echo [PASS] Text-to-speech working!
) else (
    echo [FAIL] Text-to-speech failed
    type temp_tts.json
)

echo.

echo ================================================
echo Test 3: Testing Speech-to-Text (Transcribe)
echo ================================================

if exist test.mp3 (
    echo Found test.mp3, uploading...
    curl -s -X POST "%API_URL%/voice" -F "audio=@test.mp3" -F "language=hi" -F "sessionId=test-voice-123" > temp_voice.json
    
    findstr "transcript" temp_voice.json >nul
    
    if %errorlevel%==0 (
        echo [PASS] Speech-to-text working!
        type temp_voice.json
    ) else (
        echo [FAIL] Speech-to-text failed
        type temp_voice.json
    )
) else (
    echo [SKIP] No test.mp3 file found
    echo To test speech-to-text, create a test.mp3 file with some speech
)

echo.

echo ================================================
echo Test Summary
echo ================================================

findstr "OK" temp_response.json >nul

if %errorlevel%==0 (
    echo [PASS] Voice services: READY
    echo [PASS] Text-to-speech: WORKING
    
    if exist test.mp3 (
        findstr "transcript" temp_voice.json >nul
        if %errorlevel%==0 (
            echo [PASS] Speech-to-text: WORKING
            echo.
            echo All voice features are working!
        ) else (
            echo [FAIL] Speech-to-text: FAILED
            echo.
            echo Check the error above and fix speech-to-text
        )
    ) else (
        echo [SKIP] Speech-to-text: NOT TESTED (no test.mp3)
        echo.
        echo Voice features are ready, but create test.mp3 to fully test
    )
) else (
    echo [FAIL] Voice services: NOT CONFIGURED
    echo.
    echo Please configure AWS services before using voice features
)

REM Cleanup
del temp_response.json 2>nul
del temp_tts.json 2>nul
del temp_voice.json 2>nul

echo.
pause
