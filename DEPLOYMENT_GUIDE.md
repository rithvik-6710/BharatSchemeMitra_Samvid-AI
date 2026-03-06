# 🚀 Production Deployment Guide

## Overview

This guide covers deploying the enhanced Bharat Scheme Mitra to AWS for production use.

---

## 🏗️ Architecture for Production

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFront (CDN)                          │
│                  SSL/TLS Termination                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│   S3 Bucket  │          │ API Gateway  │
│  (Frontend)  │          │   (REST)     │
└──────────────┘          └──────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
            ┌──────────────┐          ┌──────────────┐
            │   Lambda     │          │  ECS Fargate │
            │  (Serverless)│          │  (Container) │
            └──────┬───────┘          └──────┬───────┘
                   │                         │
        ┌──────────┴─────────────────────────┴──────────┐
        │                                                │
        ▼                ▼              ▼               ▼
   ┌────────┐      ┌─────────┐    ┌────────┐     ┌─────────┐
   │Bedrock │      │DynamoDB │    │   S3   │     │ EC2     │
   │(AI)    │      │(Data)   │    │(Docs)  │     │(Trans)  │
   └────────┘      └─────────┘    └────────┘     └─────────┘
```

---

## 📋 Prerequisites

- AWS Account with admin access
- AWS CLI configured
- Docker installed (for container deployment)
- Node.js 18+ and Python 3.11+
- Domain name (optional, for custom domain)

---

## 🎯 Deployment Options

### Option 1: Serverless (Lambda + API Gateway) - Recommended

**Pros:**
- Auto-scaling
- Pay per request
- No server management
- High availability

**Cons:**
- Cold start latency
- 15-minute timeout limit

### Option 2: Container (ECS Fargate)

**Pros:**
- No cold starts
- Long-running processes
- More control

**Cons:**
- Higher cost
- Need to manage scaling

### Option 3: Traditional (EC2 + Load Balancer)

**Pros:**
- Full control
- Predictable costs

**Cons:**
- Manual scaling
- Server management

---

## 🚀 Option 1: Serverless Deployment (Recommended)

### Step 1: Prepare Backend for Lambda

Create `backend/lambda_handler.py`:

```python
"""
Lambda handler for Bharat Scheme Mitra
"""
import json
from app_enhanced import app

def lambda_handler(event, context):
    """AWS Lambda handler"""
    # Convert API Gateway event to Flask request
    from werkzeug.wrappers import Request
    from io import BytesIO
    
    # Handle API Gateway proxy integration
    if 'httpMethod' in event:
        method = event['httpMethod']
        path = event['path']
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        # Create WSGI environment
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': event.get('queryStringParameters', ''),
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': str(len(body)),
            'wsgi.input': BytesIO(body.encode() if body else b''),
            'wsgi.url_scheme': 'https',
            'SERVER_NAME': headers.get('host', 'localhost'),
            'SERVER_PORT': '443',
        }
        
        # Add headers
        for key, value in headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # Call Flask app
        with app.request_context(environ):
            response = app.full_dispatch_request()
            
            return {
                'statusCode': response.status_code,
                'headers': dict(response.headers),
                'body': response.get_data(as_text=True)
            }
    
    return {
        'statusCode': 400,
        'body': json.dumps({'error': 'Invalid request'})
    }
```

### Step 2: Create SAM Template

Create `template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Bharat Scheme Mitra - Enhanced

Globals:
  Function:
    Timeout: 30
    MemorySize: 1024
    Runtime: python3.11
    Environment:
      Variables:
        BEDROCK_REGION: us-east-1
        S3_BUCKET: !Ref DocumentsBucket
        SESSIONS_TABLE: !Ref SessionsTable
        USERS_TABLE: !Ref UsersTable

