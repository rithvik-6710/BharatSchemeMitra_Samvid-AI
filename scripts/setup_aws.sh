#!/bin/bash
# =============================================================
# scripts/setup_aws.sh
# One-command setup for all required AWS resources.
# Run this FIRST before starting the backend.
#
# Usage: chmod +x scripts/setup_aws.sh && ./scripts/setup_aws.sh
# =============================================================

set -e

REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$ACCOUNT_ID" ]; then
  echo "❌ AWS CLI not configured. Run: aws configure"
  exit 1
fi

BUCKET_NAME="welfare-docs-${ACCOUNT_ID}-2026"

echo ""
echo "🇮🇳  Bharat Scheme Mitra — AWS Infrastructure Setup"
echo "    Region:  $REGION"
echo "    Account: $ACCOUNT_ID"
echo "    Bucket:  $BUCKET_NAME"
echo ""

# ── 1. DynamoDB Tables ─────────────────────────────────────────
echo "📦 Creating DynamoDB tables..."

aws dynamodb create-table \
  --table-name welfare-sessions \
  --attribute-definitions AttributeName=sessionId,AttributeType=S \
  --key-schema AttributeName=sessionId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION --no-cli-pager 2>/dev/null \
  && echo "   ✅ welfare-sessions created" \
  || echo "   ℹ️  welfare-sessions already exists"

aws dynamodb create-table \
  --table-name welfare-users \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION --no-cli-pager 2>/dev/null \
  && echo "   ✅ welfare-users created" \
  || echo "   ℹ️  welfare-users already exists"

aws dynamodb create-table \
  --table-name welfare-schemes \
  --attribute-definitions \
    AttributeName=schemeId,AttributeType=S \
    AttributeName=category,AttributeType=S \
  --key-schema \
    AttributeName=schemeId,KeyType=HASH \
    AttributeName=category,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION --no-cli-pager 2>/dev/null \
  && echo "   ✅ welfare-schemes created" \
  || echo "   ℹ️  welfare-schemes already exists"

# TTL on sessions — auto-delete after 30 days
aws dynamodb update-time-to-live \
  --table-name welfare-sessions \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region $REGION --no-cli-pager 2>/dev/null || true

# ── 2. S3 Bucket ───────────────────────────────────────────────
echo ""
echo "🪣 Creating S3 bucket..."

aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $REGION \
  --create-bucket-configuration LocationConstraint=$REGION \
  --no-cli-pager 2>/dev/null \
  && echo "   ✅ $BUCKET_NAME created" \
  || echo "   ℹ️  Bucket already exists"

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --no-cli-pager 2>/dev/null && echo "   ✅ Public access blocked"

# ── 3. Bedrock Model Access ────────────────────────────────────
echo ""
echo "🧠 Checking Bedrock access..."
aws bedrock list-foundation-models \
  --region $REGION \
  --query 'modelSummaries[?contains(modelId,`claude-3`)].modelId' \
  --output text --no-cli-pager 2>/dev/null \
  && echo "   ✅ Bedrock accessible" \
  || echo "   ⚠️  Enable Bedrock model access in AWS Console → ap-south-1 → Model access"

# ── 4. Write .env ──────────────────────────────────────────────
echo ""
echo "⚙️  Writing backend/.env ..."

cat > backend/.env <<EOF
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET=${BUCKET_NAME}
# Set this after running scripts/setup_indictrans2_ec2.sh
INDICTRANS2_URL=http://YOUR_EC2_PUBLIC_IP:5001
EOF

echo "   ✅ backend/.env written"

# ── 5. Done ───────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════"
echo "✅ AWS setup complete!"
echo ""
echo "Next steps:"
echo "  1. Launch EC2 (g4dn.xlarge or t3.large, Ubuntu 22.04)"
echo "     Open port 5001 in Security Group"
echo "     Then run: scripts/setup_indictrans2_ec2.sh on the EC2"
echo ""
echo "  2. Update backend/.env with your EC2 public IP"
echo "     INDICTRANS2_URL=http://YOUR_EC2_IP:5001"
echo ""
echo "  3. Seed scheme knowledge base:"
echo "     python scripts/seed_schemes.py"
echo ""
echo "  4. Start backend:"
echo "     cd backend && python app.py"
echo ""
echo "  5. Start frontend:"
echo "     cd frontend && npm install && npm start"
echo "══════════════════════════════════════════════════════"
