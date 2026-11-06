import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import Icon from '../Icon/Icon';
import { useFloatingPosition, useOutsideClose } from '../Select/floating';
import '../Select/Select.css';
import './DatePicker.css';
import {
  addDays,
  addMonths,
  capitalize,
  formatDisplayDate,
  monthGrid,
  MONTHS,
  MONTHS_SHORT,
  parseKey,
  toKey,
  WEEKDAYS,
} from './calendarUtils';

/**
 * Campo de fecha con calendario desplegable. Valor 'YYYY-MM-DD'.
 * onChange recibe { target: { value, name } } como un input nativo.
 * - min / max: límites ('YYYY-MM-DD')
 * - isDateEnabled(key): para habilitar solo ciertas fechas
 * - startView: 'days' | 'years' (útil para fechas de nacimiento)
 */
function DatePicker({
  id,
  name,
  value,
  onChange,
  min,
  max,
  isDateEnabled,
  required = false,
  disabled = false,
  placeholder = 'Elige una fecha',
  startView = 'days',
  className = '',
  'aria-label': ariaLabel,
}) {
  const autoId = useId();
  const triggerId = id || `date-${autoId}`;
  const dialogId = `${triggerId}-calendar`;

  const triggerRef = useRef(null);
  const panelRef = useRef(null);
  const gridRef = useRef(null);

  const [open, setOpen] = useState(false);
  const [view, setView] = useState('days');
  const [focused, setFocused] = useState(() => new Date());

  const position = useFloatingPosition(open, triggerRef, 380);
  const close = useCallback(() => setOpen(false), []);
  useOutsideClose(open, [triggerRef, panelRef], close);

  const minDate = parseKey(min);
  const maxDate = parseKey(max);
  const todayKey = toKey(new Date());

  const isEnabled = (date) => {
    const key = toKey(date);
    if (min && key < min) return false;
    if (max && key > max) return false;
    return isDateEnabled ? isDateEnabled(key) : true;
  };

  const initialFocus = () => {
    const selected = parseKey(value);
    if (selected) return selected;
    const today = new Date();
    if (maxDate && today > maxDate) return maxDate;
    if (minDate && today < minDate) return minDate;
    return today;
  };

  const openPanel = () => {
    if (disabled) return;
    setFocused(initialFocus());
    setView(value ? 'days' : startView);
    setOpen(true);
  };

  const emit = (key) => {
    const target = { value: key, name, id: triggerId };
    onChange?.({ target, currentTarget: target, preventDefault() {} });
  };

  const choose = (date) => {
    if (!isEnabled(date)) return;
    emit(toKey(date));
    setOpen(false);
    triggerRef.current?.focus();
  };

  // Lleva el foco del teclado al día enfocado
  useEffect(() => {
    if (!open || view !== 'days') return;
    gridRef.current?.querySelector(`[data-key="${toKey(focused)}"]`)?.focus({ preventScroll: true });
  }, [open, view, focused]);

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

  const handleGridKey = (event) => {
    const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (moves[event.key]) {
      event.preventDefault();
      setFocused((date) => addDays(date, moves[event.key]));
    } else if (event.key === 'PageUp' || event.key === 'PageDown') {
      event.preventDefault();
      setFocused((date) => addMonths(date, event.key === 'PageUp' ? -1 : 1));
    } else if (event.key === 'Home' || event.key === 'End') {
      event.preventDefault();
      setFocused((date) => addDays(date, event.key === 'Home' ? -((date.getDay() + 6) % 7) : 6 - ((date.getDay() + 6) % 7)));
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      choose(focused);
    }
  };

  const year = focused.getFullYear();
  const month = focused.getMonth();
  const canGoPrev = !minDate || new Date(year, month, 1) > new Date(minDate.getFullYear(), minDate.getMonth(), 1);
  const canGoNext = !maxDate || new Date(year, month, 1) < new Date(maxDate.getFullYear(), maxDate.getMonth(), 1);
  const yearStart = year - (year % 12);
  const monthHasEnabledDays = (y, m) => {
    const last = new Date(y, m + 1, 0).getDate();
    for (let day = 1; day <= last; day += 1) {
      if (isEnabled(new Date(y, m, day))) return true;
    }
    return false;
  };
  const yearInRange = (y) => (!minDate || y >= minDate.getFullYear()) && (!maxDate || y <= maxDate.getFullYear());

  const shift = (step) => {
    if (view === 'days') setFocused((date) => addMonths(date, step));
    if (view === 'months') setFocused((date) => new Date(date.getFullYear() + step, date.getMonth(), 1));
    if (view === 'years') setFocused((date) => new Date(date.getFullYear() + step * 12, date.getMonth(), 1));
  };

  const headerLabel = view === 'days'
    ? `${capitalize(MONTHS[month])} ${year}`
    : view === 'months'
      ? String(year)
      : `${yearStart} – ${yearStart + 11}`;

  const prevDisabled = view === 'days' ? !canGoPrev : view === 'months' ? !yearInRange(year - 1) : minDate && yearStart <= minDate.getFullYear();
  const nextDisabled = view === 'days' ? !canGoNext : view === 'months' ? !yearInRange(year + 1) : maxDate && yearStart + 11 >= maxDate.getFullYear();

  const todayDate = new Date();

  return (
    <div className={`ui-select ui-date ${open ? 'is-open' : ''}`}>
      <button
        ref={triggerRef}
        id={triggerId}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={dialogId}
        aria-label={ariaLabel}
        className={`ui-select-trigger ${className}`}
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openPanel())}
        onKeyDown={(event) => {
          if (!open && (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            openPanel();
          }
        }}
      >
        <Icon name="calendar" size={17} className="ui-date-icon" />
        <span className={`ui-select-value ${value ? '' : 'is-placeholder'}`}>
          {value ? formatDisplayDate(value) : placeholder}
        </span>
        <Icon name="chevronDown" size={16} strokeWidth={2.4} className="ui-select-chevron" />
      </button>

      <input
        className="ui-select-native"
        tabIndex={-1}
        aria-hidden="true"
        name={name}
        value={value || ''}
        required={required}
        onChange={() => {}}
        onInvalid={() => triggerRef.current?.focus()}
      />

      {open && createPortal(
        <div
          ref={panelRef}
          id={dialogId}
          role="dialog"
          aria-modal="false"
          aria-label="Calendario"
          className="ui-popover ui-calendar"
          style={{ ...position, maxHeight: undefined }}
        >
          <div className="ui-calendar-header">
            <button
              type="button"
              className="ui-calendar-nav"
              onClick={() => shift(-1)}
              disabled={Boolean(prevDisabled)}
              aria-label="Anterior"
            >
              <Icon name="chevronLeft" size={18} strokeWidth={2.4} />
            </button>
            <button
              type="button"
              className="ui-calendar-title"
              onClick={() => setView(view === 'days' ? 'months' : 'years')}
              disabled={view === 'years'}
              aria-live="polite"
            >
              {headerLabel}
              {view !== 'years' && <Icon name="chevronDown" size={14} strokeWidth={2.6} />}
            </button>
            <button
              type="button"
              className="ui-calendar-nav"
              onClick={() => shift(1)}
              disabled={Boolean(nextDisabled)}
              aria-label="Siguiente"
            >
              <Icon name="chevronRight" size={18} strokeWidth={2.4} />
            </button>
          </div>

          {view === 'days' && (
            <>
              <div className="ui-calendar-weekdays" aria-hidden="true">
                {WEEKDAYS.map((day, index) => <span key={index}>{day}</span>)}
              </div>
              <div ref={gridRef} className="ui-calendar-days" role="grid" onKeyDown={handleGridKey}>
                {monthGrid(focused).map((date) => {
                  const key = toKey(date);
                  const outside = date.getMonth() !== month;
                  const enabled = isEnabled(date);
                  const isSelected = key === value;
                  const isFocused = key === toKey(focused);
                  return (
                    <button
                      key={key}
                      type="button"
                      role="gridcell"
                      data-key={key}
                      tabIndex={isFocused ? 0 : -1}
                      aria-selected={isSelected}
                      aria-label={formatDisplayDate(key)}
                      disabled={!enabled}
                      className={[
                        'ui-calendar-day',
                        outside && 'is-outside',
                        enabled && 'is-available',
                        isSelected && 'is-selected',
                        key === todayKey && 'is-today',
                      ].filter(Boolean).join(' ')}
                      onClick={() => choose(date)}
                    >
                      {date.getDate()}
                    </button>
                  );
                })}
              </div>
            </>
          )}

          {view === 'months' && (
            <div className="ui-calendar-grid">
              {MONTHS_SHORT.map((label, index) => {
                const enabled = monthHasEnabledDays(year, index);
                const selectedDate = parseKey(value);
                const isSelected = selectedDate && selectedDate.getFullYear() === year && selectedDate.getMonth() === index;
                return (
                  <button
                    key={label}
                    type="button"
                    disabled={!enabled}
                    className={`ui-calendar-cell ${isSelected ? 'is-selected' : ''} ${enabled ? 'is-available' : ''}`}
                    onClick={() => { setFocused(new Date(year, index, 1)); setView('days'); }}
                  >
                    {capitalize(label)}
                  </button>
                );
              })}
            </div>
          )}

          {view === 'years' && (
            <div className="ui-calendar-grid">
              {Array.from({ length: 12 }, (_, index) => yearStart + index).map((item) => (
                <button
                  key={item}
                  type="button"
                  disabled={!yearInRange(item)}
                  className={`ui-calendar-cell ${parseKey(value)?.getFullYear() === item ? 'is-selected' : ''} ${yearInRange(item) ? 'is-available' : ''}`}
                  onClick={() => { setFocused(new Date(item, month, 1)); setView('months'); }}
                >
                  {item}
                </button>
              ))}
            </div>
          )}

          <div className="ui-calendar-footer">
            {!required && value ? (
              <button type="button" className="ui-calendar-link" onClick={() => { emit(''); setOpen(false); }}>
                Borrar
              </button>
            ) : <span />}
            {isEnabled(todayDate) && (
              <button type="button" className="ui-calendar-link" onClick={() => choose(todayDate)}>
                Hoy
              </button>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default DatePicker;
