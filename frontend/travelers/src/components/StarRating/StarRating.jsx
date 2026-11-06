import { useId, useState } from 'react';

import Icon from '../Icon/Icon';
import './StarRating.css';

const LABELS = ['', 'Malo', 'Regular', 'Bueno', 'Muy bueno', 'Excelente'];

/** Estrellas de solo lectura: admite medias estrellas (4.5). */
export function Stars({ value = 0, size = 16, label }) {
  const rounded = Math.round(value * 2) / 2;
  return (
    <span className="stars" role="img" aria-label={label || `${value} de 5 estrellas`}>
      {[1, 2, 3, 4, 5].map((star) => {
        const fill = rounded >= star ? 100 : rounded >= star - 0.5 ? 50 : 0;
        return (
          <span key={star} className="star" style={{ width: size, height: size }}>
            <Icon name="star" size={size} strokeWidth={1.6} className="star-base" />
            {fill > 0 && (
              <span className="star-fill" style={{ width: `${fill}%` }}>
                <Icon name="star" size={size} strokeWidth={1.6} />
              </span>
            )}
          </span>
        );
      })}
    </span>
  );
}

/** Selector de 1 a 5 estrellas (radio buttons accesibles). */
export function StarInput({ value, onChange, name }) {
  const autoId = useId();
  const groupName = name || `stars-${autoId}`;
  const [hover, setHover] = useState(0);
  const shown = hover || value;

  return (
    <div className="star-input">
      <div className="star-input-stars" role="radiogroup" aria-label="Calificación" onMouseLeave={() => setHover(0)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <label
            key={star}
            className={`star-input-option ${shown >= star ? 'is-on' : ''}`}
            onMouseEnter={() => setHover(star)}
          >
            <input
              type="radio"
              name={groupName}
              value={star}
              checked={value === star}
              onChange={() => onChange(star)}
              className="visually-hidden"
            />
            <Icon name="star" size={34} strokeWidth={1.5} />
            <span className="visually-hidden">{star} {star === 1 ? 'estrella' : 'estrellas'}</span>
          </label>
        ))}
      </div>
      <span className="star-input-label" aria-live="polite">{LABELS[shown] || 'Elige una calificación'}</span>
    </div>
  );
}
