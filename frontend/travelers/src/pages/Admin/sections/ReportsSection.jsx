import { useCallback, useEffect, useMemo, useState } from 'react';

import api from '../../../api/axiosConfig';
import DatePicker from '../../../components/DatePicker/DatePicker';
import { todayKey } from '../../../components/DatePicker/calendarUtils';
import Icon from '../../../components/Icon/Icon';
import Toast from '../../../components/Toast/Toast';
import { downloadFile } from '../../../utils/download';
import { formatCurrency, getErrorMessage } from '../../../utils/format';

const RANGES = [
  { key: '3m', label: '3 meses', months: 3 },
  { key: '6m', label: '6 meses', months: 6 },
  { key: '12m', label: '12 meses', months: 12 },
  { key: 'year', label: 'Este año' },
];

const STATUS_CLASS = { confirmada: 'is-good', pendiente: 'is-warning', cancelada: 'is-critical' };

function rangeFor(key) {
  const today = new Date();
  const end = todayKey();
  if (key === 'year') return { desde: `${today.getFullYear()}-01-01`, hasta: end };
  const months = RANGES.find((range) => range.key === key)?.months || 12;
  const start = new Date(today.getFullYear(), today.getMonth() - months + 1, 1);
  const pad = (n) => String(n).padStart(2, '0');
  return { desde: `${start.getFullYear()}-${pad(start.getMonth() + 1)}-01`, hasta: end };
}

function compactMoney(value) {
  const number = Number(value || 0);
  if (number >= 1_000_000) return `$${(number / 1_000_000).toFixed(number >= 10_000_000 ? 0 : 1)} M`;
  if (number >= 1_000) return `$${Math.round(number / 1_000)} mil`;
  return `$${number}`;
}

/** Columnas de ventas por mes (una sola serie) con tooltip al pasar el mouse. */
function MonthlyChart({ months }) {
  const [hover, setHover] = useState(null);
  const width = 720;
  const height = 260;
  const pad = { top: 16, right: 12, bottom: 34, left: 56 };
  const max = Math.max(...months.map((m) => Number(m.ventas)), 1);
  const niceMax = (() => {
    const exp = 10 ** Math.floor(Math.log10(max));
    return Math.ceil(max / exp) * exp;
  })();
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const slot = plotW / Math.max(months.length, 1);
  const barW = Math.min(36, slot * 0.6);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => niceMax * t);
  const y = (value) => pad.top + plotH - (Number(value) / niceMax) * plotH;

  return (
    <div className="report-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Ventas netas por mes">
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)} className="report-grid" />
            <text x={pad.left - 8} y={y(tick)} className="report-axis" textAnchor="end" dominantBaseline="middle">
              {compactMoney(tick)}
            </text>
          </g>
        ))}
        {months.map((month, index) => {
          const x = pad.left + slot * index + (slot - barW) / 2;
          const value = Number(month.ventas);
          const top = y(value);
          const barH = Math.max(pad.top + plotH - top, value > 0 ? 2 : 0);
          const r = Math.min(4, barW / 2, barH);
          return (
            <g key={month.mes}>
              {barH > 0 && (
                <path
                  className={`report-bar ${hover === index ? 'is-hover' : ''}`}
                  d={`M${x},${pad.top + plotH} V${top + r} Q${x},${top} ${x + r},${top} H${x + barW - r} Q${x + barW},${top} ${x + barW},${top + r} V${pad.top + plotH} Z`}
                />
              )}
              {(months.length <= 12 || index % 2 === 0) && (
                <text x={x + barW / 2} y={height - 12} className="report-axis" textAnchor="middle">
                  {month.etiqueta}
                </text>
              )}
              {/* Zona de hover más grande que la barra */}
              <rect
                x={pad.left + slot * index}
                y={pad.top}
                width={slot}
                height={plotH}
                fill="transparent"
                tabIndex={0}
                aria-label={`${month.etiqueta}: ${formatCurrency(value)}, ${month.reservas} reservas`}
                onMouseEnter={() => setHover(index)}
                onMouseLeave={() => setHover(null)}
                onFocus={() => setHover(index)}
                onBlur={() => setHover(null)}
              />
            </g>
          );
        })}
        <line x1={pad.left} x2={width - pad.right} y1={pad.top + plotH} y2={pad.top + plotH} className="report-baseline" />
      </svg>
      {hover !== null && (
        <div
          className="report-tooltip"
          style={{ left: `${((pad.left + slot * hover + slot / 2) / width) * 100}%`, top: `${(y(months[hover].ventas) / height) * 100}%` }}
        >
          <strong>{months[hover].etiqueta}</strong>
          <span>{formatCurrency(months[hover].ventas)}</span>
          <span>{months[hover].reservas} reservas · {months[hover].viajeros} viajeros</span>
        </div>
      )}
    </div>
  );
}

