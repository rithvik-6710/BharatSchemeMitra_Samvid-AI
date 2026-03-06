/**
 * DocUpload.jsx — Bharat Scheme Mitra v3.0
 * Upload documents → Amazon Textract OCR → AI field extraction → scheme matching
 *
 * Supported documents:
 *   Aadhaar, PAN, Income Certificate, Ration Card, Caste Certificate,
 *   Bank Passbook, Land Record (Khasra), Disability Certificate, Job Card
 */

import { useState, useRef } from 'react';
import axios from 'axios';

const DOC_TYPES = [
  { value: 'aadhaar',      label: '🪪 Aadhaar Card',           hint: 'Name · DOB · Address · Aadhaar number' },
  { value: 'pan',          label: '💳 PAN Card',               hint: 'Name · PAN number · DOB' },
  { value: 'income_cert',  label: '📜 Income Certificate',     hint: 'Annual income · Family size' },
  { value: 'ration_card',  label: '🍚 Ration Card',            hint: 'Family members · Category (APL/BPL/AAY)' },
  { value: 'caste_cert',   label: '📋 Caste Certificate',      hint: 'Caste category (SC/ST/OBC)' },
  { value: 'bank_passbook',label: '🏦 Bank Passbook',          hint: 'Account number · IFSC · Bank name' },
  { value: 'land_record',  label: '🌾 Land Record / Khasra',   hint: 'Land area · Survey number · Owner name' },
  { value: 'disability',   label: '♿ Disability Certificate',  hint: 'Disability type · Percentage' },
  { value: 'job_card',     label: '💼 MGNREGA Job Card',       hint: 'Job card number · Family members' },
  { value: 'general',      label: '📄 Other Document',         hint: 'Any government document' },
];

const FIELD_LABELS = {
  name:               '👤 Name',
  dob:                '📅 Date of Birth',
  id_number:          '🔢 ID / Card Number',
  address:            '📍 Address',
  gender:             '⚧ Gender',
  document_type:      '📄 Document Type',
  income:             '💰 Annual Income',
  category:           '🏷 Category (APL/BPL)',
  land_area:          '🌾 Land Area',
  survey_number:      '📌 Survey Number',
  account_number:     '🏦 Account Number',
  bank_name:          '🏦 Bank Name',
  ifsc:               '🔀 IFSC Code',
  disability_type:    '♿ Disability Type',
  disability_percent: '📊 Disability %',
  job_card_number:    '💼 Job Card Number',
  family_members:     '👨‍👩‍👧 Family Members',
};

