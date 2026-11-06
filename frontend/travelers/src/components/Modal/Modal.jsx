import { useEffect, useId } from 'react';

import Icon from '../Icon/Icon';

import './Modal.css';

/**
 * Ventana modal reutilizable. Se cierra con Esc, con el botón X o al hacer clic fuera.
 * size: "small" | "medium" | "large"
 */
function Modal({ title, subtitle, onClose, size = 'medium', children, footer }) {
  const titleId = useId();

  useEffect(() => {
    const handleKey = (event) => {
      if (event.key === 'Escape') onClose();
    };

    window.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className={`modal modal-${size}`} role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="modal-header">
          <div>
            <h2 id={titleId}>{title}</h2>
            {subtitle && <p className="modal-subtitle">{subtitle}</p>}
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Cerrar">
            <Icon name="close" size={20} />
          </button>
        </div>

        <div className="modal-body">{children}</div>

        {footer && <div className="modal-actions">{footer}</div>}
      </div>
    </div>
  );
}

export default Modal;
