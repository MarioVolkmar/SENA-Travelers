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
