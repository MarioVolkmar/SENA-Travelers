import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import Icon from '../Icon/Icon';
import { useFloatingPosition, useOutsideClose } from '../Select/floating';
import '../Select/Select.css';
import './DatePicker.css';
import { capitalize, formatMonthKey, MONTHS_SHORT } from './calendarUtils';

/**
 * Selector de mes con calendario de meses. Valor 'YYYY-MM' o '' (cualquier fecha).
 * `available`: meses que tienen paquetes; los demás se ven deshabilitados.
 */
function MonthPicker({
  id,
  value,
  onChange,
  available = [],
  emptyLabel = 'Cualquier fecha',
  className = '',
  'aria-label': ariaLabel,
}) {
  const autoId = useId();
  const triggerId = id || `month-${autoId}`;
  const panelId = `${triggerId}-panel`;

  const triggerRef = useRef(null);
  const panelRef = useRef(null);
  const [open, setOpen] = useState(false);

  const availableSet = new Set(available);
  const years = [...new Set(available.map((key) => Number(key.slice(0, 4))))].sort();
  const firstYear = years[0] ?? new Date().getFullYear();
  const lastYear = years[years.length - 1] ?? firstYear;
  const [year, setYear] = useState(firstYear);

  const position = useFloatingPosition(open, triggerRef, 340);
  const close = useCallback(() => setOpen(false), []);
  useOutsideClose(open, [triggerRef, panelRef], close);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === 'Escape') {
        event.stopPropagation();
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [open]);

  // Al abrir, enfoca el mes elegido o el primero disponible
  useEffect(() => {
    if (!open) return;
    const target = panelRef.current?.querySelector('.ui-calendar-cell.is-selected')
      || panelRef.current?.querySelector('.ui-calendar-cell:not(:disabled)');
    target?.focus({ preventScroll: true });
  }, [open, year]);

  const openPanel = () => {
    setYear(value ? Number(value.slice(0, 4)) : firstYear);
    setOpen(true);
  };

  const emit = (key) => {
    const target = { value: key, id: triggerId };
    onChange?.({ target, currentTarget: target, preventDefault() {} });
    setOpen(false);
    triggerRef.current?.focus();
  };

  const handleGridKey = (event) => {
    const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -3, ArrowDown: 3 };
    if (!moves[event.key]) return;
    event.preventDefault();
    const cells = [...panelRef.current.querySelectorAll('.ui-calendar-cell')];
    const index = cells.indexOf(document.activeElement);
    for (let next = index + moves[event.key]; next >= 0 && next < cells.length; next += moves[event.key]) {
      if (!cells[next].disabled) {
        cells[next].focus();
        break;
      }
    }
  };

  return (
    <div className={`ui-select ui-date ${open ? 'is-open' : ''}`}>
      <button
        ref={triggerRef}
        id={triggerId}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={ariaLabel}
        className={`ui-select-trigger ${className}`}
        onClick={() => (open ? setOpen(false) : openPanel())}
        onKeyDown={(event) => {
          if (!open && (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            openPanel();
          }
        }}
      >
        <span className="ui-select-value">{value ? formatMonthKey(value) : emptyLabel}</span>
        <Icon name="chevronDown" size={16} strokeWidth={2.4} className="ui-select-chevron" />
      </button>

      {open && createPortal(
        <div
          ref={panelRef}
          id={panelId}
          role="dialog"
          aria-label="Elige el mes del viaje"
          className="ui-popover ui-calendar ui-calendar-months"
          style={{ ...position, maxHeight: undefined }}
        >
          <div className="ui-calendar-header">
            <button
              type="button"
              className="ui-calendar-nav"
              onClick={() => setYear((current) => current - 1)}
              disabled={year <= firstYear}
              aria-label="Año anterior"
            >
              <Icon name="chevronLeft" size={18} strokeWidth={2.4} />
            </button>
            <span className="ui-calendar-title is-static" aria-live="polite">{year}</span>
            <button
              type="button"
              className="ui-calendar-nav"
              onClick={() => setYear((current) => current + 1)}
              disabled={year >= lastYear}
              aria-label="Año siguiente"
            >
              <Icon name="chevronRight" size={18} strokeWidth={2.4} />
            </button>
          </div>

          <div className="ui-calendar-grid" onKeyDown={handleGridKey}>
            {MONTHS_SHORT.map((label, index) => {
              const key = `${year}-${String(index + 1).padStart(2, '0')}`;
              const enabled = availableSet.has(key);
              return (
                <button
                  key={key}
                  type="button"
                  disabled={!enabled}
                  aria-pressed={key === value}
                  aria-label={`${formatMonthKey(key)}${enabled ? '' : ' (sin paquetes)'}`}
                  className={`ui-calendar-cell ${key === value ? 'is-selected' : ''} ${enabled ? 'is-available' : ''}`}
                  onClick={() => emit(key)}
                >
                  {capitalize(label)}
                  {enabled && <span className="ui-calendar-dot" aria-hidden="true" />}
                </button>
              );
            })}
          </div>

          <p className="ui-calendar-hint">
            <span className="ui-calendar-dot" aria-hidden="true" /> Meses con salidas disponibles
          </p>

          <div className="ui-calendar-footer">
            <button type="button" className="ui-calendar-link" onClick={() => emit('')}>
              {emptyLabel}
            </button>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default MonthPicker;
