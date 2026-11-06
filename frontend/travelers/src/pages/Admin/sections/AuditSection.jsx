import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import DatePicker from '../../../components/DatePicker/DatePicker';
import Icon from '../../../components/Icon/Icon';
import Pagination, { usePagination } from '../../../components/Pagination/Pagination';
import Select from '../../../components/Select/Select';

const ENTITIES = {
  paquete: { label: 'Paquetes', icon: 'box' },
  producto: { label: 'Productos', icon: 'grid' },
  proveedor: { label: 'Proveedores', icon: 'building' },
  usuario: { label: 'Usuarios', icon: 'users' },
  reserva: { label: 'Reservas', icon: 'ticket' },
  orden_pago: { label: 'Pagos a proveedores', icon: 'card' },
  configuracion: { label: 'Configuración', icon: 'sparkle' },
  ciudad: { label: 'Ciudades', icon: 'pin' },
  cupon: { label: 'Cupones', icon: 'tag' },
  resena: { label: 'Reseñas', icon: 'star' },
  recordatorio: { label: 'Recordatorios', icon: 'calendar' },
};

function formatDateTime(value) {
  if (!value) return '';
  return new Date(value).toLocaleString('es-CO', {
    day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

/** Bitácora: quién hizo qué cambio en la consola y cuándo. */
function AuditSection() {
  const [entries, setEntries] = useState(null);
  const [filters, setFilters] = useState({ entidad: '', desde: '', hasta: '', buscar: '' });
  const [search, setSearch] = useState('');

  const load = useCallback(async () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const response = await api.get('/audit/', { params: { ...params, limit: 1000 } });
    setEntries(response.data);
  }, [filters]);

  useEffect(() => {
    load().catch(() => setEntries([]));
  }, [load]);

  // La búsqueda de texto se aplica al dejar de escribir
  useEffect(() => {
    const timer = window.setTimeout(() => setFilters((current) => (
      current.buscar === search.trim() ? current : { ...current, buscar: search.trim() }
    )), 350);
    return () => window.clearTimeout(timer);
  }, [search]);

  const pager = usePagination(entries || [], [filters], 25);
  const update = (key) => (event) => setFilters((current) => ({ ...current, [key]: event.target.value }));

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Bitácora</h1>
          <p>Registro de los cambios que hacen los administradores: quién, qué y cuándo.</p>
        </div>
      </div>

      <div className="surface">
        <div className="admin-toolbar admin-audit-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar en la descripción" aria-label="Buscar en la bitácora" />
          </label>
          <div className="admin-audit-filters">
            <Select value={filters.entidad} onChange={update('entidad')} className="admin-select" aria-label="Filtrar por módulo">
              <option value="">Todos los módulos</option>
              {Object.entries(ENTITIES).map(([key, entity]) => <option key={key} value={key}>{entity.label}</option>)}
            </Select>
            <DatePicker value={filters.desde} onChange={update('desde')} max={filters.hasta || undefined} placeholder="Desde" className="admin-select" aria-label="Desde" />
            <DatePicker value={filters.hasta} onChange={update('hasta')} min={filters.desde || undefined} placeholder="Hasta" className="admin-select" aria-label="Hasta" />
          </div>
        </div>

        {!entries ? (
          <p className="page-status">Cargando bitácora...</p>
        ) : entries.length === 0 ? (
          <p className="admin-empty">No hay registros con esos filtros.</p>
        ) : (
          <ol className="admin-timeline">
            {pager.items.map((entry) => {
              const entity = ENTITIES[entry.entidad] || { label: entry.entidad, icon: 'history' };
              return (
                <li key={entry.id_registro} className="admin-timeline-item">
                  <span className={`admin-timeline-icon is-${entry.accion}`}>
                    <Icon name={entity.icon} size={16} />
                  </span>
                  <div className="admin-timeline-body">
                    <p className="admin-strong">{entry.descripcion}</p>
                    <p className="admin-muted">
                      {entry.usuario_nombre} · {entity.label} · {formatDateTime(entry.fecha)}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
        <Pagination {...pager} label="registros" />
      </div>
    </>
  );
}

export default AuditSection;
