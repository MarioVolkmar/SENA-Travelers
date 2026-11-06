import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Avatar from '../../components/Avatar/Avatar';
import useConfirm from '../../components/ConfirmDialog/useConfirm';
import Toast from '../../components/Toast/Toast';
import Icon from '../../components/Icon/Icon';
import IconButton from '../../components/IconButton/IconButton';
import ProductFormModal from '../../components/ProductFormModal/ProductFormModal';
import { useAuth } from '../../context/AuthContext';
import { formatCurrency, formatDate, formatDateRange, getErrorMessage } from '../../utils/format';
import { productTypeIcon, productTypeLabel, unitShortLabel, useProductTypes } from '../../utils/productTypes';
import PaymentOrderDetail from '../../components/PaymentOrderDetail/PaymentOrderDetail';
import { ORDER_BADGE, ORDER_STATUS_LABELS } from '../../utils/paymentOrders';
import { useAdminAction } from '../Admin/adminShared';

import '../Admin/AdminDashboard.css';
import './ProviderPanel.css';

import Select from '../../components/Select/Select';
const SECTIONS = [
  { key: 'resumen', label: 'Resumen', icon: 'home' },
  { key: 'productos', label: 'Mis productos', icon: 'grid' },
  { key: 'pagos', label: 'Mis pagos', icon: 'card' },
  { key: 'empresa', label: 'Mi empresa', icon: 'building' },
];

