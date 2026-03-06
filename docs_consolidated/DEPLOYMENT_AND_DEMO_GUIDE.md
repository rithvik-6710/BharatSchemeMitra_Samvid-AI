# 🚀 Deployment & Demo Video Guide

## Quick Deployment Options

### Option 1: Render.com (Easiest - FREE) ⭐ RECOMMENDED
### Option 2: Heroku (Easy - FREE tier available)
### Option 3: AWS (Production - Costs ~$14/month)
### Option 4: Vercel + Railway (Modern - FREE tier)

---

## 🎯 Option 1: Render.com (RECOMMENDED FOR HACKATHON)

**Why Render?**
- ✅ Completely FREE for hackathons
- ✅ Easy deployment (5 minutes)
- ✅ Automatic HTTPS
- ✅ No credit card required
- ✅ Live URL immediately

### Step 1: Prepare Your Code

Create `render.yaml` in root:

```yaml
services:
  # Backend
  - type: web
    name: bharat-scheme-backend
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && gunicorn app:app"
    envVars:
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_DEFAULT_REGION
        value: ap-south-1
      - key: S3_BUCKET
        value: welfare-docs-843374720127-2026
      - key: SESSIONS_TABLE
        value: user-sessions
      - key: USERS_TABLE
        value: user-profiles
      - key: SCHEMES_CACHE_TABLE
        value: schemeuser

  # Frontend
  - type: web
    name: bharat-scheme-frontend
    env: static
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: frontend/build
    envVars:
      - key: REACT_APP_API_URL
        fromService:
          type: web
          name: bharat-scheme-backend
          envVarKey: RENDER_EXTERNAL_URL
```

### Step 2: Add gunicorn to requirements.txt

```bash
cd backend
echo "gunicorn==21.2.0" >> requirements.txt
```

### Step 3: Deploy to Render

1. **Go to**: https://render.com
2. **Sign up** with GitHub
3. **Click**: "New" → "Blueprint"
4. **Connect** your GitHub repository
5. **Render will auto-detect** `render.yaml`
6. **Add environment variables**:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
7. **Click**: "Apply"

**Done!** You'll get URLs like:
- Backend: `https://bharat-scheme-backend.onrender.com`
- Frontend: `https://bharat-scheme-frontend.onrender.com`

---

## 🎯 Option 2: Heroku (Alternative)

### Step 1: Install Heroku CLI

```bash
# Windows
winget install Heroku.HerokuCLI

# Mac
brew tap heroku/brew && brew install heroku

# Login
heroku login
```

### Step 2: Create Procfile for Backend

Create `backend/Procfile`:
```
web: gunicorn app:app
```

### Step 3: Deploy Backend

```bash
cd backend

# Create Heroku app
heroku create bharat-scheme-backend

# Set environment variables
heroku config:set AWS_ACCESS_KEY_ID=your_key
heroku config:set AWS_SECRET_ACCESS_KEY=your_secret
heroku config:set AWS_DEFAULT_REGION=ap-south-1
heroku config:set S3_BUCKET=welfare-docs-843374720127-2026

# Deploy
git init
git add .
git commit -m "Deploy backend"
heroku git:remote -a bharat-scheme-backend
git push heroku main
```

### Step 4: Deploy Frontend to Vercel

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts, set environment variable:
# REACT_APP_API_URL=https://bharat-scheme-backend.herokuapp.com
```

**Done!** You'll get:
- Backend: `https://bharat-scheme-backend.herokuapp.com`
- Frontend: `https://your-app.vercel.app`

---

## 🎯 Option 3: AWS (Production Deployment)

### Quick AWS Deployment

```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Configure AWS
aws configure

# Deploy backend
cd backend
sam init
sam build
sam deploy --guided

# Deploy frontend to S3
cd frontend
npm run build
aws s3 mb s3://bharat-scheme-frontend
aws s3 sync build/ s3://bharat-scheme-frontend/
aws s3 website s3://bharat-scheme-frontend/ --index-document index.html
```

**URLs**:
- Backend: API Gateway URL (from SAM output)
- Frontend: `http://bharat-scheme-frontend.s3-website-ap-south-1.amazonaws.com`

---

## 🎯 Option 4: Railway (Modern & Fast)

### Step 1: Deploy Backend

1. Go to: https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variables
6. Railway auto-detects Python and deploys

### Step 2: Deploy Frontend to Netlify

```bash
cd frontend

# Install Netlify CLI
npm install -g netlify-cli

# Build
npm run build

# Deploy
netlify deploy --prod --dir=build
```

---

## 🎥 Demo Video Guide

### What to Show (5-7 minutes)

#### 1. Introduction (30 seconds)
```
Script:
"Hi! I'm presenting Bharat Scheme Mitra - an AI-powered assistant 
that helps 500 million Indians discover government welfare schemes 
in their own language, using voice or text."
```

**Show**: Landing page with Indian flag colors

---

