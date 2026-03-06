# 🎬 Demo Video Script (7 Minutes)

## 📋 Preparation Checklist

### Before Recording
- [ ] Deploy to Render.com (live URL working)
- [ ] Test all features on live URL
- [ ] Close unnecessary browser tabs
- [ ] Clear browser notifications
- [ ] Set browser zoom to 100%
- [ ] Test microphone
- [ ] Open AWS Console in another tab
- [ ] Have this script visible
- [ ] Practice 2-3 times

---

## 🎤 Full Script (Read & Practice)

### [0:00 - 0:30] INTRODUCTION

**SAY:**
> "Hello! I'm presenting Bharat Scheme Mitra - an AI-powered welfare assistant that helps 500 million Indian citizens discover and apply for government schemes in their own language, using voice or text."

**SHOW:**
- Open live URL
- Show landing page with Indian flag colors
- Show language dropdown (15 languages)

---

### [0:30 - 1:15] PROBLEM & SOLUTION

**SAY:**
> "The problem we're solving: Over 500 million eligible Indian citizens never receive government benefits due to three main barriers - language barriers, complex eligibility criteria, and low digital literacy.
>
> Our solution uses 8 AWS GenAI services to create an intelligent, multilingual assistant. We use Amazon Bedrock for AI conversations, Transcribe for voice input, Polly for voice output, DynamoDB for data storage, and 4 more services."

**SHOW:**
- Slide or text showing problem statistics
- List of AWS services

---

### [1:15 - 2:15] MULTILINGUAL SUPPORT

**SAY:**
> "Let me demonstrate our multilingual capabilities. We support 15 Indian languages including Hindi, Tamil, Telugu, Bengali, and more. Watch as I switch to Hindi..."

**DO:**
1. Click language dropdown
2. Select "हिंदी (Hindi)"
3. Show interface changing to Hindi

**SAY:**
> "Now I'll type in Hindi: 'मैं किसान हूं' - which means 'I am a farmer'"

**DO:**
1. Type: "मैं किसान हूं"
2. Press send
3. Wait for response

**SAY:**
> "Notice how the bot responds in Hindi, asking relevant follow-up questions about my farming situation."

**SHOW:**
- Bot response in Hindi
- Smooth conversation flow

---

### [2:15 - 3:15] VOICE INPUT DEMO

**SAY:**
> "Many rural users have low literacy. That's why we support voice input in 10 Indian languages using Amazon Transcribe. Let me demonstrate..."

**DO:**
1. Click microphone icon
2. Speak clearly in Hindi: "मुझे खेती के लिए योजना चाहिए"
   (Translation: "I need schemes for farming")
3. Show transcription appearing

**SAY:**
> "The system transcribes my voice using Amazon Transcribe and processes it through our AI engine."

**SHOW:**
- Transcription appearing in real-time
- Bot responding with relevant schemes

---

### [3:15 - 4:30] AI RECOMMENDATIONS

**SAY:**
> "Our AI is intelligent. It builds a user profile and provides personalized recommendations. Watch this..."

**DO:**
1. Type: "I am a farmer from Maharashtra with 5 acres of land"
2. Press send
3. Wait for response

**SAY:**
> "Notice how the bot extracted three pieces of information: my occupation as a farmer, my location in Maharashtra, and my land size of 5 acres. This appears in the profile widget on the right."

**SHOW:**
- Profile widget appearing/updating
- Personalized scheme recommendations

**SAY:**
> "Now it shows me three schemes specifically relevant to my profile, with reasons why each scheme is perfect for me. For example, PM-KISAN is highlighted because it's designed for farmers with small landholdings like mine."

**SHOW:**
- Scheme cards with "Why for you" reasons
- Hover over scheme cards

---

### [4:30 - 5:30] APPLICATION GUIDANCE

**SAY:**
> "Users often struggle with the application process. We provide step-by-step guidance. Let me ask..."

**DO:**
1. Type: "How to apply for PM-KISAN?"
2. Press send
3. Wait for response

**SAY:**
> "The bot provides an interactive step-by-step guide. Each step includes the action needed, helpful tips, and warnings about common mistakes. It even estimates the time required - 15 to 30 minutes in this case."

**SHOW:**
- Step-by-step application guide
- Tips and warnings for each step
- Time estimate

**SAY:**
> "Users can also click this speaker icon to hear the steps in their language using Amazon Polly's neural voices."

