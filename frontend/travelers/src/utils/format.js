const currencyFormatter = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
});

export function formatCurrency(value) {
  return currencyFormatter.format(Number(value || 0));
}

// Las fechas "YYYY-MM-DD" se interpretan en hora local para evitar el desfase de un día
export function formatDate(value) {
  if (!value) return '';

  return parseLocalDate(value)
    .toLocaleDateString('es-CO', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
    .replace('.', '');
}

function parseLocalDate(value) {
  const [year, month, day] = String(value).split('T')[0].split('-').map(Number);
  return new Date(year, month - 1, day);
}

// "4 días · 3 noches"
export function tripLength(start, end) {
  if (!start || !end) return '';

  const days = Math.round((parseLocalDate(end) - parseLocalDate(start)) / 86400000) + 1;
  const nights = Math.max(days - 1, 0);

  const daysText = `${days} ${days === 1 ? 'día' : 'días'}`;
  if (nights === 0) return daysText;

  return `${daysText} · ${nights} ${nights === 1 ? 'noche' : 'noches'}`;
}

// "3 – 6 dic 2026" o "29 dic 2026 – 2 ene 2027"
export function formatDateRange(start, end) {
  if (!start || !end) return '';

  const a = parseLocalDate(start);
  const b = parseLocalDate(end);
  const month = (date) => date.toLocaleDateString('es-CO', { month: 'short' }).replace('.', '');

  if (a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()) {
    return `${a.getDate()} – ${b.getDate()} ${month(b)} ${b.getFullYear()}`;
  }

  return `${a.getDate()} ${month(a)} ${a.getFullYear()} – ${b.getDate()} ${month(b)} ${b.getFullYear()}`;
}

// Todas las fechas entre inicio y fin, en formato "YYYY-MM-DD"
export function datesBetween(start, end) {
  const result = [];
  const current = parseLocalDate(start);
  const last = parseLocalDate(end);

  while (current <= last && result.length < 60) {
    const y = current.getFullYear();
    const m = String(current.getMonth() + 1).padStart(2, '0');
    const d = String(current.getDate()).padStart(2, '0');
    result.push(`${y}-${m}-${d}`);
    current.setDate(current.getDate() + 1);
  }

  return result;
}

export function formatLongDate(value) {
  if (!value) return '';

  const text = parseLocalDate(value).toLocaleDateString('es-CO', {
    weekday: 'long',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function finalPrice(touristPackage) {
  const price = Number(touristPackage.precio || 0);
  const discount = Number(touristPackage.descuento || 0);

  return discount > 0 ? price - (price * discount) / 100 : price;
}

// FastAPI devuelve "detail" como texto o, en errores 422, como lista de objetos
export function getErrorMessage(error, fallback = 'Ocurrió un error inesperado') {
  const detail = error?.response?.data?.detail;

  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('. ');

  return fallback;
}

export const ROLE_ADMIN = 1;
export const ROLE_CLIENT = 2;
export const ROLE_PROVIDER = 3;
