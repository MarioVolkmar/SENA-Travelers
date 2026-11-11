import { useEffect } from 'react';

const SITE_NAME = 'Travelers';
const DEFAULT_TITLE = 'Travelers · Paquetes turísticos por Colombia';

/**
 * Pone el título de la pestaña del navegador: "Mis reservas · Travelers".
 * Sin título (o mientras carga) deja el título general del sitio.
 */
export default function usePageTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} · ${SITE_NAME}` : DEFAULT_TITLE;
  }, [title]);
}
