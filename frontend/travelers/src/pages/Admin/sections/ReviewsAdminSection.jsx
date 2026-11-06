import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import Pagination, { usePagination } from '../../../components/Pagination/Pagination';
import { Stars } from '../../../components/StarRating/StarRating';
import Toast from '../../../components/Toast/Toast';
import { formatDate } from '../../../utils/format';
import { matches, useAdminAction } from '../adminShared';

const FILTERS = [
  { key: '', label: 'Todas' },
  { key: 'visible', label: 'Visibles' },
  { key: 'oculta', label: 'Ocultas' },
  { key: 'bajas', label: '1–2 estrellas' },
];

function ReviewsAdminSection() {
  const [reviews, setReviews] = useState(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const { busy, message, error, run } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const response = await api.get('/reviews/');
    setReviews(response.data);
  }, []);

  useEffect(() => {
    load().catch(() => setReviews([]));
  }, [load]);

  const visible = (reviews || [])
    .filter((review) => {
      if (filter === 'bajas') return review.calificacion <= 2;
      return !filter || review.estado === filter;
    })
    .filter((review) => !query || matches(review.paquete, query) || matches(review.autor, query) || matches(review.comentario, query));
  const pager = usePagination(visible, [query, filter]);

  const toggle = async (review) => {
    const hide = review.estado === 'visible';
    const accepted = await confirm({
      title: hide ? 'Ocultar reseña' : 'Mostrar reseña',
      subtitle: `${review.autor} · ${review.paquete}`,
      message: hide
        ? 'Dejará de verse en la página del paquete y no contará en el promedio. El viajero la seguirá viendo como oculta.'
        : 'Volverá a publicarse en la página del paquete.',
      confirmLabel: hide ? 'Ocultar' : 'Mostrar',
      tone: hide ? 'danger' : 'primary',
    });
    if (!accepted) return;
    const { ok } = await run(
      () => api.patch(`/reviews/${review.id_resena}/status`, { estado: hide ? 'oculta' : 'visible' }),
      hide ? 'Reseña ocultada.' : 'Reseña publicada de nuevo.'
    );
    if (ok) await load();
  };

  if (!reviews) return <p className="page-status">Cargando reseñas...</p>;

  const shown = reviews.filter((review) => review.estado === 'visible');
  const average = shown.length ? shown.reduce((sum, review) => sum + review.calificacion, 0) / shown.length : 0;

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Reseñas</h1>
          <p>Lo que opinan los viajeros. Puedes ocultar las que no cumplan las normas.</p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="admin-summary">
        <div className="admin-stat highlight">
          <span>Calificación promedio</span>
          <strong>{shown.length ? average.toFixed(1) : '—'}</strong>
        </div>
        <div className="admin-stat"><span>Reseñas publicadas</span><strong>{shown.length}</strong></div>
        <div className="admin-stat warning"><span>De 1 o 2 estrellas</span><strong>{reviews.filter((r) => r.calificacion <= 2).length}</strong></div>
      </div>

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por paquete, viajero o texto" aria-label="Buscar reseñas" />
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar reseñas">
            {FILTERS.map((option) => (
              <button key={option.key} type="button" className="chip" aria-pressed={filter === option.key} onClick={() => setFilter(option.key)}>
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reseña</th>
                <th>Paquete</th>
                <th>Fecha</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {pager.items.map((review) => (
                <tr key={review.id_resena}>
                  <td className="admin-review-cell">
                    <Stars value={review.calificacion} size={14} />
                    <span className="admin-strong"> {review.autor}</span>
                    {review.comentario && <p className="admin-review-text">{review.comentario}</p>}
                  </td>
                  <td>{review.paquete}</td>
                  <td className="admin-muted">{formatDate(review.fecha)}</td>
                  <td><span className={`badge badge-${review.estado === 'visible' ? 'activo' : 'inactivo'}`}>{review.estado}</span></td>
                  <td>
                    <div className="admin-actions">
                      <IconButton
                        icon={review.estado === 'visible' ? 'ban' : 'eye'}
                        label={review.estado === 'visible' ? 'Ocultar' : 'Mostrar'}
                        variant={review.estado === 'visible' ? 'danger' : 'success'}
                        disabled={busy}
                        onClick={() => toggle(review)}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {visible.length === 0 && (
            <p className="admin-empty">{reviews.length === 0 ? 'Aún no hay reseñas.' : 'No hay reseñas con esos filtros.'}</p>
          )}
        </div>
        <Pagination {...pager} label="reseñas" />
      </div>
      {dialog}
    </>
  );
}

export default ReviewsAdminSection;
