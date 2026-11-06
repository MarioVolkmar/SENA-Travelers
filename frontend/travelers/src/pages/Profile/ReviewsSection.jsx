import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Icon from '../../components/Icon/Icon';
import ReviewModal from '../../components/ReviewModal/ReviewModal';
import { Stars } from '../../components/StarRating/StarRating';
import Toast from '../../components/Toast/Toast';
import { formatDate } from '../../utils/format';

/** Viajes por calificar y reseñas ya publicadas. */
function ReviewsSection() {
  const [pending, setPending] = useState(null);
  const [mine, setMine] = useState([]);
  const [reviewing, setReviewing] = useState(null);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    const [pendingResponse, mineResponse] = await Promise.all([
      api.get('/reviews/me/pending').catch(() => ({ data: [] })),
      api.get('/reviews/me').catch(() => ({ data: [] })),
    ]);
    setPending(pendingResponse.data);
    setMine(mineResponse.data);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (!pending) return <p className="page-status">Cargando reseñas...</p>;

  return (
    <>
      <div className="account-panel">
        <h2>Viajes por calificar</h2>
        {pending.length === 0 ? (
          <p className="account-muted">
            Cuando regreses de un viaje podrás calificarlo aquí y ayudar a otros viajeros a elegir.
          </p>
        ) : (
          <ul className="account-rows">
            {pending.map((trip) => (
              <li key={trip.reserva_id} className="account-row">
                <div>
                  <p className="account-row-label">{trip.codigo_reserva} · viajaste el {formatDate(trip.fecha_reserva)}</p>
                  <p className="account-row-value">{trip.paquete}</p>
                </div>
                <button type="button" className="btn btn-primary btn-small" onClick={() => setReviewing(trip)}>
                  <Icon name="star" size={16} /> Calificar
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="account-panel">
        <h2>Mis reseñas</h2>
        {mine.length === 0 ? (
          <p className="account-muted">Todavía no has publicado reseñas.</p>
        ) : (
          <ul className="account-reviews">
            {mine.map((review) => (
              <li key={review.id_resena}>
                <div className="account-review-header">
                  <Link to={`/packages/${review.paquete_id}`}>{review.paquete}</Link>
                  <Stars value={review.calificacion} size={15} />
                </div>
                {review.comentario && <p>{review.comentario}</p>}
                <span className="account-muted">
                  {formatDate(review.fecha)}
                  {review.estado === 'oculta' && ' · Oculta por el equipo de Travelers'}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {reviewing && (
        <ReviewModal
          trip={reviewing}
          onClose={() => setReviewing(null)}
          onSaved={async () => {
            setReviewing(null);
            setNotice('¡Gracias! Tu reseña ya está publicada.');
            await load();
          }}
        />
      )}
      <Toast text={notice} />
    </>
  );
}

export default ReviewsSection;
