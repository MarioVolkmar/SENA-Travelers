import { useEffect, useLayoutEffect, useState } from 'react';

/**
 * Posición fija de un panel flotante debajo (o encima, si no cabe) de su botón.
 * Se recalcula con scroll y cambio de tamaño, así funciona también dentro de modales.
 */
export function useFloatingPosition(open, anchorRef, preferredHeight = 320, align = 'start') {
  const [style, setStyle] = useState(null);

  useLayoutEffect(() => {
    if (!open) return undefined;

    const update = () => {
      const anchor = anchorRef.current;
      if (!anchor) return;
      const rect = anchor.getBoundingClientRect();
      const gap = 8;
      const spaceBelow = window.innerHeight - rect.bottom - gap;
      const spaceAbove = rect.top - gap;
      const above = spaceBelow < Math.min(preferredHeight, 220) && spaceAbove > spaceBelow;
      const maxHeight = Math.max(160, Math.min(preferredHeight, (above ? spaceAbove : spaceBelow) - 8));
      const minWidth = rect.width;
      const left = align === 'end'
        ? Math.max(8, rect.right - Math.max(minWidth, 0))
        : Math.min(rect.left, window.innerWidth - Math.max(minWidth, 240) - 8);

      setStyle({
        position: 'fixed',
        left: Math.max(8, left),
        minWidth,
        maxHeight,
        ...(above
          ? { bottom: window.innerHeight - rect.top + gap }
          : { top: rect.bottom + gap }),
      });
    };

    update();
    window.addEventListener('resize', update);
    window.addEventListener('scroll', update, true);
    return () => {
      window.removeEventListener('resize', update);
      window.removeEventListener('scroll', update, true);
    };
  }, [open, anchorRef, preferredHeight, align]);

  return open ? style || { position: 'fixed', visibility: 'hidden' } : null;
}

/** Cierra el panel al hacer clic fuera del botón y del panel. */
export function useOutsideClose(open, refs, onClose) {
  useEffect(() => {
    if (!open) return undefined;
    const handle = (event) => {
      if (refs.some((ref) => ref.current?.contains(event.target))) return;
      onClose();
    };
    document.addEventListener('mousedown', handle);
    document.addEventListener('touchstart', handle);
    return () => {
      document.removeEventListener('mousedown', handle);
      document.removeEventListener('touchstart', handle);
    };
  }, [open, refs, onClose]);
}
