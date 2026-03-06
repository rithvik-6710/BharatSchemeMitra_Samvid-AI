import { useState, useRef, useEffect } from "react";
import axios from "axios";
import DocUpload from "./components/DocUpload";
import VoiceRecorder from "./components/VoiceRecorder";
import "./App.css";
import SchemeCards from "./components/SchemeCards";

const API = process.env.REACT_APP_API_URL || "http://localhost:5000";

const LANGS = [
  { code: "hi", label: "हिंदी", name: "Hindi" },
  { code: "en", label: "English", name: "English" },
  { code: "ta", label: "தமிழ்", name: "Tamil" },
  { code: "te", label: "తెలుగు", name: "Telugu" },
  { code: "bn", label: "বাংলা", name: "Bengali" },
  { code: "mr", label: "मराठी", name: "Marathi" },
  { code: "gu", label: "ગુજરાતી", name: "Gujarati" },
  { code: "kn", label: "ಕನ್ನಡ", name: "Kannada" },
  { code: "ml", label: "മലയാളം", name: "Malayalam" },
  { code: "pa", label: "ਪੰਜਾਬੀ", name: "Punjabi" },
  { code: "or", label: "ଓଡ଼ିଆ", name: "Odia" },
  { code: "as", label: "অসমীয়া", name: "Assamese" },
  { code: "ur", label: "اردو", name: "Urdu" },
];

const WELCOME = {
  hi: "नमस्ते! मैं भारत स्कीम मित्र हूं 🙏\nआप किस सरकारी योजना के बारे में जानना चाहते हैं?",
  en: "Hello! I am Bharat Scheme Mitra 🙏\nWhich government welfare scheme can I help you with today?",
  ta: "வணக்கம்! நான் பாரத் திட்ட மித்ரா 🙏\nநீங்கள் எந்த அரசு திட்டத்தைப் பற்றி அறிய விரும்புகிறீர்கள்?",
  te: "నమస్కారం! నేను భారత్ స్కీమ్ మిత్రా 🙏\nమీరు ఏ ప్రభుత్వ పథకం గురించి తెలుసుకోవాలనుకుంటున్నారు?",
  bn: "নমস্কার! আমি ভারত স্কিম মিত্র 🙏\nআপনি কোন সরকারি প্রকল্প সম্পর্কে জানতে চান?",
  mr: "नमस्कार! मी भारत स्कीम मित्र आहे 🙏\nआपण कोणत्या सरकारी योजनेबद्दल जाणून घेऊ इच्छिता?",
  gu: "નમસ્તે! હું ભારત સ્કીમ મિત્ર છું 🙏\nઆપ કઈ સરકારી યોજના વિશે જાણવા માંગો છો?",
  kn: "ನಮಸ್ಕಾರ! ನಾನು ಭಾರತ್ ಸ್ಕೀಮ್ ಮಿತ್ರ 🙏\nನೀವು ಯಾವ ಸರ್ಕಾರಿ ಯೋಜನೆಯ ಬಗ್ಗೆ ತಿಳಿಯಲು ಬಯಸುತ್ತೀರಿ?",
  ml: "നമസ്കാരം! ഞാൻ ഭാരത് സ്കീം മിത്ര ആണ് 🙏\nഏത് ഗവൺമെന്റ് പദ്ധതിയെക്കുറിച്ച് അറിയണം?",
  pa: "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਭਾਰਤ ਸਕੀਮ ਮਿੱਤਰ ਹਾਂ 🙏\nਤੁਸੀਂ ਕਿਹੜੀ ਸਰਕਾਰੀ ਯੋਜਨਾ ਬਾਰੇ ਜਾਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?",
};