function ProviderPanel() {
  const { user } = useAuth();
  const types = useProductTypes();
  const [searchParams, setSearchParams] = useSearchParams();

  const [dashboard, setDashboard] = useState(null);
  const [cities, setCities] = useState([]);
  const [loadError, setLoadError] = useState('');

  const active = SECTIONS.find((section) => section.key === searchParams.get('seccion')) || SECTIONS[0];

  const load = useCallback(async () => {
    try {
      const [dashboardResponse, citiesResponse] = await Promise.all([
        api.get('/providers/me/dashboard'),
        api.get('/cities/'),
      ]);
      setDashboard(dashboardResponse.data);
      setCities(citiesResponse.data);
    } catch (requestError) {
      setLoadError(getErrorMessage(requestError, 'No fue posible cargar tu panel.'));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const goTo = (key) => setSearchParams(key === 'resumen' ? {} : { seccion: key });
  const cityName = (id) => cities.find((city) => city.id_ciudad === id)?.nombre || '';

  if (loadError) return <p className="page-status">{loadError}</p>;
  if (!dashboard) return <p className="page-status">Cargando tu panel...</p>;

  const { proveedor } = dashboard;

  return (
    <div className="admin-layout provider-layout">
      <aside className="admin-sidebar provider-sidebar">
        <div className="admin-identity">
          <Avatar user={user} size={44} />
          <div>
            <p className="admin-identity-name">{proveedor.nombre_empresa}</p>
            <p className="admin-identity-role">Proveedor · {user.nombre.split(' ')[0]}</p>
          </div>
        </div>

        <p className="admin-sidebar-title">Mi panel</p>
        <nav className="admin-menu" aria-label="Secciones del panel">
          {SECTIONS.map((section) => (
            <button
              key={section.key}
              type="button"
              aria-current={active.key === section.key ? 'page' : undefined}
              className={`admin-menu-item ${active.key === section.key ? 'active' : ''}`}
              onClick={() => goTo(section.key)}
            >
              <Icon name={section.icon} size={20} />
              <span>{section.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="admin-main">
        {active.key === 'resumen' && (
          <SummarySection dashboard={dashboard} cityName={cityName} goTo={goTo} user={user} />
        )}
        {active.key === 'productos' && (
          <ProductsSection dashboard={dashboard} cities={cities} types={types} cityName={cityName} reload={load} />
        )}
        {active.key === 'pagos' && (
          <PaymentsSection provider={proveedor} goTo={goTo} />
        )}
        {active.key === 'empresa' && (
          <CompanySection provider={proveedor} cities={cities} reload={load} />
        )}
      </section>
    </div>
  );
}

// ---------------------------------------------------------------
// Resumen
// ---------------------------------------------------------------

function SummarySection({ dashboard, cityName, goTo, user }) {
  const { resumen, paquetes } = dashboard;

  const cards = [
    { label: 'Productos activos', value: resumen.productos_activos, highlight: true, section: 'productos' },
    { label: 'Paquetes que te incluyen', value: resumen.paquetes },
    { label: 'Viajeros confirmados próximos', value: resumen.viajeros_proximos },
  ];

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Hola, {user.nombre.split(' ')[0]}</h1>
          <p>Así van los servicios de {dashboard.proveedor.nombre_empresa} en Travelers.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => goTo('productos')}>
          Gestionar productos
        </button>
      </div>

      <div className="admin-summary">
        {cards.map((card) => (
          card.section ? (
            <button
              key={card.label}
              type="button"
              className={`admin-stat ${card.highlight ? 'highlight' : ''}`}
              onClick={() => goTo(card.section)}
            >
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </button>
          ) : (
            <div key={card.label} className="admin-stat">
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </div>
          )
        ))}
      </div>

      <div className="surface">
        <div className="admin-panel-header">
          <h2>Paquetes donde están tus servicios</h2>
        </div>

        {paquetes.length === 0 ? (
          <p className="admin-empty">
            Todavía ningún paquete incluye tus productos. Cuando el administrador los agregue, aquí verás las salidas y cuántos viajeros van.
          </p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Paquete</th>
                  <th>Fechas</th>
                  <th>Tus servicios</th>
                  <th>Viajeros confirmados</th>
                  <th>Por confirmar</th>
                </tr>
              </thead>
              <tbody>
                {paquetes.map((item) => (
                  <tr key={item.id_paquete_turistico}>
                    <td>
                      <span className="admin-strong">{item.nombre}</span>
                      <br />
                      <span className="admin-muted">
                        {cityName(item.ciudad_id)}{item.estado !== 'activo' && ' · inactivo'}
                      </span>
                    </td>
                    <td className="admin-muted">{formatDateRange(item.fecha_inicio, item.fecha_fin)}</td>
                    <td>{item.productos.join(', ')}</td>
                    <td>
                      <span className="admin-strong">{item.viajeros_confirmados}</span>
                      <span className="admin-muted"> en {item.reservas_confirmadas} reservas</span>
                    </td>
                    <td className="admin-muted">{item.viajeros_pendientes} personas</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

// ---------------------------------------------------------------
// Mis productos
// ---------------------------------------------------------------

function ProductsSection({ dashboard, cities, types, cityName, reload }) {
  const [editing, setEditing] = useState(null);
  const { busy, message, error, run, clear } = useAdminAction();
  const { confirm, dialog } = useConfirm();
  const { productos, paquetes, proveedor } = dashboard;

  const packagesUsing = (product) =>
    paquetes.filter((item) => item.productos.includes(product.nombre)).length;

  const toggleStatus = async (product) => {
    const estado = product.estado === 'activo' ? 'inactivo' : 'activo';
    const accepted = await confirm({
      title: estado === 'activo' ? 'Activar producto' : 'Pausar producto',
      subtitle: product.nombre,
      message: estado === 'activo'
        ? 'Travelers podrá volver a incluirlo en paquetes.'
        : 'Mientras esté en pausa no se agregará a nuevos paquetes.',
      confirmLabel: estado === 'activo' ? 'Activar' : 'Pausar',
      tone: estado === 'activo' ? 'primary' : 'danger',
    });
    if (!accepted) return;
    const { ok } = await run(
      () => api.patch(`/products/${product.id_producto}/status`, { estado }),
      estado === 'activo' ? `«${product.nombre}» vuelve a estar disponible.` : `«${product.nombre}» quedó en pausa.`
    );
    if (ok) await reload();
  };

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Mis productos</h1>
          <p>Hoteles, comidas, transportes, tours... los servicios que ofreces para los paquetes.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => { clear(); setEditing('new'); }}>
          + Nuevo producto
        </button>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      {productos.length === 0 ? (
        <div className="empty-state">
          <p>Aún no tienes productos. Agrega tu primer servicio para que el equipo de Travelers pueda incluirlo en los paquetes.</p>
          <button type="button" className="btn btn-primary" onClick={() => setEditing('new')}>Crear mi primer producto</button>
        </div>
      ) : (
        <div className="provider-products">
          {productos.map((product) => {
            const usedIn = packagesUsing(product);
            const isActive = product.estado === 'activo';

            return (
              <article key={product.id_producto} className={`provider-product ${isActive ? '' : 'is-paused'}`}>
                <div className="provider-product-top">
                  <span className="provider-product-icon">
                    <Icon name={productTypeIcon(product.tipo_producto)} size={24} />
                  </span>
                  <span className={`badge badge-${product.estado}`}>{isActive ? 'Activo' : 'En pausa'}</span>
                </div>
                <p className="provider-product-type">{productTypeLabel(types, product.tipo_producto)}</p>
                <h3>{product.nombre}</h3>
                <p className="provider-product-description">{product.descripcion}</p>
                <dl className="provider-product-data">
                  <div><dt>Costo {unitShortLabel(product.unidad_cobro)}</dt><dd>{formatCurrency(product.costo)}</dd></div>
                  <div><dt>Ciudad</dt><dd>{cityName(product.ciudad_id)}</dd></div>
                  <div><dt>Paquetes</dt><dd>{usedIn}</dd></div>
                </dl>
                <div className="provider-product-actions">
                  <IconButton icon="edit" label="Editar" onClick={() => { clear(); setEditing(product); }} />
                  <IconButton
                    icon={isActive ? 'pause' : 'play'}
                    label={isActive ? 'Pausar' : 'Activar'}
                    variant={isActive ? 'warning' : 'success'}
                    disabled={busy}
                    onClick={() => toggleStatus(product)}
                  />
                </div>
              </article>
            );
          })}
        </div>
      )}

      {editing && (
        <ProductFormModal
          product={editing === 'new' ? null : editing}
          cities={cities}
          types={types}
          fixedProviderId={proveedor.id_proveedor}
          onClose={() => setEditing(null)}
          onSaved={async (saved, wasEdit) => {
            setEditing(null);
            await run(() => reload(), `«${saved.nombre}» ${wasEdit ? 'actualizado' : 'creado'}.`);
          }}
        />
      )}
      {dialog}
    </>
  );
}

// ---------------------------------------------------------------
// Mis pagos
// ---------------------------------------------------------------

const PAYMENT_FILTERS = [
  { key: '', label: 'Todas' },
  { key: 'pendiente', label: 'Pendientes' },
  { key: 'aprobada', label: 'Aprobadas' },
  { key: 'pagada', label: 'Pagadas' },
  { key: 'anulada', label: 'Anuladas' },
];

function PaymentsSection({ provider, goTo }) {
  const [orders, setOrders] = useState(null);
  const [filter, setFilter] = useState('');
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    api.get('/provider-payments/me').then((response) => setOrders(response.data)).catch(() => setOrders([]));
  }, []);

  if (!orders) return <p className="page-status">Cargando tus pagos...</p>;

  const total = (states) => orders
    .filter((order) => states.includes(order.estado))
    .reduce((sum, order) => sum + Number(order.monto), 0);

  const nextDue = orders
    .filter((order) => ['pendiente', 'aprobada'].includes(order.estado))
    .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento))[0];

  const visible = orders.filter((order) => !filter || order.estado === filter);

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Mis pagos</h1>
          <p>Lo que Travelers te paga por los servicios de cada reserva confirmada.</p>
        </div>
      </div>

      {!provider.numero_cuenta && (
        <div className="alert alert-error">
          <span>
            Aún no registras una cuenta bancaria, así que no podemos transferirte.{' '}
            <button type="button" className="link-button" onClick={() => goTo('empresa')}>Agregar datos bancarios</button>
          </span>
        </div>
      )}

      <div className="admin-summary">
        <div className="admin-stat highlight">
          <span>Por cobrar</span>
          <strong>{formatCurrency(total(['pendiente', 'aprobada']))}</strong>
        </div>
        <div className="admin-stat">
          <span>Aprobado, en proceso de pago</span>
          <strong>{formatCurrency(total(['aprobada']))}</strong>
        </div>
        <div className="admin-stat">
          <span>Ya pagado</span>
          <strong>{formatCurrency(total(['pagada']))}</strong>
        </div>
        <div className="admin-stat">
          <span>Próximo vencimiento</span>
          <strong>{nextDue ? formatDate(nextDue.fecha_vencimiento) : '—'}</strong>
        </div>
      </div>

      <div className="surface">
        <div className="admin-toolbar">
          <div className="admin-filters" role="group" aria-label="Filtrar por estado">
            {PAYMENT_FILTERS.map((option) => (
              <button key={option.key} type="button" className="chip" aria-pressed={filter === option.key} onClick={() => setFilter(option.key)}>
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {orders.length === 0 ? (
          <p className="admin-empty">
            Todavía no tienes órdenes de pago. Se crean cuando un viajero paga una reserva de un paquete que incluye tus servicios.
          </p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Orden</th>
                  <th>Paquete y viaje</th>
                  <th>Viajeros</th>
                  <th>Monto</th>
                  <th>Vence</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((order) => (
                  <tr key={order.id_orden}>
                    <td>
                      <button type="button" className="link-button admin-strong" onClick={() => setDetail(order)}>
                        {order.codigo}
                      </button>
                    </td>
                    <td>
                      <span className="admin-strong">{order.paquete}</span>
                      <br />
                      <span className="admin-muted">{order.codigo_reserva} · {formatDate(order.fecha_viaje)}</span>
                    </td>
                    <td>{order.viajeros}</td>
                    <td className="admin-strong">{formatCurrency(order.monto)}</td>
                    <td className="admin-muted">
                      {order.estado === 'pagada' ? `Pagada ${formatDate(order.fecha_pago)}` : formatDate(order.fecha_vencimiento)}
                    </td>
                    <td><span className={`badge badge-${ORDER_BADGE[order.estado]}`}>{ORDER_STATUS_LABELS[order.estado]}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {visible.length === 0 && <p className="admin-empty">No hay órdenes con ese estado.</p>}
          </div>
        )}
      </div>

      {detail && <PaymentOrderDetail order={detail} onClose={() => setDetail(null)} />}
    </>
  );
}

// ---------------------------------------------------------------
// Mi empresa
// ---------------------------------------------------------------

function CompanySection({ provider, cities, reload }) {
  const [form, setForm] = useState({
    nombre_empresa: provider.nombre_empresa,
    telefono: provider.telefono,
    direccion: provider.direccion,
    ciudad_id: String(provider.ciudad_id),
    banco: provider.banco || '',
    tipo_cuenta: provider.tipo_cuenta || 'ahorros',
    numero_cuenta: provider.numero_cuenta || '',
    titular_cuenta: provider.titular_cuenta || '',
  });
  const { busy, message, error, run } = useAdminAction();

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  const handleSubmit = async (event) => {
    event.preventDefault();
    const { ok } = await run(
      () => api.patch(`/providers/${provider.id_proveedor}`, {
        nombre_empresa: form.nombre_empresa.trim(),
        telefono: form.telefono.trim(),
        direccion: form.direccion.trim(),
        ciudad_id: Number(form.ciudad_id),
        // Los datos bancarios son opcionales: solo se envían si los llenó
        ...(form.numero_cuenta.trim() && {
          banco: form.banco.trim(),
          tipo_cuenta: form.tipo_cuenta,
          numero_cuenta: form.numero_cuenta.trim(),
          titular_cuenta: form.titular_cuenta.trim(),
        }),
      }),
      'Datos de la empresa actualizados.',
      'No fue posible guardar los datos.'
    );
    if (ok) await reload();
  };

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Mi empresa</h1>
          <p>Estos datos los ve el equipo de Travelers para coordinar los servicios.</p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <form className="surface admin-form-grid provider-company" onSubmit={handleSubmit}>
        <div className="field field-full">
          <label htmlFor="company-name">Nombre de la empresa</label>
          <input id="company-name" value={form.nombre_empresa} onChange={update('nombre_empresa')} minLength={2} maxLength={100} required />
        </div>
        <div className="field">
          <label htmlFor="company-rut">RUT</label>
          <input id="company-rut" value={provider.rut} disabled />
          <span className="field-hint">Para cambiarlo, escribe al administrador.</span>
        </div>
        <div className="field">
          <label htmlFor="company-phone">Teléfono</label>
          <input id="company-phone" value={form.telefono} onChange={update('telefono')} minLength={7} maxLength={30} required />
        </div>
        <div className="field">
          <label htmlFor="company-address">Dirección</label>
          <input id="company-address" value={form.direccion} onChange={update('direccion')} minLength={5} maxLength={45} required />
        </div>
        <div className="field">
          <label htmlFor="company-city">Ciudad</label>
          <Select id="company-city" value={form.ciudad_id} onChange={update('ciudad_id')} required>
            {cities.map((city) => (
              <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
            ))}
          </Select>
        </div>
        <div className="field-full provider-bank-title">
          <h2>Cuenta para recibir pagos</h2>
          <p className="admin-muted">Travelers transfiere aquí el valor de tus órdenes de pago.</p>
        </div>
        <div className="field">
          <label htmlFor="bank-name">Banco</label>
          <input
            id="bank-name"
            value={form.banco}
            onChange={update('banco')}
            placeholder="Ej.: Bancolombia"
            minLength={2}
            maxLength={60}
            required={Boolean(form.numero_cuenta)}
          />
        </div>
        <div className="field">
          <label htmlFor="bank-type">Tipo de cuenta</label>
          <Select id="bank-type" value={form.tipo_cuenta} onChange={update('tipo_cuenta')}>
            <option value="ahorros">Ahorros</option>
            <option value="corriente">Corriente</option>
          </Select>
        </div>
        <div className="field">
          <label htmlFor="bank-number">Número de cuenta</label>
          <input
            id="bank-number"
            inputMode="numeric"
            pattern="[0-9-]+"
            value={form.numero_cuenta}
            onChange={update('numero_cuenta')}
            minLength={5}
            maxLength={30}
          />
        </div>
        <div className="field">
          <label htmlFor="bank-holder">Titular</label>
          <input
            id="bank-holder"
            value={form.titular_cuenta}
            onChange={update('titular_cuenta')}
            minLength={2}
            maxLength={100}
            required={Boolean(form.numero_cuenta)}
          />
        </div>

        <div className="field-full">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </>
  );
}

export default ProviderPanel;