**DO:**
- Click speaker icon
- Let TTS play for 3-5 seconds
- Click again to stop

---

### [5:30 - 6:15] AWS INFRASTRUCTURE

**SAY:**
> "Let me show you our AWS infrastructure. This is a production-grade solution using 8 AWS services."

**DO:**
1. Switch to AWS Console tab
2. Navigate to DynamoDB

**SAY:**
> "Here's Amazon DynamoDB storing user sessions and profiles in real-time."

**SHOW:**
- DynamoDB tables (user-sessions, user-profiles)
- Recent items

**DO:**
- Navigate to S3

**SAY:**
> "Here's Amazon S3 storing uploaded documents and voice recordings."

**SHOW:**
- S3 bucket with files

**DO:**
- Navigate to CloudWatch

**SAY:**
> "And here's Amazon CloudWatch showing real-time logs and monitoring."

**SHOW:**
- CloudWatch logs
- Recent log entries

**SAY:**
> "We also use Amazon Bedrock for AI, Transcribe for speech-to-text, Polly for text-to-speech, Textract for document OCR, and Comprehend for language detection."

---

### [6:15 - 6:45] COST & SCALABILITY

**SAY:**
> "Now, let's talk about cost and scalability. Our solution costs only 14 dollars per month for 1000 daily users. That's extremely cost-effective for the value provided.
>
> Because we're built on AWS serverless architecture using Lambda and DynamoDB, we can automatically scale to millions of users without any infrastructure management. This means we can truly serve 500 million Indians."

**SHOW:**
- Cost breakdown slide or table
- Architecture diagram

---

### [6:45 - 7:00] CLOSING

**SAY:**
> "To summarize: Bharat Scheme Mitra is production-ready, uses 8 AWS GenAI services, supports 15 Indian languages, costs only 14 dollars per month, and can scale to millions of users. It's ready to help 500 million Indians access their rightful benefits. Thank you!"

**SHOW:**
- Final slide with:
  - GitHub repository link
  - Live demo URL
  - Contact information
  - "Built with ❤️ for 500M+ Indians"

---

## 🎯 Key Points to Emphasize

1. **Problem Scale**: 500 million citizens affected
2. **AWS Services**: 8+ production-grade services
3. **Multilingual**: 15 Indian languages
4. **Voice Support**: For low-literacy users
5. **AI Intelligence**: Personalized recommendations
6. **Cost-Effective**: $14/month for 1000 users
7. **Scalable**: Serverless architecture
8. **Production-Ready**: Real AWS infrastructure

---

## 💡 Delivery Tips

### Voice & Pace
- Speak clearly and confidently
- Don't rush - pause between sections
- Vary your tone to maintain interest
- Smile while speaking (it shows in your voice)

### Screen Actions
- Move mouse slowly and deliberately
- Don't click too fast
- Let responses fully load before continuing
- Highlight important elements

### Technical Issues
- If something doesn't work, stay calm
- Have a backup plan (localhost)
- Practice beforehand to avoid issues

---

## 🎬 Recording Settings

### OBS Studio
- Resolution: 1920x1080
- FPS: 30
- Format: MP4
- Bitrate: 2500 kbps

### Loom
- Quality: High (1080p)
- Camera: Optional (bottom right)
- Microphone: On

---

## 📤 After Recording

### Edit (Optional)
- Trim beginning/end
- Remove long pauses
- Add title slide (first 3 seconds)
- Add background music (low volume)

### Export
- Format: MP4
- Resolution: 1080p
- Quality: High

### Upload
- Platform: YouTube
- Privacy: Unlisted (for hackathon)
- Title: "Bharat Scheme Mitra - AI Welfare Assistant | AWS GenAI Hackathon"
- Description: Include GitHub link and live demo URL

---

## ✅ Final Checklist

- [ ] Practiced script 2-3 times
- [ ] All features tested on live URL
- [ ] Recording software ready
- [ ] Microphone tested
- [ ] Browser prepared (tabs closed, zoom 100%)
- [ ] AWS Console ready in another tab
- [ ] Confident and ready to record

---

## 🎉 You're Ready!

**Remember:**
- Be confident
- Speak clearly
- Show, don't just tell
- Highlight AWS services
- Emphasize impact (500M users)
- Keep it under 7 minutes

**Good luck! You've got this! 🏆🇮🇳**
