import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./ConversationalChat.css";

const API = process.env.REACT_APP_API_URL || "http://localhost:5000";

export default function ConversationalChat({ language, sessionId, onProfileUpdate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState({});
  const [showProfile, setShowProfile] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const addMessage = (role, content, metadata = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.random(),
        role,
        content,
        timestamp: new Date().toISOString(),
        ...metadata,
      },
    ]);
  };

  const sendMessage = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    addMessage("user", msg);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat`, {
        message: msg,
        sessionId,
        language,
      });

      const { reply, intent, user_profile, sentiment } = res.data;

      // Update user profile
      if (user_profile && Object.keys(user_profile).length > 0) {
        setUserProfile(user_profile);
        if (onProfileUpdate) {
          onProfileUpdate(user_profile);
        }
      }

      addMessage("bot", reply, { intent, sentiment });
    } catch (error) {
      addMessage("bot", {
        type: "error",
        text:
          language === "hi"
            ? "⚠️ कनेक्शन में समस्या है। कृपया दोबारा कोशिश करें।"
            : "⚠️ Connection error. Please try again.",
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const renderMessage = (msg) => {
    const content = msg.content;

    // Handle different response types
    if (typeof content === "string") {
      // CRITICAL FIX: Check if string looks like JSON
      if (content.trim().startsWith("{") || content.trim().startsWith("[")) {
        console.error("⚠️ Received JSON string instead of object:", content.substring(0, 100));
        try {
          const parsed = JSON.parse(content);
          // Recursively render the parsed object
          return renderMessage({ ...msg, content: parsed });
        } catch (e) {
          console.error("❌ Failed to parse JSON string:", e);
          return <p className="message-text error">⚠️ Error displaying response. Please try again.</p>;
        }
      }
      return <p className="message-text">{content}</p>;
    }

    if (content.type === "application_guidance") {
      return renderApplicationGuidance(content);
    }

    if (content.type === "eligibility_check") {
      return renderEligibilityCheck(content);
    }

    if (content.type === "document_help") {
      return renderDocumentHelp(content);
    }
    
    // Handle text_response type
    if (content.type === "text_response" && content.text) {
      return <p className="message-text">{content.text}</p>;
    }

    // Default scheme cards
    if (content.schemes && Array.isArray(content.schemes)) {
      return renderSchemeCards(content);
    }
    
    // CRITICAL FIX: If we have intro but no schemes, show the intro text
    if (content.intro && !content.schemes) {
      return <p className="message-text">{content.intro}</p>;
    }

    // Last resort: show error instead of raw JSON
    console.error("⚠️ Unknown content format:", content);
    return <p className="message-text error">⚠️ Error displaying response. Please try again.</p>;
  };

  const renderApplicationGuidance = (data) => (
    <div className="application-guidance">
      <h3 className="guidance-title">📋 {data.scheme_name}</h3>
      <p className="guidance-intro">{data.intro}</p>

      <div className="steps-container">
        {data.steps?.map((step, idx) => (
          <div key={idx} className="step-card">
            <div className="step-header">
              <span className="step-number">{typeof step.step === 'object' ? idx + 1 : step.step}</span>
              <h4 className="step-title">{typeof step.title === 'string' ? step.title : JSON.stringify(step.title)}</h4>
            </div>
            <p className="step-description">{typeof step.description === 'string' ? step.description : JSON.stringify(step.description)}</p>
            {step.tips && Array.isArray(step.tips) && step.tips.length > 0 && (
              <ul className="step-tips">
                {step.tips.map((tip, i) => (
                  <li key={i}>💡 {typeof tip === 'string' ? tip : JSON.stringify(tip)}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      {data.documents_needed && Array.isArray(data.documents_needed) && (
        <div className="documents-section">
          <h4>📄 Documents Needed:</h4>
          <ul>
            {data.documents_needed.map((doc, i) => (
              <li key={i}>{typeof doc === 'string' ? doc : JSON.stringify(doc)}</li>
            ))}
          </ul>
        </div>
      )}

      {data.estimated_time && (
        <p className="estimated-time">⏱️ Estimated time: {data.estimated_time}</p>
      )}

      {data.follow_up && <p className="follow-up">{data.follow_up}</p>}
    </div>
  );

  const renderEligibilityCheck = (data) => (
    <div className="eligibility-check">
      <p className="intro">{data.intro}</p>

      {data.eligible_schemes && data.eligible_schemes.length > 0 && (
        <div className="eligible-schemes">
          <h4>✅ You may be eligible for:</h4>
          {data.eligible_schemes.map((scheme, idx) => (
            <div key={idx} className="eligible-scheme-card">
              <h5>{scheme.name}</h5>
              <p className="reason">👉 {scheme.reason}</p>
            </div>
          ))}
        </div>
      )}

      {data.need_more_info && data.question && (
        <div className="clarifying-question">
          <p className="question-label">To help you better:</p>
          <p className="question">{data.question}</p>
        </div>
      )}

      {data.follow_up && <p className="follow-up">{data.follow_up}</p>}
    </div>
  );

  const renderDocumentHelp = (data) => (
    <div className="document-help">
      <p className="intro">{data.intro}</p>

      {data.documents && data.documents.length > 0 && (
        <div className="documents-list">
          {data.documents.map((doc, idx) => (
            <div key={idx} className="document-card">
              <h4>📄 {doc.name}</h4>
              <p className="doc-description">{doc.description}</p>
              {doc.where_to_get && (
                <p className="where-to-get">
                  <strong>Where to get:</strong> {doc.where_to_get}
                </p>
              )}
              {doc.tips && doc.tips.length > 0 && (
                <ul className="doc-tips">
                  {doc.tips.map((tip, i) => (
                    <li key={i}>💡 {tip}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {data.follow_up && <p className="follow-up">{data.follow_up}</p>}
    </div>
  );

  const renderSchemeCards = (data) => (
    <div className="scheme-cards">
      {data.intro && <p className="intro">{data.intro}</p>}

      {data.schemes.map((scheme, idx) => (
        <div key={idx} className="scheme-card">
          <div className="scheme-header">
            <h4 className="scheme-name">{scheme.name}</h4>
            <span className={`category-badge ${scheme.category}`}>
              {scheme.category}
            </span>
          </div>

          {scheme.why_relevant && (
            <p className="why-relevant">
              <strong>Why for you:</strong> {scheme.why_relevant}
            </p>
          )}

          <p className="benefit">
            <strong>💰 Benefit:</strong> {typeof scheme.benefit === 'string' ? scheme.benefit : JSON.stringify(scheme.benefit)}
          </p>

          <p className="eligibility">
            <strong>✅ Eligibility:</strong> {typeof scheme.eligibility === 'string' ? scheme.eligibility : (Array.isArray(scheme.eligibility) ? scheme.eligibility.join(', ') : JSON.stringify(scheme.eligibility))}
          </p>

          {scheme.documents && Array.isArray(scheme.documents) && scheme.documents.length > 0 && (
            <div className="documents">
              <strong>📄 Documents:</strong>
              <ul>
                {scheme.documents.map((doc, i) => (
                  <li key={i}>{typeof doc === 'string' ? doc : JSON.stringify(doc)}</li>
                ))}
              </ul>
            </div>
          )}

          {scheme.apply_steps && Array.isArray(scheme.apply_steps) && scheme.apply_steps.length > 0 && (
            <details className="apply-steps">
              <summary>How to Apply</summary>
              <ol>
                {scheme.apply_steps.map((step, i) => (
                  <li key={i}>{typeof step === 'string' ? step : JSON.stringify(step)}</li>
                ))}
              </ol>
            </details>
          )}

          {scheme.apply_url && (
            <a
              href={scheme.apply_url}
              target="_blank"
              rel="noopener noreferrer"
              className="apply-link"
            >
              Apply Now →
            </a>
          )}

          <button
            className="details-btn"
            onClick={() =>
              sendMessage(
                language === "hi"
                  ? `${scheme.name} के बारे में और बताएं`
                  : `Tell me more about ${scheme.name}`
              )
            }
          >
            Learn More
          </button>
        </div>
      ))}

      {data.follow_up && <p className="follow-up">{data.follow_up}</p>}
    </div>
  );

  return (
    <div className="conversational-chat">
      {/* Profile Summary */}
      {Object.keys(userProfile).length > 0 && (
        <div className="profile-summary">
          <button
            className="profile-toggle"
            onClick={() => setShowProfile(!showProfile)}
          >
            👤 Your Profile {showProfile ? "▼" : "▶"}
          </button>
          {showProfile && (
            <div className="profile-details">
              {userProfile.occupation && (
                <span className="profile-tag">👔 {userProfile.occupation}</span>
              )}
              {userProfile.state && (
                <span className="profile-tag">📍 {userProfile.state}</span>
              )}
              {userProfile.age_group && (
                <span className="profile-tag">🎂 {userProfile.age_group}</span>
              )}
              {userProfile.income_bracket && (
                <span className="profile-tag">💰 {userProfile.income_bracket}</span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-row ${msg.role}`}>
            {msg.role === "bot" && <div className="avatar">🤖</div>}
            <div className={`message-bubble ${msg.role}`}>
              {renderMessage(msg)}
              {msg.sentiment === "NEGATIVE" && msg.role === "user" && (
                <span className="sentiment-indicator" title="We detected frustration">
                  😟
                </span>
              )}
            </div>
            {msg.role === "user" && <div className="avatar">👤</div>}
          </div>
        ))}

        {loading && (
          <div className="message-row bot">
            <div className="avatar">🤖</div>
            <div className="message-bubble bot loading">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <input
          ref={inputRef}
          className="message-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
          placeholder={
            language === "hi"
              ? "अपना सवाल यहाँ लिखें..."
              : "Type your question here..."
          }
          disabled={loading}
        />
        <button
          className="send-button"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          ➤
        </button>
      </div>
    </div>
  );
}
