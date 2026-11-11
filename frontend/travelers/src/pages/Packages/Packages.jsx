import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

import bannerImage from '../../assets/images/banner.jpg';
import PackageCard from '../../components/PackageCard/PackageCard';
import { PackageGridSkeleton } from '../../components/Skeleton/Skeleton';
import PageHero from '../../components/PageHero/PageHero';
import usePackageCatalog from '../../hooks/usePackageCatalog';
import { finalPrice } from '../../utils/format';
import { buildSearch } from '../../utils/packageSearch';
import Icon from '../../components/Icon/Icon';

import './Packages.css';

import Select from '../../components/Select/Select';
import MonthPicker from '../../components/DatePicker/MonthPicker';
import usePageTitle from '../../hooks/usePageTitle';
const SORTS = {
  fecha: { label: 'Próxima salida', compare: (a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio) },
  menor: { label: 'Menor precio', compare: (a, b) => finalPrice(a) - finalPrice(b) },
  mayor: { label: 'Mayor precio', compare: (a, b) => finalPrice(b) - finalPrice(a) },
  // Los paquetes sin reseñas van al final; en empate decide la otra medida
  calificacion: {
    label: 'Mejor calificados',
    compare: (a, b) => (b.rating?.promedio ?? -1) - (a.rating?.promedio ?? -1)
      || (b.rating?.total ?? 0) - (a.rating?.total ?? 0),
  },
  resenas: {
    label: 'Más reseñas',
    compare: (a, b) => (b.rating?.total ?? 0) - (a.rating?.total ?? 0)
      || (b.rating?.promedio ?? -1) - (a.rating?.promedio ?? -1),
  },
};

// Filtro por calificación: valor de la URL, texto y mínimo de estrellas (0 = basta con tener reseñas).
// Es una lista (no un objeto) porque JavaScript pone primero las llaves numéricas y desordenaba las opciones.
const RATING_OPTIONS = [
  { key: '4.5', label: '4.5 ★', min: 4.5 },
  { key: '4', label: '4 ★', min: 4 },
  { key: '3', label: '3 ★', min: 3 },
  { key: '', label: 'Cualquiera' },
  { key: 'resenas', label: 'Con reseñas', min: 0 },
];

