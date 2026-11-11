import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import bannerImage from '../../assets/images/banner.jpg';
import fallbackImage from '../../assets/images/fondo.png';
import Icon from '../../components/Icon/Icon';
import PageHero from '../../components/PageHero/PageHero';
import ReviewModal from '../../components/ReviewModal/ReviewModal';
import Toast from '../../components/Toast/Toast';
import { downloadFile } from '../../utils/download';
import { formatCurrency, formatDate, getErrorMessage } from '../../utils/format';

import './Reservations.css';
import usePageTitle from '../../hooks/usePageTitle';
import { PageSkeleton } from '../../components/Skeleton/Skeleton';

const PAYMENT_METHODS = ['Tarjeta de crédito', 'Tarjeta débito', 'PSE', 'Nequi'];

const STATUS_LABELS = {
  pendiente: 'Pendiente de pago',
  confirmada: 'Confirmada',
  cancelada: 'Cancelada',
};

const PAYMENT_STATUS_LABELS = {
  aprobado: 'Pagado',
  reembolsado: 'Reembolsado',
  reembolso_parcial: 'Reembolso parcial',
};

function parseDate(value) {
  const [year, month, day] = value.split('T')[0].split('-').map(Number);
  return new Date(year, month - 1, day);
}

function startOfToday() {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

// Pasos completados de la barra de progreso: reservada → pagada → viaje
function completedSteps(reservation) {
  if (reservation.estado === 'pendiente') return 1;
  if (reservation.estado !== 'confirmada') return 0;

  return parseDate(reservation.fecha_reserva) <= startOfToday() ? 3 : 2;
}

// Último día de cancelación gratuita según la política del backend
function freeCancellationUntil(reservation, policy) {
  if (!policy) return null;

  const deadline = parseDate(reservation.fecha_reserva);
  deadline.setDate(deadline.getDate() - policy.dias_sin_penalidad);
  return deadline;
}

function canStillCancel(reservation) {
  return ['pendiente', 'confirmada'].includes(reservation.estado)
    && parseDate(reservation.fecha_reserva) > startOfToday();
}

function formatShortDate(date) {
  return date.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' }).replace('.', '');
}

function Reservations() {
  usePageTitle('Mis reservas');
  const location = useLocation();

  const [reservations, setReservations] = useState([]);
  const [payments, setPayments] = useState({});
  const [packages, setPackages] = useState({});
  const [covers, setCovers] = useState({});
  const [loading, setLoading] = useState(true);
  const [needsProfile, setNeedsProfile] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState(
    location.state?.createdCode
      ? `Reserva ${location.state.createdCode} creada. Realiza el pago para confirmarla.`
      : ''
  );

  const [policy, setPolicy] = useState(null);
  const [cancelling, setCancelling] = useState(null); // { reservation, preview }

  const [payingReservation, setPayingReservation] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState(PAYMENT_METHODS[0]);
  const [actionLoading, setActionLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [pendingReviews, setPendingReviews] = useState({});
  const [reviewing, setReviewing] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [notice, setNotice] = useState({ text: '', tone: 'success' });
  const [stripe, setStripe] = useState({ enabled: false, test_mode: true });
  const [searchParams, setSearchParams] = useSearchParams();
  const confirmedSession = useRef(null);

  // ¿Está configurado Stripe en el backend? Si no, se usa el pago simulado
  useEffect(() => {
    api.get('/payments/stripe/config')
      .then((response) => setStripe(response.data))
      .catch(() => setStripe({ enabled: false, test_mode: true }));
  }, []);

  const loadPendingReviews = useCallback(() => {
    api.get('/reviews/me/pending')
      .then((response) => setPendingReviews(Object.fromEntries(response.data.map((item) => [item.reserva_id, item]))))
      .catch(() => setPendingReviews({}));
  }, []);

  useEffect(() => {
    loadPendingReviews();
  }, [loadPendingReviews]);

  const downloadVoucher = async (reservation) => {
    setDownloading(reservation.id_reserva);
    setNotice({ text: '', tone: 'success' });
    try {
      await downloadFile(`/vouchers/${reservation.id_reserva}`, `voucher-${reservation.codigo_reserva}.pdf`);
      setNotice({ text: `Voucher ${reservation.codigo_reserva} descargado.`, tone: 'success' });
    } catch (downloadError) {
      setNotice({ text: getErrorMessage(downloadError, downloadError.message || 'No fue posible descargar el voucher.'), tone: 'error' });
    } finally {
      setDownloading(null);
    }
  };

  const loadData = useCallback(async () => {
    setError('');

    try {
      const [reservationsResponse, paymentsResponse, coversResponse] = await Promise.all([
        api.get('/reservations/me'),
        api.get('/payments/me').catch(() => ({ data: [] })),
        api.get('/packages/images/covers').catch(() => ({ data: [] })),
      ]);

      // Pendientes primero, luego las más recientes
      const order = { pendiente: 0, confirmada: 1, cancelada: 2 };
      const sorted = [...reservationsResponse.data].sort(
        (a, b) => (order[a.estado] ?? 3) - (order[b.estado] ?? 3) || b.id_reserva - a.id_reserva
      );
      setReservations(sorted);

      setPayments(
        Object.fromEntries(paymentsResponse.data.map((payment) => [payment.reserva_id, payment]))
      );

      setCovers(
        Object.fromEntries(coversResponse.data.map((cover) => [cover.paquete_id, cover.imagen_url]))
      );

      const packageIds = [...new Set(sorted.map((item) => item.id_paquete_turistico))];
      const packageResponses = await Promise.all(
        packageIds.map((id) => api.get(`/packages/${id}`).catch(() => null))
      );

      setPackages(
        Object.fromEntries(
          packageResponses.filter(Boolean).map((response) => [response.data.id_paquete_turistico, response.data])
        )
      );
    } catch (requestError) {
      if (requestError.response?.status === 403) {
        setNeedsProfile(true);
      } else {
        setError(getErrorMessage(requestError, 'No fue posible cargar tus reservas.'));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    api.get('/reservations/cancellation-policy')
      .then((response) => setPolicy(response.data))
      .catch(() => setPolicy(null));
  }, []);

  const handlePay = async () => {
    setActionLoading(true);
    setModalError('');

    try {
      const response = await api.post('/payments/', {
        reserva_id: payingReservation.id_reserva,
        metodo_pago: paymentMethod,
        valor: payingReservation.total_reserva,
      });

      setMessage(`Pago aprobado. Referencia: ${response.data.referencia_pago}`);
      setPayingReservation(null);
      await loadData();
    } catch (requestError) {
      setModalError(getErrorMessage(requestError, 'No fue posible registrar el pago.'));
    } finally {
      setActionLoading(false);
    }
  };

  // Stripe, paso 1: el backend crea la sesión de pago y el navegador va a la página de Stripe
  const handleStripePay = async () => {
    setActionLoading(true);
    setModalError('');

    try {
      const response = await api.post('/payments/stripe/checkout', { reserva_id: payingReservation.id_reserva });
      window.location.assign(response.data.checkout_url);
    } catch (requestError) {
      setModalError(getErrorMessage(requestError, 'No fue posible abrir la página de pago.'));
      setActionLoading(false);
    }
  };

  // Stripe, paso 2: al volver, Stripe agrega ?stripe_session=<id>; el backend la consulta y confirma la reserva.
  // Si el viajero se arrepiente en la página de Stripe, vuelve con ?pago=cancelado.
  const stripeSession = searchParams.get('stripe_session');
  const paymentCancelled = searchParams.get('pago') === 'cancelado';
  useEffect(() => {
    if (paymentCancelled) {
      setNotice({ text: 'Cancelaste el pago. Tu reserva sigue pendiente; puedes pagarla cuando quieras.', tone: 'error' });
      setSearchParams({}, { replace: true });
      return;
    }

    if (!stripeSession || confirmedSession.current === stripeSession) return;
    confirmedSession.current = stripeSession; // evita confirmarla dos veces

    api.post('/payments/stripe/confirm', { session_id: stripeSession })
      .then((response) => {
        const paid = response.data.status === 'paid';
        setNotice({ text: `${response.data.codigo_reserva}: ${response.data.message}`, tone: paid ? 'success' : 'error' });
        if (paid) loadData();
      })
      .catch((requestError) => {
        setNotice({ text: getErrorMessage(requestError, 'No fue posible confirmar el pago.'), tone: 'error' });
      })
      .finally(() => {
        // Se limpia la dirección para que al recargar no se vuelva a consultar
        setSearchParams({}, { replace: true });
      });
  }, [stripeSession, paymentCancelled, loadData, setSearchParams]);

  // Paso 1: pedir al backend cuánto costaría cancelar hoy
  const openCancel = async (reservation) => {
    setActionLoading(true);
    setError('');
    setModalError('');

    try {
      const response = await api.get(`/reservations/${reservation.id_reserva}/cancellation`);
      setCancelling({ reservation, preview: response.data });
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible consultar la cancelación.'));
    } finally {
      setActionLoading(false);
    }
  };

  // Paso 2: confirmar
  const confirmCancel = async () => {
    const { reservation } = cancelling;

    setActionLoading(true);
    setModalError('');

    try {
      const response = await api.patch(`/reservations/${reservation.id_reserva}/cancel`);
      const refund = Number(response.data.reembolso || 0);
      const penalty = Number(response.data.penalidad_cancelacion || 0);

      let text = `Reserva ${reservation.codigo_reserva} cancelada.`;
      if (refund > 0) text += ` Te reembolsaremos ${formatCurrency(refund)}.`;
      if (penalty > 0) text += ` Se aplicó una penalidad de ${formatCurrency(penalty)}.`;

      setMessage(text);
      setCancelling(null);
      await loadData();
    } catch (requestError) {
      setModalError(getErrorMessage(requestError, 'No fue posible cancelar la reserva.'));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <PageSkeleton />;
  }

  if (needsProfile) {
    return (
      <section className="page page-narrow">
        <div className="page-header">
          <h1>Mis reservas</h1>
        </div>
        <div className="empty-state">
          <p>Para hacer y ver reservas primero debes completar tu perfil de cliente.</p>
          <Link to="/profile" className="btn btn-primary">Completar perfil</Link>
        </div>
      </section>
    );
  }

  return (
    <>
    <PageHero image={bannerImage} eyebrow="Tus viajes" title="Mis reservas">
      <p>Paga tus reservas pendientes para confirmarlas, o cancélalas según la política de cancelación.</p>
    </PageHero>

    <section className="page page-narrow page-after-hero">

      {message && (
        <div className="alert alert-success">
          <Icon name="check" size={22} strokeWidth={2.2} />
          <span>{message}</span>
        </div>
      )}
      {error && <div className="alert alert-error">{error}</div>}

      {reservations.length === 0 ? (
        <div className="empty-state">
          <p>Todavía no tienes reservas.</p>
          <Link to="/packages" className="btn btn-primary">Ver paquetes turísticos</Link>
        </div>
      ) : (
        <div className="reservations-list">
          {reservations.map((reservation) => {
            const touristPackage = packages[reservation.id_paquete_turistico];
            const payment = payments[reservation.id_reserva];
            const isPending = reservation.estado === 'pendiente';
            const isCancelled = reservation.estado === 'cancelada';
            const cancellable = canStillCancel(reservation);
            const freeUntil = freeCancellationUntil(reservation, policy);
            const freeStill = freeUntil && startOfToday() <= freeUntil;
            const penalty = Number(reservation.penalidad_cancelacion || 0);
            const refund = Number(reservation.reembolso || 0);
            const steps = completedSteps(reservation);
            const name = touristPackage?.nombre || `Paquete #${reservation.id_paquete_turistico}`;

            return (
              <article
                key={reservation.id_reserva}
                className={`reservation-card ${isCancelled ? 'is-cancelled' : ''}`}
              >
                <Link to={`/packages/${reservation.id_paquete_turistico}`} className="reservation-media">
                  <img
                    src={covers[reservation.id_paquete_turistico] || fallbackImage}
                    alt={name}
                    loading="lazy"
                    onError={(event) => { event.currentTarget.src = fallbackImage; }}
                  />
                </Link>

                <div className="reservation-body">
                  <div className="reservation-header">
                    <div>
                      <p className="reservation-code">{reservation.codigo_reserva}</p>
                      <h2>
                        <Link to={`/packages/${reservation.id_paquete_turistico}`}>{name}</Link>
                      </h2>
                    </div>
                    <span className={`badge badge-${reservation.estado}`}>
                      {STATUS_LABELS[reservation.estado] || reservation.estado}
                    </span>
                  </div>

                  <dl className="reservation-details">
                    <div><dt>Fecha de viaje</dt><dd>{formatDate(reservation.fecha_reserva)}</dd></div>
                    <div>
                      <dt>Viajeros</dt>
                      <dd>{reservation.cantidad_personas} {reservation.cantidad_personas === 1 ? 'persona' : 'personas'}</dd>
                    </div>
                    <div><dt>Total</dt><dd className="reservation-total">{formatCurrency(reservation.total_reserva)}</dd></div>
                    {payment && (
                      <div>
                        <dt>Pago · {PAYMENT_STATUS_LABELS[payment.estado_pago] || payment.estado_pago}</dt>
                        <dd>{payment.metodo_pago} · {payment.referencia_pago}</dd>
                      </div>
                    )}
                    {isCancelled && reservation.fecha_cancelacion && (
                      <>
                        <div><dt>Penalidad</dt><dd>{formatCurrency(penalty)}</dd></div>
                        <div><dt>Reembolso</dt><dd>{formatCurrency(refund)}</dd></div>
                      </>
                    )}
                  </dl>

                  {cancellable && freeUntil && (
                    <p className={`reservation-policy ${freeStill ? '' : 'is-late'}`}>
                      <Icon name="clock" size={16} />
                      {freeStill
                        ? `Cancelación gratis hasta el ${formatShortDate(freeUntil)}`
                        : isPending
                          ? 'Pasó el plazo de cancelación gratis, pero como no has pagado no hay penalidad'
                          : `Pasó el plazo de cancelación gratis (${formatShortDate(freeUntil)}): cancelar tiene una penalidad del ${policy.porcentaje_penalidad} %`}
                    </p>
                  )}

                  {!isCancelled && (
                    <div
                      className="reservation-progress"
                      role="img"
                      aria-label={['', 'Reservada, falta el pago', 'Reservada y pagada', 'Viaje realizado'][steps]}
                    >
                      {[1, 2, 3].map((step) => (
                        <span key={step} className={step <= steps ? 'done' : ''} />
                      ))}
                    </div>
                  )}

                  {(cancellable || reservation.estado === 'confirmada') && (
                    <div className="reservation-actions">
                      {reservation.estado === 'confirmada' && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => downloadVoucher(reservation)}
                          disabled={downloading === reservation.id_reserva}
                        >
                          <Icon name="download" size={18} />
                          {downloading === reservation.id_reserva ? 'Generando...' : 'Voucher PDF'}
                        </button>
                      )}
                      {pendingReviews[reservation.id_reserva] && (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => setReviewing(pendingReviews[reservation.id_reserva])}
                        >
                          <Icon name="star" size={18} />
                          Calificar viaje
                        </button>
                      )}
                      {isPending && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => {
                            setPayingReservation(reservation);
                            setModalError('');
                          }}
                          disabled={actionLoading}
                        >
                          Pagar {formatCurrency(reservation.total_reserva)}
                        </button>
                      )}
                      {cancellable && (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => openCancel(reservation)}
                          disabled={actionLoading}
                        >
                          Cancelar reserva
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      <Toast text={notice.text} tone={notice.tone} />

      {reviewing && (
        <ReviewModal
          trip={reviewing}
          onClose={() => setReviewing(null)}
          onSaved={() => {
            setReviewing(null);
            loadPendingReviews();
            setNotice({ text: '¡Gracias! Tu reseña ya está publicada.', tone: 'success' });
          }}
        />
      )}

      {cancelling && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="cancel-title">
          <div className="modal">
            <h2 id="cancel-title">Cancelar reserva</h2>
            <p className="cancel-subtitle">
              {packages[cancelling.reservation.id_paquete_turistico]?.nombre || cancelling.reservation.codigo_reserva}
              {' · '}viaje el {formatDate(cancelling.reservation.fecha_reserva)}
            </p>

            {modalError && <div className="alert alert-error">{modalError}</div>}

            {!cancelling.preview.puede_cancelar ? (
              <div className="alert alert-error">{cancelling.preview.motivo}</div>
            ) : (
              <>
                {cancelling.preview.con_penalidad ? (
                  <div className="cancel-notice is-late">
                    <strong>Ya pasó el plazo de cancelación gratis</strong>
                    <span>
                      El plazo terminó el {formatDate(cancelling.preview.fecha_limite_sin_penalidad)}.
                      Se cobra una penalidad del {cancelling.preview.porcentaje_penalidad} % de lo pagado.
                    </span>
                  </div>
                ) : (
                  <div className="cancel-notice">
                    <strong>Cancelación sin penalidad</strong>
                    <span>
                      {Number(cancelling.preview.monto_pagado) > 0
                        ? `Estás dentro del plazo (hasta el ${formatDate(cancelling.preview.fecha_limite_sin_penalidad)}): te devolvemos todo.`
                        : 'Todavía no has pagado esta reserva, así que no hay ningún cobro.'}
                    </span>
                  </div>
                )}

                {Number(cancelling.preview.monto_pagado) > 0 && (
                  <dl className="cancel-summary">
                    <div><dt>Pagaste</dt><dd>{formatCurrency(cancelling.preview.monto_pagado)}</dd></div>
                    <div>
                      <dt>Penalidad</dt>
                      <dd className={cancelling.preview.con_penalidad ? 'is-penalty' : ''}>
                        {cancelling.preview.con_penalidad ? '− ' : ''}{formatCurrency(cancelling.preview.penalidad)}
                      </dd>
                    </div>
                    <div className="cancel-summary-total"><dt>Te reembolsamos</dt><dd>{formatCurrency(cancelling.preview.reembolso)}</dd></div>
                  </dl>
                )}

                <p className="field-hint">El reembolso es simulado: no se mueve dinero real.</p>
              </>
            )}

            <div className="modal-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setCancelling(null)} disabled={actionLoading}>
                Volver
              </button>
              {cancelling.preview.puede_cancelar && (
                <button type="button" className="btn btn-danger" onClick={confirmCancel} disabled={actionLoading}>
                  {actionLoading ? 'Cancelando...' : 'Sí, cancelar reserva'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {payingReservation && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="pay-title">
          <div className="modal">
            <h2 id="pay-title">Pagar reserva</h2>
            <p className="pay-summary">
              <span>{payingReservation.codigo_reserva}</span>
              <strong>{formatCurrency(payingReservation.total_reserva)}</strong>
            </p>

            {modalError && <div className="alert alert-error">{modalError}</div>}

            {stripe.enabled ? (
              <>
                <div className="pay-gateway">
                  <Icon name="shield" size={22} />
                  <p>
                    Pagarás en la página segura de <strong>Stripe</strong> con tu tarjeta.
                    Al terminar volverás aquí y tu reserva se confirmará sola.
                  </p>
                </div>
                {stripe.test_mode && (
                  <div className="pay-sandbox">
                    <strong>Modo de pruebas: no se cobra dinero real.</strong>
                    <span>Tarjeta aprobada: 4242 4242 4242 4242</span>
                    <span>Tarjeta rechazada: 4000 0000 0000 0002</span>
                    <span>Fecha: cualquiera futura (ej. 12/34) · CVC: cualquier número de 3 dígitos</span>
                  </div>
                )}
              </>
            ) : (
            <>
            <fieldset className="pay-methods">
              <legend className="field-label">Método de pago</legend>
              {PAYMENT_METHODS.map((method) => (
                <label key={method} className={`pay-method ${paymentMethod === method ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="payment-method"
                    value={method}
                    checked={paymentMethod === method}
                    onChange={() => setPaymentMethod(method)}
                  />
                  <Icon name="card" size={20} />
                  {method}
                </label>
              ))}
            </fieldset>

            <p className="field-hint">Este es un pago simulado: no se cobra dinero real.</p>
            </>
            )}

            <div className="modal-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setPayingReservation(null)}
                disabled={actionLoading}
              >
                Volver
              </button>
              {stripe.enabled ? (
                <button type="button" className="btn btn-primary" onClick={handleStripePay} disabled={actionLoading}>
                  {actionLoading ? 'Abriendo la página de pago...' : 'Ir a pagar con Stripe'}
                </button>
              ) : (
                <button type="button" className="btn btn-primary" onClick={handlePay} disabled={actionLoading}>
                  {actionLoading ? 'Procesando...' : 'Confirmar pago'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
    </>
  );
}

export default Reservations;
