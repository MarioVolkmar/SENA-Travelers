import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { formatCurrency } from '../../../utils/format';
import { useAdminAction } from '../adminShared';
import { clampToRange, inRange, LIMITS, useLimits } from '../../../utils/limits';
import NumberField from '../../../components/NumberField/NumberField';

const FREE_DAY_PRESETS = [3, 7, 15, 30];
const PENALTY_PRESETS = [0, 20, 30, 50];
const EXAMPLE_PAYMENT = 1000000;

function PresetChips({ values, current, suffix, onPick, label }) {
  return (
    <div className="admin-filters settings-presets" role="group" aria-label={label}>
      {values.map((value) => (
        <button
          key={value}
          type="button"
          className="chip"
          aria-pressed={Number(current) === value}
          onClick={() => onPick(String(value))}
        >
          {value}{suffix}
        </button>
      ))}
    </div>
  );
}

function SettingsSection() {
  useLimits(); // vuelve a pintar cuando llegan los límites del backend
  const [days, setDays] = useState('');
  const [paymentDay, setPaymentDay] = useState('');
  const [freeDays, setFreeDays] = useState('');
  const [penalty, setPenalty] = useState('');
  const [reminderDays, setReminderDays] = useState('');
  const [paymentHours, setPaymentHours] = useState('');
  const savePaymentHours = useAdminAction();
  const saveReminder = useAdminAction();
  const runReminders = useAdminAction();
  const [saved, setSaved] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const save = useAdminAction();
  const savePolicy = useAdminAction();

  const applySettings = (data) => {
    setDays(String(data.dias_pago_proveedores));
    setPaymentDay(String(data.dia_pago_proveedores));
    setFreeDays(String(data.dias_cancelacion_gratis));
    setPenalty(String(data.porcentaje_penalidad_cancelacion));
    setReminderDays(String(data.dias_recordatorio_viaje));
    setPaymentHours(String(data.horas_para_pagar));
    setSaved(data);
  };

  useEffect(() => {
    api.get('/settings/')
      .then((response) => applySettings(response.data))
      .finally(() => setLoaded(true));
  }, []);

  const handleSave = async (event) => {
    event.preventDefault();
    const { ok, result } = await save.run(
      () => api.patch('/settings/', { dias_pago_proveedores: Number(days), dia_pago_proveedores: Number(paymentDay) }),
      'Pagos a proveedores actualizados. El plazo aplica a las órdenes nuevas; el día de pago, a todas las aprobadas.'
    );
    if (ok) applySettings(result.data);
  };

  const handleSavePolicy = async (event) => {
    event.preventDefault();
    const { ok, result } = await savePolicy.run(
      () => api.patch('/settings/', {
        dias_cancelacion_gratis: Number(freeDays),
        porcentaje_penalidad_cancelacion: Number(penalty),
      }),
      'Política de cancelación actualizada. Aplica a las cancelaciones que se hagan desde ahora.'
    );
    if (ok) applySettings(result.data);
  };

  const handleSaveReminder = async (event) => {
    event.preventDefault();
    const { ok, result } = await saveReminder.run(
      () => api.patch('/settings/', { dias_recordatorio_viaje: Number(reminderDays) }),
      'Recordatorio actualizado.'
    );
    if (ok) applySettings(result.data);
  };

  const handleSavePaymentHours = async (event) => {
    event.preventDefault();
    const { ok, result } = await savePaymentHours.run(
      () => api.patch('/settings/', { horas_para_pagar: Number(paymentHours) }),
      'Plazo para pagar actualizado. Aplica a todas las reservas pendientes.'
    );
    if (ok) applySettings(result.data);
  };

  const handleRunReminders = async () => {
    const { ok, result } = await runReminders.run(() => api.post('/reminders/run'));
    if (ok) {
      const count = result.data.enviados;
      runReminders.clear();
      await runReminders.run(
        async () => {},
        count === 0 ? 'No había recordatorios pendientes.' : `Se enviaron ${count} ${count === 1 ? 'recordatorio' : 'recordatorios'}.`
      );
    }
  };

  if (!loaded) return <p className="page-status">Cargando configuración...</p>;

  const penaltyValue = clampToRange(penalty, LIMITS.cancellationPenalty);
  const daysOk = inRange(days, LIMITS.providerPaymentDays);
  const paymentDayOk = inRange(paymentDay, LIMITS.providerPaymentDay);
  const providerChanged = saved
    && (Number(days) !== saved.dias_pago_proveedores || Number(paymentDay) !== saved.dia_pago_proveedores);
  const reminderOk = inRange(reminderDays, LIMITS.reminderDays);
  const freeDaysOk = inRange(freeDays, LIMITS.freeCancellationDays);
  const penaltyOk = inRange(penalty, LIMITS.cancellationPenalty);
  const paymentHoursOk = inRange(paymentHours, LIMITS.paymentHours);
  // Mensaje de rango en rojo cuando el número escrito no es válido
  const rangeError = (ok, limits, unit) => (ok ? null : (
    <span className="field-hint" style={{ color: 'var(--color-danger)' }} role="alert">
      Escribe un número entero entre {limits.min} y {limits.max}{unit}.
    </span>
  ));
  const policyChanged = saved
    && (Number(freeDays) !== saved.dias_cancelacion_gratis || Number(penalty) !== saved.porcentaje_penalidad_cancelacion);

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Configuración</h1>
          <p>Reglas generales de la operación de Travelers.</p>
        </div>
      </div>

      <form className="surface settings-block" onSubmit={handleSave}>
        <div className="admin-panel-header"><h2>Pagos a proveedores</h2></div>
        <p className="settings-policy-summary">
          Cada orden debe aprobarse a más tardar <strong>{saved.dias_pago_proveedores} días</strong> después del viaje
          (a los administradores les llega un aviso 2 días antes del plazo). Las órdenes aprobadas se pagan el
          {' '}<strong>día {saved.dia_pago_proveedores}</strong> de cada mes.
        </p>
        {save.message && <div className="alert alert-success">{save.message}</div>}
        {save.error && <div className="alert alert-error">{save.error}</div>}

        <div className="admin-two-columns settings-policy-grid">
          <NumberField
            id="setting-days"
            label="Plazo para aprobar (días después del viaje)"
            value={days}
            onChange={(event) => setDays(event.target.value)}
            range={LIMITS.providerPaymentDays}
            unit=" días"
            hint={`El administrador tiene ${days || '…'} días después del viaje para aprobar la orden (entre ${LIMITS.providerPaymentDays.min} y ${LIMITS.providerPaymentDays.max}).`}
          />
          <NumberField
            id="setting-payment-day"
            label="Día de pago (día del mes)"
            value={paymentDay}
            onChange={(event) => setPaymentDay(event.target.value)}
            range={LIMITS.providerPaymentDay}
            hint={`Las órdenes aprobadas se pagan ese día de cada mes (entre ${LIMITS.providerPaymentDay.min} y ${LIMITS.providerPaymentDay.max}, para que exista en todos los meses).`}
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={save.busy || !daysOk || !paymentDayOk || !providerChanged}>
          {save.busy ? 'Guardando...' : 'Guardar'}
        </button>
      </form>

      <form className="surface settings-block" onSubmit={handleSaveReminder}>
        <div className="admin-panel-header">
          <h2>Recordatorio antes del viaje</h2>
        </div>
        <p className="settings-policy-summary">
          Los viajeros con reserva confirmada reciben un correo y un aviso en la campana
          {' '}<strong>{saved.dias_recordatorio_viaje} {saved.dias_recordatorio_viaje === 1 ? 'día' : 'días'}</strong> antes de su viaje.
          El sistema revisa cada hora; no se envía dos veces.
        </p>
        {saveReminder.message && <div className="alert alert-success">{saveReminder.message}</div>}
        {saveReminder.error && <div className="alert alert-error">{saveReminder.error}</div>}
        {runReminders.message && <div className="alert alert-success">{runReminders.message}</div>}
        {runReminders.error && <div className="alert alert-error">{runReminders.error}</div>}
        <div className="field">
          <label htmlFor="setting-reminder">Días de anticipación</label>
          <PresetChips values={[1, 3, 5, 7]} current={reminderDays} suffix=" días" onPick={setReminderDays} label="Días sugeridos" />
          <input
            id="setting-reminder"
            type="number"
            min={LIMITS.reminderDays.min}
            max={LIMITS.reminderDays.max}
            step="1"
            aria-invalid={!reminderOk}
            value={reminderDays}
            onChange={(event) => setReminderDays(event.target.value)}
            required
          />
          {rangeError(reminderOk, LIMITS.reminderDays, ' días') || (
            <span className="field-hint">Entre {LIMITS.reminderDays.min} y {LIMITS.reminderDays.max} días antes del viaje.</span>
          )}
        </div>
        <div className="admin-form-actions">
          <button type="button" className="btn btn-secondary" onClick={handleRunReminders} disabled={runReminders.busy}>
            {runReminders.busy ? 'Enviando...' : 'Enviar pendientes ahora'}
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saveReminder.busy || !reminderOk || Number(reminderDays) === saved.dias_recordatorio_viaje}
          >
            {saveReminder.busy ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </form>

      <form className="surface settings-block" onSubmit={handleSavePaymentHours}>
        <div className="admin-panel-header">
          <h2>Plazo para pagar las reservas</h2>
        </div>
        <p className="settings-policy-summary">
          Una reserva pendiente se cancela sola si no se paga en
          {' '}<strong>{saved.horas_para_pagar} {saved.horas_para_pagar === 1 ? 'hora' : 'horas'}</strong>, y sus cupos quedan libres.
          El viajero recibe un correo y un aviso en la campana. El sistema revisa cada 15 minutos.
        </p>
        {savePaymentHours.message && <div className="alert alert-success">{savePaymentHours.message}</div>}
        {savePaymentHours.error && <div className="alert alert-error">{savePaymentHours.error}</div>}
        <div className="field">
          <label htmlFor="setting-payment-hours">Horas para pagar</label>
          <PresetChips values={[12, 24, 48, 72]} current={paymentHours} suffix=" h" onPick={setPaymentHours} label="Horas sugeridas" />
          <input
            id="setting-payment-hours"
            type="number"
            min={LIMITS.paymentHours.min}
            max={LIMITS.paymentHours.max}
            step="1"
            aria-invalid={!paymentHoursOk}
            value={paymentHours}
            onChange={(event) => setPaymentHours(event.target.value)}
            required
          />
          {rangeError(paymentHoursOk, LIMITS.paymentHours, ' horas') || (
            <span className="field-hint">
              Entre {LIMITS.paymentHours.min} y {LIMITS.paymentHours.max} horas (una semana) desde que se crea la reserva.
            </span>
          )}
        </div>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={savePaymentHours.busy || !paymentHoursOk || Number(paymentHours) === saved.horas_para_pagar}
        >
          {savePaymentHours.busy ? 'Guardando...' : 'Guardar'}
        </button>
      </form>

      <form className="surface" onSubmit={handleSavePolicy}>
        <div className="admin-panel-header">
          <h2>Política de cancelación</h2>
        </div>
        <p className="settings-policy-summary">
          Gratis hasta <strong>{saved.dias_cancelacion_gratis} días</strong> antes del viaje; después se cobra
          {' '}<strong>{saved.porcentaje_penalidad_cancelacion} %</strong> de lo pagado. Desde el día del viaje ya no se puede cancelar.
        </p>
        {savePolicy.message && <div className="alert alert-success">{savePolicy.message}</div>}
        {savePolicy.error && <div className="alert alert-error">{savePolicy.error}</div>}

        <div className="admin-two-columns settings-policy-grid">
          <div className="field">
            <label htmlFor="setting-free-days">Días de cancelación gratis</label>
            <PresetChips values={FREE_DAY_PRESETS} current={freeDays} suffix=" días" onPick={setFreeDays} label="Días sugeridos" />
            <input
              id="setting-free-days"
              type="number"
              min={LIMITS.freeCancellationDays.min}
              max={LIMITS.freeCancellationDays.max}
              step="1"
              aria-invalid={!freeDaysOk}
              value={freeDays}
              onChange={(event) => setFreeDays(event.target.value)}
              required
            />
            {rangeError(freeDaysOk, LIMITS.freeCancellationDays, ' días') || (
              <span className="field-hint">
                {Number(freeDays) === 0
                  ? 'Sin periodo gratis: siempre se cobra penalidad si ya pagó.'
                  : `Quien cancele ${freeDays} días o más antes del viaje recibe el reembolso completo.`}
                {` (entre ${LIMITS.freeCancellationDays.min} y ${LIMITS.freeCancellationDays.max} días)`}
              </span>
            )}
          </div>

          <div className="field">
            <label htmlFor="setting-penalty">Penalidad por cancelación tardía (%)</label>
            <PresetChips values={PENALTY_PRESETS} current={penalty} suffix=" %" onPick={setPenalty} label="Porcentajes sugeridos" />
            <input
              id="setting-penalty"
              type="number"
              min={LIMITS.cancellationPenalty.min}
              max={LIMITS.cancellationPenalty.max}
              step="1"
              aria-invalid={!penaltyOk}
              value={penalty}
              onChange={(event) => setPenalty(event.target.value)}
              required
            />
            {rangeError(penaltyOk, LIMITS.cancellationPenalty, ' %') || (
              <span className="field-hint">
                Ejemplo: sobre un pago de {formatCurrency(EXAMPLE_PAYMENT)} se retienen
                {' '}{formatCurrency((EXAMPLE_PAYMENT * penaltyValue) / 100)} y se reembolsan
                {' '}{formatCurrency((EXAMPLE_PAYMENT * (100 - penaltyValue)) / 100)}.
              </span>
            )}
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={savePolicy.busy || !policyChanged || !freeDaysOk || !penaltyOk}>
          {savePolicy.busy ? 'Guardando...' : 'Guardar política'}
        </button>
      </form>
    </>
  );
}

export default SettingsSection;