function Packages() {
  usePageTitle('Paquetes turísticos');
  const { packages, loading, error } = usePackageCatalog({ withAvailability: true });
  const [searchParams, setSearchParams] = useSearchParams();

  const city = searchParams.get('ciudad') || '';
  const month = searchParams.get('mes') || '';
  const people = Number(searchParams.get('personas') || 0);
  const query = searchParams.get('q') || '';
  // Cada palabra (o una relacionada: "playa" → mar, Caribe, islas...) debe aparecer en el paquete
  const search = buildSearch(query);
  const onlyDeals = searchParams.get('oferta') === '1';
  const sort = SORTS[searchParams.get('orden')] ? searchParams.get('orden') : 'fecha';
  const ratingOption = RATING_OPTIONS.find((option) => option.key === (searchParams.get('estrellas') || ''))
    || RATING_OPTIONS.find((option) => option.key === '');
  const ratingKey = ratingOption.key;
  const minRating = ratingOption.min;

  const updateParam = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
  };

  const cities = useMemo(() => {
    const unique = new Map();
    packages.forEach((item) => item.city && unique.set(String(item.city.id_ciudad), item.city));
    return [...unique.values()].sort((a, b) => a.nombre.localeCompare(b.nombre));
  }, [packages]);

  const months = useMemo(
    () => [...new Set(packages.map((item) => item.fecha_inicio.slice(0, 7)))].sort(),
    [packages]
  );

  const visible = packages
    .filter(search.matches)
    .filter((item) => !onlyDeals || Number(item.descuento) > 0)
    .filter((item) => !city || String(item.ciudad_id) === city)
    .filter((item) => !month || item.fecha_inicio.startsWith(month))
    .filter((item) => !people || item.availableSlots === undefined || item.availableSlots >= people)
    .filter((item) => minRating === undefined || (item.rating && item.rating.promedio >= minRating))
    .sort(SORTS[sort].compare);

  const hasFilters = Boolean(query || city || month || people || ratingKey || onlyDeals);
  const dealsCount = packages.filter((item) => Number(item.descuento) > 0).length;

  if (loading) {
    return (
      <section className="page packages-loading">
        <PackageGridSkeleton className="packages-grid" count={6} />
      </section>
    );
  }

  if (error) {
    return <p className="page-status">{error}</p>;
  }

  return (
    <>
    <PageHero
      image={packages.find((item) => item.cover)?.cover || bannerImage}
      eyebrow={`Colombia · ${cities.length} destinos`}
      title="Explora paquetes"
    >
      <p>
        {visible.length} {visible.length === 1 ? 'paquete disponible' : 'paquetes disponibles'}
        {people > 0 && ` para ${people} ${people === 1 ? 'persona' : 'personas'}`}
        {' '}· precios por persona en pesos colombianos
      </p>
    </PageHero>

    <section className="page page-after-hero">

      <form className="packages-search" role="search" onSubmit={(event) => event.preventDefault()}>
        <Icon name="search" size={20} />
        <input
          type="search"
          value={query}
          onChange={(event) => updateParam('q', event.target.value)}
          placeholder="Busca por destino o experiencia: playa, café, rafting, Caribe…"
          aria-label="Buscar paquetes"
        />
        {query && (
          <button type="button" className="packages-search-clear" onClick={() => updateParam('q', '')} aria-label="Borrar búsqueda">
            <Icon name="close" size={16} />
          </button>
        )}
      </form>
      {search.related.length > 0 && (
        <p className="packages-search-related">
          También buscamos: {search.related.slice(0, 8).join(', ')}{search.related.length > 8 ? '…' : ''}
        </p>
      )}

      <div className="packages-toolbar">
        <div className="packages-chips" role="group" aria-label="Filtrar por destino">
          <button type="button" className="chip" aria-pressed={!city} onClick={() => updateParam('ciudad', '')}>
            Todos
          </button>
          {cities.map((item) => (
            <button
              key={item.id_ciudad}
              type="button"
              className="chip"
              aria-pressed={city === String(item.id_ciudad)}
              onClick={() => updateParam('ciudad', String(item.id_ciudad))}
            >
              {item.nombre}
            </button>
          ))}
        </div>

        <div className="packages-selects">
          <button
            type="button"
            className="packages-toggle"
            aria-pressed={onlyDeals}
            onClick={() => updateParam('oferta', onlyDeals ? '' : '1')}
            title={dealsCount ? `${dealsCount} ${dealsCount === 1 ? 'paquete' : 'paquetes'} con descuento` : 'Ningún paquete tiene descuento ahora'}
          >
            <Icon name="tag" size={16} />
            Con descuento
            {dealsCount > 0 && <span className="packages-toggle-count">{dealsCount}</span>}
          </button>

          <label className="packages-select">
            <span>Mes</span>
            <MonthPicker
              value={month}
              onChange={(event) => updateParam('mes', event.target.value)}
              available={months}
              emptyLabel="Cualquiera"
            />
          </label>

          <label className="packages-select">
            <span>Calificación</span>
            <Select value={ratingKey} onChange={(event) => updateParam('estrellas', event.target.value)}>
              {RATING_OPTIONS.map((option) => (
                <option key={option.key || 'todas'} value={option.key}>{option.label}</option>
              ))}
            </Select>
          </label>

          <label className="packages-select">
            <span>Ordenar</span>
            <Select value={sort} onChange={(event) => updateParam('orden', event.target.value === 'fecha' ? '' : event.target.value)}>
              {Object.entries(SORTS).map(([key, option]) => (
                <option key={key} value={key}>{option.label}</option>
              ))}
            </Select>
          </label>
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="empty-state">
          <p>No encontramos paquetes con esos filtros.</p>
          {hasFilters && (
            <button type="button" className="btn btn-secondary" onClick={() => setSearchParams({}, { replace: true })}>
              Quitar filtros
            </button>
          )}
        </div>
      ) : (
        <div className="packages-grid">
          {visible.map((item) => (
            <PackageCard key={item.id_paquete_turistico} touristPackage={item} />
          ))}
        </div>
      )}
    </section>
    </>
  );
}

export default Packages;
