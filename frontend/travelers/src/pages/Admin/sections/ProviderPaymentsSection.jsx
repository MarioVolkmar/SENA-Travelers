import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import Modal from '../../../components/Modal/Modal';
import PaymentOrderDetail from '../../../components/PaymentOrderDetail/PaymentOrderDetail';
import { ORDER_BADGE, ORDER_STATUS_LABELS } from '../../../utils/paymentOrders';
import { formatCurrency, formatDate } from '../../../utils/format';
import { matches, useAdminAction } from '../adminShared';

import Select from '../../../components/Select/Select';
const FILTERS = [
  { key: '', label: 'Todas' },
  { key: 'pendiente', label: 'Pendientes' },
  { key: 'aprobada', label: 'Aprobadas' },
  { key: 'pagada', label: 'Pagadas' },
  { key: 'anulada', label: 'Anuladas' },
];

function sumBy(orders, states) {
  return orders.filter((order) => states.includes(order.estado)).reduce((sum, order) => sum + Number(order.monto), 0);
}

function isOverdue(order) {
  if (!['pendiente', 'aprobada'].includes(order.estado)) return false;
  const [year, month, day] = order.fecha_vencimiento.split('-').map(Number);
  return new Date(year, month - 1, day) < new Date(new Date().toDateString());
}

/** Formulario para registrar el pago (referencia de la transferencia) o anular la orden. */
function OrderActionModal({ order, mode, provider, onClose, onDone }) {
  const [referencia, setReferencia] = useState('');
  const [nota, setNota] = useState('');
  const { busy, error, run } = useAdminAction();
  const isPay = mode === 'pay';

  const handleSubmit = async (event) => {
    event.preventDefault();
    const { ok, result } = await run(() => (
      isPay
        ? api.patch(`/provider-payments/${order.id_orden}/pay`, { referencia_pago: referencia.trim(), nota: nota.trim() || null })
        : api.patch(`/provider-payments/${order.id_orden}/annul`, { nota: nota.trim() })
    ));
    if (ok) onDone(result.data);
  };

  const hasBank = provider?.numero_cuenta;

  return (
    <Modal
      title={isPay ? 'Registrar pago' : 'Anular orden'}
      subtitle={`${order.codigo} · ${order.nombre_proveedor} · ${formatCurrency(order.monto)}`}
      size="small"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={busy}>Cancelar</button>
          <button type="submit" form="order-action" className={`btn ${isPay ? 'btn-primary' : 'btn-danger'}`} disabled={busy}>
            {busy ? 'Guardando...' : isPay ? 'Marcar como pagada' : 'Anular orden'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}

      {isPay && (
        <div className={`alert ${hasBank ? 'alert-info' : 'alert-error'}`}>
          {hasBank ? (
            <span>
              Transferir a <strong>{provider.titular_cuenta || provider.nombre_empresa}</strong> · {provider.banco} ·
              cuenta de {provider.tipo_cuenta} <strong>{provider.numero_cuenta}</strong>
            </span>
          ) : (
            <span>El proveedor todavía no registró sus datos bancarios.</span>
          )}
        </div>
      )}

      <form id="order-action" onSubmit={handleSubmit}>
        {isPay && (
          <div className="field">
            <label htmlFor="order-ref">Referencia de la transferencia</label>
            <input id="order-ref" value={referencia} onChange={(event) => setReferencia(event.target.value)} minLength={3} maxLength={60} required />
          </div>
        )}
        <div className="field">
          <label htmlFor="order-note">{isPay ? 'Nota (opcional)' : 'Motivo de la anulación'}</label>
          <input
            id="order-note"
            value={nota}
            onChange={(event) => setNota(event.target.value)}
            minLength={isPay ? undefined : 3}
            maxLength={255}
            required={!isPay}
          />
        </div>
        <p className="field-hint">Los pagos son simulados: aquí solo se registra la transferencia.</p>
      </form>
    </Modal>
  );
}

