import { useEffect, useState } from 'react';

import api from '../api/axiosConfig';

/**
 * Límites razonables para precios y cantidades (en pesos colombianos).
 * La fuente de verdad es el backend (backend/app/core/constants.py → LIMITS), que los entrega en
 * GET /config/limits. Estos valores solo se usan mientras llega la respuesta o si no se puede consultar.
 */
export const LIMITS = {
  packagePrice: { min: 10_000, max: 20_000_000 },   // precio por persona de un paquete
  productCost: { min: 1_000, max: 10_000_000 },     // costo de un producto
  packageSlots: { min: 1, max: 100 },               // cupo máximo de personas
  packageDiscount: { min: 0, max: 90 },             // descuento en %
  packageProductQuantity: { min: 1, max: 30 },      // cantidad de un producto dentro del paquete
  reservationTravelers: { min: 1, max: 10 },        // viajeros por reserva
  couponPercent: { min: 1, max: 90 },               // cupón por porcentaje
  couponValue: { min: 1_000, max: 5_000_000 },      // cupón por valor fijo
  couponUses: { min: 1, max: 10_000 },              // usos máximos de un cupón
  couponMinPurchase: { min: 0, max: 50_000_000 },   // compra mínima para usar el cupón
  providerPaymentDays: { min: 0, max: 180 },        // días para pagar a proveedores después del viaje
  reminderDays: { min: 1, max: 30 },                // días de anticipación del recordatorio
  freeCancellationDays: { min: 0, max: 90 },        // días de cancelación gratis
  cancellationPenalty: { min: 0, max: 100 },        // penalidad por cancelación tardía (%)
  paymentHours: { min: 1, max: 168 },               // horas para pagar una reserva pendiente
  providerPaymentDay: { min: 1, max: 28 },          // día del mes en que se pagan las órdenes aprobadas
};

let request = null;
const listeners = new Set();

/** Pide los límites al backend una sola vez y los copia sobre LIMITS. */
export function loadLimits() {
  if (!request) {
    request = api.get('/config/limits')
      .then((response) => {
        Object.entries(response.data?.limites || {}).forEach(([key, range]) => {
          if (range && Number.isFinite(range.min) && Number.isFinite(range.max)) LIMITS[key] = range;
        });
        listeners.forEach((listener) => listener());
      })
      .catch(() => {
        request = null; // se reintenta la próxima vez; mientras tanto quedan los de respaldo
      });
  }
  return request;
}

/** Los límites actuales; el componente se vuelve a pintar cuando llegan los del backend. */
export function useLimits() {
  const [, setVersion] = useState(0);

  useEffect(() => {
    const listener = () => setVersion((current) => current + 1);
    listeners.add(listener);
    loadLimits();
    return () => listeners.delete(listener);
  }, []);

  return LIMITS;
}

/** ¿El valor escrito es un entero dentro del rango? (vacío cuenta como no válido) */
export function inRange(value, { min, max }) {
  if (value === '' || value === null || value === undefined) return false;
  const number = Number(value);
  return Number.isInteger(number) && number >= min && number <= max;
}

/** El valor llevado al rango, para los textos de ejemplo mientras se escribe. */
export function clampToRange(value, { min, max }) {
  return Math.min(Math.max(Math.round(Number(value) || 0), min), max);
}
