import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import fallbackImage from '../../../assets/images/fondo.png';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import { formatCurrency, formatDateRange } from '../../../utils/format';
import { matches, useAdminAction } from '../adminShared';
import ConfirmDeleteModal from './ConfirmDeleteModal';
import PackageFormModal from './PackageFormModal';
import PackageImagesModal from './PackageImagesModal';

const FILTERS = [
  { key: '', label: 'Todos' },
  { key: 'activo', label: 'Activos' },
  { key: 'inactivo', label: 'Inactivos' },
];

function PackagesSection({ searchParams, onDataChanged }) {
  const [packages, setPackages] = useState(null);
  const [cities, setCities] = useState([]);
  const [products, setProducts] = useState([]);
  const [covers, setCovers] = useState({});
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [editing, setEditing] = useState(searchParams.get('nuevo') ? 'new' : null);
  const [imagesFor, setImagesFor] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { busy, message, error, run, clear } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const [packagesResponse, citiesResponse, productsResponse, coversResponse] = await Promise.all([
      api.get('/packages/admin'),
      api.get('/cities/'),
      api.get('/products/admin'),
      api.get('/packages/images/covers').catch(() => ({ data: [] })),
    ]);

    setPackages([...packagesResponse.data].sort((a, b) => b.fecha_inicio.localeCompare(a.fecha_inicio)));
    setCities(citiesResponse.data);
    setProducts(productsResponse.data);
    setCovers(Object.fromEntries(coversResponse.data.map((cover) => [cover.paquete_id, cover.imagen_url])));
  }, []);

  useEffect(() => {
    load().catch(() => setPackages([]));
  }, [load]);

  const cityName = (id) => cities.find((city) => city.id_ciudad === id)?.nombre || '';

  const toggleStatus = async (touristPackage) => {
    const nextStatus = touristPackage.estado === 'activo' ? 'inactivo' : 'activo';
    const accepted = await confirm({
      title: nextStatus === 'activo' ? 'Activar paquete' : 'Desactivar paquete',
      subtitle: touristPackage.nombre,
      message: nextStatus === 'activo'
        ? 'El paquete volverá a aparecer en el catálogo y se podrá reservar.'
        : 'El paquete dejará de aparecer en el catálogo. Las reservas existentes no cambian.',
      confirmLabel: nextStatus === 'activo' ? 'Activar' : 'Desactivar',
      tone: nextStatus === 'activo' ? 'primary' : 'danger',
    });
    if (!accepted) return;
    const { ok } = await run(
      () => api.patch(`/packages/${touristPackage.id_paquete_turistico}/status`, { estado: nextStatus }),
      `«${touristPackage.nombre}» ${nextStatus === 'activo' ? 'activado' : 'desactivado'}.`
    );

    if (ok) {
      await load();
      onDataChanged();
    }
  };

  if (!packages) return <p className="page-status">Cargando paquetes...</p>;

  const visible = packages
    .filter((item) => !filter || item.estado === filter)
    .filter((item) => !query || matches(item.nombre, query) || matches(cityName(item.ciudad_id), query));

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Paquetes</h1>
          <p>Crea, edita y publica los paquetes turísticos del catálogo.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => { clear(); setEditing('new'); }}>
          + Nuevo paquete
        </button>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por nombre o destino"
              aria-label="Buscar paquetes"
            />
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar por estado">
            {FILTERS.map((option) => (
              <button
                key={option.key}
                type="button"
                className="chip"
                aria-pressed={filter === option.key}
                onClick={() => setFilter(option.key)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="paquetes">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Paquete</th>
                <th>Fechas</th>
                <th>Precio</th>
                <th>Cupo</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((touristPackage) => {
                const isActive = touristPackage.estado === 'activo';

                return (
                  <tr key={touristPackage.id_paquete_turistico}>
                    <td>
                      <span className="admin-thumb-cell">
                        <img src={covers[touristPackage.id_paquete_turistico] || fallbackImage} alt="" loading="lazy" />
                        <span>
                          <span className="admin-strong">{touristPackage.nombre}</span>
                          <br />
                          <span className="admin-muted">{cityName(touristPackage.ciudad_id)}</span>
                        </span>
                      </span>
                    </td>
                    <td className="admin-muted">{formatDateRange(touristPackage.fecha_inicio, touristPackage.fecha_fin)}</td>
                    <td>
                      <span className="admin-strong">{formatCurrency(touristPackage.precio)}</span>
                      {touristPackage.descuento > 0 && <span className="admin-muted"> · −{touristPackage.descuento}%</span>}
                    </td>
                    <td>{touristPackage.cupo_max}</td>
                    <td><span className={`badge badge-${touristPackage.estado}`}>{touristPackage.estado}</span></td>
                    <td>
                      <div className="admin-actions">
                        <IconButton icon="edit" label="Editar" onClick={() => { clear(); setEditing(touristPackage.id_paquete_turistico); }} />
                        <IconButton icon="image" label="Fotos" variant="info" onClick={() => setImagesFor(touristPackage)} />
                        <IconButton
                          icon={isActive ? 'pause' : 'play'}
                          label={isActive ? 'Desactivar' : 'Activar'}
                          variant={isActive ? 'warning' : 'success'}
                          disabled={busy}
                          onClick={() => toggleStatus(touristPackage)}
                        />
                        <IconButton icon="trash" label="Eliminar" variant="danger" onClick={() => setDeleting(touristPackage)} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && <p className="admin-empty">No hay paquetes con esos filtros.</p>}
        </div>
      </div>

      {editing && (
        <PackageFormModal
          packageId={editing === 'new' ? null : editing}
          cities={cities}
          products={products}
          onClose={() => setEditing(null)}
          onSaved={async (saved, wasEdit) => {
            setEditing(null);
            await run(() => load(), wasEdit ? `«${saved.nombre}» actualizado.` : `«${saved.nombre}» creado. Ahora agrégale fotos.`);
            onDataChanged();
            if (!wasEdit) setImagesFor(saved);
          }}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal
          title="Eliminar paquete"
          name={deleting.nombre}
          consequences={[
            'Solo se puede si no tiene reservas; si las tiene, desactívalo.',
            'Se borran sus fotos registradas y su lista de productos (los productos no se borran).',
            'Las fotos subidas desde la consola también se borran del bucket de S3.',
          ]}
          request={() => api.delete(`/packages/${deleting.id_paquete_turistico}`)}
          onClose={() => setDeleting(null)}
          onDeleted={async () => {
            const name = deleting.nombre;
            setDeleting(null);
            await run(() => load(), `«${name}» eliminado.`);
            onDataChanged();
          }}
        />
      )}

      {imagesFor && (
        <PackageImagesModal
          touristPackage={imagesFor}
          onClose={() => setImagesFor(null)}
          onChanged={() => load()}
        />
      )}
      {dialog}
    </>
  );
}

export default PackagesSection;
