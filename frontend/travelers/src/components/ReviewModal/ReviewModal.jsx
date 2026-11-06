import { useState } from 'react';

import api from '../../api/axiosConfig';
import { getErrorMessage } from '../../utils/format';
import Modal from '../Modal/Modal';
import { StarInput } from '../StarRating/StarRating';

const MAX_LENGTH = 600;

/** Formulario para calificar un viaje ya realizado. */
function ReviewModal({ trip, onClose, onSaved }) {
  const [stars, setStars] = useState(0);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!stars) {
      setError('Elige de 1 a 5 estrellas.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const response = await api.post('/reviews/', {
        reserva_id: trip.reserva_id,
        calificacion: stars,
        comentario: comment.trim() || null,
      });
      onSaved(response.data);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar tu reseña.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title="¿Cómo estuvo tu viaje?"
      subtitle={`${trip.paquete} · ${trip.codigo_reserva}`}
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>Ahora no</button>
          <button type="submit" form="review-form" className="btn btn-primary" disabled={saving}>
            {saving ? 'Publicando...' : 'Publicar reseña'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}
      <form id="review-form" onSubmit={handleSubmit}>
        <StarInput value={stars} onChange={setStars} />
        <div className="field" style={{ marginTop: 18 }}>
          <label htmlFor="review-comment">Cuéntale a otros viajeros (opcional)</label>
          <textarea
            id="review-comment"
            rows={5}
            maxLength={MAX_LENGTH}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="¿Qué te gustó? ¿Qué recomendarías?"
          />
          <span className="field-hint">{comment.length}/{MAX_LENGTH} · Se publica con tu nombre y la inicial de tu apellido.</span>
        </div>
      </form>
    </Modal>
  );
}

export default ReviewModal;
