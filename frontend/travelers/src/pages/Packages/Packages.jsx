import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

import bannerImage from '../../assets/images/banner.jpg';
import PackageCard from '../../components/PackageCard/PackageCard';
import PageHero from '../../components/PageHero/PageHero';
import usePackageCatalog from '../../hooks/usePackageCatalog';
import { finalPrice } from '../../utils/format';

import './Packages.css';

import Select from '../../components/Select/Select';
import MonthPicker from '../../components/DatePicker/MonthPicker';
const SORTS = {
  fecha: { label: 'Próxima salida', compare: (a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio) },
  menor: { label: 'Menor precio', compare: (a, b) => finalPrice(a) - finalPrice(b) },
  mayor: { label: 'Mayor precio', compare: (a, b) => finalPrice(b) - finalPrice(a) },
};

function Packages() {
  const { packages, loading, error } = usePackageCatalog({ withAvailability: true });
  const [searchParams, setSearchParams] = useSearchParams();

  const city = searchParams.get('ciudad') || '';
  const month = searchParams.get('mes') || '';
  const people = Number(searchParams.get('personas') || 0);
  const sort = SORTS[searchParams.get('orden')] ? searchParams.get('orden') : 'fecha';

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
    .filter((item) => !city || String(item.ciudad_id) === city)
    .filter((item) => !month || item.fecha_inicio.startsWith(month))
    .filter((item) => !people || item.availableSlots === undefined || item.availableSlots >= people)
    .sort(SORTS[sort].compare);

  const hasFilters = Boolean(city || month || people);

  if (loading) {
    return <p className="page-status">Cargando paquetes turísticos...</p>;
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
