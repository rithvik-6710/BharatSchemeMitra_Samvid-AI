import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
// Removed StrictMode to prevent double-rendering and duplicate messages
root.render(<App />);
