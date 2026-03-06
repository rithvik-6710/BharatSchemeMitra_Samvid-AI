/**
 * SchemeCard.jsx
 * Displays one matched government scheme with benefit, eligibility, docs, and apply link.
 */

import axios from 'axios';

export default function SchemeCard({ scheme, matchScore, language, apiUrl }) {
  const playInfo = async () => {
    const text = `${scheme.name}. ${scheme.benefit}`;
    try {
      const res = await axios.post(`${apiUrl}/speak`, { text, language }, { responseType: 'blob' });
      new Audio(URL.createObjectURL(res.data)).play();
    } catch { /* optional */ }
  };

  const matchColor = matchScore >= 90 ? '#22c55e' : matchScore >= 75 ? '#f59e0b' : '#888';

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.name}>{scheme.name}</span>
        {matchScore && (
          <span style={{ ...styles.match, color: matchColor }}>{matchScore}% ✓</span>
        )}
      </div>
      <div style={styles.benefit}>💰 {scheme.benefit}</div>
      <div style={styles.who}>👥 {scheme.who_can_apply}</div>
      <div style={styles.docs}>📄 {scheme.documents}</div>
      <div style={styles.actions}>
        <a
          href={scheme.apply_url || '#'}
          target="_blank"
          rel="noreferrer"
          style={styles.applyBtn}
        >
          How to Apply →
        </a>
        <button style={styles.speakBtn} onClick={playInfo}>🔊</button>
      </div>
    </div>
  );
}

const styles = {
  card: {
    background: '#1a1a1a', border: '1px solid #2a2a2a',
    borderRadius: '12px', padding: '14px',
    display: 'flex', flexDirection: 'column', gap: '6px',
  },
  header:   { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' },
  name:     { fontSize: '13px', fontWeight: '700', color: '#eee', flex: 1, lineHeight: '1.3' },
  match:    { fontSize: '11px', fontWeight: '700', white_space: 'nowrap', flexShrink: 0 },
  benefit:  { fontSize: '12.5px', color: '#FF6B00', fontWeight: '700' },
  who:      { fontSize: '11.5px', color: '#888', lineHeight: '1.5' },
  docs:     { fontSize: '11px',   color: '#666', lineHeight: '1.5' },
  actions:  { display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px' },
  applyBtn: {
    background: '#FF6B00', color: '#fff', borderRadius: '7px',
    padding: '5px 12px', fontSize: '11px', fontWeight: '700',
    textDecoration: 'none', cursor: 'pointer',
  },
  speakBtn: {
    background: 'none', border: 'none', cursor: 'pointer',
    fontSize: '14px', opacity: '.5',
  },
};
