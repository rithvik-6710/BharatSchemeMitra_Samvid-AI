import React from "react";
import "./SchemeCards.css";

// Safely convert string OR array to array — fixes the crash
function toArray(val) {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === "string") return val.split(/[,;|\n]+/).map(s => s.trim()).filter(Boolean);
  return [String(val)];
}

function getCategoryIcon(cat) {
  if (!cat) return "📋";
  const c = cat.toLowerCase();
  if (c.includes("agri") || c.includes("farm")) return "🌾";
  if (c.includes("health"))  return "🏥";
  if (c.includes("hous"))    return "🏠";
  if (c.includes("edu"))     return "📚";
  if (c.includes("wom"))     return "👩";
  if (c.includes("employ"))  return "💼";
  if (c.includes("disab"))   return "♿";
  if (c.includes("fin") || c.includes("loan")) return "💳";
  return "📋";
}

export default function SchemeCards({ data, onSpeak, language = "en" }) {
  // Debug log
  console.log("🎴 SchemeCards received data:", data);
  console.log("🌍 Language:", language);
  
  // Translation map for UI labels
  const labels = {
    en: {
      whoCanApply: "WHO CAN APPLY",
      documentsRequired: "DOCUMENTS REQUIRED",
      howToApply: "HOW TO APPLY",
      applyNow: "Apply Now",
      searchOnline: "Search Online",
      applicationSteps: "Application Steps",
      documentsNeeded: "Documents Needed",
      estimatedTime: "Estimated time",
      applicationGuide: "Application Guide"
    },
    hi: {
      whoCanApply: "कौन आवेदन कर सकता है",
      documentsRequired: "आवश्यक दस्तावेज",
      howToApply: "आवेदन कैसे करें",
      applyNow: "अभी आवेदन करें",
      searchOnline: "ऑनलाइन खोजें",
      applicationSteps: "आवेदन चरण",
      documentsNeeded: "आवश्यक दस्तावेज",
      estimatedTime: "अनुमानित समय",
      applicationGuide: "आवेदन गाइड"
    },
    te: {
      whoCanApply: "ఎవరు దరఖాస్తు చేసుకోవచ్చు",
      documentsRequired: "అవసరమైన పత్రాలు",
      howToApply: "ఎలా దరఖాస్తు చేయాలి",
      applyNow: "ఇప్పుడు దరఖాస్తు చేయండి",
      searchOnline: "ఆన్‌లైన్ శోధించండి",
      applicationSteps: "దరఖాస్తు దశలు",
      documentsNeeded: "అవసరమైన పత్రాలు",
      estimatedTime: "అంచనా సమయం",
      applicationGuide: "దరఖాస్తు గైడ్"
    },
    ta: {
      whoCanApply: "யார் விண்ணப்பிக்கலாம்",
      documentsRequired: "தேவையான ஆவணங்கள்",
      howToApply: "எப்படி விண்ணப்பிப்பது",
      applyNow: "இப்போது விண்ணப்பிக்கவும்",
      searchOnline: "ஆன்லைனில் தேடுங்கள்",
      applicationSteps: "விண்ணப்ப படிகள்",
      documentsNeeded: "தேவையான ஆவணங்கள்",
      estimatedTime: "மதிப்பிடப்பட்ட நேரம்",
      applicationGuide: "விண்ணப்ப வழிகாட்டி"
    },
    bn: {
      whoCanApply: "কে আবেদন করতে পারবেন",
      documentsRequired: "প্রয়োজনীয় নথি",
      howToApply: "কীভাবে আবেদন করবেন",
      applyNow: "এখনই আবেদন করুন",
      searchOnline: "অনলাইনে খুঁজুন",
      applicationSteps: "আবেদন ধাপ",
      documentsNeeded: "প্রয়োজনীয় নথি",
      estimatedTime: "আনুমানিক সময়",
      applicationGuide: "আবেদন গাইড"
    },
    mr: {
      whoCanApply: "कोण अर्ज करू शकते",
      documentsRequired: "आवश्यक कागदपत्रे",
      howToApply: "अर्ज कसा करावा",
      applyNow: "आता अर्ज करा",
      searchOnline: "ऑनलाइन शोधा",
      applicationSteps: "अर्ज पायऱ्या",
      documentsNeeded: "आवश्यक कागदपत्रे",
      estimatedTime: "अंदाजे वेळ",
      applicationGuide: "अर्ज मार्गदर्शक"
    }
  };
  
  // Get labels for current language, fallback to English
  const t = labels[language] || labels.en;
  
  // Handle application guidance with steps
  if (data?.type === "application_guidance" && data?.steps) {
    return (
      <div className="scheme-wrap">
        <div className="scheme-card application-guidance">
          {/* Header */}
          <div className="scheme-head">
            <div className="scheme-name-row">
              <span className="scheme-category-icon">📋</span>
              <h3 className="scheme-name">{data.scheme_name || "Application Guide"}</h3>
            </div>
            <button className="scheme-tts" onClick={() => onSpeak(formatGuidanceForTTS(data))} title="Listen to all steps">
              🔊
            </button>
          </div>

          {/* Intro */}
          {data.intro && (
            <p className="guidance-intro">{data.intro}</p>
          )}

          {/* Steps */}
          <div className="scheme-section">
            <div className="scheme-section-label">📝 {t.applicationSteps}</div>
            <ol className="scheme-steps application-steps">
              {data.steps.map((step, idx) => (
                <li key={idx} className="application-step">
                  <strong>{typeof step.title === 'string' ? step.title : `Step ${idx + 1}`}</strong>
                  {step.description && (
                    <p className="step-description">{typeof step.description === 'string' ? step.description : ''}</p>
                  )}
                  {step.tips && Array.isArray(step.tips) && step.tips.length > 0 && (
                    <ul className="step-tips">
                      {step.tips.map((tip, i) => (
                        <li key={i}>💡 {typeof tip === 'string' ? tip : ''}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ol>
          </div>

          {/* Documents needed */}
          {data.documents_needed && Array.isArray(data.documents_needed) && data.documents_needed.length > 0 && (
            <div className="scheme-section">
              <div className="scheme-section-label">📄 {t.documentsNeeded}</div>
              <div className="scheme-tags">
                {data.documents_needed.map((doc, i) => (
                  <span key={i} className="scheme-tag">{typeof doc === 'string' ? doc : ''}</span>
                ))}
              </div>
            </div>
          )}

          {/* Estimated time */}
          {data.estimated_time && (
            <div className="estimated-time">
              ⏱️ {t.estimatedTime}: {data.estimated_time}
            </div>
          )}

          {/* Follow-up */}
          {data.follow_up && (
            <div className="next-question">
              <span className="next-q-icon">💬</span>
              <span>{data.follow_up}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Handle regular scheme cards
  const schemes = data?.schemes || [];
  
  // If no schemes and no intro/text, show a message
  if (schemes.length === 0 && !data?.intro && !data?.text) {
    console.warn("⚠️ No schemes to display in SchemeCards");
    return (
      <div className="scheme-wrap">
        <div className="scheme-card">
          <p className="bubble-text">
            {data?.language === "hi" 
              ? "⚠️ कोई योजना नहीं मिली। कृपया अधिक जानकारी दें।"
              : "⚠️ No schemes found. Please provide more details about your profile."}
          </p>
        </div>
      </div>
    );
  }
  
  // If there's intro/text but no schemes, show the text
  if (schemes.length === 0 && (data?.intro || data?.text)) {
    return (
      <div className="scheme-wrap">
        <div className="scheme-card">
          <p className="bubble-text">{data.intro || data.text}</p>
          {data?.follow_up && (
            <div className="next-question">
              <span className="next-q-icon">💬</span>
              <span>{data.follow_up}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="scheme-wrap">
      {schemes.map((s, idx) => (
        <div key={idx} className="scheme-card">

          {/* ── Header ── */}
          <div className="scheme-head">
            <div className="scheme-name-row">
              <span className="scheme-category-icon">{getCategoryIcon(s.category)}</span>
              <h3 className="scheme-name">{s.name}</h3>
            </div>
            <button className="scheme-tts" onClick={() => onSpeak(formatForTTS(s))} title="Listen">
              🔊
            </button>
          </div>

          {/* ── Benefit ── */}
          {s.benefit && (
            <div className="scheme-benefit-box">
              <span className="scheme-benefit-icon">💰</span>
              <span className="scheme-benefit-text">{s.benefit}</span>
            </div>
          )}

          {/* ── Eligibility ── */}
          {toArray(s.eligibility).length > 0 && (
            <div className="scheme-section">
              <div className="scheme-section-label">👥 {t.whoCanApply}</div>
              <ul className="scheme-list">
                {toArray(s.eligibility).map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}

          {/* ── Documents ── */}
          {toArray(s.documents).length > 0 && (
            <div className="scheme-section">
              <div className="scheme-section-label">📄 {t.documentsRequired}</div>
              <div className="scheme-tags">
                {toArray(s.documents).map((d, i) => (
                  <span key={i} className="scheme-tag">{d}</span>
                ))}
              </div>
            </div>
          )}

          {/* ── Steps ── */}
          {toArray(s.steps).length > 0 && (
            <div className="scheme-section">
              <div className="scheme-section-label">📝 {t.howToApply}</div>
              <ol className="scheme-steps">
                {toArray(s.steps).map((st, i) => <li key={i}>{st}</li>)}
              </ol>
            </div>
          )}

          {/* ── Actions ── */}
          <div className="scheme-actions">
            {s.official_link ? (
              <a className="scheme-apply-btn" href={s.official_link} target="_blank" rel="noreferrer">
                {t.applyNow} →
              </a>
            ) : (
              <a
                className="scheme-apply-btn"
                href={`https://www.google.com/search?q=${encodeURIComponent(s.name + " government scheme apply")}`}
                target="_blank"
                rel="noreferrer"
              >
                {t.searchOnline} →
              </a>
            )}
          </div>

        </div>
      ))}

      {/* ── Follow-up Question ── */}
      {data?.next_question && (
        <div className="next-question">
          <span className="next-q-icon">💬</span>
          <span>{data.next_question}</span>
        </div>
      )}
    </div>
  );
}

function formatForTTS(s) {
  const parts = [s.name];
  if (s.benefit) parts.push(`Benefit: ${s.benefit}`);
  const elig = toArray(s.eligibility);
  if (elig.length) parts.push(`Eligibility: ${elig.join(", ")}`);
  const docs = toArray(s.documents);
  if (docs.length) parts.push(`Documents needed: ${docs.join(", ")}`);
  return parts.join(". ");
}

function formatGuidanceForTTS(data) {
  let text = data.intro || "";
  text += ". Here are the application steps. ";
  
  if (data.steps && Array.isArray(data.steps)) {
    data.steps.forEach((step, idx) => {
      const stepNum = typeof step.step === 'number' ? step.step : (idx + 1);
      const title = typeof step.title === 'string' ? step.title : '';
      const desc = typeof step.description === 'string' ? step.description : '';
      text += `Step ${stepNum}. ${title}. ${desc}. `;
    });
  }
  
  if (data.documents_needed && Array.isArray(data.documents_needed)) {
    text += "Documents needed: " + data.documents_needed.join(", ") + ". ";
  }
  
  if (data.estimated_time) {
    text += `Estimated time: ${data.estimated_time}. `;
  }
  
  if (data.follow_up) {
    text += data.follow_up;
  }
  
  return text;
}