const QUICK_PROMPTS = {
  hi: [
    "मैं किसान हूं", 
    "स्वास्थ्य योजना", 
    "महिला योजना", 
    "आवास योजना",
    "शिक्षा योजना",
    "पेंशन योजना",
    "व्यवसाय ऋण",
    "बीमा योजना"
  ],
  en: [
    "I am a farmer", 
    "Health schemes", 
    "Women schemes", 
    "Housing help",
    "Education schemes",
    "Pension schemes",
    "Business loans",
    "Insurance schemes"
  ],
  ta: [
    "நான் விவசாயி", 
    "சுகாதார திட்டம்", 
    "பெண்கள் திட்டம்", 
    "வீட்டு உதவி",
    "கல்வி திட்டம்",
    "ஓய்வூதிய திட்டம்",
    "வணிக கடன்",
    "காப்பீட்டு திட்டம்"
  ],
  te: [
    "నేను రైతు", 
    "ఆరోగ్య పథకాలు", 
    "మహిళా పథకాలు", 
    "గృహ సహాయం",
    "విద్యా పథకాలు",
    "పెన్షన్ పథకాలు",
    "వ్యాపార రుణాలు",
    "బీమా పథకాలు"
  ],
  bn: [
    "আমি কৃষক", 
    "স্বাস্থ্য প্রকল্প", 
    "মহিলা প্রকল্প", 
    "আবাসন সাহায্য",
    "শিক্ষা প্রকল্প",
    "পেনশন প্রকল্প",
    "ব্যবসায়িক ঋণ",
    "বীমা প্রকল্প"
  ],
  mr: [
    "मी शेतकरी आहे", 
    "आरोग्य योजना", 
    "महिला योजना", 
    "गृहनिर्माण मदत",
    "शिक्षण योजना",
    "निवृत्तीवेतन योजना",
    "व्यवसाय कर्ज",
    "विमा योजना"
  ],
  gu: [
    "હું ખેડૂત છું", 
    "આરોગ્ય યોજના", 
    "મહિલા યોજના", 
    "આવાસ સહાય",
    "શિક્ષણ યોજના",
    "પેન્શન યોજના",
    "વ્યવસાય લોન",
    "વીમા યોજના"
  ],
  kn: [
    "ನಾನು ರೈತ", 
    "ಆರೋಗ್ಯ ಯೋಜನೆಗಳು", 
    "ಮಹಿಳಾ ಯೋಜನೆಗಳು", 
    "ವಸತಿ ಸಹಾಯ",
    "ಶಿಕ್ಷಣ ಯೋಜನೆಗಳು",
    "ಪಿಂಚಣಿ ಯೋಜನೆಗಳು",
    "ವ್ಯಾಪಾರ ಸಾಲ",
    "ವಿಮಾ ಯೋಜನೆಗಳು"
  ],
  ml: [
    "ഞാൻ കർഷകൻ", 
    "ആരോഗ്യ പദ്ധതികൾ", 
    "വനിതാ പദ്ധതികൾ", 
    "ഭവന സഹായം",
    "വിദ്യാഭ്യാസ പദ്ധതികൾ",
    "പെൻഷൻ പദ്ധതികൾ",
    "ബിസിനസ് വായ്പ",
    "ഇൻഷുറൻസ് പദ്ധതികൾ"
  ],
  pa: [
    "ਮੈਂ ਕਿਸਾਨ ਹਾਂ", 
    "ਸਿਹਤ ਯੋਜਨਾਵਾਂ", 
    "ਔਰਤਾਂ ਦੀਆਂ ਯੋਜਨਾਵਾਂ", 
    "ਘਰ ਸਹਾਇਤਾ",
    "ਸਿੱਖਿਆ ਯੋਜਨਾਵਾਂ",
    "ਪੈਨਸ਼ਨ ਯੋਜਨਾਵਾਂ",
    "ਕਾਰੋਬਾਰ ਕਰਜ਼ਾ",
    "ਬੀਮਾ ਯੋਜਨਾਵਾਂ"
  ],
  or: [
    "ମୁଁ କୃଷକ", 
    "ସ୍ୱାସ୍ଥ୍ୟ ଯୋଜନା", 
    "ମହିଳା ଯୋଜନା", 
    "ଗୃହ ସହାୟତା",
    "ଶିକ୍ଷା ଯୋଜନା",
    "ପେନସନ ଯୋଜନା",
    "ବ୍ୟବସାୟ ଋଣ",
    "ବୀମା ଯୋଜନା"
  ],
  as: [
    "মই কৃষক", 
    "স্বাস্থ্য আঁচনি", 
    "মহিলা আঁচনি", 
    "গৃহ সাহায্য",
    "শিক্ষা আঁচনি",
    "পেঞ্চন আঁচনি",
    "ব্যৱসায় ঋণ",
    "বীমা আঁচনি"
  ],
  ur: [
    "میں کسان ہوں", 
    "صحت کی اسکیمیں", 
    "خواتین کی اسکیمیں", 
    "رہائش کی مدد",
    "تعلیم کی اسکیمیں",
    "پنشن کی اسکیمیں",
    "کاروباری قرض",
    "انشورنس اسکیمیں"
  ],
};

