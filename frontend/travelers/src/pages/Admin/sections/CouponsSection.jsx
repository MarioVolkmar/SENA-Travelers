import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import DatePicker from '../../../components/DatePicker/DatePicker';
import { laterKey, todayKey } from '../../../components/DatePicker/calendarUtils';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import Modal from '../../../components/Modal/Modal';
import Pagination, { usePagination } from '../../../components/Pagination/Pagination';
import Select from '../../../components/Select/Select';
import Toast from '../../../components/Toast/Toast';
import { formatCurrency, formatDate, getErrorMessage } from '../../../utils/format';
import { LIMITS, useLimits } from '../../../utils/limits';
import { matches, useAdminAction } from '../adminShared';
import ConfirmDeleteModal from './ConfirmDeleteModal';
import NumberField, { numberError } from '../../../components/NumberField/NumberField';

const FILTERS = [
  { key: '', label: 'Todos' },
  { key: 'vigente', label: 'Vigentes' },
  { key: 'inactivo', label: 'Inactivos' },
  { key: 'vencido', label: 'Vencidos' },
];

function couponState(coupon) {
  const today = todayKey();
  if (coupon.estado !== 'activo') return { key: 'inactivo', label: 'Inactivo', badge: 'inactivo' };
  if (coupon.fecha_fin < today) return { key: 'vencido', label: 'Vencido', badge: 'cancelada' };
  if (coupon.usos_maximos && coupon.usos >= coupon.usos_maximos) return { key: 'vencido', label: 'Agotado', badge: 'cancelada' };
  if (coupon.fecha_inicio > today) return { key: 'vigente', label: 'Programado', badge: 'pendiente' };
  return { key: 'vigente', label: 'Vigente', badge: 'activo' };
}

function discountLabel(coupon) {
  return coupon.tipo === 'porcentaje' ? `${Number(coupon.valor)} %` : formatCurrency(coupon.valor);
}

const EMPTY = {
  codigo: '',
  descripcion: '',
  tipo: 'porcentaje',
  valor: '',
  fecha_inicio: todayKey(),
  fecha_fin: '',
  usos_maximos: '',
  monto_minimo: '',
  estado: 'activo',
};

