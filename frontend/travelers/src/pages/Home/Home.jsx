import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import bannerImage from '../../assets/images/banner.jpg';
import HeroSlider from '../../components/HeroSlider/HeroSlider';
import Icon from '../../components/Icon/Icon';
import DestinationsMap from '../../components/DestinationsMap/DestinationsMap';
import PackageCard from '../../components/PackageCard/PackageCard';
import usePackageCatalog from '../../hooks/usePackageCatalog';
import { finalPrice, formatCurrency, tripLength } from '../../utils/format';

import './Home.css';

import Select from '../../components/Select/Select';
import MonthPicker from '../../components/DatePicker/MonthPicker';
const FEATURES = [
  {
    icon: 'calendar',
    title: 'Reserva en minutos',
    text: 'Elige la fecha y el número de viajeros; ves los cupos disponibles al instante.',
  },
  {
    icon: 'users',
    title: 'Viaja acompañado',
    text: 'Registra a tus acompañantes en la misma reserva y paga todo en un solo paso.',
  },
  {
    icon: 'mail',
    title: 'Confirmación al instante',
    text: 'Recibes el código de reserva y la confirmación del pago en tu correo.',
  },
];

function monthKey(date) {
  return date.slice(0, 7);
}

function Home() {
  const navigate = useNavigate();
  const { packages, loading } = usePackageCatalog();

  const [destination, setDestination] = useState('');
  const [month, setMonth] = useState('');
  const [people, setPeople] = useState('2');

  const destinations = useMemo(() => {
    const unique = new Map();
    packages.forEach((item) => item.city && unique.set(item.city.id_ciudad, item.city));
    return [...unique.values()].sort((a, b) => a.nombre.localeCompare(b.nombre));
  }, [packages]);

  const months = useMemo(
    () => [...new Set(packages.map((item) => monthKey(item.fecha_inicio)))].sort(),
    [packages]
  );

  const featured = packages.slice(0, 6);
  // Un paquete al azar en cada visita (se prefieren los que tienen foto de portada).
  // El número aleatorio se sortea una sola vez al abrir la página.
  const [bannerSeed] = useState(() => Math.random());
  const bannerPackage = useMemo(() => {
    if (packages.length === 0) return null;
    const withCover = packages.filter((item) => item.cover);
    const pool = withCover.length > 0 ? withCover : packages;
    return pool[Math.floor(bannerSeed * pool.length)];
  }, [packages, bannerSeed]);

  const handleSearch = (event) => {
    event.preventDefault();

    const params = new URLSearchParams();
    if (destination) params.set('ciudad', destination);
    if (month) params.set('mes', month);
    if (people) params.set('personas', people);

    navigate(`/packages?${params.toString()}`);
  };

  return (
    <div className="home">
      <HeroSlider packages={packages} totalDestinations={destinations.length} />

      <form className="home-search" onSubmit={handleSearch}>
        <label className="home-search-field">
          <span>Destino</span>
          <Select value={destination} onChange={(event) => setDestination(event.target.value)}>
            <option value="">Todos los destinos</option>
            {destinations.map((city) => (
              <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
            ))}
          </Select>
        </label>

        <label className="home-search-field">
          <span>Cuándo</span>
          <MonthPicker
            value={month}
            onChange={(event) => setMonth(event.target.value)}
            available={months}
            emptyLabel="Cualquier fecha"
          />
        </label>

        <label className="home-search-field">
          <span>Viajeros</span>
          <Select value={people} onChange={(event) => setPeople(event.target.value)}>
            {Array.from({ length: 10 }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>
                {value} {value === 1 ? 'persona' : 'personas'}
              </option>
            ))}
          </Select>
        </label>

        <button type="submit" className="home-search-button">
          <Icon name="search" size={20} strokeWidth={2.2} />
          Buscar paquetes
        </button>
      </form>

      <section className="container home-section">
        <div className="home-section-header">
          <div>
            <p className="eyebrow">Destacados</p>
            <h2>Paquetes para esta temporada</h2>
          </div>
          <Link to="/packages" className="btn btn-outline">
            Ver todos los paquetes
            <Icon name="arrowRight" size={18} />
          </Link>
        </div>

        {loading ? (
          <p className="page-status">Cargando paquetes...</p>
        ) : featured.length === 0 ? (
          <div className="empty-state"><p>Pronto tendremos paquetes disponibles.</p></div>
        ) : (
          <div className="home-grid">
            {featured.map((item) => (
              <PackageCard key={item.id_paquete_turistico} touristPackage={item} variant="featured" />
            ))}
          </div>
        )}
      </section>

      {!loading && packages.length > 0 && (
        <section className="container home-section">
          <div className="home-section-header">
            <div>
              <p className="eyebrow">Mapa de destinos</p>
              <h2>¿A dónde quieres ir?</h2>
            </div>
          </div>
          <DestinationsMap packages={packages} />
        </section>
      )}

      <section className="container home-section">
        <div className="home-features">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="home-feature">
              <span className="home-feature-icon">
                <Icon name={feature.icon} size={26} />
              </span>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      {bannerPackage && (
        <section className="container home-section">
          <div className="home-banner">
            <img src={bannerPackage.cover || bannerImage} alt="" className="home-banner-image" />
            <div className="home-banner-overlay" />
            <div className="home-banner-content">
              <h2>{bannerPackage.nombre}</h2>
              <p>
                {tripLength(bannerPackage.fecha_inicio, bannerPackage.fecha_fin)}.{' '}
                {bannerPackage.descripcion.split('.')[1]?.trim()
                  ? `${bannerPackage.descripcion.split('.')[1].trim()}.`
                  : bannerPackage.descripcion}
              </p>
              <Link to={`/packages/${bannerPackage.id_paquete_turistico}`} className="home-banner-button">
                Ver paquete · {formatCurrency(finalPrice(bannerPackage))}
              </Link>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

export default Home;