#### 2. Problem Statement (45 seconds)
```
Script:
"Over 500 million Indian citizens are eligible for government schemes 
but never receive them due to language barriers, complex eligibility 
criteria, and low digital literacy. Our solution uses AWS GenAI services 
to solve this problem."
```

**Show**: Slide with statistics

---

#### 3. Multilingual Support (1 minute)
```
Script:
"We support 15 Indian languages. Let me switch to Hindi..."
```

**Show**:
1. Language dropdown
2. Select Hindi
3. Interface changes to Hindi
4. Type: "मैं किसान हूं" (I am a farmer)
5. Bot responds in Hindi

---

#### 4. Voice Input (1 minute)
```
Script:
"Users can speak in their language. Let me demonstrate..."
```

**Show**:
1. Click microphone icon
2. Speak in Hindi: "मुझे खेती के लिए योजना चाहिए"
3. Show transcription appearing
4. Bot responds with schemes

---

#### 5. AI Recommendations (1.5 minutes)
```
Script:
"Our AI understands context and provides personalized recommendations. 
Watch how it remembers my profile..."
```

**Show**:
1. Type: "I am a farmer from Maharashtra with 5 acres"
2. Bot extracts profile (show profile widget)
3. Bot shows 3 personalized schemes with "Why for you" reasons
4. Click on PM-KISAN scheme card

---

#### 6. Application Guidance (1 minute)
```
Script:
"Users get step-by-step guidance for applying to schemes..."
```

**Show**:
1. Ask: "How to apply for PM-KISAN?"
2. Bot shows interactive step-by-step guide
3. Each step has tips and warnings
4. Click speaker icon to hear steps in Hindi

---

#### 7. AWS Services (1 minute)
```
Script:
"We use 8+ AWS services for a production-grade solution..."
```

**Show**:
1. Open AWS Console
2. Show DynamoDB tables with data
3. Show S3 bucket with files
4. Show CloudWatch logs
5. Mention: Bedrock, Transcribe, Polly, Comprehend, etc.

---

#### 8. Cost & Scalability (30 seconds)
```
Script:
"Our solution costs only $14 per month for 1000 daily users 
and can scale to millions of users using AWS serverless architecture."
```

**Show**: Cost breakdown slide

---

#### 9. Closing (30 seconds)
```
Script:
"Bharat Scheme Mitra is production-ready, cost-effective, 
and can help 500 million Indians access their rightful benefits. 
Thank you!"
```

**Show**: Final slide with GitHub link and contact

---

## 🎬 Recording Tools

### Option 1: OBS Studio (FREE - Best Quality)
1. Download: https://obsproject.com/
2. Settings:
   - Resolution: 1920x1080
   - FPS: 30
   - Format: MP4
3. Add sources:
   - Display Capture (for screen)
   - Audio Input (for voice)
4. Record and edit

### Option 2: Loom (FREE - Easiest)
1. Install: https://www.loom.com/
2. Click "Record"
3. Select "Screen + Camera"
4. Record demo
5. Auto-uploads and gives shareable link

### Option 3: Windows Game Bar (Built-in)
1. Press `Win + G`
2. Click record button
3. Record demo
4. Saves to Videos/Captures folder

---

## 📝 Demo Script Template

### Full Script (Copy & Practice)

```
[0:00 - 0:30] INTRODUCTION
"Hello! I'm presenting Bharat Scheme Mitra - an AI-powered welfare 
assistant built on AWS. It helps 500 million Indians discover and 
apply for government schemes in their own language."

[0:30 - 1:15] PROBLEM & SOLUTION
"The problem: Over 500 million eligible citizens never receive benefits 
due to language barriers, complex processes, and low digital literacy.

Our solution: We use AWS GenAI services - Bedrock for AI conversations, 
Transcribe for voice input, Polly for voice output, and 6 more services 
to create an intelligent, multilingual assistant."

[1:15 - 2:15] MULTILINGUAL DEMO
"Let me show you. We support 15 Indian languages. I'll switch to Hindi...
[Switch language]
Now I'll type: 'मैं किसान हूं' - meaning 'I am a farmer'
[Type and show response]
The bot responds in Hindi with relevant schemes."

[2:15 - 3:15] VOICE INPUT DEMO
"Users can also speak in their language. Let me demonstrate...
[Click microphone]
[Speak in Hindi]: 'मुझे खेती के लिए योजना चाहिए'
[Show transcription]
The bot transcribes using Amazon Transcribe and responds with schemes."

[3:15 - 4:30] AI RECOMMENDATIONS
"Our AI is smart. Watch how it builds a user profile...
[Type]: 'I am a farmer from Maharashtra with 5 acres'
[Show profile widget appearing]
The bot extracted my occupation, location, and land size. Now it shows 
personalized schemes with reasons why each scheme is perfect for me."

[4:30 - 5:30] APPLICATION GUIDANCE
"Users get step-by-step guidance. Let me ask...
[Type]: 'How to apply for PM-KISAN?'
[Show step-by-step guide]
Each step has tips and warnings. Users can click the speaker icon to 
hear the steps in their language."

[5:30 - 6:15] AWS SERVICES
"Let me show you our AWS infrastructure...
[Open AWS Console]
Here's DynamoDB storing user sessions and profiles...
Here's S3 with uploaded documents...
Here's CloudWatch showing real-time logs...
We use 8+ AWS services for a production-grade solution."

[6:15 - 6:45] COST & IMPACT
"Our solution costs only $14 per month for 1000 daily users. 
It's built on AWS serverless architecture, so it can scale to 
millions of users automatically. This can help 500 million Indians 
access their rightful benefits."

[6:45 - 7:00] CLOSING
"Bharat Scheme Mitra is production-ready, cost-effective, and 
can make a real impact. Thank you!"
```

