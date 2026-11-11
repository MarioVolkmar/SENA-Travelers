import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { finalPrice, formatCurrency } from '../../utils/format';
import Icon from '../Icon/Icon';
import './DestinationsMap.css';

// Mapa base oscuro de Esri (no requiere llave de API); los nombres van en una capa aparte
const TILES = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
const LABELS = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}';
const ATTRIBUTION = 'Mapa &copy; <a href="https://www.esri.com">Esri</a>, HERE, Garmin, &copy; colaboradores de OpenStreetMap';
const COLOMBIA_CENTER = [4.6, -74.3];
// Colombia completa (con San Andrés y Leticia) y un margen para moverse un poco alrededor
const COLOMBIA_BOUNDS = [[-4.3, -82], [13.5, -66.8]];
const PAN_LIMITS = [[-12, -92], [20, -58]];

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]));
}

/**
 * Mapa de destinos: un pin por ciudad con paquetes activos.
 * Al tocar un destino se abre el catálogo filtrado por esa ciudad.
 */
function DestinationsMap({ packages }) {
  const navigate = useNavigate();
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef({});
  const [active, setActive] = useState(null);

  // Agrupa los paquetes por ciudad (solo las que tienen coordenadas)
  const destinations = useMemo(() => {
    const byCity = new Map();
    packages.forEach((item) => {
      const city = item.city;
      if (!city || city.latitud === null || city.latitud === undefined || city.longitud === null) return;
      const entry = byCity.get(city.id_ciudad) || { city, count: 0, from: Infinity, cover: null };
      entry.count += 1;
      entry.from = Math.min(entry.from, finalPrice(item));
      entry.cover = entry.cover || item.cover;
      byCity.set(city.id_ciudad, entry);
    });
    return [...byCity.values()].sort((a, b) => b.count - a.count || a.city.nombre.localeCompare(b.city.nombre));
  }, [packages]);

  // Crea el mapa una sola vez
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined;

    const map = L.map(containerRef.current, {
      center: COLOMBIA_CENTER,
      zoom: 5,
      minZoom: 4,
      maxZoom: 12,
      // Zoom en cuartos de nivel: el encuadre se ajusta a Colombia sin alejarse de más
      zoomSnap: 0.25,
      zoomDelta: 0.5,
      maxBounds: PAN_LIMITS,
      maxBoundsViscosity: 0.8,
      scrollWheelZoom: false, // no secuestra el scroll de la página
      zoomControl: true,
      attributionControl: true,
    });
    L.tileLayer(TILES, { attribution: ATTRIBUTION, maxZoom: 16 }).addTo(map);
    L.tileLayer(LABELS, { maxZoom: 16, opacity: 0.55 }).addTo(map);
    mapRef.current = map;

    // Con poco zoom los nombres se enciman: solo se muestran al acercarse
    const syncLabels = () => {
      containerRef.current?.classList.toggle('show-labels', map.getZoom() >= 7);
    };
    map.on('zoomend', syncLabels);
    syncLabels();

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Pinta los pines cada vez que cambian los destinos
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    Object.values(markersRef.current).forEach((marker) => marker.remove());
    markersRef.current = {};

    destinations.forEach((entry) => {
      const { city } = entry;
      const icon = L.divIcon({
        className: 'map-pin',
        html: `<span class="map-pin-dot"></span><span class="map-pin-label">${escapeHtml(city.nombre)}<b>${entry.count}</b></span>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });
      const marker = L.marker([Number(city.latitud), Number(city.longitud)], {
        icon,
        keyboard: true,
        title: `${city.nombre}: ${entry.count} ${entry.count === 1 ? 'paquete' : 'paquetes'}`,
        riseOnHover: true,
      });
      marker.on('click', () => setActive(city.id_ciudad));
      marker.on('keypress', (event) => {
        if (event.originalEvent.key === 'Enter') setActive(city.id_ciudad);
      });
      marker.addTo(map);
      markersRef.current[city.id_ciudad] = marker;
    });

    // Encuadra los destinos; sin destinos (o con uno solo) muestra Colombia completa
    const bounds = destinations.length > 1
      ? L.latLngBounds(destinations.map((entry) => [Number(entry.city.latitud), Number(entry.city.longitud)]))
      : L.latLngBounds(COLOMBIA_BOUNDS);
    map.fitBounds(bounds, { padding: [28, 28], maxZoom: 7 });
  }, [destinations]);

  // Resalta el pin elegido y lo centra
  useEffect(() => {
    Object.entries(markersRef.current).forEach(([id, marker]) => {
      marker.getElement()?.classList.toggle('is-active', Number(id) === active);
    });
    const marker = markersRef.current[active];
    if (marker && mapRef.current) {
      mapRef.current.panTo(marker.getLatLng(), { animate: true });
    }
  }, [active, destinations]);

  const selected = destinations.find((entry) => entry.city.id_ciudad === active);

  if (destinations.length === 0) return null;

  return (
    <div className="destinations-map">
      <div className="destinations-map-canvas" ref={containerRef} aria-label="Mapa de destinos de Colombia" role="region" />

      <aside className="destinations-map-panel">
        {selected ? (
          <div className="destinations-map-card">
            {selected.cover && <img src={selected.cover} alt="" />}
            <div className="destinations-map-card-body">
              <p className="eyebrow">{selected.city.departamento}</p>
              <h3>{selected.city.nombre}</h3>
              <p>
                {selected.count} {selected.count === 1 ? 'paquete' : 'paquetes'} · desde{' '}
                <strong>{formatCurrency(selected.from)}</strong>
              </p>
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={() => navigate(`/packages?ciudad=${selected.city.id_ciudad}`)}
              >
                Ver paquetes en {selected.city.nombre}
                <Icon name="arrowRight" size={18} />
              </button>
            </div>
          </div>
        ) : (
          <p className="destinations-map-hint">Toca un destino del mapa o de la lista para ver sus paquetes.</p>
        )}

        <ul className="destinations-map-list">
          {destinations.map((entry) => (
            <li key={entry.city.id_ciudad}>
              <button
                type="button"
                className={entry.city.id_ciudad === active ? 'is-active' : ''}
                aria-pressed={entry.city.id_ciudad === active}
                onClick={() => setActive(entry.city.id_ciudad)}
              >
                <Icon name="pin" size={15} />
                <span>{entry.city.nombre}</span>
                <small>{entry.count}</small>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}

export default DestinationsMap;
