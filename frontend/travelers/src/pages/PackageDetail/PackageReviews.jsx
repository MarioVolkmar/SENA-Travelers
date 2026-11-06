import { useEffect, useState } from 'react';

import api from '../../api/axiosConfig';
import Avatar from '../../components/Avatar/Avatar';
import { Stars } from '../../components/StarRating/StarRating';
import { formatDate } from '../../utils/format';

const PREVIEW = 4;

/** Reseñas públicas del paquete: promedio, distribución y comentarios. */
function PackageReviews({ packageId, onSummary }) {
  const [data, setData] = useState(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    api.get(`/reviews/package/${packageId}`)
      .then((response) => {
        setData(response.data);
        onSummary?.(response.data);
      })
      .catch(() => setData({ promedio: 0, total: 0, distribucion: {}, resenas: [] }));
  }, [packageId, onSummary]);

  if (!data) return null;

  const visible = showAll ? data.resenas : data.resenas.slice(0, PREVIEW);

  return (
    <section className="detail-reviews" aria-labelledby="reviews-title">
      <h2 id="reviews-title">Opiniones de viajeros</h2>

      {data.total === 0 ? (
        <p className="detail-reviews-empty">
          Este paquete todavía no tiene reseñas. Quienes viajen podrán calificarlo después de su viaje.
        </p>
      ) : (
        <>
          <div className="detail-reviews-summary">
            <div className="detail-reviews-score">
              <strong>{data.promedio.toFixed(1)}</strong>
              <Stars value={data.promedio} size={18} />
              <span>{data.total} {data.total === 1 ? 'reseña' : 'reseñas'}</span>
            </div>
            <ul className="detail-reviews-bars" aria-label="Distribución de calificaciones">
              {[5, 4, 3, 2, 1].map((stars) => {
                const count = data.distribucion[String(stars)] || 0;
                const percent = data.total ? Math.round((count / data.total) * 100) : 0;
                return (
                  <li key={stars}>
                    <span>{stars} ★</span>
                    <span className="detail-reviews-bar"><span style={{ width: `${percent}%` }} /></span>
                    <span>{count}</span>
                  </li>
                );
              })}
            </ul>
          </div>

          <ul className="detail-reviews-list">
            {visible.map((review) => (
              <li key={review.id_resena} className="detail-review">
                <div className="detail-review-header">
                  <Avatar user={{ nombre: review.autor, foto_url: review.autor_foto }} size={40} />
                  <div>
                    <strong>{review.autor}</strong>
                    <span>{formatDate(review.fecha)}</span>
                  </div>
                  <Stars value={review.calificacion} size={15} />
                </div>
                {review.comentario && <p>{review.comentario}</p>}
              </li>
            ))}
          </ul>

          {data.resenas.length > PREVIEW && (
            <button type="button" className="btn btn-secondary" onClick={() => setShowAll((value) => !value)}>
              {showAll ? 'Ver menos' : `Ver las ${data.resenas.length} reseñas`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

export default PackageReviews;
