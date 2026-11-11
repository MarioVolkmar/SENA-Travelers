import { useEffect, useRef, useState } from 'react';

import Icon from '../Icon/Icon';
import './ShareButton.css';

/**
 * Botón "Compartir" con un menú: WhatsApp, Facebook, correo y copiar enlace.
 * En celulares que lo permiten agrega "Más opciones" (el menú para compartir del sistema).
 */
function ShareButton({ title, text, url = window.location.href }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const wrapRef = useRef(null);
  const canNativeShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function';

  // Cierra el menú al tocar fuera o con Escape
  useEffect(() => {
    if (!open) return undefined;
    const handlePointer = (event) => {
      if (!wrapRef.current?.contains(event.target)) setOpen(false);
    };
    const handleKey = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', handlePointer);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('pointerdown', handlePointer);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open]);

  const message = `${text || title} ${url}`;
  const options = [
    { key: 'whatsapp', label: 'WhatsApp', icon: 'chat', href: `https://wa.me/?text=${encodeURIComponent(message)}` },
    { key: 'facebook', label: 'Facebook', icon: 'globe', href: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}` },
    {
      key: 'correo',
      label: 'Correo',
      icon: 'mail',
      href: `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(message)}`,
    },
  ];

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // Navegadores sin permiso de portapapeles: copia con un campo temporal
      const field = document.createElement('textarea');
      field.value = url;
      document.body.appendChild(field);
      field.select();
      document.execCommand('copy');
      field.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const nativeShare = async () => {
    setOpen(false);
    try {
      await navigator.share({ title, text, url });
    } catch {
      // El usuario cerró el menú del sistema: no pasa nada
    }
  };

  return (
    <div className="share" ref={wrapRef}>
      <button
        type="button"
        className="share-button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <Icon name="share" size={18} />
        <span>Compartir</span>
      </button>

      {open && (
        <div className="share-menu" role="menu" aria-label="Compartir paquete">
          {options.map((option) => (
            <a
              key={option.key}
              role="menuitem"
              className="share-option"
              href={option.href}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setOpen(false)}
            >
              <Icon name={option.icon} size={18} />
              {option.label}
            </a>
          ))}
          <button type="button" role="menuitem" className="share-option" onClick={copyLink}>
            <Icon name={copied ? 'check' : 'link'} size={18} />
            {copied ? '¡Enlace copiado!' : 'Copiar enlace'}
          </button>
          {canNativeShare && (
            <button type="button" role="menuitem" className="share-option" onClick={nativeShare}>
              <Icon name="share" size={18} />
              Más opciones…
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default ShareButton;