Resources:
  # API Gateway
  ApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Cors:
        AllowMethods: "'*'"
        AllowHeaders: "'*'"
        AllowOrigin: "'*'"

  # Lambda Function
  BharatSchemeMitraFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: backend/
      Handler: lambda_handler.lambda_handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /{proxy+}
            Method: ANY
      Policies:
        - AmazonBedrockFullAccess
        - AmazonDynamoDBFullAccess
        - AmazonS3FullAccess
        - AmazonTranscribeFullAccess
        - AmazonPollyFullAccess
        - AmazonTextractFullAccess
        - ComprehendFullAccess

  # DynamoDB Tables
  SessionsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: welfare-sessions
      AttributeDefinitions:
        - AttributeName: sessionId
          AttributeType: S
      KeySchema:
        - AttributeName: sessionId
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true

  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: welfare-users
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
      KeySchema:
        - AttributeName: userId
          KeyType: HASH
      BillingMode: PAY_PER_REQUEST

  # S3 Bucket for Documents
  DocumentsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'bsm-documents-${AWS::AccountId}'
      CorsConfiguration:
        CorsRules:
          - AllowedOrigins: ['*']
            AllowedMethods: [GET, PUT, POST]
            AllowedHeaders: ['*']

Outputs:
  ApiUrl:
    Description: API Gateway endpoint URL
    Value: !Sub 'https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com/prod/'
```

### Step 3: Deploy with SAM

```bash
# Install SAM CLI
pip install aws-sam-cli

# Build
sam build

# Deploy
sam deploy --guided

# Follow prompts:
# Stack Name: bharat-scheme-mitra
# AWS Region: us-east-1
# Confirm changes: Y
# Allow SAM CLI IAM role creation: Y
# Save arguments to config: Y
```

### Step 4: Deploy Frontend to S3 + CloudFront

```bash
# Build frontend
cd frontend
npm run build

# Create S3 bucket
aws s3 mb s3://bsm-frontend-${ACCOUNT_ID}

# Enable static website hosting
aws s3 website s3://bsm-frontend-${ACCOUNT_ID} \
  --index-document index.html \
  --error-document index.html

# Upload build
aws s3 sync build/ s3://bsm-frontend-${ACCOUNT_ID}/

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name bsm-frontend-${ACCOUNT_ID}.s3.amazonaws.com \
  --default-root-object index.html
```

---

## 🐳 Option 2: Container Deployment (ECS Fargate)

### Step 1: Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .
COPY data/ ../data/

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app_enhanced:app"]
```

### Step 2: Build and Push to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name bharat-scheme-mitra

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t bharat-scheme-mitra .

# Tag image
docker tag bharat-scheme-mitra:latest \
  ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/bharat-scheme-mitra:latest

