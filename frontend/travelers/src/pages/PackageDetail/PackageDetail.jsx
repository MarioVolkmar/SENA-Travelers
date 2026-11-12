import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import fallbackImage from '../../assets/images/fondo.png';
import FavoriteButton from '../../components/FavoriteButton/FavoriteButton';
import ShareButton from '../../components/ShareButton/ShareButton';
import Icon from '../../components/Icon/Icon';
import { Stars } from '../../components/StarRating/StarRating';
import PackageReviews from './PackageReviews';
import RelatedPackages from '../../components/RelatedPackages/RelatedPackages';
import { productTypeIcon } from '../../utils/productTypes';
import { useLimits } from '../../utils/limits';
import { describedIncludes, includeItems } from '../../utils/packageIncludes';
import { useAuth } from '../../context/AuthContext';
import {
  datesBetween,
  finalPrice,
  formatCurrency,
  formatDate,
  formatDateRange,
  getErrorMessage,
  ROLE_CLIENT,
  tripLength,
} from '../../utils/format';

import './PackageDetail.css';

import DatePicker from '../../components/DatePicker/DatePicker';
import { todayKey, yearsBeforeKey } from '../../components/DatePicker/calendarUtils';
import usePageTitle from '../../hooks/usePageTitle';
import { PageSkeleton } from '../../components/Skeleton/Skeleton';
import { IVA_PERCENT, splitIva } from '../../utils/taxes';
const MOSAIC_SIZE = 4;

const emptyCompanion = { nombre: '', documento: '', fecha_nacimiento: '' };

// Fechas del paquete en las que todavía se puede reservar: desde mañana
function bookableDates(touristPackage) {
  const now = new Date();
  const todayKey = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-');

  return datesBetween(touristPackage.fecha_inicio, touristPackage.fecha_fin).filter((date) => date > todayKey);
}

