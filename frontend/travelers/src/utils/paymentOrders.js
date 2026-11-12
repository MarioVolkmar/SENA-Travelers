// Estados de las órdenes de pago a proveedores
export const ORDER_STATUS_LABELS = {
  pendiente: 'Pendiente',
  aprobada: 'Aprobada',
  pagada: 'Pagada',
  anulada: 'Anulada',
};

// Reutiliza los colores de los badges existentes
export const ORDER_BADGE = {
  pendiente: 'pendiente',
  aprobada: 'activo',
  pagada: 'confirmada',
  anulada: 'cancelada',
};

function parseDay(value) {
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day);
}

/** Días entre hoy y una fecha "AAAA-MM-DD" (negativo si ya pasó). */
export function daysUntil(value) {
  const today = new Date(new Date().toDateString());
  return Math.round((parseDay(value) - today) / 86400000);
}

/**
 * Qué fecha importa de una orden y qué tan urgente es:
 * - pendiente: el plazo para que un administrador la apruebe (fecha_vencimiento)
 * - aprobada: la fecha de pago programada
 * Niveles: vencida (rojo), urgente ≤ 2 días (naranja), pronto ≤ 7 días (amarillo), normal.
 */
export function orderUrgency(order) {
  let date = null;
  let label = '';
  if (order.estado === 'pendiente') {
    date = order.fecha_vencimiento;
    label = 'Aprobar antes del';
  } else if (order.estado === 'aprobada') {
    date = order.fecha_pago_programada || order.fecha_vencimiento;
    label = 'Se paga el';
  }
  if (!date) return { level: 'closed', date: null, days: null, label: '', sortKey: Number.MAX_SAFE_INTEGER };

  const days = daysUntil(date);
  let level = 'normal';
  if (days < 0) level = 'overdue';
  else if (days <= 2) level = 'urgent';
  else if (days <= 7) level = 'soon';
  return { level, date, days, label, sortKey: days };
}

/** "vencida hace 3 días", "vence hoy", "faltan 5 días". */
export function daysLabel(days) {
  if (days === null || days === undefined) return '';
  if (days < 0) return `vencida hace ${-days} ${days === -1 ? 'día' : 'días'}`;
  if (days === 0) return 'hoy';
  return `faltan ${days} ${days === 1 ? 'día' : 'días'}`;
}