# Push image
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/bharat-scheme-mitra:latest
```

### Step 3: Create ECS Cluster and Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name bsm-cluster

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster bsm-cluster \
  --service-name bsm-service \
  --task-definition bsm-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

Create `task-definition.json`:

```json
{
  "family": "bsm-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "bsm-container",
      "image": "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/bharat-scheme-mitra:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "BEDROCK_REGION", "value": "us-east-1"},
        {"name": "S3_BUCKET", "value": "bsm-documents"},
        {"name": "SESSIONS_TABLE", "value": "welfare-sessions"},
        {"name": "USERS_TABLE", "value": "welfare-users"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/bsm",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## 🔒 Security Configuration

### 1. Enable HTTPS

```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name api.bharatschememitr.in \
  --validation-method DNS

# Add to API Gateway or CloudFront
```

### 2. Configure WAF

```bash
# Create WAF Web ACL
aws wafv2 create-web-acl \
  --name bsm-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules file://waf-rules.json
```

### 3. Enable CloudWatch Logs

```bash
# Create log group
aws logs create-log-group --log-group-name /aws/lambda/bsm

# Set retention
aws logs put-retention-policy \
  --log-group-name /aws/lambda/bsm \
  --retention-in-days 30
```

### 4. Set up IAM Roles

```yaml
# Least privilege IAM policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "s3:GetObject",
        "s3:PutObject",
        "transcribe:StartTranscriptionJob",
        "transcribe:GetTranscriptionJob",
        "polly:SynthesizeSpeech",
        "textract:DetectDocumentText",
        "comprehend:DetectDominantLanguage",
        "comprehend:DetectSentiment"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📊 Monitoring & Alerts

### 1. CloudWatch Dashboards

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name BSM-Dashboard \
  --dashboard-body file://dashboard.json
```

### 2. Set up Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name bsm-high-errors \
  --alarm-description "Alert when error rate > 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold

# High latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name bsm-high-latency \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold
```

### 3. Enable X-Ray Tracing

```python
# Add to app_enhanced.py
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

xray_recorder.configure(service='BharatSchemeMitra')
XRayMiddleware(app, xray_recorder)
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy Backend
        run: |
          cd backend
          sam build
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
      
      - name: Deploy Frontend
        run: |
          cd frontend
          npm install
          npm run build
          aws s3 sync build/ s3://bsm-frontend-${ACCOUNT_ID}/
          aws cloudfront create-invalidation --distribution-id ${DIST_ID} --paths "/*"
```

---

## 💰 Cost Optimization

### Estimated Monthly Costs (1000 users/day)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 100K requests | $0.20 |
| API Gateway | 100K requests | $0.35 |
| DynamoDB | 1M reads, 100K writes | $1.25 |
| S3 | 10GB storage, 100K requests | $0.50 |
| Bedrock | 1M tokens | $3.00 |
| Transcribe | 100 hours | $2.40 |
| Polly | 1M characters | $4.00 |
| CloudFront | 10GB transfer | $0.85 |
| **Total** | | **~$12.55/month** |

### Cost Optimization Tips

1. **Use DynamoDB On-Demand** - Pay per request
2. **Enable S3 Lifecycle Policies** - Move old docs to Glacier
3. **Use CloudFront Caching** - Reduce origin requests
4. **Optimize Bedrock Prompts** - Reduce token usage
5. **Set DynamoDB TTL** - Auto-delete old sessions

---

## 🧪 Testing in Production

### Smoke Tests

```bash
# Health check
curl https://api.yourdomain.com/health

# Chat endpoint
curl -X POST https://api.yourdomain.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "language": "en"}'

# Voice endpoint
curl -X POST https://api.yourdomain.com/voice \
  -F "audio=@test.webm" \
  -F "language=hi"
```

### Load Testing

```bash
# Install artillery
npm install -g artillery

# Run load test
artillery quick --count 100 --num 10 https://api.yourdomain.com/health
```

---

## 📈 Scaling Configuration

### Auto-Scaling for Lambda

```yaml
# In template.yaml
AutoScalingTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MaxCapacity: 100
    MinCapacity: 2
    ResourceId: !Sub 'function:${BharatSchemeMitraFunction}:provisioned-concurrency'
    ScalableDimension: lambda:function:ProvisionedConcurrentExecutions
```

### Auto-Scaling for ECS

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/bsm-cluster/bsm-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10
```

---

## 🎉 Post-Deployment Checklist

- [ ] SSL certificate configured
- [ ] Custom domain set up
- [ ] WAF rules enabled
- [ ] CloudWatch alarms configured
- [ ] X-Ray tracing enabled
- [ ] Backup strategy in place
- [ ] CI/CD pipeline working
- [ ] Load testing completed
- [ ] Documentation updated
- [ ] Team trained on monitoring

---

## 📞 Support & Maintenance

### Daily Tasks
- Check CloudWatch dashboards
- Review error logs
- Monitor costs

### Weekly Tasks
- Review performance metrics
- Update dependencies
- Check security advisories

### Monthly Tasks
- Cost optimization review
- Capacity planning
- Disaster recovery drill

---

## 🚀 You're Live!

Your Bharat Scheme Mitra is now running in production on AWS!

**Next Steps:**
1. Monitor metrics in CloudWatch
2. Set up alerts for critical issues
3. Plan for scaling based on usage
4. Collect user feedback
5. Iterate and improve

Good luck! 🇮🇳
