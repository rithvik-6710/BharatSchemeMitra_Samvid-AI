#!/bin/bash
# =============================================================
# setup_indictrans2_ec2.sh
# One-command setup for IndicTrans2 on AWS EC2
#
# Recommended instance: g4dn.xlarge (GPU, ~$0.50/hr) for fast inference
# Budget option:        t3.large (CPU only, slower but cheaper)
#
# HOW TO USE:
# 1. Launch EC2 instance (Ubuntu 22.04, g4dn.xlarge)
# 2. Open port 5001 in Security Group (inbound, from your backend IP)
# 3. SSH into instance: ssh -i your-key.pem ubuntu@EC2_PUBLIC_IP
# 4. Run: chmod +x setup_indictrans2_ec2.sh && ./setup_indictrans2_ec2.sh
# =============================================================

set -e

echo ""
echo "🇮🇳 Setting up IndicTrans2 on EC2"
echo "   Model: ai4bharat/indictrans2-en-indic-1B"
echo "   Languages: 22 Indian languages"
echo ""

# ── System packages ───────────────────────────────────────────
echo "📦 Installing system packages..."
sudo apt-get update -q
sudo apt-get install -y python3.11 python3.11-venv python3-pip git curl

# ── GPU check ─────────────────────────────────────────────────
if nvidia-smi &>/dev/null; then
    echo "  ✅ GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
    HAS_GPU=true
else
    echo "  ℹ️  No GPU detected — will run on CPU (slower, but works)"
    HAS_GPU=false
fi

# ── Project setup ─────────────────────────────────────────────
echo ""
echo "📂 Setting up project..."
mkdir -p ~/indictrans2_server
cd ~/indictrans2_server

# Copy server files (assuming already uploaded via scp)
# scp -i your-key.pem -r indictrans2_server/ ubuntu@EC2_IP:~/

# ── Python virtual environment ────────────────────────────────
echo ""
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip -q

# Install PyTorch (GPU or CPU)
if [ "$HAS_GPU" = true ]; then
    echo "  Installing PyTorch with CUDA support..."
    pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cu118 -q
else
    echo "  Installing PyTorch (CPU)..."
    pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu -q
fi

pip install -r requirements.txt -q
echo "  ✅ Dependencies installed"

# ── Download IndicTrans2 model ────────────────────────────────
echo ""
echo "🧠 Downloading IndicTrans2 model (~2GB, this takes 5-10 mins)..."
python3 -c "
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
print('  Downloading tokenizer...')
tokenizer = AutoTokenizer.from_pretrained('ai4bharat/indictrans2-en-indic-1B', trust_remote_code=True)
print('  Downloading model weights...')
model = AutoModelForSeq2SeqLM.from_pretrained('ai4bharat/indictrans2-en-indic-1B', trust_remote_code=True)
print('  ✅ Model downloaded and cached')
"
echo "  ✅ IndicTrans2 model ready"

# ── Set up systemd service ────────────────────────────────────
echo ""
echo "⚙️  Setting up auto-start service..."
sudo cp indictrans2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable indictrans2
sudo systemctl start indictrans2
sleep 3

# ── Test the server ───────────────────────────────────────────
echo ""
echo "🧪 Testing translation server..."
sleep 5  # Wait for model to fully load

TEST_RESPONSE=$(curl -s -X POST http://localhost:5001/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "You are eligible for PM-KISAN scheme", "source": "en", "target": "hi"}' 2>/dev/null)

if echo "$TEST_RESPONSE" | grep -q "translated"; then
    echo "  ✅ Translation test passed!"
    echo "  Response: $TEST_RESPONSE"
else
    echo "  ⚠️  Server may still be loading the model. Wait 30s and retry:"
    echo "     curl -X POST http://localhost:5001/translate -H 'Content-Type: application/json' -d '{\"text\":\"Hello\",\"source\":\"en\",\"target\":\"hi\"}'"
fi

# ── Print connection info ──────────────────────────────────────
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_EC2_IP")

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ IndicTrans2 Server is LIVE!"
echo ""
echo "  Public IP:    $PUBLIC_IP"
echo "  API URL:      http://$PUBLIC_IP:5001"
echo "  Health check: http://$PUBLIC_IP:5001/health"
echo ""
echo "  Now update backend/.env:"
echo "  INDICTRANS2_URL=http://$PUBLIC_IP:5001"
echo ""
echo "  IMPORTANT: Open port 5001 in your EC2 Security Group"
echo "  (Allow inbound TCP 5001 from your backend server IP)"
echo "═══════════════════════════════════════════════════════"
