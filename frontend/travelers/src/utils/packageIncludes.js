// Lo que puede incluir un paquete. Las claves coinciden con PACKAGE_INCLUDE_TYPES del backend.
export const PACKAGE_INCLUDES = [
  { key: 'alojamiento', label: 'Alojamiento', icon: 'bed' },
  { key: 'desayuno', label: 'Desayunos', icon: 'utensils' },
  { key: 'alimentacion', label: 'Alimentación completa', icon: 'utensils' },
  { key: 'transporte', label: 'Transporte terrestre', icon: 'bus' },
  { key: 'vuelos', label: 'Tiquetes aéreos', icon: 'plane' },
  { key: 'traslados', label: 'Traslados aeropuerto–hotel', icon: 'bus' },
  { key: 'tours', label: 'Tours guiados', icon: 'compass' },
  { key: 'actividades', label: 'Actividades y excursiones', icon: 'mountain' },
  { key: 'entradas', label: 'Entradas a parques y museos', icon: 'ticket' },
  { key: 'guia', label: 'Guía turístico', icon: 'users' },
  { key: 'seguro', label: 'Seguro de viaje', icon: 'shield' },
  { key: 'asistencia', label: 'Asistencia 24/7', icon: 'clock' },
];

export const EMPTY_INCLUDES = { tipos: [], otros: [] };

/** Lista para mostrar: primero los del catálogo y luego los escritos a mano. */
export function includeItems(incluye) {
  if (!incluye) return [];
  const known = PACKAGE_INCLUDES.filter((item) => incluye.tipos?.includes(item.key))
    .map((item) => ({ key: item.key, text: item.label, icon: item.icon }));
  const extras = (incluye.otros || []).map((text) => ({ key: `otro-${text}`, text, icon: 'check' }));
  return [...known, ...extras];
}

// "Incluye alojamiento, desayunos y recorrido." -> ["Alojamiento", "Desayunos", "Recorrido"]
export function describedIncludes(description) {
  if (!description) return [];
  const match = description.match(/incluye\s+([^.]+)\./i);
  if (!match) return [];

  // "A, B, C y D con ida y regreso": se separa por comas y solo la primera " y "
  // del último tramo une dos elementos (la de "ida y regreso" no se toca)
  const parts = match[1].split(/,\s*/).map((item) => item.trim().replace(/^y\s+/i, ''));
  const last = parts.pop() || '';
  const joinIndex = last.search(/\s+y\s+/i);

  if (joinIndex > 0 && parts.length > 0) {
    parts.push(last.slice(0, joinIndex), last.slice(joinIndex).replace(/^\s+y\s+/i, ''));
  } else {
    parts.push(last);
  }

  return parts
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => item.charAt(0).toUpperCase() + item.slice(1));
}