---

## 🎨 Demo Video Checklist

### Before Recording
- [ ] Deploy to live URL (Render/Heroku)
- [ ] Test all features work on live URL
- [ ] Prepare demo data (test messages)
- [ ] Open AWS Console in another tab
- [ ] Close unnecessary browser tabs
- [ ] Clear browser notifications
- [ ] Set browser zoom to 100%
- [ ] Test microphone and audio
- [ ] Practice script 2-3 times

### During Recording
- [ ] Speak clearly and confidently
- [ ] Show features slowly (don't rush)
- [ ] Highlight key innovations
- [ ] Show AWS Console
- [ ] Mention cost-effectiveness
- [ ] Show real-time responses

### After Recording
- [ ] Trim beginning/end
- [ ] Add title slide (optional)
- [ ] Add background music (optional)
- [ ] Export as MP4 (1080p)
- [ ] Upload to YouTube (unlisted)
- [ ] Add to README.md

---

## 📤 Submission Checklist

### For Hackathon
- [ ] Live URL deployed and working
- [ ] Demo video recorded (5-7 minutes)
- [ ] Demo video uploaded to YouTube
- [ ] GitHub repository cleaned up
- [ ] README.md updated with live URL
- [ ] README.md updated with demo video link
- [ ] All documentation in docs_consolidated/
- [ ] AWS services verified and working
- [ ] Test from different device/browser

### README.md Updates

Add these sections to your README.md:

```markdown
## 🌐 Live Demo

**Live Application**: https://bharat-scheme-frontend.onrender.com
**Backend API**: https://bharat-scheme-backend.onrender.com

## 🎥 Demo Video

Watch our 7-minute demo: [YouTube Link](https://youtu.be/your-video-id)

### Quick Demo
1. Switch to Hindi language
2. Type: "मैं किसान हूं" (I am a farmer)
3. See personalized scheme recommendations
4. Click microphone to try voice input
5. Ask: "How to apply for PM-KISAN?"
6. Get step-by-step guidance
```

---

## 🚀 Quick Deployment Commands

### Render (Recommended)
```bash
# 1. Add gunicorn
cd backend
echo "gunicorn==21.2.0" >> requirements.txt

# 2. Commit changes
git add .
git commit -m "Add Render deployment config"
git push

# 3. Go to render.com and deploy
```

### Heroku
```bash
# Backend
cd backend
heroku create bharat-scheme-backend
git push heroku main

# Frontend
cd frontend
vercel
```

### Test Your Deployment
```bash
# Test backend
curl https://your-backend-url.com/health

# Test chat
curl -X POST https://your-backend-url.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am a farmer", "language": "en"}'
```

---

## 💡 Pro Tips

### For Demo Video
1. **Keep it under 7 minutes** - judges have limited time
2. **Show, don't tell** - demonstrate features live
3. **Highlight AWS services** - show AWS Console
4. **Mention cost** - $14/month is impressive
5. **Show real use case** - farmer scenario is relatable
6. **Good audio quality** - use a decent microphone
7. **Practice 2-3 times** - smooth delivery matters

### For Deployment
1. **Test thoroughly** - try all features on live URL
2. **Use free tiers** - Render/Heroku for hackathons
3. **Keep it simple** - don't over-engineer
4. **Monitor logs** - check for errors after deployment
5. **Have backup** - keep localhost working too

---

## 🆘 Troubleshooting

### Deployment Issues

**Issue**: Backend won't start
```bash
# Check logs
heroku logs --tail
# or
render logs (in dashboard)

# Common fix: Add gunicorn
pip install gunicorn
```

**Issue**: Frontend can't connect to backend
```bash
# Update frontend .env
REACT_APP_API_URL=https://your-backend-url.com

# Rebuild
npm run build
```

**Issue**: AWS credentials not working
```bash
# Verify credentials
aws sts get-caller-identity

# Re-add to deployment platform
```

---

## 🎉 You're Ready!

Follow this guide to:
1. ✅ Deploy to live URL (30 minutes)
2. ✅ Record demo video (1 hour)
3. ✅ Submit to hackathon (5 minutes)

**Good luck! You've got this! 🏆🇮🇳**