function CouponFormModal({ coupon, onClose, onSaved }) {
  useLimits(); // vuelve a pintar cuando llegan los límites del backend
  const [form, setForm] = useState(() => (coupon
    ? {
      ...EMPTY,
      ...coupon,
      descripcion: coupon.descripcion || '',
      valor: String(Number(coupon.valor)),
      usos_maximos: coupon.usos_maximos ?? '',
      monto_minimo: coupon.monto_minimo ? String(Number(coupon.monto_minimo)) : '',
    }
    : EMPTY));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  // Rangos de los números: con alguno fuera de rango no se deja guardar
  const valueRange = form.tipo === 'porcentaje' ? LIMITS.couponPercent : LIMITS.couponValue;
  const numbersInvalid = Boolean(
    numberError(form.valor, valueRange)
    || numberError(form.usos_maximos, LIMITS.couponUses, { optional: true })
    || numberError(form.monto_minimo, LIMITS.couponMinPurchase, { optional: true })
  );

  // Si el nuevo inicio queda después del fin, el fin se borra para elegirlo de nuevo
  const updateStart = (event) => {
    const start = event.target.value;
    setForm((current) => ({
      ...current,
      fecha_inicio: start,
      fecha_fin: current.fecha_fin && current.fecha_fin < start ? '' : current.fecha_fin,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    const payload = {
      codigo: form.codigo.trim().toUpperCase(),
      descripcion: form.descripcion.trim() || null,
      tipo: form.tipo,
      valor: Number(form.valor),
      fecha_inicio: form.fecha_inicio,
      fecha_fin: form.fecha_fin,
      usos_maximos: form.usos_maximos === '' ? null : Number(form.usos_maximos),
      monto_minimo: form.monto_minimo === '' ? null : Number(form.monto_minimo),
      estado: form.estado,
    };
    try {
      const response = coupon
        ? await api.patch(`/coupons/${coupon.id_cupon}`, payload)
        : await api.post('/coupons/', payload);
      onSaved(response.data, Boolean(coupon));
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar el cupón.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={coupon ? 'Editar cupón' : 'Nuevo cupón'}
      subtitle="Los viajeros lo escriben al reservar para obtener el descuento."
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>Cancelar</button>
          <button type="submit" form="coupon-form" className="btn btn-primary" disabled={saving || numbersInvalid}>
            {saving ? 'Guardando...' : coupon ? 'Guardar cambios' : 'Crear cupón'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}
      <form id="coupon-form" className="admin-form-grid" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="coupon-code">Código</label>
          <input
            id="coupon-code"
            value={form.codigo}
            onChange={(event) => setForm((current) => ({ ...current, codigo: event.target.value.toUpperCase() }))}
            pattern="[A-Za-z0-9_-]{3,30}"
            title="Entre 3 y 30 letras, números, guiones"
            placeholder="VERANO2026"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="coupon-state">Estado</label>
          <Select id="coupon-state" value={form.estado} onChange={update('estado')}>
            <option value="activo">Activo</option>
            <option value="inactivo">Inactivo</option>
          </Select>
        </div>
        <div className="field field-full">
          <label htmlFor="coupon-desc">Descripción (la ve el viajero)</label>
          <input id="coupon-desc" value={form.descripcion} onChange={update('descripcion')} maxLength={150} placeholder="10 % en paquetes de temporada" />
        </div>
        <div className="field">
          <label htmlFor="coupon-type">Tipo de descuento</label>
          <Select id="coupon-type" value={form.tipo} onChange={update('tipo')}>
            <option value="porcentaje">Porcentaje (%)</option>
            <option value="valor">Valor fijo (COP)</option>
          </Select>
        </div>
        <NumberField
          id="coupon-value"
          label={form.tipo === 'porcentaje' ? 'Porcentaje' : 'Valor en pesos'}
          value={form.valor}
          onChange={update('valor')}
          range={valueRange}
          money={form.tipo !== 'porcentaje'}
          unit={form.tipo === 'porcentaje' ? ' %' : ''}
          hint={form.tipo === 'porcentaje'
            ? `Entre ${LIMITS.couponPercent.min} y ${LIMITS.couponPercent.max} %.`
            : `Entre ${formatCurrency(LIMITS.couponValue.min)} y ${formatCurrency(LIMITS.couponValue.max)}.`}
        />
        <div className="field">
          <label htmlFor="coupon-start">Válido desde</label>
          <DatePicker id="coupon-start" value={form.fecha_inicio} onChange={updateStart} min={todayKey()} required />
        </div>
        <div className="field">
          <label htmlFor="coupon-end">Válido hasta</label>
          <DatePicker id="coupon-end" value={form.fecha_fin} onChange={update('fecha_fin')} min={laterKey(form.fecha_inicio, todayKey())} required />
        </div>
        <NumberField
          id="coupon-uses"
          label="Usos máximos"
          placeholder="Sin límite"
          value={form.usos_maximos}
          onChange={update('usos_maximos')}
          range={LIMITS.couponUses}
          optional
          hint={`Opcional. Entre ${LIMITS.couponUses.min} y ${LIMITS.couponUses.max.toLocaleString('es-CO')} usos.`}
        />
        <NumberField
          id="coupon-min"
          label="Compra mínima (COP)"
          placeholder="Sin mínimo"
          value={form.monto_minimo}
          onChange={update('monto_minimo')}
          range={LIMITS.couponMinPurchase}
          optional
          money
          hint={`Opcional. Hasta ${formatCurrency(LIMITS.couponMinPurchase.max)}.`}
        />
      </form>
    </Modal>
  );
}

function CouponsSection() {
  const [coupons, setCoupons] = useState(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('');
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { busy, message, error, run, clear } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const response = await api.get('/coupons/');
    setCoupons(response.data);
  }, []);

  useEffect(() => {
    load().catch(() => setCoupons([]));
  }, [load]);

  const visible = (coupons || [])
    .filter((coupon) => !filter || couponState(coupon).key === filter)
    .filter((coupon) => !query || matches(coupon.codigo, query) || matches(coupon.descripcion, query));
  const pager = usePagination(visible, [query, filter]);

  const toggle = async (coupon) => {
    const activate = coupon.estado !== 'activo';
    const accepted = await confirm({
      title: activate ? 'Activar cupón' : 'Desactivar cupón',
      subtitle: coupon.codigo,
      message: activate ? 'Los viajeros podrán volver a usarlo.' : 'Dejará de aplicar en nuevas reservas. Las reservas ya hechas no cambian.',
      confirmLabel: activate ? 'Activar' : 'Desactivar',
      tone: activate ? 'primary' : 'danger',
    });
    if (!accepted) return;
    const { ok } = await run(
      () => api.patch(`/coupons/${coupon.id_cupon}`, { estado: activate ? 'activo' : 'inactivo' }),
      `Cupón ${coupon.codigo} ${activate ? 'activado' : 'desactivado'}.`
    );
    if (ok) await load();
  };

  if (!coupons) return <p className="page-status">Cargando cupones...</p>;

  const totalUses = coupons.reduce((sum, coupon) => sum + coupon.usos, 0);
  const active = coupons.filter((coupon) => couponState(coupon).label === 'Vigente').length;

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Cupones</h1>
          <p>Descuentos que los viajeros aplican al reservar.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => { clear(); setEditing('new'); }}>
          + Nuevo cupón
        </button>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="admin-summary">
        <div className="admin-stat highlight"><span>Vigentes</span><strong>{active}</strong></div>
        <div className="admin-stat"><span>Cupones creados</span><strong>{coupons.length}</strong></div>
        <div className="admin-stat"><span>Veces usados</span><strong>{totalUses}</strong></div>
      </div>

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por código" aria-label="Buscar cupones" />
          </label>
          <div className="admin-filters" role="group" aria-label="Filtrar cupones">
            {FILTERS.map((option) => (
              <button key={option.key} type="button" className="chip" aria-pressed={filter === option.key} onClick={() => setFilter(option.key)}>
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Cupón</th>
                <th>Descuento</th>
                <th>Vigencia</th>
                <th>Usos</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {pager.items.map((coupon) => {
                const state = couponState(coupon);
                return (
                  <tr key={coupon.id_cupon}>
                    <td>
                      <span className="admin-coupon-code">{coupon.codigo}</span>
                      {coupon.descripcion && <><br /><span className="admin-muted">{coupon.descripcion}</span></>}
                    </td>
                    <td>
                      <span className="admin-strong">{discountLabel(coupon)}</span>
                      {coupon.monto_minimo && <><br /><span className="admin-muted">desde {formatCurrency(coupon.monto_minimo)}</span></>}
                    </td>
                    <td className="admin-muted">{formatDate(coupon.fecha_inicio)} – {formatDate(coupon.fecha_fin)}</td>
                    <td>{coupon.usos}{coupon.usos_maximos ? ` / ${coupon.usos_maximos}` : ''}</td>
                    <td><span className={`badge badge-${state.badge}`}>{state.label}</span></td>
                    <td>
                      <div className="admin-actions">
                        <IconButton icon="edit" label="Editar" onClick={() => { clear(); setEditing(coupon); }} />
                        <IconButton
                          icon={coupon.estado === 'activo' ? 'pause' : 'play'}
                          label={coupon.estado === 'activo' ? 'Desactivar' : 'Activar'}
                          variant={coupon.estado === 'activo' ? 'warning' : 'success'}
                          disabled={busy}
                          onClick={() => toggle(coupon)}
                        />
                        <IconButton icon="trash" label="Eliminar" variant="danger" hidden={coupon.usos > 0} onClick={() => setDeleting(coupon)} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {visible.length === 0 && (
            <p className="admin-empty">{coupons.length === 0 ? 'Aún no has creado cupones.' : 'No hay cupones con esos filtros.'}</p>
          )}
        </div>
        <Pagination {...pager} label="cupones" />
      </div>

      {editing && (
        <CouponFormModal
          coupon={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={async (saved, wasEdit) => {
            setEditing(null);
            await run(() => load(), `Cupón ${saved.codigo} ${wasEdit ? 'actualizado' : 'creado'}.`);
          }}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal
          title="Eliminar cupón"
          name={deleting.codigo}
          consequences={['Solo se puede si nunca se ha usado; si ya se usó, desactívalo.']}
          request={() => api.delete(`/coupons/${deleting.id_cupon}`)}
          onClose={() => setDeleting(null)}
          onDeleted={async () => {
            const code = deleting.codigo;
            setDeleting(null);
            await run(() => load(), `Cupón ${code} eliminado.`);
          }}
        />
      )}
      {dialog}
    </>
  );
}

export default CouponsSection;
