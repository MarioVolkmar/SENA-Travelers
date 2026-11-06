// Fechas como texto 'YYYY-MM-DD' en hora local (sin saltos por zona horaria)

export const WEEKDAYS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

export const MONTHS = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

export const MONTHS_SHORT = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

const pad = (number) => String(number).padStart(2, '0');

export function toKey(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function parseKey(key) {
  if (!key) return null;
  const [year, month, day] = String(key).slice(0, 10).split('-').map(Number);
  if (!year || !month) return null;
  return new Date(year, month - 1, day || 1);
}

export function monthKeyOf(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;
}

export function addDays(date, days) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
}

export function addMonths(date, months) {
  const target = new Date(date.getFullYear(), date.getMonth() + months, 1);
  const lastDay = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate();
  return new Date(target.getFullYear(), target.getMonth(), Math.min(date.getDate(), lastDay));
}

/** 42 días (6 semanas, lunes primero) que cubren el mes de `date`. */
export function monthGrid(date) {
  const first = new Date(date.getFullYear(), date.getMonth(), 1);
  const offset = (first.getDay() + 6) % 7; // lunes = 0
  const start = addDays(first, -offset);
  return Array.from({ length: 42 }, (_, index) => addDays(start, index));
}

export function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function formatDisplayDate(key) {
  const date = parseKey(key);
  if (!date) return '';
  return `${date.getDate()} de ${MONTHS[date.getMonth()]} de ${date.getFullYear()}`;
}

export function formatMonthKey(key) {
  const date = parseKey(key);
  if (!date) return '';
  return `${capitalize(MONTHS[date.getMonth()])} de ${date.getFullYear()}`;
}

export function todayKey() {
  return toKey(new Date());
}
