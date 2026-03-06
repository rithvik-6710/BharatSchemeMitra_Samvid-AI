# ⚡ Quick Deploy Guide (5 Minutes)

## 🚀 Deploy to Render.com (FREE)

### Step 1: Push to GitHub (if not already)
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy on Render
1. Go to: **https://render.com**
2. Click **"Sign Up"** (use GitHub)
3. Click **"New"** → **"Blueprint"**
4. Connect your GitHub repository
5. Render will detect `render.yaml` automatically
6. Add these environment variables:
   - `AWS_ACCESS_KEY_ID`: (your AWS key)
   - `AWS_SECRET_ACCESS_KEY`: (your AWS secret)
7. Click **"Apply"**

### Step 3: Wait (3-5 minutes)
Render will:
- ✅ Build backend
- ✅ Build frontend
- ✅ Deploy both services
- ✅ Give you live URLs

### Step 4: Get Your URLs
You'll get:
- **Backend**: `https://bharat-scheme-backend.onrender.com`
- **Frontend**: `https://bharat-scheme-frontend.onrender.com`

### Step 5: Test
Open frontend URL and test:
- ✅ Language switching
- ✅ Text chat
- ✅ Voice input
- ✅ Scheme recommendations

---

## 🎥 Record Demo Video (30 Minutes)

### Option 1: Loom (Easiest)
1. Install: https://www.loom.com/
2. Click "Start Recording"
3. Select "Screen + Camera"
4. Follow demo script (see DEPLOYMENT_AND_DEMO_GUIDE.md)
5. Stop recording
6. Get shareable link

### Option 2: OBS Studio (Best Quality)
1. Download: https://obsproject.com/
2. Add "Display Capture" source
3. Add "Audio Input" source
4. Click "Start Recording"
5. Follow demo script
6. Click "Stop Recording"
7. Upload to YouTube

---

## 📝 Demo Script (7 Minutes)

### 1. Introduction (30s)
"Hi! This is Bharat Scheme Mitra - helping 500M Indians access welfare schemes using AWS GenAI."

### 2. Show Features (5 minutes)
- Switch to Hindi language
- Type: "मैं किसान हूं"
- Show voice input
- Show personalized recommendations
- Show application guidance
- Click speaker icon for TTS

### 3. Show AWS Console (1 minute)
- Open DynamoDB tables
- Show S3 bucket
- Show CloudWatch logs
- Mention 8+ AWS services

### 4. Closing (30s)
"Production-ready, costs $14/month, can scale to millions. Thank you!"

---

## ✅ Final Checklist

- [ ] Code pushed to GitHub
- [ ] Deployed to Render.com
- [ ] Both URLs working
- [ ] Tested all features on live URL
- [ ] Demo video recorded
- [ ] Demo video uploaded to YouTube
- [ ] README.md updated with live URLs
- [ ] README.md updated with video link

---

## 🔗 Update README.md

Add this section to your README.md:

```markdown
## 🌐 Live Demo

**🚀 Try it now**: https://bharat-scheme-frontend.onrender.com

**Backend API**: https://bharat-scheme-backend.onrender.com

## 🎥 Demo Video

**Watch our demo**: [YouTube Link](https://youtu.be/your-video-id)

### Quick Test
1. Open the live URL
2. Switch to Hindi language
3. Type: "मैं किसान हूं" (I am a farmer)
4. See AI recommendations
5. Try voice input (click microphone)
```

---

## 💡 Pro Tips

1. **First deployment takes 5-10 minutes** - be patient
2. **Free tier sleeps after 15 min inactivity** - first request may be slow
3. **Test before recording demo** - ensure everything works
4. **Practice demo script 2-3 times** - smooth delivery
5. **Keep demo under 7 minutes** - judges have limited time

---

## 🆘 Need Help?

See detailed guide: `docs_consolidated/DEPLOYMENT_AND_DEMO_GUIDE.md`

---

**You're ready to deploy and demo! 🎉**