/** Barras horizontales con etiqueta y valor (top paquetes, destinos, estados). */
function BarList({ items, valueKey, format = (v) => v, labelKey, statusKey }) {
  const max = Math.max(...items.map((item) => Number(item[valueKey])), 1);
  return (
    <ul className="report-barlist">
      {items.map((item) => {
        const value = Number(item[valueKey]);
        return (
          <li key={item[labelKey]} title={`${item[labelKey]}: ${format(value)}`}>
            <div className="report-barlist-row">
              <span className="report-barlist-label">{item[labelKey]}</span>
              <span className="report-barlist-value">{format(value)}</span>
            </div>
            <span className="report-barlist-track">
              <span
                className={`report-barlist-fill ${statusKey ? STATUS_CLASS[item[statusKey]] || '' : ''}`}
                style={{ width: `${Math.max((value / max) * 100, value > 0 ? 2 : 0)}%` }}
              />
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function ReportsSection() {
  const [preset, setPreset] = useState('12m');
  const [range, setRange] = useState(() => rangeFor('12m'));
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState('');
  const [notice, setNotice] = useState({ text: '', tone: 'success' });

  const load = useCallback(async () => {
    setError('');
    try {
      const response = await api.get('/reports/summary', { params: range });
      setReport(response.data);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible generar el reporte.'));
    }
  }, [range]);

  useEffect(() => {
    load();
  }, [load]);

  const choosePreset = (key) => {
    setPreset(key);
    setRange(rangeFor(key));
  };

  const exportAs = async (formato) => {
    setExporting(formato);
    setNotice({ text: '', tone: 'success' });
    try {
      await downloadFile('/reports/export', `reporte-travelers.${formato}`, { ...range, formato });
      setNotice({ text: formato === 'pdf' ? 'Reporte PDF descargado.' : 'Reporte de Excel descargado.', tone: 'success' });
    } catch (exportError) {
      setNotice({ text: getErrorMessage(exportError, exportError.message || 'No fue posible exportar.'), tone: 'error' });
    } finally {
      setExporting('');
    }
  };

  const kpis = report?.kpis;
  const cards = useMemo(() => (kpis ? [
    { label: 'Ventas netas', value: formatCurrency(kpis.ventas_netas), highlight: true },
    { label: 'Margen (ventas − proveedores)', value: formatCurrency(kpis.margen) },
    { label: 'Reservas', value: kpis.reservas },
    { label: 'Viajeros', value: kpis.viajeros },
    { label: 'Ticket promedio', value: formatCurrency(kpis.ticket_promedio) },
    { label: 'Tasa de cancelación', value: `${kpis.tasa_cancelacion} %`, warning: kpis.tasa_cancelacion > 20 },
    { label: 'Descuentos con cupones', value: formatCurrency(kpis.descuentos_cupones) },
    { label: 'Calificación promedio', value: kpis.calificacion_promedio ? `${kpis.calificacion_promedio} ★` : '—' },
  ] : []), [kpis]);

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Reportes</h1>
          <p>Ventas, reservas y destinos del periodo. Exporta a Excel o PDF.</p>
        </div>
        <div className="report-exports">
          <button type="button" className="btn btn-secondary" onClick={() => exportAs('xlsx')} disabled={!report || Boolean(exporting)}>
            <Icon name="download" size={18} /> {exporting === 'xlsx' ? 'Generando...' : 'Excel'}
          </button>
          <button type="button" className="btn btn-primary" onClick={() => exportAs('pdf')} disabled={!report || Boolean(exporting)}>
            <Icon name="download" size={18} /> {exporting === 'pdf' ? 'Generando...' : 'PDF'}
          </button>
        </div>
      </div>

      <Toast text={notice.text} tone={notice.tone} />

      {/* Filtros en una sola fila, sobre las gráficas */}
      <div className="report-filters surface">
        <div className="admin-filters" role="group" aria-label="Periodo">
          {RANGES.map((option) => (
            <button key={option.key} type="button" className="chip" aria-pressed={preset === option.key} onClick={() => choosePreset(option.key)}>
              {option.label}
            </button>
          ))}
        </div>
        <div className="report-range">
          <DatePicker
            value={range.desde}
            onChange={(event) => { setPreset(''); setRange((current) => ({ ...current, desde: event.target.value })); }}
            max={range.hasta}
            className="admin-select"
            aria-label="Desde"
            required
          />
          <span className="admin-muted">a</span>
          <DatePicker
            value={range.hasta}
            onChange={(event) => { setPreset(''); setRange((current) => ({ ...current, hasta: event.target.value })); }}
            min={range.desde}
            className="admin-select"
            aria-label="Hasta"
            required
          />
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {!report && !error && <p className="page-status">Generando reporte...</p>}

      {report && (
        <>
          <div className="admin-summary">
            {cards.map((card) => (
              <div key={card.label} className={`admin-stat ${card.highlight ? 'highlight' : ''} ${card.warning ? 'warning' : ''}`}>
                <span>{card.label}</span>
                <strong>{card.value}</strong>
              </div>
            ))}
          </div>

          <section className="surface report-panel">
            <div className="admin-panel-header"><h2>Ventas netas por mes</h2></div>
            {report.ventas_por_mes.every((month) => Number(month.ventas) === 0) ? (
              <p className="admin-empty">No hubo ventas en este periodo.</p>
            ) : (
              <MonthlyChart months={report.ventas_por_mes} />
            )}
          </section>

          <div className="admin-two-columns">
            <section className="surface report-panel">
              <div className="admin-panel-header"><h2>Paquetes más vendidos</h2></div>
              {report.top_paquetes.length === 0
                ? <p className="admin-empty">Sin reservas en el periodo.</p>
                : <BarList items={report.top_paquetes} valueKey="ventas" labelKey="paquete" format={formatCurrency} />}
            </section>

            <section className="surface report-panel">
              <div className="admin-panel-header"><h2>Reservas por estado</h2></div>
              {report.reservas_por_estado.length === 0
                ? <p className="admin-empty">Sin reservas en el periodo.</p>
                : <BarList items={report.reservas_por_estado} valueKey="total" labelKey="etiqueta" statusKey="estado" />}
            </section>
          </div>

          <section className="surface report-panel">
            <div className="admin-panel-header"><h2>Ventas por destino</h2></div>
            {report.por_destino.length === 0 ? (
              <p className="admin-empty">Sin reservas en el periodo.</p>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr><th>Destino</th><th>Reservas</th><th>Ventas netas</th><th>Participación</th></tr>
                  </thead>
                  <tbody>
                    {report.por_destino.map((row) => {
                      const share = Number(kpis.ventas_netas) ? (Number(row.ventas) / Number(kpis.ventas_netas)) * 100 : 0;
                      return (
                        <tr key={row.destino}>
                          <td className="admin-strong">{row.destino}</td>
                          <td>{row.reservas}</td>
                          <td className="admin-strong">{formatCurrency(row.ventas)}</td>
                          <td className="admin-muted">{share.toFixed(1)} %</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}

export default ReportsSection;
