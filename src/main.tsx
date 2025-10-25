import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import Overlay from './Overlay';

// Check if this is the overlay window
const isOverlay = window.location.hash === '#overlay';

// Add class to body for overlay-specific styling
if (isOverlay) {
  document.body.classList.add('overlay-window');
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {isOverlay ? <Overlay /> : <App />}
  </React.StrictMode>
);