function ProviderPaymentsSection() {
  const [orders, setOrders] = useState(null);
  const [providers, setProviders] = useState([]);
  const [filter, setFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [query, setQuery] = useState('');
  const [detail, setDetail] = useState(null);
  const [action, setAction] = useState(null); // { order, mode: 'pay' | 'annul' }
  const { busy, message, error, run, clear } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const [ordersResponse, providersResponse] = await Promise.all([
      api.get('/provider-payments/'),
      api.get('/providers/'),
    ]);
    setOrders(ordersResponse.data);
    setProviders(providersResponse.data);
  }, []);

  useEffect(() => {
    load().catch(() => setOrders([]));
  }, [load]);

  const approve = async (order) => {
    const accepted = await confirm({
      title: 'Aprobar orden de pago',
      subtitle: `${order.codigo} · ${order.nombre_proveedor}`,
      message: `La orden por ${formatCurrency(order.monto)} quedará lista para transferir.`,
      confirmLabel: 'Aprobar',
    });
    if (!accepted) return;

    const { ok } = await run(
      () => api.patch(`/provider-payments/${order.id_orden}/approve`),
      `Orden ${order.codigo} aprobada para pago.`
    );
    if (ok) await load();
  };

  if (!orders) return <p className="page-status">Cargando órdenes de pago...</p>;

  const visible = orders
    .filter((order) => !filter || order.estado === filter)
    .filter((order) => !providerFilter || String(order.proveedor_id) === providerFilter)
    .filter((order) => !query || matches(order.codigo, query) || matches(order.codigo_reserva, query) || matches(order.paquete, query));

  const overdue = orders.filter(isOverdue);

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Pagos a proveedores</h1>
          <p>Se generan solas cuando una reserva queda pagada: una orden por cada proveedor del paquete.</p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="admin-summary">
        <div className="admin-stat highlight">
          <span>Por pagar</span>
          <strong>{formatCurrency(sumBy(orders, ['pendiente', 'aprobada']))}</strong>
        </div>
        <div className="admin-stat">
          <span>Aprobadas, listas para transferir</span>
          <strong>{formatCurrency(sumBy(orders, ['aprobada']))}</strong>
        </div>
        <div className={`admin-stat ${overdue.length ? 'warning' : ''}`}>
          <span>Vencidas</span>
          <strong>{overdue.length}</strong>
        </div>
        <div className="admin-stat">
          <span>Pagado</span>
          <strong>{formatCurrency(sumBy(orders, ['pagada']))}</strong>
        </div>
      </div>

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por orden, reserva o paquete"
              aria-label="Buscar órdenes"
            />
          </label>
          <label className="admin-search" style={{ maxWidth: 230 }}>
            <Icon name="building" size={16} />
            <Select
              value={providerFilter}
              onChange={(event) => setProviderFilter(event.target.value)}
              aria-label="Filtrar por proveedor"
              style={{ border: 'none', background: 'transparent', font: 'inherit', flex: 1 }}
            >
              <option value="">Todos los proveedores</option>
              {providers.map((provider) => (
                <option key={provider.id_proveedor} value={provider.id_proveedor}>{provider.nombre_empresa}</option>
              ))}
            </Select>
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar por estado">
            {FILTERS.map((option) => (
              <button key={option.key} type="button" className="chip" aria-pressed={filter === option.key} onClick={() => setFilter(option.key)}>
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="órdenes">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Orden</th>
                <th>Proveedor</th>
                <th>Reserva</th>
                <th>Monto</th>
                <th>Vence</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((order) => {
                const open = ['pendiente', 'aprobada'].includes(order.estado);

                return (
                  <tr key={order.id_orden}>
                    <td>
                      <button type="button" className="link-button admin-strong" onClick={() => setDetail(order)}>
                        {order.codigo}
                      </button>
                    </td>
                    <td>{order.nombre_proveedor}</td>
                    <td>
                      <span className="admin-strong">{order.codigo_reserva}</span>
                      <br />
                      <span className="admin-muted">{order.paquete} · {formatDate(order.fecha_viaje)}</span>
                    </td>
                    <td className="admin-strong">{formatCurrency(order.monto)}</td>
                    <td className={isOverdue(order) ? 'order-overdue' : 'admin-muted'}>
                      {formatDate(order.fecha_vencimiento)}{isOverdue(order) && ' · vencida'}
                    </td>
                    <td><span className={`badge badge-${ORDER_BADGE[order.estado]}`}>{ORDER_STATUS_LABELS[order.estado]}</span></td>
                    <td>
                      <div className="admin-actions">
                        <IconButton icon="eye" label="Ver detalle" variant="info" onClick={() => setDetail(order)} />
                        <IconButton
                          icon="thumbUp"
                          label="Aprobar"
                          variant="success"
                          hidden={order.estado !== 'pendiente'}
                          disabled={busy}
                          onClick={() => approve(order)}
                        />
                        <IconButton
                          icon="dollar"
                          label="Registrar pago"
                          variant="primary"
                          hidden={!open}
                          onClick={() => { clear(); setAction({ order, mode: 'pay' }); }}
                        />
                        <IconButton
                          icon="ban"
                          label="Anular"
                          variant="danger"
                          hidden={!open}
                          onClick={() => { clear(); setAction({ order, mode: 'annul' }); }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && (
            <p className="admin-empty">
              {orders.length === 0
                ? 'Aún no hay órdenes. Si ya tenías reservas pagadas, genéralas desde Configuración.'
                : 'No hay órdenes con esos filtros.'}
            </p>
          )}
        </div>
      </div>

      {detail && <PaymentOrderDetail order={detail} onClose={() => setDetail(null)} />}

      {action && (
        <OrderActionModal
          order={action.order}
          mode={action.mode}
          provider={providers.find((provider) => provider.id_proveedor === action.order.proveedor_id)}
          onClose={() => setAction(null)}
          onDone={async (saved) => {
            setAction(null);
            await run(() => load(), saved.estado === 'pagada' ? `Orden ${saved.codigo} pagada.` : `Orden ${saved.codigo} anulada.`);
          }}
        />
      )}
      {dialog}
    </>
  );
}

export default ProviderPaymentsSection;