function PackageDetail() {
  const limits = useLimits();
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  const [touristPackage, setTouristPackage] = useState(null);
  usePageTitle(touristPackage?.nombre);
  const [images, setImages] = useState([]);
  const [lightbox, setLightbox] = useState(null);
  const [city, setCity] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [cancellationPolicy, setCancellationPolicy] = useState(null);
  const [clientProfile, setClientProfile] = useState(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [fechaReserva, setFechaReserva] = useState('');
  const [cantidadPersonas, setCantidadPersonas] = useState(1);
  const [companions, setCompanions] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [couponInput, setCouponInput] = useState('');
  const [coupon, setCoupon] = useState(null);
  const [couponError, setCouponError] = useState('');
  const [checkingCoupon, setCheckingCoupon] = useState(false);
  const [rating, setRating] = useState(null);
  const [includedProducts, setIncludedProducts] = useState([]);
  const handleReviewSummary = useCallback((summary) => setRating(summary.total > 0 ? summary : null), []);

  const checkCoupon = useCallback(async (code, people) => {
    setCheckingCoupon(true);
    setCouponError('');
    try {
      const response = await api.post('/coupons/validate', {
        codigo: code.trim(),
        id_paquete_turistico: Number(id),
        cantidad_personas: Number(people),
      });
      setCoupon(response.data);
    } catch (requestError) {
      setCoupon(null);
      setCouponError(getErrorMessage(requestError, 'No fue posible validar el cupón.'));
    } finally {
      setCheckingCoupon(false);
    }
  }, [id]);

  // Si cambia el número de viajeros, el descuento se recalcula
  useEffect(() => {
    if (coupon) checkCoupon(coupon.codigo, cantidadPersonas);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cantidadPersonas]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError('');

      try {
        const packageResponse = await api.get(`/packages/${id}`);
        const data = packageResponse.data;

        setTouristPackage(data);
        setFechaReserva(bookableDates(data)[0] || '');

        const [imagesResponse, availabilityResponse, citiesResponse, policyResponse, includesResponse] = await Promise.all([
          api.get(`/packages/${id}/images`).catch(() => ({ data: [] })),
          api.get(`/reservations/availability/${id}`).catch(() => ({ data: null })),
          api.get('/cities/').catch(() => ({ data: [] })),
          api.get('/reservations/cancellation-policy').catch(() => ({ data: null })),
          api.get(`/packages/${id}/includes`).catch(() => ({ data: [] })),
        ]);

        setCancellationPolicy(policyResponse.data);
        setIncludedProducts(includesResponse.data);

        setImages(imagesResponse.data.filter((image) => image.imagen_url));
        setAvailability(availabilityResponse.data);
        setCity(citiesResponse.data.find((item) => item.id_ciudad === data.ciudad_id) || null);
      } catch (requestError) {
        setError(
          requestError.response?.status === 404
            ? 'El paquete turístico no existe.'
            : 'No fue posible cargar el paquete turístico.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // Saber si el usuario ya tiene perfil de cliente (es requisito para reservar)
  useEffect(() => {
    if (!isAuthenticated || !user || user.rol_id !== ROLE_CLIENT) {
      setClientProfile(null);
      return;
    }

    api.get('/clients/me')
      .then((response) => setClientProfile(response.data))
      .catch(() => setClientProfile(null));
  }, [isAuthenticated, user]);

  // Siempre hay (personas - 1) acompañantes
  useEffect(() => {
    setCompanions((current) => {
      const needed = Math.max(cantidadPersonas - 1, 0);
      const next = current.slice(0, needed);

      while (next.length < needed) next.push({ ...emptyCompanion });

      return next;
    });
  }, [cantidadPersonas]);

  // Navegación del visor de fotos con el teclado
  useEffect(() => {
    if (lightbox === null) return undefined;

    const handleKey = (event) => {
      if (event.key === 'Escape') setLightbox(null);
      if (event.key === 'ArrowRight') setLightbox((index) => (index + 1) % images.length);
      if (event.key === 'ArrowLeft') setLightbox((index) => (index - 1 + images.length) % images.length);
    };

    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [lightbox, images.length]);

  const handleCompanionChange = (index, field, value) => {
    setCompanions((current) =>
      current.map((companion, i) => (i === index ? { ...companion, [field]: value } : companion))
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError('');
    setSubmitting(true);

    try {
      const response = await api.post('/reservations/', {
        id_paquete_turistico: touristPackage.id_paquete_turistico,
        fecha_reserva: fechaReserva,
        cantidad_personas: Number(cantidadPersonas),
        codigo_cupon: coupon ? coupon.codigo : undefined,
        acompanantes: companions.map((companion) => ({
          nombre: companion.nombre.trim(),
          documento: companion.documento.trim(),
          fecha_nacimiento: companion.fecha_nacimiento,
        })),
      });

      navigate('/reservations', {
        state: { createdCode: response.data.codigo_reserva },
      });
    } catch (requestError) {
      setFormError(getErrorMessage(requestError, 'No fue posible crear la reserva'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <PageSkeleton />;
  }

  if (error) {
    return (
      <div className="page-status">
        <p>{error}</p>
        <Link to="/packages" className="btn btn-secondary">Volver a paquetes</Link>
      </div>
    );
  }

  const unitPrice = finalPrice(touristPackage);
  const total = unitPrice * Number(cantidadPersonas || 0);
  const availableSlots = availability?.cupos_disponibles ?? touristPackage.cupo_max;
  const maxPeople = Math.min(availableSlots, limits.reservationTravelers.max);
  const isInactive = touristPackage.estado !== 'activo';
  // «Qué incluye»: 1) lo elegido en el formulario del paquete; 2) si no hay, la frase
  // «Incluye ...» de la descripción; 3) si tampoco, los productos del paquete
  const chosenItems = includeItems(touristPackage.incluye);
  const describedItems = describedIncludes(touristPackage.descripcion);
  const included = chosenItems.length > 0
    ? chosenItems
    : describedItems.length > 0
    ? describedItems.map((text) => ({ key: text, text, icon: 'check' }))
    : includedProducts.map((item, index) => ({
      key: `${item.nombre}-${index}`,
      text: item.cantidad > 1 ? `${item.nombre} (×${item.cantidad})` : item.nombre,
      icon: productTypeIcon(item.tipo_producto),
    }));
  const travelDates = bookableDates(touristPackage);
  const hasEnded = travelDates.length === 0;
  const mosaic = images.length > 0 ? images.slice(0, MOSAIC_SIZE) : [{ id_imagen: 0, imagen_url: fallbackImage }];

  const renderBookingContent = () => {
    if (isInactive) {
      return <div className="alert alert-info">Este paquete no está disponible actualmente.</div>;
    }

    if (hasEnded) {
      return (
        <>
          <div className="alert alert-info">Este paquete ya no tiene fechas disponibles para reservar.</div>
          <Link to="/packages" className="btn btn-secondary btn-block">Ver otros paquetes</Link>
        </>
      );
    }

    if (availableSlots === 0) {
      return <div className="alert alert-info">Este paquete ya no tiene cupos disponibles.</div>;
    }

    if (!isAuthenticated) {
      return (
        <>
          <p className="booking-note">Inicia sesión para reservar este paquete.</p>
          <Link to="/login" state={{ from: `/packages/${id}` }} className="btn btn-primary btn-block">
            Iniciar sesión
          </Link>
          <p className="booking-note">
            ¿No tienes cuenta? <Link to="/register">Regístrate</Link>
          </p>
        </>
      );
    }

    if (!user || clientProfile === undefined) {
      return <p className="booking-note">Cargando...</p>;
    }

    if (user.rol_id !== ROLE_CLIENT) {
      return <div className="alert alert-info">Solo los clientes pueden hacer reservas.</div>;
    }

    if (clientProfile === null) {
      return (
        <>
          <div className="alert alert-info">Para reservar primero completa tu perfil de cliente.</div>
          <Link to="/profile" className="btn btn-primary btn-block">Completar perfil</Link>
        </>
      );
    }

    return (
      <form onSubmit={handleSubmit}>
        {formError && <div className="alert alert-error">{formError}</div>}

        <div className="booking-box">
          <div className="booking-row booking-row-field">
            <label className="field-label" htmlFor="booking-date">Fecha de viaje</label>
            <DatePicker
              id="booking-date"
              value={fechaReserva}
              onChange={(event) => setFechaReserva(event.target.value)}
              min={travelDates[0]}
              max={travelDates[travelDates.length - 1]}
              isDateEnabled={(key) => travelDates.includes(key)}
              required
            />
          </div>

          <div className="booking-row">
            <div>
              <span className="field-label">Viajeros</span>
              <p className="booking-people">
                {cantidadPersonas} {cantidadPersonas === 1 ? 'persona' : 'personas'}
              </p>
            </div>
            <div className="booking-stepper">
              <button
                type="button"
                className="icon-btn"
                aria-label="Quitar viajero"
                disabled={cantidadPersonas <= 1}
                onClick={() => setCantidadPersonas((value) => Math.max(1, value - 1))}
              >
                −
              </button>
              <span aria-live="polite">{cantidadPersonas}</span>
              <button
                type="button"
                className="icon-btn"
                aria-label="Agregar viajero"
                disabled={cantidadPersonas >= maxPeople}
                onClick={() => setCantidadPersonas((value) => Math.min(maxPeople, value + 1))}
              >
                +
              </button>
            </div>
          </div>
        </div>

        {companions.length > 0 && (
          <div className="booking-companions">
            <p className="booking-companions-title">Acompañantes</p>

            {companions.map((companion, index) => (
              <fieldset key={index} className="companion">
                <legend>
                  <span className="companion-number">{index + 1}</span>
                  Acompañante {index + 1}
                </legend>

                <div className="field">
                  <label htmlFor={`companion-name-${index}`}>Nombre completo</label>
                  <input
                    id={`companion-name-${index}`}
                    value={companion.nombre}
                    onChange={(event) => handleCompanionChange(index, 'nombre', event.target.value)}
                    minLength={2}
                    required
                  />
                </div>

                <div className="companion-row">
                  <div className="field">
                    <label htmlFor={`companion-doc-${index}`}>Documento</label>
                    <input
                      id={`companion-doc-${index}`}
                      value={companion.documento}
                      onChange={(event) => handleCompanionChange(index, 'documento', event.target.value)}
                      minLength={5}
                      required
                    />
                  </div>
                  <div className="field">
                    <label htmlFor={`companion-birth-${index}`}>Nacimiento</label>
                    <DatePicker
                      id={`companion-birth-${index}`}
                      startView="years"
                      min={yearsBeforeKey(110)}
                      max={yearsBeforeKey(7, fechaReserva || todayKey())}
                      placeholder="Elige la fecha"
                      value={companion.fecha_nacimiento}
                      onChange={(event) => handleCompanionChange(index, 'fecha_nacimiento', event.target.value)}
                      required
                    />
                    <span className="field-hint">Mínimo 7 años el día del viaje.</span>
                  </div>
                </div>
              </fieldset>
            ))}
          </div>
        )}

        <div className="booking-coupon">
          {coupon ? (
            <div className="booking-coupon-applied">
              <Icon name="tag" size={18} />
              <span>
                <strong>{coupon.codigo}</strong>
                {coupon.descripcion ? ` · ${coupon.descripcion}` : ''}
              </span>
              <button
                type="button"
                className="link-button"
                onClick={() => { setCoupon(null); setCouponInput(''); }}
              >
                Quitar
              </button>
            </div>
          ) : (
            <div className="booking-coupon-form">
              <label htmlFor="booking-coupon" className="visually-hidden">Código de cupón</label>
              <input
                id="booking-coupon"
                value={couponInput}
                onChange={(event) => setCouponInput(event.target.value.toUpperCase())}
                placeholder="¿Tienes un cupón?"
                maxLength={30}
                autoComplete="off"
              />
              <button
                type="button"
                className="btn btn-secondary btn-small"
                disabled={!couponInput.trim() || checkingCoupon}
                onClick={() => checkCoupon(couponInput, cantidadPersonas)}
              >
                {checkingCoupon ? 'Validando...' : 'Aplicar'}
              </button>
            </div>
          )}
          {couponError && <p className="booking-coupon-error" role="alert">{couponError}</p>}
        </div>

        <div className="booking-summary">
          <p>
            <span>{formatCurrency(unitPrice)} × {cantidadPersonas}</span>
            <span>{formatCurrency(total)}</span>
          </p>
          {coupon && (
            <p className="booking-discount">
              <span>Cupón {coupon.codigo}</span>
              <span>− {formatCurrency(coupon.descuento)}</span>
            </p>
          )}
          {/* El precio ya incluye el IVA: aquí solo se desglosa */}
          <p className="booking-tax">
            <span>Valor sin IVA</span>
            <span>{formatCurrency(splitIva(coupon ? coupon.total : total).base)}</span>
          </p>
          <p className="booking-tax">
            <span>IVA ({IVA_PERCENT} %)</span>
            <span>{formatCurrency(splitIva(coupon ? coupon.total : total).iva)}</span>
          </p>
          <p className="booking-total">
            <span>Total <small>(IVA incluido)</small></span>
            <span>{formatCurrency(coupon ? coupon.total : total)}</span>
          </p>
        </div>

        <button type="submit" className="btn btn-primary btn-block booking-submit" disabled={submitting}>
          {submitting ? 'Reservando...' : 'Reservar ahora'}
        </button>

        <p className="booking-note">No se cobra nada todavía: pagas desde «Mis reservas».</p>
      </form>
    );
  };

  return (
    <section className="page detail-page">
      <Link to="/packages" className="detail-back">
        <Icon name="arrowLeft" size={16} strokeWidth={2.2} />
        Paquetes{city ? ` / ${city.nombre}` : ''}
      </Link>

      <div className="detail-heading">
        <div>
          <h1>{touristPackage.nombre}</h1>
          {rating && (
            <a href="#reviews-title" className="detail-rating">
              <Stars value={rating.promedio} size={16} />
              <strong>{rating.promedio.toFixed(1)}</strong>
              <span>· {rating.total} {rating.total === 1 ? 'reseña' : 'reseñas'}</span>
            </a>
          )}
          <p>
            {city ? `${city.nombre}, ${city.departamento} · ` : ''}
            {formatDateRange(touristPackage.fecha_inicio, touristPackage.fecha_fin)} ·{' '}
            {tripLength(touristPackage.fecha_inicio, touristPackage.fecha_fin)}
          </p>
        </div>
        <div className="detail-heading-actions">
          <FavoriteButton packageId={touristPackage.id_paquete_turistico} packageName={touristPackage.nombre} variant="inline" />
          <ShareButton
            title={`${touristPackage.nombre} · Travelers`}
            text={`Mira este paquete: ${touristPackage.nombre}, desde ${formatCurrency(unitPrice)} por persona.`}
          />
          {!isInactive && !hasEnded && (
            <span className="detail-slots">
              {availableSlots === 0 ? 'Agotado' : `${availableSlots} cupos disponibles`}
            </span>
          )}
        </div>
      </div>

      <div className={`detail-mosaic detail-mosaic-${mosaic.length}`}>
        {mosaic.map((image, index) => (
          <button
            key={image.id_imagen}
            type="button"
            className="detail-mosaic-item"
            onClick={() => images.length > 0 && setLightbox(index)}
            aria-label={`Ampliar foto ${index + 1}`}
            disabled={images.length === 0}
          >
            <img
              src={image.imagen_url}
              alt={index === 0 ? touristPackage.nombre : ''}
              loading={index === 0 ? 'eager' : 'lazy'}
              onError={(event) => { event.currentTarget.src = fallbackImage; }}
            />
          </button>
        ))}

        {images.length > MOSAIC_SIZE && (
          <button type="button" className="detail-all-photos" onClick={() => setLightbox(0)}>
            <Icon name="grid" size={16} />
            Ver las {images.length} fotos
          </button>
        )}
      </div>

      <div className="detail-layout">
        <div className="detail-main">
          <div className="detail-facts">
            <div className="detail-fact">
              <span>Duración</span>
              <strong>{tripLength(touristPackage.fecha_inicio, touristPackage.fecha_fin)}</strong>
            </div>
            <div className="detail-fact">
              <span>Salida</span>
              <strong>{formatDate(touristPackage.fecha_inicio)}</strong>
            </div>
            <div className="detail-fact">
              <span>Grupo máximo</span>
              <strong>{touristPackage.cupo_max} personas</strong>
            </div>
            {touristPackage.descuento > 0 && (
              <div className="detail-fact">
                <span>Descuento</span>
                <strong>{touristPackage.descuento}%</strong>
              </div>
            )}
          </div>

          <h2>Sobre este viaje</h2>
          <p className="detail-description">{touristPackage.descripcion}</p>

          {included.length > 0 && (
            <>
              <h2>Qué incluye</h2>
              <ul className="detail-included">
                {included.map((item) => (
                  <li key={item.key}>
                    <span><Icon name={item.icon} size={20} /></span>
                    {item.text}
                  </li>
                ))}
              </ul>
            </>
          )}

          <PackageReviews packageId={touristPackage.id_paquete_turistico} onSummary={handleReviewSummary} />
        </div>

        <aside className="detail-booking">
          <p className="booking-price">
            {touristPackage.descuento > 0 && (
              <span className="booking-old-price">{formatCurrency(touristPackage.precio)}</span>
            )}
            <strong>{formatCurrency(unitPrice)}</strong>
            <span>por persona · IVA incluido</span>
          </p>

          {renderBookingContent()}

          {cancellationPolicy && !isInactive && !hasEnded && (
            <p className="booking-policy">
              <Icon name="clock" size={16} />
              <span>
                {cancellationPolicy.horas_para_pagar && (
                  <>Tendrás {cancellationPolicy.horas_para_pagar} {cancellationPolicy.horas_para_pagar === 1 ? 'hora' : 'horas'} para pagar la reserva; si no, se cancela sola.{' '}</>
                )}
                Cancelación gratis hasta {cancellationPolicy.dias_sin_penalidad} días antes del viaje.
                Después, penalidad del {cancellationPolicy.porcentaje_penalidad} % de lo pagado.
              </span>
            </p>
          )}
        </aside>
      </div>

      <RelatedPackages current={touristPackage} />

      {lightbox !== null && (
        <div className="lightbox" role="dialog" aria-modal="true" aria-label="Fotos del paquete">
          <button type="button" className="lightbox-close" onClick={() => setLightbox(null)} aria-label="Cerrar">
            <Icon name="close" size={24} />
          </button>

          <button
            type="button"
            className="lightbox-nav lightbox-prev"
            onClick={() => setLightbox((lightbox - 1 + images.length) % images.length)}
            aria-label="Foto anterior"
          >
            <Icon name="arrowLeft" size={24} />
          </button>

          <figure className="lightbox-figure">
            <img src={images[lightbox].imagen_url} alt={`Foto ${lightbox + 1} de ${images.length}`} />
            <figcaption>{lightbox + 1} / {images.length}</figcaption>
          </figure>

          <button
            type="button"
            className="lightbox-nav lightbox-next"
            onClick={() => setLightbox((lightbox + 1) % images.length)}
            aria-label="Foto siguiente"
          >
            <Icon name="arrowRight" size={24} />
          </button>
        </div>
      )}
    </section>
  );
}

export default PackageDetail;
