import { useEffect, useState } from 'react';

import api from '../api/axiosConfig';

// Ícono de cada tipo del catálogo del backend (GET /products/types)
export const PRODUCT_TYPE_ICONS = {
  hospedaje: 'bed',
  alimentacion: 'utensils',
  transporte: 'bus',
  tour: 'compass',
  actividad: 'mountain',
  entrada: 'ticket',
  seguro: 'shield',
  otro: 'sparkle',
};

export function productTypeIcon(key) {
  return PRODUCT_TYPE_ICONS[key] || 'sparkle';
}

// Nombre visible de un tipo; los valores antiguos (p. ej. "viaje") se muestran capitalizados
export function productTypeLabel(types, key) {
  const found = types.find((type) => type.clave === key);
  if (found) return found.nombre;
  return key ? key.charAt(0).toUpperCase() + key.slice(1) : '';
}

// Unidades de cobro (GET /products/units). Respaldo local por si la API no responde.
const FALLBACK_UNITS = [
  { clave: 'persona', nombre: 'Por persona' },
  { clave: 'noche', nombre: 'Por persona por noche' },
  { clave: 'dia', nombre: 'Por persona por día' },
  { clave: 'servicio', nombre: 'Por servicio (grupo)' },
];

const SHORT_UNIT = { persona: 'por persona', noche: 'por noche', dia: 'por día', servicio: 'por servicio' };

export function unitShortLabel(key) {
  return SHORT_UNIT[key] || 'por persona';
}

export function useProductUnits() {
  const [units, setUnits] = useState(FALLBACK_UNITS);

  useEffect(() => {
    api.get('/products/units').then((response) => setUnits(response.data)).catch(() => {});
  }, []);

  return units;
}

export function useProductTypes() {
  const [types, setTypes] = useState([]);

  useEffect(() => {
    api.get('/products/types').then((response) => setTypes(response.data)).catch(() => setTypes([]));
  }, []);

  return types;
}
