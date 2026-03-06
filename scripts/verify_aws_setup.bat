@echo off
REM verify_aws_setup.bat - Verify AWS services configuration for Windows
REM Run this to check if all AWS services are properly configured

echo.
echo Verifying AWS Configuration...
echo.

REM Check AWS CLI
echo 1. Checking AWS CLI...
where aws >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AWS CLI installed
) else (
    echo [ERROR] AWS CLI not installed
    echo    Install: https://aws.amazon.com/cli/
    exit /b 1
)
echo.

REM Check AWS credentials
echo 2. Checking AWS Credentials...
aws sts get-caller-identity >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AWS credentials valid
    for /f "tokens=*" %%a in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT=%%a
    echo    Account: %ACCOUNT%
) else (
    echo [ERROR] AWS credentials invalid
    echo    Check your .env file
    exit /b 1
)
echo.

REM Check S3 bucket
echo 3. Checking S3 Bucket...
set BUCKET=welfare-docs-843374720127-2026
aws s3 ls s3://%BUCKET% >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] S3 bucket accessible: %BUCKET%
) else (
    echo [WARNING] S3 bucket not found: %BUCKET%
    echo    Create it: aws s3 mb s3://%BUCKET% --region ap-south-1
)
echo.

REM Check DynamoDB tables
echo 4. Checking DynamoDB Tables...
set REGION=ap-south-1

aws dynamodb describe-table --table-name welfare-sessions --region %REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] DynamoDB table exists: welfare-sessions
) else (
    echo [WARNING] DynamoDB table not found: welfare-sessions
    echo    Create it: See HOW_TO_CONFIGURE_AWS.md Step 2
)

aws dynamodb describe-table --table-name welfare-users --region %REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] DynamoDB table exists: welfare-users
) else (
    echo [WARNING] DynamoDB table not found: welfare-users
    echo    Create it: See HOW_TO_CONFIGURE_AWS.md Step 2
)
echo.

REM Check SNS topics
echo 5. Checking SNS Topics...
aws sns list-topics --region %REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] SNS accessible
    echo    Check AWS Console for topics
) else (
    echo [WARNING] No SNS topics found (optional)
    echo    Create one: See HOW_TO_CONFIGURE_AWS.md - SMS Notifications
)
echo.

REM Check SES verified emails
echo 6. Checking SES Verified Emails...
aws ses list-verified-email-addresses --region %REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] SES accessible
    echo    Check AWS Console for verified emails
) else (
    echo [WARNING] No SES verified emails (optional)
    echo    Verify one: See HOW_TO_CONFIGURE_AWS.md - Email Notifications
)
echo.

REM Check Bedrock access
echo 7. Checking Bedrock Access...
aws bedrock list-foundation-models --region us-east-1 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Bedrock accessible
) else (
    echo [ERROR] Bedrock not accessible
    echo    Check IAM permissions
)
echo.

REM Check .env file
echo 8. Checking .env File...
if exist "backend\.env" (
    echo [OK] .env file exists
    
    findstr /C:"AWS_ACCESS_KEY_ID" backend\.env >nul 2>&1
    if %errorlevel% equ 0 (
        echo    [OK] AWS_ACCESS_KEY_ID set
    ) else (
        echo    [ERROR] AWS_ACCESS_KEY_ID missing
    )
    
    findstr /C:"AWS_SECRET_ACCESS_KEY" backend\.env >nul 2>&1
    if %errorlevel% equ 0 (
        echo    [OK] AWS_SECRET_ACCESS_KEY set
    ) else (
        echo    [ERROR] AWS_SECRET_ACCESS_KEY missing
    )
    
    findstr /C:"S3_BUCKET" backend\.env >nul 2>&1
    if %errorlevel% equ 0 (
        echo    [OK] S3_BUCKET set
    ) else (
        echo    [WARNING] S3_BUCKET not set
    )
    
    findstr /C:"SESSIONS_TABLE" backend\.env >nul 2>&1
    if %errorlevel% equ 0 (
        echo    [OK] SESSIONS_TABLE set
    ) else (
        echo    [WARNING] SESSIONS_TABLE not set (optional)
    )
    
    findstr /C:"USERS_TABLE" backend\.env >nul 2>&1
    if %errorlevel% equ 0 (
        echo    [OK] USERS_TABLE set
    ) else (
        echo    [WARNING] USERS_TABLE not set (optional)
    )
) else (
    echo [ERROR] .env file not found
    echo    Copy from: copy backend\.env.example backend\.env
)
echo.

REM Summary
echo ================================================================
echo SUMMARY
echo ================================================================
echo.
echo Core Services (Required):
echo   - AWS Credentials: Check above
echo   - Bedrock: Check above
echo   - S3: Check above
echo   - Transcribe: Automatic with credentials
echo   - Polly: Automatic with credentials
echo   - Comprehend: Automatic with credentials
echo.
echo Optional Services:
echo   - DynamoDB: Check above
echo   - SNS: Check above
echo   - SES: Check above
echo   - CloudWatch: Automatic with credentials
echo.
echo Next Steps:
echo   1. Fix any [ERROR] items above
echo   2. Optionally configure [WARNING] services
echo   3. Run: cd backend ^&^& python app.py
echo   4. Test: curl http://localhost:5000/health
echo.
echo For detailed setup instructions, see: HOW_TO_CONFIGURE_AWS.md
echo.

pause