// Browser TTS language codes - Only languages with good browser support
const TTS_LANG_MAP = {
  hi: "hi-IN",  // Hindi - Good support
  en: "en-IN",  // English - Excellent support
  // Other languages have poor browser TTS support - disabled
};

// Languages with good TTS support (browser can pronounce correctly)
const TTS_SUPPORTED_LANGS = ["hi", "en"];

function getSessionId() {
  let id = sessionStorage.getItem("bsm_sess");
  if (!id) {
    id = "sess-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);
    sessionStorage.setItem("bsm_sess", id);
  }
  return id;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [lang, setLang] = useState("hi");
  const [loading, setLoading] = useState(false);
  const [showDocs, setShowDocs] = useState(false);
  const [sessionId, setSessionId] = useState(getSessionId);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // FIX 1 — Welcome message updates correctly when language changes
  useEffect(() => {
    const newId = "sess-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);
    sessionStorage.setItem("bsm_sess", newId);
    setSessionId(newId);
    setMessages([{
      id: Date.now(),
      role: "bot",
      text: WELCOME[lang] || WELCOME.en,
    }]);
    setShowDocs(false);
  }, [lang]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addMessage = (role, text) => {
    const newMessage = { id: Date.now() + Math.random(), role, text };
    console.log("➕ Adding message:", role, typeof text, text);
    
    // Prevent duplicate messages (check last message)
    setMessages((prev) => {
      // Check if last message is identical (within 1 second)
      if (prev.length > 0) {
        const lastMsg = prev[prev.length - 1];
        const isDuplicate = 
          lastMsg.role === role &&
          JSON.stringify(lastMsg.text) === JSON.stringify(text) &&
          (Date.now() - lastMsg.id) < 1000; // Within 1 second
        
        if (isDuplicate) {
          console.log("⚠️ Duplicate message detected, skipping");
          return prev; // Don't add duplicate
        }
      }
      
      return [...prev, newMessage];
    });
    
    return newMessage;
  };

  const sendMessage = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return; // Prevent if already loading
    
    addMessage("user", msg);
    setInput("");
    setLoading(true);
    
    try {
      const res = await axios.post(`${API}/chat`, 
        { message: msg, sessionId, language: lang },
        { timeout: 90000 } // Increased to 90 seconds for translation-heavy requests
      );
      console.log("✅ Backend response received:", res.data);
      console.log("📦 Reply type:", typeof res.data.reply, res.data.reply);
      
      // CRITICAL FIX: Check if reply has actual content
      if (res.data.reply) {
        // If reply is an object, check if it has schemes or text
        if (typeof res.data.reply === 'object') {
          const hasSchemes = res.data.reply.schemes && Array.isArray(res.data.reply.schemes) && res.data.reply.schemes.length > 0;
          const hasSteps = res.data.reply.steps && Array.isArray(res.data.reply.steps) && res.data.reply.steps.length > 0;
          const hasText = res.data.reply.text || res.data.reply.intro;
          
          console.log("🔍 Response validation:", { hasSchemes, hasSteps, hasText });
          
          // Only add if there's actual content
          if (hasSchemes || hasSteps || hasText) {
            addMessage("bot", res.data.reply);
          } else {
            console.warn("⚠️ Empty response object received:", res.data.reply);
            addMessage("bot", lang === "hi" 
              ? "⚠️ कोई योजना नहीं मिली। कृपया अधिक जानकारी दें।"
              : "⚠️ No schemes found. Please provide more details.");
          }
        } else {
          // String response
          addMessage("bot", res.data.reply);
        }
      } else {
        console.warn("⚠️ No reply in response:", res.data);
        addMessage("bot", lang === "hi" 
          ? "⚠️ कोई जवाब नहीं मिला। कृपया दोबारा कोशिश करें।"
          : "⚠️ No response received. Please try again.");
      }
    } catch (error) {
      console.error("Chat error:", error);
      let errorMsg = lang === "hi"
        ? "⚠️ कनेक्शन में समस्या है। कृपया दोबारा कोशिश करें।"
        : "⚠️ Connection error. Please try again.";
      
      // More specific error messages
      if (error.code === 'ECONNABORTED') {
        errorMsg = lang === "hi"
          ? "⚠️ समय समाप्त हो गया। कृपया छोटा सवाल पूछें।"
          : "⚠️ Request timed out. Please try a shorter question.";
      } else if (error.response?.data?.error) {
        errorMsg = `⚠️ ${error.response.data.error}`;
      }
      
      addMessage("bot", errorMsg);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleVoiceResult = ({ transcript, reply, fallback_notice }) => {
    stopTTS(); // Stop any playing TTS
    addMessage("user", `🎤 "${transcript}"`);
    addMessage("bot", reply);
    // Show fallback notice if present
    if (fallback_notice) {
      addMessage("bot", `ℹ️ ${fallback_notice}`);
    }
  };

  const handleVoiceError = (err) => {
    stopTTS(); // Stop any playing TTS
    addMessage("bot", `⚠️ ${err}`);
  };

  const handleVoiceStart = () => {
    stopTTS(); // Stop TTS when recording starts
  };

  // FIX 2 — Browser speech synthesis with toggle functionality
  const playTTS = (text) => {
    try {
      // Check if TTS is supported for this language
      if (!TTS_SUPPORTED_LANGS.includes(lang)) {
        console.log(`TTS not supported for ${lang} - browser cannot pronounce correctly`);
        return; // Silently skip TTS for unsupported languages
      }
      
      if (!window.speechSynthesis) return;
      
      // If already speaking, stop it (toggle functionality)
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        return;
      }
      
      // Handle different content types
      let speakText = "";
      
      if (typeof text === "string") {
        speakText = text;
      } else if (text && typeof text === "object") {
        // Handle application guidance with steps
        if (text.type === "application_guidance" && text.steps) {
          speakText = text.intro || "";
          speakText += ". Here are the steps. ";
          text.steps.forEach((step, idx) => {
            const stepNum = typeof step.step === 'number' ? step.step : (idx + 1);
            const title = typeof step.title === 'string' ? step.title : '';
            const desc = typeof step.description === 'string' ? step.description : '';
            speakText += `Step ${stepNum}. ${title}. ${desc}. `;
          });
          if (text.follow_up) {
            speakText += text.follow_up;
          }
        } 
        // Handle scheme cards
        else if (text.schemes && Array.isArray(text.schemes)) {
          speakText = text.intro || "";
          text.schemes.forEach((scheme, idx) => {
            speakText += ` Scheme ${idx + 1}. ${scheme.name}. `;
            if (scheme.benefit) speakText += `Benefit: ${scheme.benefit}. `;
          });
        }
        // Fallback for other objects
        else {
          speakText = text.intro || text.text || JSON.stringify(text);
        }
      }
      
      // Remove all emojis before speaking
      speakText = speakText.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F000}-\u{1F02F}\u{1F0A0}-\u{1F0FF}\u{1F100}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2300}-\u{23FF}\u{2B50}\u{2B55}\u{231A}\u{231B}\u{2328}\u{23CF}\u{23E9}-\u{23F3}\u{23F8}-\u{23FA}\u{24C2}\u{25AA}\u{25AB}\u{25B6}\u{25C0}\u{25FB}-\u{25FE}\u{2600}-\u{2604}\u{260E}\u{2611}\u{2614}\u{2615}\u{2618}\u{261D}\u{2620}\u{2622}\u{2623}\u{2626}\u{262A}\u{262E}\u{262F}\u{2638}-\u{263A}\u{2640}\u{2642}\u{2648}-\u{2653}\u{265F}\u{2660}\u{2663}\u{2665}\u{2666}\u{2668}\u{267B}\u{267E}\u{267F}\u{2692}-\u{2697}\u{2699}\u{269B}\u{269C}\u{26A0}\u{26A1}\u{26A7}\u{26AA}\u{26AB}\u{26B0}\u{26B1}\u{26BD}\u{26BE}\u{26C4}\u{26C5}\u{26C8}\u{26CE}\u{26CF}\u{26D1}\u{26D3}\u{26D4}\u{26E9}\u{26EA}\u{26F0}-\u{26F5}\u{26F7}-\u{26FA}\u{26FD}\u{2702}\u{2705}\u{2708}-\u{270D}\u{270F}\u{2712}\u{2714}\u{2716}\u{271D}\u{2721}\u{2728}\u{2733}\u{2734}\u{2744}\u{2747}\u{274C}\u{274E}\u{2753}-\u{2755}\u{2757}\u{2763}\u{2764}\u{2795}-\u{2797}\u{27A1}\u{27B0}\u{27BF}\u{2934}\u{2935}\u{2B05}-\u{2B07}\u{2B1B}\u{2B1C}\u{2B50}\u{2B55}\u{3030}\u{303D}\u{3297}\u{3299}]/gu, '').trim();
      
      if (!speakText) return;
      
      const utterance = new SpeechSynthesisUtterance(speakText);
      utterance.lang  = TTS_LANG_MAP[lang] || "hi-IN";
      utterance.rate  = 0.9;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.log("TTS error:", e);
    }
  };

  // Stop TTS when needed
  const stopTTS = () => {
    try {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    } catch (e) {
      console.log("Stop TTS error:", e);
    }
  };

  const handleDocExtracted = (data) => {
    const summary = Object.entries(data)
      .filter(([, v]) => v && typeof v === "string")
      .map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)
      .join(", ");
    sendMessage(
      lang === "hi"
        ? `मैंने अपना दस्तावेज़ अपलोड किया। जानकारी: ${summary}। इसके आधार पर मुझे कौन सी योजनाएं मिलेंगी?`
        : `I uploaded my document. Details: ${summary}. Which schemes am I eligible for?`
    );
    setShowDocs(false);
  };

  const quickPrompts = QUICK_PROMPTS[lang] || QUICK_PROMPTS.en;

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="logo">
          <img
            src="/logo.png"
            alt="BSM logo"
            className="logo-img"
            style={{ width: 42, height: 42, borderRadius: 14 }}
            onError={(e) => { e.target.style.display = "none"; }}
          />
          <div>
            <div className="logo-badge">
              <span className="badge-dot"></span>
              <span>Official Scheme Guidance • Prototype</span>
            </div>
            <div className="logo-name">
              BSM <span className="logo-en">Bharat Scheme Mitra</span>
            </div>
            <div className="logo-sub">
              AI Welfare Assistant 🇮🇳 • Multilingual • Voice-enabled
            </div>
          </div>
        </div>
        <div className="header-right">
          <select
            className="lang-select"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            aria-label="Select language"
          >
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label} · {l.name}
              </option>
            ))}
          </select>
          <button
            className={`doc-toggle ${showDocs ? "active" : ""}`}
            onClick={() => setShowDocs((s) => !s)}
            title="Upload document"
          >
            📄 Doc
          </button>
        </div>
      </header>

      {/* ── Document Upload Panel ── */}
      {showDocs && (
        <DocUpload
          apiUrl={API}
          language={lang}
          onExtracted={handleDocExtracted}
          onClose={() => setShowDocs(false)}
        />
      )}

      {/* ── Messages ── */}
      <main className="messages" role="log" aria-live="polite">
        {messages.map((m) => (
          <div key={m.id} className={`bubble-row ${m.role}`}>
            {m.role === "bot" && <div className="avatar">🤖</div>}
            <div className={`bubble ${m.role}`}>
              {typeof m.text === "string" ? (
                <p className="bubble-text">{m.text}</p>
              ) : (
                <SchemeCards data={m.text} onSpeak={(t) => playTTS(t)} language={lang} />
              )}
              {/* Only show speaker icon for supported languages and non-error messages */}
              {m.role === "bot" && 
               TTS_SUPPORTED_LANGS.includes(lang) && 
               !m.text.toString().includes("⚠️") && 
               !m.text.toString().includes("Connection error") && 
               !m.text.toString().includes("timed out") && (
                <button
                  className="tts-btn"
                  onClick={() => playTTS(m.text)}
                  title="Listen"
                  aria-label="Play audio"
                >
                  🔊
                </button>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="bubble-row bot">
            <div className="avatar">🤖</div>
            <div className="bubble bot loading">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      {/* ── Quick Prompts ── */}
      <div className="quick-bar" role="group" aria-label="Quick questions">
        {quickPrompts.map((p) => (
          <button 
            key={p} 
            className="quick-chip" 
            onClick={() => sendMessage(p)}
            disabled={loading}
          >
            {p}
          </button>
        ))}
      </div>

      {/* ── Input ── */}
      <footer className="input-area">
        <input
          ref={inputRef}
          className="text-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder={
            lang === "hi" ? "अपना सवाल यहाँ लिखें..." : "Type your question here..."
          }
          disabled={loading}
          aria-label="Message input"
        />
        <button
          className="send-btn"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          aria-label="Send message"
        >
          ➤
        </button>
        <VoiceRecorder
          language={lang}
          sessionId={sessionId}
          apiUrl={API}
          onResult={handleVoiceResult}
          onError={handleVoiceError}
          onStart={handleVoiceStart}
        />
      </footer>
    </div>
  );
}