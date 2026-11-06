import { useEffect, useState } from 'react';

import Icon from '../Icon/Icon';
import './Toast.css';

const DURATION = { success: 4500, error: 7000 };

/**
 * Aviso flotante en la esquina inferior: se ve aunque la página tenga scroll.
 * Se oculta solo; si el texto cambia vuelve a aparecer.
 */
function Toast({ text, tone = 'success' }) {
  const [hiddenText, setHiddenText] = useState(null);

  useEffect(() => {
    if (!text) {
      setHiddenText(null); // el mismo aviso puede volver a mostrarse
      return undefined;
    }
    const timer = window.setTimeout(() => setHiddenText(text), DURATION[tone] || 5000);
    return () => window.clearTimeout(timer);
  }, [text, tone]);

  if (!text || hiddenText === text) return null;

  return (
    <div className={`toast toast-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <span className="toast-icon">
        <Icon name={tone === 'error' ? 'close' : 'check'} size={18} />
      </span>
      <p>{text}</p>
      <button type="button" className="toast-close" aria-label="Cerrar aviso" onClick={() => setHiddenText(text)}>
        <Icon name="close" size={16} />
      </button>
    </div>
  );
}

export default Toast;
