import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import fallbackImage from '../../assets/images/hero.jpg';
import { finalPrice, formatCurrency, tripLength } from '../../utils/format';
import Icon from '../Icon/Icon';

import './HeroSlider.css';

const SLIDE_DURATION = 7000; // ms que dura cada destino antes de abrir la siguiente tarjeta
const OPEN_DURATION = 900; // ms de la animación de apertura
const VISIBLE_CARDS = 4;

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

function shortDescription(text) {
  const firstSentence = text.split('. ')[0];
  return firstSentence.endsWith('.') ? firstSentence : `${firstSentence}.`;
}

/**
 * Slider de destinos con "timed card opening": cada pocos segundos la
 * siguiente tarjeta se abre hasta ocupar todo el fondo.
 */
function HeroSlider({ packages, totalDestinations }) {
  const heroRef = useRef(null);
  const cardRefs = useRef({});

  const [index, setIndex] = useState(0);
  const [opening, setOpening] = useState(null); // { image, from, to, expanded }
  const [hovered, setHovered] = useState(false);
  const [userPaused, setUserPaused] = useState(false);

  const count = packages.length;
  const paused = hovered || userPaused || Boolean(opening) || count < 2;
  const current = packages[index];

  // Las siguientes tarjetas, empezando por la que viene después de la actual
  const upcoming = Array.from({ length: Math.min(VISIBLE_CARDS, Math.max(count - 1, 0)) }, (_, offset) => {
    const position = (index + offset + 1) % count;
    return { item: packages[position], position };
  });

  const goTo = useCallback((target) => {
    if (opening || target === index) return;

    const card = cardRefs.current[target];
    const hero = heroRef.current;

    // Sin tarjeta visible (p. ej. al ir hacia atrás) o con movimiento reducido: cambio directo
    if (!card || !hero || prefersReducedMotion()) {
      setIndex(target);
      return;
    }

    const heroBox = hero.getBoundingClientRect();
    const cardBox = card.getBoundingClientRect();

    setOpening({
      image: packages[target].cover || fallbackImage,
      target,
      expanded: false,
      from: {
        top: cardBox.top - heroBox.top,
        left: cardBox.left - heroBox.left,
        width: cardBox.width,
        height: cardBox.height,
      },
    });
  }, [index, opening, packages]);

  const next = useCallback(() => goTo((index + 1) % count), [goTo, index, count]);
  const previous = () => goTo((index - 1 + count) % count);

  // Inicia la expansión en el siguiente frame para que el navegador anime el cambio
  useEffect(() => {
    if (!opening || opening.expanded) return undefined;

    const frame = requestAnimationFrame(() => {
      setOpening((value) => value && { ...value, expanded: true });
    });

    return () => cancelAnimationFrame(frame);
  }, [opening]);

  // Al terminar la apertura, la tarjeta pasa a ser el destino activo
  useEffect(() => {
    if (!opening?.expanded) return undefined;

    const timer = setTimeout(() => {
      setIndex(opening.target);
      setOpening(null);
    }, OPEN_DURATION);

    return () => clearTimeout(timer);
  }, [opening]);

  // Temporizador del cambio automático
  useEffect(() => {
    if (paused) return undefined;

    const timer = setTimeout(next, SLIDE_DURATION);
    return () => clearTimeout(timer);
  }, [paused, next, index]);

  if (!current) {
    return (
      <header className="hero-slider" ref={heroRef}>
        <img src={fallbackImage} alt="" className="hero-slider-bg" />
        <div className="hero-slider-shade" />
      </header>
    );
  }

  const openingStyle = opening && (opening.expanded
    ? { top: 0, left: 0, width: '100%', height: '100%', borderRadius: 0 }
    : { ...opening.from, borderRadius: 18 });

  return (
    <header
      ref={heroRef}
      className="hero-slider"
      aria-roledescription="carrusel"
      aria-label="Destinos destacados"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setHovered(true)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setHovered(false);
      }}
    >
      <img key={`bg-${index}`} src={current.cover || fallbackImage} alt="" className="hero-slider-bg" />
      <div className="hero-slider-shade" />

      {opening && (
        <div
          className="hero-slider-opening"
          style={{ ...openingStyle, backgroundImage: `url("${opening.image}")` }}
          aria-hidden="true"
        />
      )}

      <div className="hero-slider-inner">
        <div className="hero-slider-text" key={`text-${index}`} aria-live={userPaused ? 'polite' : 'off'}>
          <p className="hero-slider-location">
            {current.city ? `${current.city.nombre}, ${current.city.departamento}` : 'Colombia'}
            <span> · {tripLength(current.fecha_inicio, current.fecha_fin)}</span>
          </p>
          <h1>{current.city?.nombre || current.nombre}</h1>
          <p className="hero-slider-name">{current.nombre}</p>
          <p className="hero-slider-description">{shortDescription(current.descripcion)}</p>

          <div className="hero-slider-actions">
            <Link to={`/packages/${current.id_paquete_turistico}`} className="hero-slider-cta">
              <span className="hero-slider-cta-icon"><Icon name="arrowRight" size={18} strokeWidth={2.4} /></span>
              Ver paquete
            </Link>
            <span className="hero-slider-price">
              desde <strong>{formatCurrency(finalPrice(current))}</strong>
            </span>
          </div>
        </div>

        <div className="hero-slider-cards" role="list" aria-label="Siguientes destinos">
          {upcoming.map(({ item, position }, order) => (
            <button
              key={item.id_paquete_turistico}
              ref={(element) => { cardRefs.current[position] = element; }}
              type="button"
              role="listitem"
              className={`hero-card ${opening?.target === position ? 'is-opening' : ''}`}
              style={{ '--order': order }}
              onClick={() => goTo(position)}
              aria-label={`Ver ${item.nombre}`}
            >
              <img src={item.cover || fallbackImage} alt="" loading="lazy" />
              <span className="hero-card-text">
                <small>{item.city?.nombre}</small>
                <strong>{item.nombre}</strong>
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="hero-slider-controls">
        <div className="hero-slider-buttons">
          <button type="button" onClick={previous} aria-label="Destino anterior" disabled={Boolean(opening)}>
            <Icon name="arrowLeft" size={18} />
          </button>
          <button type="button" onClick={next} aria-label="Siguiente destino" disabled={Boolean(opening)}>
            <Icon name="arrowRight" size={18} />
          </button>
          <button
            type="button"
            className="hero-slider-pause"
            onClick={() => setUserPaused((value) => !value)}
            aria-label={userPaused ? 'Reanudar el cambio automático' : 'Pausar el cambio automático'}
            aria-pressed={userPaused}
          >
            {userPaused ? <Icon name="arrowRight" size={16} /> : <span className="hero-slider-pause-icon" aria-hidden="true" />}
          </button>
        </div>

        <div className="hero-slider-progress" aria-hidden="true">
          <span
            key={`progress-${index}`}
            style={{ animationDuration: `${SLIDE_DURATION}ms`, animationPlayState: paused ? 'paused' : 'running' }}
          />
        </div>

        <p className="hero-slider-count">
          <span className="visually-hidden">Destino </span>
          {String(index + 1).padStart(2, '0')}
          <small> / {String(count).padStart(2, '0')}</small>
        </p>
      </div>

      {totalDestinations > 0 && (
        <p className="hero-slider-badge">{totalDestinations} destinos en Colombia</p>
      )}
    </header>
  );
}

export default HeroSlider;
