/**
 * IVA de Colombia. Los precios de Travelers YA lo incluyen (Estatuto del Consumidor):
 * aquí solo se desglosa. Es el mismo cálculo del backend (backend/app/core/taxes.py).
 */
export const IVA_PERCENT = 19;

/** { base, iva } de un valor con IVA incluido; base + iva siempre da el total exacto. */
export function splitIva(total) {
  const cents = Math.round(Number(total || 0) * 100);
  const baseCents = Math.round(cents / (1 + IVA_PERCENT / 100));
  return { base: baseCents / 100, iva: (cents - baseCents) / 100 };
}
