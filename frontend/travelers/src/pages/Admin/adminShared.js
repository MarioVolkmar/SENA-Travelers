import { useCallback, useState } from 'react';

import { getErrorMessage } from '../../utils/format';

export const ROLE_NAMES = { 1: 'Administrador', 2: 'Cliente', 3: 'Proveedor' };

export const RESERVATION_STATUSES = ['pendiente', 'confirmada', 'cancelada'];

export const PAYMENT_STATUS_LABELS = {
  aprobado: 'Aprobado',
  rechazado: 'Rechazado',
  cancelado: 'Cancelado',
  reembolsado: 'Reembolsado',
  reembolso_parcial: 'Reembolso parcial',
};

/**
 * Ejecuta acciones de la consola (guardar, activar, borrar...) y maneja
 * el estado "ocupado" y los mensajes de éxito o error.
 */
export function useAdminAction() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const clear = useCallback(() => {
    setMessage('');
    setError('');
  }, []);

  const run = useCallback(async (request, successText, fallback = 'No fue posible completar la acción.') => {
    setBusy(true);
    setMessage('');
    setError('');

    try {
      const result = await request();
      if (successText) setMessage(successText);
      return { ok: true, result };
    } catch (requestError) {
      setError(getErrorMessage(requestError, fallback));
      return { ok: false, error: requestError };
    } finally {
      setBusy(false);
    }
  }, []);

  return { busy, message, error, run, clear, setError };
}

export function matches(text, query) {
  return String(text || '').toLowerCase().includes(query.trim().toLowerCase());
}
