import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import Modal from '../../../components/Modal/Modal';
import PaymentOrderDetail from '../../../components/PaymentOrderDetail/PaymentOrderDetail';
import { daysLabel, ORDER_BADGE, ORDER_STATUS_LABELS, orderUrgency } from '../../../utils/paymentOrders';
import { formatCurrency, formatDate, getErrorMessage } from '../../../utils/format';
import { matches, useAdminAction } from '../adminShared';

import Select from '../../../components/Select/Select';

const FILTERS = [
  { key: '', label: 'Todas' },
  { key: 'pendiente', label: 'Pendientes' },
  { key: 'aprobada', label: 'Aprobadas' },
  { key: 'pagada', label: 'Pagadas' },
  { key: 'anulada', label: 'Anuladas' },
];

const SORTS = {
  urgencia: { label: 'Más urgentes primero', compare: (a, b) => orderUrgency(a).sortKey - orderUrgency(b).sortKey || b.id_orden - a.id_orden },
  plazo: { label: 'Plazo de aprobación', compare: (a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento) },
  recientes: { label: 'Más recientes', compare: (a, b) => b.id_orden - a.id_orden },
  monto: { label: 'Mayor monto', compare: (a, b) => Number(b.monto) - Number(a.monto) },
};

const URGENCY_TEXT = {
  overdue: 'Vencida',
  urgent: '2 días o menos',
  soon: 'Esta semana',
  normal: 'Con tiempo',
};

function sumBy(orders, states) {
  return orders.filter((order) => states.includes(order.estado)).reduce((sum, order) => sum + Number(order.monto), 0);
}

/** Datos bancarios del proveedor, o el aviso de que aún no los registra. */
function BankInfo({ provider }) {
  if (!provider?.numero_cuenta) {
    return (
      <div className="alert alert-error">
        <span>
          <strong>El proveedor aún no ha completado sus datos bancarios.</strong> No se puede aprobar ni pagar esta orden
          hasta que los registre en su panel de proveedor.
        </span>
      </div>
    );
  }
  return (
    <div className="alert alert-info">
      <span>
        Transferir a <strong>{provider.titular_cuenta || provider.nombre_empresa}</strong> · {provider.banco} ·
        cuenta de {provider.tipo_cuenta} <strong>{provider.numero_cuenta}</strong>
      </span>
    </div>
  );
}

/** Aprobar una orden: muestra a quién se le pagará y cuándo, o el aviso de datos bancarios faltantes. */
function ApproveModal({ order, provider, schedule, onClose, onDone }) {
  const { busy, error, run } = useAdminAction();
  const hasBank = Boolean(provider?.numero_cuenta);

  const approve = async () => {
    const { ok, result } = await run(() => api.patch(`/provider-payments/${order.id_orden}/approve`));
    if (ok) onDone(result.data);
  };

  return (
    <Modal
      title="Aprobar orden de pago"
      subtitle={`${order.codigo} · ${order.nombre_proveedor} · ${formatCurrency(order.monto)}`}
      size="small"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={busy}>Cancelar</button>
          <button type="button" className="btn btn-primary" onClick={approve} disabled={busy || !hasBank}>
            {busy ? 'Aprobando...' : 'Aprobar'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}
      <BankInfo provider={provider} />
      {hasBank && (
        <p className="field-hint">
          Al aprobarla queda lista para transferir.
          {schedule && <> Se pagará el próximo día de pago: <strong>{formatDate(schedule.proximo_pago)}</strong>.</>}
        </p>
      )}
    </Modal>
  );
}