export default function DocUpload({ apiUrl, language, onExtracted, onClose }) {
  const [docType,  setDocType  ] = useState('aadhaar');
  const [result,   setResult   ] = useState(null);
  const [rawOcr,   setRawOcr   ] = useState('');
  const [loading,  setLoading  ] = useState(false);
  const [error,    setError    ] = useState('');
  const [dragOver, setDragOver ] = useState(false);
  const [fileName, setFileName ] = useState('');
  const [showRaw,  setShowRaw  ] = useState(false);
  const [step,     setStep     ] = useState(''); // 'uploading' | 'ocr' | 'parsing'
  const fileInputRef = useRef(null);

  const selectedDoc = DOC_TYPES.find(d => d.value === docType);

  const processFile = async (file) => {
    if (!file) return;

    // Validate file type
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf'];
    if (!allowed.includes(file.type)) {
      setError('Please upload a JPG, PNG, WEBP image or PDF file.');
      return;
    }

    // Validate size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError(`File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Please upload under 5MB.`);
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setRawOcr('');
    setFileName(file.name);
    setStep('uploading');

    const form = new FormData();
    form.append('document', file);
    form.append('type', docType);

    // Simulate step progression for UX
    const t1 = setTimeout(() => setStep('ocr'), 1200);
    const t2 = setTimeout(() => setStep('parsing'), 2800);

    try {
      const res = await axios.post(`${apiUrl}/upload-doc`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 45000,
      });
      clearTimeout(t1); clearTimeout(t2);
      setResult(res.data.extracted || {});
      setRawOcr(res.data.raw_text || '');
      setStep('');
    } catch (err) {
      clearTimeout(t1); clearTimeout(t2);
      const msg = err.response?.data?.error
        || 'Failed to process document. Please ensure the image is clear and well-lit.';
      setError(msg);
      setStep('');
    } finally {
      setLoading(false);
    }
  };

  const handleFileInput = (e) => processFile(e.target.files[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    processFile(e.dataTransfer.files[0]);
  };

  const validFields = result
    ? Object.entries(result).filter(([k, v]) => v && k !== 'raw_ocr' && k !== 'parse_error')
    : [];

  const STEP_LABELS = {
    uploading: { icon: '📤', text: 'Uploading to Amazon S3...' },
    ocr:       { icon: '🔍', text: 'Running Amazon Textract OCR...' },
    parsing:   { icon: '🤖', text: 'AI extracting fields with Nova...' },
  };
  const currentStep = STEP_LABELS[step];

  return (
    <div style={S.wrap}>

      {/* ── Header ── */}
      <div style={S.header}>
        <div style={S.headerLeft}>
          <span style={S.headerIcon}>📄</span>
          <div>
            <div style={S.headerTitle}>Upload Document</div>
            <div style={S.headerSub}>Amazon Textract OCR + AI extraction</div>
          </div>
        </div>
        <button style={S.closeBtn} onClick={onClose} title="Close">✕</button>
      </div>

      <div style={S.body}>

        {/* ── Doc Type Selector ── */}
        <div>
          <div style={S.label}>Select Document Type</div>
          <select
            style={S.select}
            value={docType}
            onChange={e => { setDocType(e.target.value); setResult(null); setError(''); setFileName(''); }}
            disabled={loading}
          >
            {DOC_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <div style={S.hint}>📌 Extracts: {selectedDoc?.hint}</div>
        </div>

        {/* ── Upload Zone ── */}
        <div
          style={{
            ...S.uploadZone,
            borderColor: dragOver ? '#FF6B00' : loading ? '#333' : '#2a2a2a',
            background: dragOver ? 'rgba(255,107,0,0.06)' : 'transparent',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
          onClick={() => !loading && fileInputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); !loading && setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          {loading && currentStep ? (
            <div style={S.loadingWrap}>
              <div style={S.loadingIcon}>{currentStep.icon}</div>
              <div style={S.loadingText}>{currentStep.text}</div>
              <div style={S.loadingBar}>
                <div style={{
                  ...S.loadingFill,
                  width: step === 'uploading' ? '33%' : step === 'ocr' ? '66%' : '90%',
                }} />
              </div>
              <div style={S.loadingPipeline}>
                <span style={{ ...S.pipeStep, color: '#FF6B00' }}>📤 S3</span>
                <span style={S.pipeArrow}>→</span>
                <span style={{ ...S.pipeStep, color: step === 'ocr' || step === 'parsing' ? '#FF6B00' : '#333' }}>🔍 Textract</span>
                <span style={S.pipeArrow}>→</span>
                <span style={{ ...S.pipeStep, color: step === 'parsing' ? '#FF6B00' : '#333' }}>🤖 Nova AI</span>
              </div>
            </div>
          ) : (
            <>
              <div style={S.uploadEmoji}>{fileName ? '✅' : '📷'}</div>
              <div style={S.uploadTitle}>
                {fileName ? fileName : 'Click or Drag & Drop'}
              </div>
              <div style={S.uploadSub}>JPG · PNG · PDF · WEBP · Max 5MB</div>
              <button
                style={S.uploadBtn}
                type="button"
                onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}
              >
                {fileName ? '📂 Upload Different File' : '📂 Choose File'}
              </button>
            </>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp,application/pdf"
            onChange={handleFileInput}
            style={{ display: 'none' }}
            disabled={loading}
          />
        </div>

        {/* ── Photo Tips ── */}
        {!result && !loading && (
          <div style={S.tips}>
            <div style={S.tipsTitle}>📸 Tips for best results</div>
            <div style={S.tipsGrid}>
              <span style={S.tip}>✅ Flat surface, no glare</span>
              <span style={S.tip}>✅ All 4 corners visible</span>
              <span style={S.tip}>✅ Good lighting</span>
              <span style={S.tip}>✅ Hold camera steady</span>
            </div>
          </div>
        )}

        {/* ── Error ── */}
        {error && (
          <div style={S.errorBox}>
            <div style={S.errorIcon}>⚠️</div>
            <div>
              <div style={S.errorText}>{error}</div>
              <div style={S.errorSub}>Try retaking with better lighting or a closer shot.</div>
            </div>
          </div>
        )}

        {/* ── Result ── */}
        {result && (
          <div style={S.resultBox}>
            <div style={S.resultHeader}>
              <span style={S.resultTitle}>✅ Information Extracted</span>
              <span style={S.resultBadge}>{validFields.length} fields found</span>
            </div>

            {validFields.length > 0 ? (
              <div style={S.fieldList}>
                {validFields.map(([k, v]) => (
                  <div key={k} style={S.fieldRow}>
                    <span style={S.fieldKey}>{FIELD_LABELS[k] || k.replace(/_/g, ' ')}</span>
                    <span style={S.fieldVal}>{String(v)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={S.noFields}>
                ⚠️ Could not extract fields. Try uploading a clearer image.
              </div>
            )}

            {/* Raw OCR toggle */}
            {rawOcr && (
              <>
                <button style={S.rawBtn} onClick={() => setShowRaw(s => !s)}>
                  {showRaw ? '▲ Hide raw OCR text' : '▼ Show raw OCR text (debug)'}
                </button>
                {showRaw && <div style={S.rawBox}>{rawOcr}</div>}
              </>
            )}

            {/* Action Buttons */}
            <div style={S.resultActions}>
              <button
                style={{ ...S.findBtn, opacity: validFields.length === 0 ? 0.5 : 1 }}
                onClick={() => onExtracted(result)}
                disabled={validFields.length === 0}
              >
                🔍 Find My Eligible Schemes →
              </button>
              <button
                style={S.retryBtn}
                onClick={() => { setResult(null); setError(''); setFileName(''); setRawOcr(''); }}
              >
                📂 Upload Another Document
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const S = {
  wrap: {
    background: '#0f0f0f',
    borderBottom: '1px solid #1e1e1e',
    flexShrink: 0,
    maxHeight: '62vh',
    overflowY: 'auto',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 18px', borderBottom: '1px solid #1e1e1e',
    position: 'sticky', top: 0, background: '#0f0f0f', zIndex: 10,
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '10px' },
  headerIcon: { fontSize: '22px' },
  headerTitle: { fontSize: '14px', fontWeight: '700', color: '#eee' },
  headerSub: { fontSize: '10px', color: '#444', marginTop: '2px' },
  closeBtn: {
    background: 'rgba(255,255,255,0.05)', border: '1px solid #2a2a2a',
    color: '#666', fontSize: '14px', cursor: 'pointer',
    padding: '5px 11px', borderRadius: '8px',
  },
  body: { padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: '14px' },
  label: { fontSize: '10px', fontWeight: '700', color: '#555', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' },
  select: {
    background: '#1a1a1a', color: '#ddd', border: '1px solid #2a2a2a',
    borderRadius: '10px', padding: '10px 12px', fontSize: '13px',
    cursor: 'pointer', width: '100%', outline: 'none',
  },
  hint: { fontSize: '11px', color: '#444', marginTop: '5px', paddingLeft: '2px' },
  uploadZone: {
    border: '2px dashed #2a2a2a', borderRadius: '14px',
    padding: '28px 16px', textAlign: 'center',
    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '9px',
    transition: 'all 0.2s ease', minHeight: '130px', justifyContent: 'center',
  },
  uploadEmoji: { fontSize: '34px' },
  uploadTitle: { fontSize: '14px', fontWeight: '600', color: '#bbb' },
  uploadSub: { fontSize: '11px', color: '#444' },
  uploadBtn: {
    background: 'linear-gradient(135deg, #FF6B00, #FF9040)',
    color: '#fff', border: 'none', borderRadius: '9px',
    padding: '8px 22px', fontSize: '12px', fontWeight: '700',
    cursor: 'pointer', marginTop: '4px',
  },
  loadingWrap: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', width: '100%' },
  loadingIcon: { fontSize: '28px' },
  loadingText: { fontSize: '13px', color: '#FF6B00', fontWeight: '600' },
  loadingBar: { width: '80%', height: '4px', background: '#1a1a1a', borderRadius: '4px', overflow: 'hidden' },
  loadingFill: { height: '100%', background: 'linear-gradient(90deg,#FF6B00,#FF9040)', borderRadius: '4px', transition: 'width 0.8s ease' },
  loadingPipeline: { display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' },
  pipeStep: { fontSize: '10px', fontWeight: '600', transition: 'color 0.5s' },
  pipeArrow: { fontSize: '10px', color: '#333' },
  tips: {
    background: 'rgba(255,107,0,0.04)', border: '1px solid rgba(255,107,0,0.1)',
    borderRadius: '10px', padding: '10px 14px',
  },
  tipsTitle: { fontSize: '11px', color: '#FF6B00', fontWeight: '700', marginBottom: '7px' },
  tipsGrid: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
  tip: { fontSize: '11px', color: '#666', background: '#1a1a1a', padding: '3px 9px', borderRadius: '20px', border: '1px solid #222' },
  errorBox: {
    display: 'flex', gap: '10px', alignItems: 'flex-start',
    background: 'rgba(231,76,60,0.07)', border: '1px solid rgba(231,76,60,0.18)',
    borderRadius: '10px', padding: '11px 14px',
  },
  errorIcon: { fontSize: '16px', flexShrink: 0 },
  errorText: { fontSize: '13px', color: '#e74c3c', fontWeight: '600' },
  errorSub: { fontSize: '11px', color: '#8a3a3a', marginTop: '3px' },
  resultBox: {
    background: '#111', border: '1px solid #1e1e1e',
    borderRadius: '14px', padding: '14px',
    display: 'flex', flexDirection: 'column', gap: '10px',
  },
  resultHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  resultTitle: { fontSize: '13px', color: '#06D6A0', fontWeight: '700' },
  resultBadge: { fontSize: '11px', color: '#06D6A0', background: 'rgba(6,214,160,0.08)', border: '1px solid rgba(6,214,160,0.2)', padding: '2px 9px', borderRadius: '20px' },
  fieldList: { display: 'flex', flexDirection: 'column' },
  fieldRow: {
    display: 'flex', justifyContent: 'space-between',
    alignItems: 'flex-start', padding: '7px 0',
    borderBottom: '1px solid #1a1a1a',
  },
  fieldKey: { fontSize: '12px', color: '#555', flex: '0 0 48%' },
  fieldVal: { fontSize: '12px', color: '#ddd', fontWeight: '600', flex: '0 0 48%', textAlign: 'right', wordBreak: 'break-word' },
  noFields: { fontSize: '12px', color: '#666', textAlign: 'center', padding: '8px 0' },
  rawBtn: { background: 'none', border: 'none', color: '#444', fontSize: '11px', cursor: 'pointer', textAlign: 'left', padding: '2px 0' },
  rawBox: {
    background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: '8px',
    padding: '10px', fontSize: '10px', color: '#555', lineHeight: '1.6',
    maxHeight: '80px', overflowY: 'auto', fontFamily: 'monospace', wordBreak: 'break-all',
  },
  resultActions: { display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' },
  findBtn: {
    width: '100%', background: 'linear-gradient(135deg, #FF6B00, #FF9040)',
    color: '#fff', border: 'none', borderRadius: '11px',
    padding: '12px', fontSize: '13px', fontWeight: '700', cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(255,107,0,0.25)',
  },
  retryBtn: {
    width: '100%', background: 'transparent', border: '1px solid #2a2a2a',
    color: '#666', borderRadius: '11px', padding: '10px',
    fontSize: '12px', cursor: 'pointer',
  },
};