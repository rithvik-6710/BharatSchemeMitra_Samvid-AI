/**
 * VoiceRecorder.jsx — Bharat Scheme Mitra v3.0
 *
 * Features:
 *   ✅ Click to start / click again to stop (no hold needed)
 *   ✅ Live waveform animation while recording
 *   ✅ Recording duration timer with max 60s auto-stop
 *   ✅ Audio level visualiser (volume meter)
 *   ✅ Language label shown while recording
 *   ✅ Graceful mic permission handling with clear messages
 *   ✅ Best codec auto-selection (opus → webm fallback)
 *   ✅ Sends to /voice → Amazon Transcribe → Nova AI reply
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import axios from 'axios';

const LANG_LABELS = {
  hi: 'हिंदी', en: 'English', ta: 'தமிழ்', te: 'తెలుగు',
  bn: 'বাংলা',  mr: 'मराठी',  gu: 'ગુજરાતી', kn: 'ಕನ್ನಡ',
  ml: 'മലയാളം', pa: 'ਪੰਜਾਬੀ', or: 'ଓଡ଼ିଆ',  as: 'অসমীয়া', ur: 'اردو',
};

const MAX_DURATION = 60; // seconds

export default function VoiceRecorder({ language, sessionId, apiUrl, onResult, onError, onStart }) {
  const [state,    setState   ] = useState('idle');     // idle | recording | processing
  const [duration, setDuration] = useState(0);          // seconds recorded
  const [volume,   setVolume  ] = useState(0);          // 0-1 mic volume level
  const [permErr,  setPermErr ] = useState(false);      // mic permission denied?

  const mediaRef    = useRef(null);
  const chunksRef   = useRef([]);
  const streamRef   = useRef(null);
  const timerRef    = useRef(null);
  const analyserRef = useRef(null);
  const animRef     = useRef(null);

  // ── Cleanup on unmount ──────────────────────────────────────
  useEffect(() => {
    return () => {
      clearInterval(timerRef.current);
      cancelAnimationFrame(animRef.current);
      streamRef.current?.getTracks().forEach(t => t.stop());
    };
  }, []);

  // ── Volume analyser loop ────────────────────────────────────
  const startVolumeAnalyser = (stream) => {
    try {
      const ctx      = new (window.AudioContext || window.webkitAudioContext)();
      const source   = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        const avg = data.reduce((s, v) => s + v, 0) / data.length;
        setVolume(Math.min(avg / 80, 1));
        animRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch (_) {
      // AudioContext not supported — no waveform, still works
    }
  };

  // ── Start Recording ─────────────────────────────────────────
  const startRecording = useCallback(async () => {
    setPermErr(false);
    // Notify parent to stop TTS
    if (onStart) onStart();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { 
          echoCancellation: true, 
          noiseSuppression: true, 
          autoGainControl: true,  // Added for better volume
          sampleRate: 48000       // Increased from 16000 for better quality
        }
      });
      streamRef.current = stream;
      startVolumeAnalyser(stream);

      // Best codec selection
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
        .find(m => MediaRecorder.isTypeSupported(m)) || '';

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          console.log('📼 Audio chunk:', e.data.size, 'bytes');
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        clearInterval(timerRef.current);
        cancelAnimationFrame(animRef.current);
        streamRef.current?.getTracks().forEach(t => t.stop());
        setVolume(0);
        setDuration(0);
        setState('processing');

        const blob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' });

        // Reduced minimum size check for better detection
        if (blob.size < 500) {
          onError('Recording too short. Please speak for at least 1 second.');
          setState('idle');
          return;
        }

        // Determine file extension BEFORE using it
        const ext = mimeType.includes('mp4') ? 'mp4' : mimeType.includes('ogg') ? 'ogg' : 'webm';

        // Log blob size for debugging
        console.log('🎤 Final audio blob:', blob.size, 'bytes', 'type:', blob.type);
        console.log('🎤 Format:', ext, '| Chunks:', chunksRef.current.length);

        const form = new FormData();
        form.append('audio',     blob, `recording.${ext}`);
        form.append('language',  language);
        form.append('sessionId', sessionId);

        try {
          const res = await axios.post(`${apiUrl}/voice`, form, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 65000, // Increased to 65s for Indic languages (Hindi, Tamil, etc.)
          });
          onResult(res.data);
        } catch (err) {
          // Extract detailed error message from backend
          let msg = 'Voice processing failed. Please try typing instead.';
          if (err.response?.data?.error) {
            msg = err.response.data.error;
            // Add tip if available
            if (err.response.data.tip) {
              msg += ` Tip: ${err.response.data.tip}`;
            }
          } else if (err.code === 'ECONNABORTED') {
            msg = `Voice processing timed out for ${LANG_LABELS[language] || language}. This can happen with longer recordings. Please try: 1) Speaking for 2-5 seconds only, 2) Speaking clearly and slowly, 3) Using text input instead.`;
          } else if (!err.response) {
            msg = 'Cannot connect to server. Please check your connection.';
          }
          console.error('🎤 Voice error:', err);
          console.error('🎤 Error details:', err.response?.data);
          onError(msg);
        } finally {
          setState('idle');
        }
      };

      mediaRef.current = recorder;
      recorder.start(100);
      setState('recording');

      // Duration timer + auto-stop at MAX_DURATION
      setDuration(0);
      timerRef.current = setInterval(() => {
        setDuration(d => {
          if (d + 1 >= MAX_DURATION) {
            clearInterval(timerRef.current);
            if (mediaRef.current?.state === 'recording') mediaRef.current.stop();
            return MAX_DURATION;
          }
          return d + 1;
        });
      }, 1000);

    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setPermErr(true);
        onError('Microphone permission denied. Please allow access in browser settings.');
      } else if (err.name === 'NotFoundError') {
        onError('No microphone found. Please connect a microphone and try again.');
      } else {
        onError('Could not start recording. Please check your microphone.');
      }
      setState('idle');
    }
  }, [language, sessionId, apiUrl, onResult, onError, onStart]);

  // ── Stop Recording ──────────────────────────────────────────
  const stopRecording = useCallback(() => {
    if (mediaRef.current?.state === 'recording') {
      mediaRef.current.stop();
    }
  }, []);

  // ── Toggle ──────────────────────────────────────────────────
  const handleClick = () => {
    if (state === 'idle')      startRecording();
    else if (state === 'recording') stopRecording();
  };

  // ── Format mm:ss ────────────────────────────────────────────
  const formatTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  // ── Waveform bars ───────────────────────────────────────────
  const barCount = 5;
  const bars = Array.from({ length: barCount }, (_, i) => {
    const mid    = (barCount - 1) / 2;
    const dist   = Math.abs(i - mid) / mid;
    const height = state === 'recording'
      ? Math.max(0.2, volume * (1 - dist * 0.5) + Math.random() * 0.15)
      : 0.25;
    return height;
  });

  // ── Tooltip text ────────────────────────────────────────────
  const tooltip =
    state === 'idle'       ? `Click to speak in ${LANG_LABELS[language] || 'your language'}` :
    state === 'recording'  ? 'Click to stop and send' :
                             'Processing your voice...';

  return (
    <div style={S.wrapper}>
      {/* ── Waveform / animation above button ── */}
      {state !== 'idle' && (
        <div style={S.waveWrap}>
          {state === 'recording' ? (
            <>
              <div style={S.waveform}>
                {bars.map((h, i) => (
                  <div
                    key={i}
                    style={{
                      ...S.bar,
                      height: `${h * 22}px`,
                      opacity: 0.5 + h * 0.5,
                      transition: 'height 0.08s ease',
                    }}
                  />
                ))}
              </div>
              <div style={S.recRow}>
                <div style={S.recDot} />
                <span style={S.recTime}>{formatTime(duration)}</span>
                <span style={S.recLang}>{LANG_LABELS[language] || language}</span>
              </div>
              <div style={S.progressWrap}>
                <div style={{ ...S.progressFill, width: `${(duration / MAX_DURATION) * 100}%` }} />
              </div>
            </>
          ) : (
            <div style={S.processingRow}>
              <span style={S.processingDot} />
              <span style={S.processingText}>Transcribing...</span>
            </div>
          )}
        </div>
      )}

      {/* ── Main Button ── */}
      <button
        style={{
          ...S.btn,
          background:
            state === 'recording'  ? '#e74c3c' :
            state === 'processing' ? '#333'    :
            permErr                ? '#555'    :
            'linear-gradient(135deg, #1a1a2e, #2a2a4a)',
          boxShadow: state === 'recording'
            ? `0 0 0 ${3 + volume * 8}px rgba(231,76,60,0.3), 0 4px 14px rgba(231,76,60,0.4)`
            : '0 4px 14px rgba(0,0,0,0.4)',
          transform: state === 'recording' ? 'scale(1.08)' : 'scale(1)',
          border: state === 'recording' ? '2px solid #e74c3c' : '2px solid #333',
        }}
        onClick={handleClick}
        disabled={state === 'processing'}
        title={tooltip}
        aria-label={tooltip}
      >
        <span style={S.btnIcon}>
          {state === 'idle'       ? (permErr ? '🚫' : '🎤') :
           state === 'recording'  ? '⏹' :
                                    '⏳'}
        </span>
      </button>

      {/* ── Permission error hint ── */}
      {permErr && state === 'idle' && (
        <div style={S.permHint}>Allow mic in browser</div>
      )}
    </div>
  );
}