/** Registrar el pago (referencia y comprobante opcional) o anular la orden. */
function OrderActionModal({ order, mode, provider, onClose, onDone }) {
  const [referencia, setReferencia] = useState('');
  const [nota, setNota] = useState('');
  const [receipt, setReceipt] = useState(null);
  const [receiptError, setReceiptError] = useState('');
  const { busy, error, run } = useAdminAction();
  const isPay = mode === 'pay';
  const hasBank = Boolean(provider?.numero_cuenta);

  const pickReceipt = (event) => {
    const file = event.target.files?.[0] || null;
    setReceiptError('');
    if (file && file.size > 5 * 1024 * 1024) {
      setReceiptError('La imagen no puede superar los 5 MB.');
      event.target.value = '';
      setReceipt(null);
      return;
    }
    setReceipt(file);
  };

  const clearReceipt = () => {
    setReceipt(null);
    setReceiptError('');
    const input = document.getElementById('order-receipt');
    if (input) input.value = '';
  };

  const [preview, setPreview] = useState('');
  useEffect(() => {
    if (!receipt) {
      setPreview('');
      return undefined;
    }
    const url = URL.createObjectURL(receipt);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [receipt]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const { ok, result } = await run(async () => {
      if (!isPay) return api.patch(`/provider-payments/${order.id_orden}/annul`, { nota: nota.trim() });

      const paid = await api.patch(`/provider-payments/${order.id_orden}/pay`, {
        referencia_pago: referencia.trim(),
        nota: nota.trim() || null,
      });
      if (!receipt) return paid;

      // El pago ya quedó registrado; si el comprobante falla se avisa, pero el pago no se pierde
      try {
        const body = new FormData();
        body.append('file', receipt);
        return await api.post(`/provider-payments/${order.id_orden}/receipt`, body);
      } catch (uploadError) {
        return { ...paid, receiptFailed: getErrorMessage(uploadError, 'No se pudo subir el comprobante.') };
      }
    });
    if (ok) onDone(result.data, result.receiptFailed);
  };

  return (
    <Modal
      title={isPay ? 'Registrar pago' : 'Anular orden'}
      subtitle={`${order.codigo} · ${order.nombre_proveedor} · ${formatCurrency(order.monto)}`}
      size="small"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={busy}>Cancelar</button>
          <button
            type="submit"
            form="order-action"
            className={`btn ${isPay ? 'btn-primary' : 'btn-danger'}`}
            disabled={busy || (isPay && !hasBank)}
          >
            {busy ? 'Guardando...' : isPay ? 'Marcar como pagada' : 'Anular orden'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}
      {isPay && <BankInfo provider={provider} />}

      <form id="order-action" onSubmit={handleSubmit}>
        {isPay && (
          <div className="field">
            <label htmlFor="order-ref">Referencia de la transferencia</label>
            <input
              id="order-ref"
              value={referencia}
              onChange={(event) => setReferencia(event.target.value)}
              minLength={3}
              maxLength={60}
              required
              disabled={!hasBank}
            />
          </div>
        )}
        {isPay && (
          <div className="field">
            <label htmlFor="order-receipt">Comprobante (imagen, opcional)</label>
            <input
              id="order-receipt"
              className="receipt-input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={pickReceipt}
              disabled={!hasBank}
            />
            {receipt ? (
              <div className="receipt-chosen">
                {preview && <img src={preview} alt="Vista previa del comprobante" />}
                <div className="receipt-chosen-info">
                  <strong title={receipt.name}>{receipt.name}</strong>
                  <small>{receipt.size >= 1024 * 1024 ? `${(receipt.size / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(receipt.size / 1024))} KB`}</small>
                </div>
                <label htmlFor="order-receipt" className="btn btn-outline btn-small receipt-chosen-btn">Cambiar</label>
                <IconButton icon="trash" label="Quitar comprobante" variant="danger" onClick={clearReceipt} />
              </div>
            ) : (
              <label htmlFor="order-receipt" className={`receipt-drop ${hasBank ? '' : 'disabled'}`}>
                <Icon name="image" size={22} />
                <span>
                  <strong>Elegir imagen</strong>
                  <small>Haz clic para adjuntar el comprobante de la transferencia</small>
                </span>
              </label>
            )}
            {receiptError
              ? <span className="field-hint field-error" role="alert">{receiptError}</span>
              : <span className="field-hint">JPG, PNG o WEBP de máximo 5 MB. El proveedor también podrá verlo.</span>}
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
        {isPay && <p className="field-hint">Los pagos son simulados: aquí solo se registra la transferencia.</p>}
      </form>
    </Modal>
  );
}

function ProviderPaymentsSection({ searchParams }) {
  const [orders, setOrders] = useState(null);
  const [providers, setProviders] = useState([]);
  const [schedule, setSchedule] = useState(null);
  const [filter, setFilter] = useState('');
  const [providerFilter, setProviderFilter] = useState(() => searchParams?.get('proveedor') || '');
  const [sort, setSort] = useState('urgencia');
  const [query, setQuery] = useState('');
  const [detail, setDetail] = useState(null);
  const [approving, setApproving] = useState(null);
  const [action, setAction] = useState(null); // { order, mode: 'pay' | 'annul' }
  const { message, error, run, clear } = useAdminAction();

  const load = useCallback(async () => {
    const [ordersResponse, providersResponse, scheduleResponse] = await Promise.all([
      api.get('/provider-payments/'),
      api.get('/providers/'),
      api.get('/provider-payments/schedule').catch(() => ({ data: null })),
    ]);
    setOrders(ordersResponse.data);
    setProviders(providersResponse.data);
    setSchedule(scheduleResponse.data);
  }, []);

  useEffect(() => {
    load().catch(() => setOrders([]));
  }, [load]);

  if (!orders) return <p className="page-status">Cargando órdenes de pago...</p>;

  const providerOf = (order) => providers.find((provider) => provider.id_proveedor === order.proveedor_id);

  const visible = orders
    .filter((order) => !filter || order.estado === filter)
    .filter((order) => !providerFilter || String(order.proveedor_id) === providerFilter)
    .filter((order) => !query || matches(order.codigo, query) || matches(order.codigo_reserva, query) || matches(order.paquete, query))
    .sort(SORTS[sort].compare);

  const urgencies = orders.map(orderUrgency);
  const overdue = urgencies.filter((item) => item.level === 'overdue').length;
  const urgent = urgencies.filter((item) => item.level === 'urgent').length;
  const approvedTotal = sumBy(orders, ['aprobada']);

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Pagos a proveedores</h1>
          <p>
            Se generan solas cuando una reserva queda pagada: una orden por cada proveedor del paquete.
            Un administrador la aprueba dentro de su plazo y se paga el día de pago programado.
          </p>
        </div>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="admin-summary">
        <div className="admin-stat highlight">
          <span>Próximo pago programado</span>
          <strong>{schedule ? formatDate(schedule.proximo_pago) : '—'}</strong>
          {approvedTotal > 0 && <small>{formatCurrency(approvedTotal)} en órdenes aprobadas</small>}
        </div>
        <div className="admin-stat">
          <span>Por pagar</span>
          <strong>{formatCurrency(sumBy(orders, ['pendiente', 'aprobada']))}</strong>
        </div>
        <div className="admin-stat deadline-stat">
          <span>Plazo de aprobación</span>
          {overdue || urgent ? (
            <div className="deadline-counts">
              <div className={`deadline-count overdue ${overdue ? '' : 'zero'}`}>
                <strong>{overdue}</strong>
                <small>{overdue === 1 ? 'vencida' : 'vencidas'}</small>
              </div>
              <div className={`deadline-count urgent ${urgent ? '' : 'zero'}`}>
                <strong>{urgent}</strong>
                <small>vence{urgent === 1 ? '' : 'n'} en 2 días o menos</small>
              </div>
            </div>
          ) : (
            <>
              <strong className="deadline-ok">Al día</strong>
              <small>Ninguna orden pendiente está vencida ni por vencer</small>
            </>
          )}
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
                <option key={provider.id_proveedor} value={String(provider.id_proveedor)}>{provider.nombre_empresa}</option>
              ))}
            </Select>
          </label>
          <label className="admin-search" style={{ maxWidth: 230 }}>
            <Icon name="clock" size={16} />
            <Select
              value={sort}
              onChange={(event) => setSort(event.target.value)}
              aria-label="Ordenar órdenes"
              style={{ border: 'none', background: 'transparent', font: 'inherit', flex: 1 }}
            >
              {Object.entries(SORTS).map(([key, item]) => (
                <option key={key} value={key}>{item.label}</option>
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

        <div className="order-legend" aria-label="Colores según la cercanía de la fecha">
          {Object.entries(URGENCY_TEXT).map(([level, text]) => (
            <span key={level} className={`order-legend-item order-urgency-${level}`}><i /> {text}</span>
          ))}
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
                <th>Fecha clave</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((order) => {
                const open = ['pendiente', 'aprobada'].includes(order.estado);
                const urgency = orderUrgency(order);

                return (
                  <tr key={order.id_orden} className={`order-row order-row-${urgency.level}`}>
                    <td>
                      <button type="button" className="link-button admin-strong" onClick={() => setDetail(order)}>
                        {order.codigo}
                      </button>
                    </td>
                    <td>
                      {order.nombre_proveedor}
                      {open && !order.tiene_datos_bancarios && (
                        <>
                          <br />
                          <span className="order-no-bank">Sin datos bancarios</span>
                        </>
                      )}
                    </td>
                    <td>
                      <span className="admin-strong">{order.codigo_reserva}</span>
                      <br />
                      <span className="admin-muted">{order.paquete} · {formatDate(order.fecha_viaje)}</span>
                    </td>
                    <td className="admin-strong">{formatCurrency(order.monto)}</td>
                    <td>
                      {urgency.date ? (
                        <span className={`order-urgency order-urgency-${urgency.level}`}>
                          <span className="admin-muted">{urgency.label}</span>
                          <br />
                          <strong>{formatDate(urgency.date)}</strong> · {daysLabel(urgency.days)}
                        </span>
                      ) : (
                        <span className="admin-muted">
                          {order.estado === 'pagada' ? `Pagada el ${formatDate(order.fecha_pago)}` : '—'}
                        </span>
                      )}
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
                          onClick={() => { clear(); setApproving(order); }}
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
              {orders.length === 0 ? 'Aún no hay órdenes: se crean cuando se paga una reserva.' : 'No hay órdenes con esos filtros.'}
            </p>
          )}
        </div>
      </div>

      {detail && <PaymentOrderDetail order={detail} onClose={() => setDetail(null)} />}

      {approving && (
        <ApproveModal
          order={approving}
          provider={providerOf(approving)}
          schedule={schedule}
          onClose={() => setApproving(null)}
          onDone={async (saved) => {
            setApproving(null);
            await run(() => load(), `Orden ${saved.codigo} aprobada. Se pagará el ${formatDate(saved.fecha_pago_programada)}.`);
          }}
        />
      )}

      {action && (
        <OrderActionModal
          order={action.order}
          mode={action.mode}
          provider={providerOf(action.order)}
          onClose={() => setAction(null)}
          onDone={async (saved, receiptFailed) => {
            setAction(null);
            const text = saved.estado === 'pagada'
              ? `Orden ${saved.codigo} pagada.${receiptFailed ? ` ${receiptFailed}` : ''}`
              : `Orden ${saved.codigo} anulada.`;
            await run(() => load(), text);
          }}
        />
      )}
    </>
  );
}

export default ProviderPaymentsSection;
