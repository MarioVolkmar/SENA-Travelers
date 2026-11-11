import { includeItems } from './packageIncludes';

/**
 * Buscador del catálogo.
 *
 * Las descripciones no siempre usan la palabra que escribe el viajero: nadie escribió
 * "playa" en San Andrés, pero sí "isla" y "Caribe". Por eso cada búsqueda se amplía con
 * palabras relacionadas (TEMAS) y se compara por palabras, aceptando plurales.
 */

/** Minúsculas y sin tildes, para que "cafe" encuentre "Café". */
export function normalize(text) {
  return String(text || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

// Tema → palabras relacionadas (ya normalizadas). Las de varias palabras se buscan como frase.
const THEMES = {
  playa: ['playa', 'mar', 'caribe', 'isla', 'costa', 'tayrona', 'rosario', 'bahia', 'lancha', 'buceo',
    'snorkel', 'cartagena', 'santa marta', 'san andres', 'barranquilla'],
  mar: ['mar', 'caribe', 'isla', 'costa', 'lancha', 'playa'],
  caribe: ['caribe', 'mar', 'isla', 'costa', 'cartagena', 'santa marta', 'san andres', 'barranquilla'],
  isla: ['isla', 'san andres', 'rosario'],
  costa: ['costa', 'caribe', 'mar', 'playa', 'cartagena', 'santa marta', 'san andres', 'barranquilla'],
  cafe: ['cafe', 'cafetero', 'cafetera', 'finca', 'cocora', 'salento', 'jardin'],
  montana: ['montana', 'valle', 'cocora', 'monserrate', 'paramo', 'piedra del penol', 'jardin', 'salento'],
  aventura: ['aventura', 'rafting', 'actividad', 'parapente', 'caminata', 'buceo', 'san gil', 'extremo'],
  naturaleza: ['naturaleza', 'selva', 'amazonas', 'parque', 'valle', 'fluvial', 'rio', 'tayrona', 'cocora'],
  selva: ['selva', 'amazonas', 'leticia', 'fluvial'],
  rio: ['rio', 'fluvial', 'rafting'],
  cultura: ['cultura', 'cultural', 'historia', 'historico', 'colonial', 'candelaria', 'museo', 'carnaval',
    'prehispanico', 'arquitectura'],
  historia: ['historia', 'historico', 'colonial', 'candelaria', 'murallas', 'prehispanico', 'museo'],
  colonial: ['colonial', 'historico', 'villa de leyva', 'barichara', 'raquira', 'candelaria', 'murallas'],
  pueblo: ['pueblo', 'colonial', 'guatape', 'barichara', 'raquira', 'jardin', 'salento', 'villa de leyva'],
  fiesta: ['fiesta', 'carnaval'],
  ciudad: ['ciudad', 'urbano', 'bogota', 'medellin', 'cartagena', 'barranquilla'],
  descanso: ['descanso', 'descansa', 'relax', 'isla', 'playa', 'mar'],
};

/** "playas" → "playa", "islas" → "isla", "montañas" → "montana". */
function singular(word) {
  if (word.length > 4 && word.endsWith('es') && !word.endsWith('ces')) return word.slice(0, -2);
  if (word.length > 3 && word.endsWith('s')) return word.slice(0, -1);
  return word;
}

function themeFor(word) {
  return THEMES[word] || THEMES[singular(word)] || null;
}

/** Todo el texto en el que busca: nombre, descripción, ciudad, departamento y qué incluye. */
export function searchableText(item) {
  const includes = includeItems(item.incluye).map((include) => include.text);
  return normalize([item.nombre, item.descripcion, item.city?.nombre, item.city?.departamento, ...includes].join(' '));
}

/** ¿Aparece el término en el texto? Por palabras: "mar" no encuentra "marta", "isla" sí encuentra "islas". */
function containsTerm(text, words, term) {
  if (term.includes(' ')) return text.includes(term);
  const base = singular(term);
  return words.some((word) => word === term || word === base || singular(word) === base
    || (term.length >= 5 && word.startsWith(term))); // "cafeter" → "cafetera", "cultur" → "cultural"
}

// Temas que describen el tipo de viaje (para recomendar paquetes parecidos)
const EXPERIENCE_THEMES = ['playa', 'cafe', 'montana', 'aventura', 'naturaleza', 'selva', 'cultura', 'colonial', 'pueblo', 'fiesta', 'ciudad'];

/** Temas que tiene un paquete: { "playa", "cultura", ... }. */
export function packageThemes(item) {
  return new Set(EXPERIENCE_THEMES.filter((theme) => buildSearch(theme).matches(item)));
}

/**
 * Paquetes parecidos a uno: comparten temas (playa, café, aventura...), región o precio.
 * Devuelve los `limit` con más puntos, sin incluir el mismo paquete.
 */
export function relatedPackages(current, packages, limit = 3) {
  const themes = packageThemes(current);
  const price = Number(current.precio) || 0;

  return packages
    .filter((item) => item.id_paquete_turistico !== current.id_paquete_turistico)
    .map((item) => {
      const shared = [...packageThemes(item)].filter((theme) => themes.has(theme)).length;
      const sameCity = item.ciudad_id === current.ciudad_id;
      const sameRegion = item.city?.departamento && item.city.departamento === current.city?.departamento;
      const similarPrice = price > 0 && Math.abs(Number(item.precio) - price) / price <= 0.35;
      const score = shared * 3 + (sameCity ? 4 : sameRegion ? 2 : 0) + (similarPrice ? 1 : 0)
        + (item.rating ? item.rating.promedio / 5 : 0); // en empate, mejor calificado primero
      return { item, score };
    })
    .filter(({ score }) => score >= 1)
    .sort((a, b) => b.score - a.score || a.item.fecha_inicio.localeCompare(b.item.fecha_inicio))
    .slice(0, limit)
    .map(({ item }) => item);
}

/**
 * Prepara una búsqueda: devuelve la función que dice si un paquete coincide y las
 * palabras relacionadas que se agregaron (para mostrarlas debajo del buscador).
 * Cada palabra escrita debe coincidir (ella o una relacionada) en cualquier orden.
 */
export function buildSearch(query) {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  const groups = words.map((word) => [...new Set([word, ...(themeFor(word) || [])])]);
  const related = [...new Set(groups.flatMap((group) => group.slice(1)))];

  const matches = (item) => {
    if (groups.length === 0) return true;
    const text = searchableText(item);
    const textWords = text.split(/[^a-z0-9ñ]+/).filter(Boolean);
    return groups.every((group) => group.some((term) => containsTerm(text, textWords, term)));
  };

  return { matches, related, active: groups.length > 0 };
}