const S = {
  wrapper: {
    display:        'flex',
    flexDirection:  'column',
    alignItems:     'center',
    gap:            '4px',
    position:       'relative',
  },
  waveWrap: {
    position:       'absolute',
    bottom:         '54px',
    left:           '50%',
    transform:      'translateX(-50%)',
    background:     'rgba(10,10,10,0.97)',
    border:         '1px solid #222',
    borderRadius:   '14px',
    padding:        '10px 14px',
    minWidth:       '140px',
    display:        'flex',
    flexDirection:  'column',
    alignItems:     'center',
    gap:            '6px',
    boxShadow:      '0 8px 24px rgba(0,0,0,0.6)',
    zIndex:         100,
    whiteSpace:     'nowrap',
  },
  waveform: {
    display:      'flex',
    alignItems:   'center',
    gap:          '3px',
    height:       '28px',
  },
  bar: {
    width:        '4px',
    minHeight:    '4px',
    background:   '#e74c3c',
    borderRadius: '4px',
  },
  recRow: {
    display:      'flex',
    alignItems:   'center',
    gap:          '6px',
  },
  recDot: {
    width:        '7px',
    height:       '7px',
    background:   '#e74c3c',
    borderRadius: '50%',
    animation:    'blink 1s step-start infinite',
  },
  recTime: {
    fontSize:     '13px',
    fontWeight:   '700',
    color:        '#eee',
    fontFamily:   'monospace',
  },
  recLang: {
    fontSize:     '10px',
    color:        '#555',
    background:   '#1a1a1a',
    padding:      '1px 7px',
    borderRadius: '10px',
    border:       '1px solid #2a2a2a',
  },
  progressWrap: {
    width:        '100%',
    height:       '2px',
    background:   '#1a1a1a',
    borderRadius: '2px',
    overflow:     'hidden',
  },
  progressFill: {
    height:       '100%',
    background:   '#e74c3c',
    borderRadius: '2px',
    transition:   'width 1s linear',
  },
  processingRow: {
    display:     'flex',
    alignItems:  'center',
    gap:         '7px',
    padding:     '2px 0',
  },
  processingDot: {
    width:        '8px',
    height:       '8px',
    background:   '#FF6B00',
    borderRadius: '50%',
    animation:    'blink 0.7s step-start infinite',
  },
  processingText: {
    fontSize:   '12px',
    color:      '#FF6B00',
    fontWeight: '600',
  },
  btn: {
    width:        '44px',
    height:       '44px',
    borderRadius: '50%',
    cursor:       'pointer',
    display:      'flex',
    alignItems:   'center',
    justifyContent: 'center',
    transition:   'all 0.2s ease',
    flexShrink:   0,
  },
  btnIcon: {
    fontSize: '18px',
    lineHeight: 1,
    userSelect: 'none',
  },
  permHint: {
    fontSize:   '9px',
    color:      '#666',
    textAlign:  'center',
    maxWidth:   '60px',
    lineHeight: '1.3',
  },
};

// Inject blink keyframe once
if (typeof document !== 'undefined' && !document.getElementById('bsm-blink')) {
  const style = document.createElement('style');
  style.id = 'bsm-blink';
  style.textContent = `@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`;
  document.head.appendChild(style);
}