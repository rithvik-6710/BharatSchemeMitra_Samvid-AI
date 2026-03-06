#!/bin/bash

# verify_aws_setup.sh - Verify AWS services configuration
# Run this to check if all AWS services are properly configured

echo "🔍 Verifying AWS Configuration..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check AWS CLI
echo "1️⃣ Checking AWS CLI..."
if command -v aws &> /dev/null; then
    echo -e "${GREEN}✅ AWS CLI installed${NC}"
else
    echo -e "${RED}❌ AWS CLI not installed${NC}"
    echo "   Install: https://aws.amazon.com/cli/"
    exit 1
fi
echo ""

# Check AWS credentials
echo "2️⃣ Checking AWS Credentials..."
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    USER=$(aws sts get-caller-identity --query Arn --output text)
    echo -e "${GREEN}✅ AWS credentials valid${NC}"
    echo "   Account: $ACCOUNT"
    echo "   User: $USER"
else
    echo -e "${RED}❌ AWS credentials invalid${NC}"
    echo "   Check your .env file"
    exit 1
fi
echo ""

# Check S3 bucket
echo "3️⃣ Checking S3 Bucket..."
BUCKET="welfare-docs-843374720127-2026"
if aws s3 ls "s3://$BUCKET" &> /dev/null; then
    echo -e "${GREEN}✅ S3 bucket accessible: $BUCKET${NC}"
else
    echo -e "${YELLOW}⚠️  S3 bucket not found: $BUCKET${NC}"
    echo "   Create it: aws s3 mb s3://$BUCKET --region ap-south-1"
fi
echo ""

# Check DynamoDB tables
echo "4️⃣ Checking DynamoDB Tables..."
REGION="ap-south-1"

# Check sessions table
if aws dynamodb describe-table --table-name welfare-sessions --region $REGION &> /dev/null; then
    echo -e "${GREEN}✅ DynamoDB table exists: welfare-sessions${NC}"
else
    echo -e "${YELLOW}⚠️  DynamoDB table not found: welfare-sessions${NC}"
    echo "   Create it: See HOW_TO_CONFIGURE_AWS.md Step 2"
fi

# Check users table
if aws dynamodb describe-table --table-name welfare-users --region $REGION &> /dev/null; then
    echo -e "${GREEN}✅ DynamoDB table exists: welfare-users${NC}"
else
    echo -e "${YELLOW}⚠️  DynamoDB table not found: welfare-users${NC}"
    echo "   Create it: See HOW_TO_CONFIGURE_AWS.md Step 2"
fi
echo ""

# Check SNS topics
echo "5️⃣ Checking SNS Topics..."
SNS_TOPICS=$(aws sns list-topics --region $REGION --query 'Topics[*].TopicArn' --output text 2>/dev/null)
if [ -n "$SNS_TOPICS" ]; then
    echo -e "${GREEN}✅ SNS topics found:${NC}"
    echo "$SNS_TOPICS" | tr '\t' '\n' | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  No SNS topics found (optional)${NC}"
    echo "   Create one: See HOW_TO_CONFIGURE_AWS.md - SMS Notifications"
fi
echo ""

# Check SES verified emails
echo "6️⃣ Checking SES Verified Emails..."
SES_EMAILS=$(aws ses list-verified-email-addresses --region $REGION --query 'VerifiedEmailAddresses' --output text 2>/dev/null)
if [ -n "$SES_EMAILS" ]; then
    echo -e "${GREEN}✅ SES verified emails:${NC}"
    echo "$SES_EMAILS" | tr '\t' '\n' | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  No SES verified emails (optional)${NC}"
    echo "   Verify one: See HOW_TO_CONFIGURE_AWS.md - Email Notifications"
fi
echo ""

# Check Bedrock access
echo "7️⃣ Checking Bedrock Access..."
if aws bedrock list-foundation-models --region us-east-1 &> /dev/null; then
    echo -e "${GREEN}✅ Bedrock accessible${NC}"
else
    echo -e "${RED}❌ Bedrock not accessible${NC}"
    echo "   Check IAM permissions"
fi
echo ""

# Check .env file
echo "8️⃣ Checking .env File..."
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check required variables
    if grep -q "AWS_ACCESS_KEY_ID" backend/.env; then
        echo -e "${GREEN}   ✅ AWS_ACCESS_KEY_ID set${NC}"
    else
        echo -e "${RED}   ❌ AWS_ACCESS_KEY_ID missing${NC}"
    fi
    
    if grep -q "AWS_SECRET_ACCESS_KEY" backend/.env; then
        echo -e "${GREEN}   ✅ AWS_SECRET_ACCESS_KEY set${NC}"
    else
        echo -e "${RED}   ❌ AWS_SECRET_ACCESS_KEY missing${NC}"
    fi
    
    if grep -q "S3_BUCKET" backend/.env; then
        echo -e "${GREEN}   ✅ S3_BUCKET set${NC}"
    else
        echo -e "${YELLOW}   ⚠️  S3_BUCKET not set${NC}"
    fi
    
    if grep -q "SESSIONS_TABLE" backend/.env; then
        echo -e "${GREEN}   ✅ SESSIONS_TABLE set${NC}"
    else
        echo -e "${YELLOW}   ⚠️  SESSIONS_TABLE not set (optional)${NC}"
    fi
    
    if grep -q "USERS_TABLE" backend/.env; then
        echo -e "${GREEN}   ✅ USERS_TABLE set${NC}"
    else
        echo -e "${YELLOW}   ⚠️  USERS_TABLE not set (optional)${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
    echo "   Copy from: cp backend/.env.example backend/.env"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Core Services (Required):"
echo "  • AWS Credentials: Check above"
echo "  • Bedrock: Check above"
echo "  • S3: Check above"
echo "  • Transcribe: Automatic with credentials"
echo "  • Polly: Automatic with credentials"
echo "  • Comprehend: Automatic with credentials"
echo ""
echo "Optional Services:"
echo "  • DynamoDB: Check above"
echo "  • SNS: Check above"
echo "  • SES: Check above"
echo "  • CloudWatch: Automatic with credentials"
echo ""
echo "Next Steps:"
echo "  1. Fix any ❌ errors above"
echo "  2. Optionally configure ⚠️  services"
echo "  3. Run: cd backend && python app.py"
echo "  4. Test: curl http://localhost:5000/health"
echo ""
echo "For detailed setup instructions, see: HOW_TO_CONFIGURE_AWS.md"
echo ""
