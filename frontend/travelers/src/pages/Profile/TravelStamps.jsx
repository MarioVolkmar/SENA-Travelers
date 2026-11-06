import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../../api/axiosConfig';
import fallbackImage from '../../assets/images/fondo.png';
import Icon from '../../components/Icon/Icon';
import usePackageCatalog from '../../hooks/usePackageCatalog';

/**
 * Sellos de viaje: un sello por cada destino del catálogo.
 * Se gana al tener una reserva confirmada (pagada) en ese destino.
 */
function TravelStamps({ hasClientProfile }) {
  const { packages, loading } = usePackageCatalog();
  const [earnedCities, setEarnedCities] = useState(new Set());

  useEffect(() => {
    if (!hasClientProfile) return;

    const loadEarned = async () => {
      try {
        const reservations = await api.get('/reservations/me');
        const confirmed = reservations.data.filter((item) => item.estado === 'confirmada');
        const packageIds = [...new Set(confirmed.map((item) => item.id_paquete_turistico))];

        const responses = await Promise.all(
          packageIds.map((id) => api.get(`/packages/${id}`).catch(() => null))
        );

        setEarnedCities(new Set(responses.filter(Boolean).map((response) => response.data.ciudad_id)));
      } catch {
        setEarnedCities(new Set());
      }
    };

    loadEarned();
  }, [hasClientProfile]);

  // Un sello por ciudad, con la portada del primer paquete de esa ciudad
  const stamps = [];
  const seen = new Set();

  packages.forEach((item) => {
    if (!item.city || seen.has(item.ciudad_id)) return;
    seen.add(item.ciudad_id);
    stamps.push({ id: item.ciudad_id, city: item.city.nombre, image: item.cover });
  });

  stamps.sort((a, b) => Number(earnedCities.has(b.id)) - Number(earnedCities.has(a.id)));

  const earnedCount = stamps.filter((stamp) => earnedCities.has(stamp.id)).length;

  if (loading || stamps.length === 0) return null;

  return (
    <section className="stamps">
      <div className="stamps-header">
        <div>
          <h2>Tus sellos de viaje</h2>
          <p>
            {earnedCount} de {stamps.length} destinos · cada viaje confirmado te da un sello.
          </p>
        </div>
        <Link to="/packages" className="btn btn-outline">
          {earnedCount === 0 ? 'Ganar mi primer sello' : 'Ganar más sellos'}
        </Link>
      </div>

      <ul className="stamps-grid">
        {stamps.map((stamp) => {
          const earned = earnedCities.has(stamp.id);

          return (
            <li key={stamp.id} className={`stamp ${earned ? 'is-earned' : ''}`}>
              <span className="stamp-image">
                <img
                  src={stamp.image || fallbackImage}
                  alt=""
                  loading="lazy"
                  onError={(event) => { event.currentTarget.src = fallbackImage; }}
                />
                {earned && (
                  <span className="stamp-check" aria-hidden="true">
                    <Icon name="check" size={16} strokeWidth={2.4} />
                  </span>
                )}
              </span>
              <span className="stamp-city">{stamp.city}</span>
              <span className="visually-hidden">{earned ? 'Sello obtenido' : 'Sello pendiente'}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export default TravelStamps;
