import { Link } from 'react-router-dom';

import fallbackImage from '../../assets/images/fondo.png';
import {
  finalPrice,
  formatCurrency,
  formatDateRange,
  tripLength,
} from '../../utils/format';
import FavoriteButton from '../FavoriteButton/FavoriteButton';
import Icon from '../Icon/Icon';
import { Stars } from '../StarRating/StarRating';

import './PackageCard.css';

const LOW_SLOTS = 12;

function slotsLabel(slots) {
  if (slots === undefined) return null;
  if (slots === 0) return 'Agotado';
  if (slots <= LOW_SLOTS) return `Últimos ${slots} cupos`;
  return `${slots} cupos`;
}

/**
 * variant="featured": foto grande y texto debajo (inicio).
 * variant="card": tarjeta blanca con la información dentro (listado).
 */
function PackageCard({ touristPackage, variant = 'card' }) {
  const id = touristPackage.id_paquete_turistico;
  const hasDiscount = touristPackage.descuento > 0;
  const slots = slotsLabel(touristPackage.availableSlots);

  return (
    <div className="package-card-wrap">
    <Link to={`/packages/${id}`} className={`package-card package-card-${variant}`}>
      <div className="package-card-media">
        <img
          src={touristPackage.cover || fallbackImage}
          alt={touristPackage.nombre}
          loading="lazy"
          onError={(event) => { event.currentTarget.src = fallbackImage; }}
        />

        {touristPackage.city && (
          <span className="package-card-city">
            <Icon name="pin" size={14} strokeWidth={2.2} />
            {touristPackage.city.nombre}
          </span>
        )}

        {hasDiscount && (
          <span className="package-card-discount">-{touristPackage.descuento}%</span>
        )}

        {slots && variant === 'card' && (
          <span className="package-card-slots">{slots}</span>
        )}
      </div>

      <div className="package-card-body">
        <div className="package-card-text">
          {variant === 'card' && (
            <p className="package-card-meta">
              {tripLength(touristPackage.fecha_inicio, touristPackage.fecha_fin)}
            </p>
          )}
          <h3>{touristPackage.nombre}</h3>
          {touristPackage.rating && (
            <p className="package-card-rating">
              <Stars value={touristPackage.rating.promedio} size={14} />
              <strong>{touristPackage.rating.promedio.toFixed(1)}</strong>
              <span>({touristPackage.rating.total} {touristPackage.rating.total === 1 ? 'reseña' : 'reseñas'})</span>
            </p>
          )}
          <p className="package-card-meta">
            {variant === 'featured' && `${tripLength(touristPackage.fecha_inicio, touristPackage.fecha_fin).split(' · ')[0]} · `}
            {formatDateRange(touristPackage.fecha_inicio, touristPackage.fecha_fin)}
          </p>
        </div>

        <div className="package-card-price">
          {hasDiscount && (
            <span className="package-card-old-price">{formatCurrency(touristPackage.precio)}</span>
          )}
          <strong>{formatCurrency(finalPrice(touristPackage))}</strong>
          <span className="package-card-per">por persona</span>
        </div>
      </div>
    </Link>
      <FavoriteButton packageId={id} packageName={touristPackage.nombre} />
    </div>
  );
}

export default PackageCard;
