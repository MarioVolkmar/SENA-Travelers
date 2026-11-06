import { Children, isValidElement, useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import Icon from '../Icon/Icon';
import { useFloatingPosition, useOutsideClose } from './floating';
import './Select.css';

function textOf(node) {
  if (node === null || node === undefined || typeof node === 'boolean') return '';
  if (typeof node === 'string' || typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(textOf).join('');
  if (isValidElement(node)) return textOf(node.props.children);
  return '';
}

// Lee los <option> hijos igual que un <select> nativo
function readOptions(children) {
  const options = [];
  Children.toArray(children).forEach((child) => {
    if (!isValidElement(child)) return;
    if (child.type === 'option') {
      options.push({
        value: String(child.props.value ?? textOf(child.props.children)),
        label: textOf(child.props.children),
        disabled: Boolean(child.props.disabled),
      });
    } else if (child.props?.children) {
      options.push(...readOptions(child.props.children));
    }
  });
  return options;
}

/**
 * Lista desplegable con el estilo de la página. Se usa como un <select>:
 * recibe <option> como hijos y llama a onChange con { target: { value, name } }.
 */
function Select({
  id,
  name,
  value,
  onChange,
  children,
  className = '',
  disabled = false,
  required = false,
  placeholder = 'Selecciona',
  'aria-label': ariaLabel,
}) {
  const options = readOptions(children);
  const current = String(value ?? '');
  const selectedIndex = options.findIndex((option) => option.value === current);
  const selected = options[selectedIndex];

  const autoId = useId();
  const triggerId = id || `select-${autoId}`;
  const listId = `${triggerId}-list`;

  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const triggerRef = useRef(null);
  const listRef = useRef(null);
  const typed = useRef({ text: '', time: 0 });

  const position = useFloatingPosition(open, triggerRef, 300);
  const close = useCallback(() => setOpen(false), []);
  useOutsideClose(open, [triggerRef, listRef], close);

  const openList = () => {
    if (disabled) return;
    setActive(selectedIndex >= 0 ? selectedIndex : options.findIndex((option) => !option.disabled));
    setOpen(true);
  };

  const choose = (index) => {
    const option = options[index];
    if (!option || option.disabled) return;
    setOpen(false);
    triggerRef.current?.focus();
    if (option.value !== current) {
      const target = { value: option.value, name, id: triggerId };
      onChange?.({ target, currentTarget: target, preventDefault() {} });
    }
  };

  const move = (from, step) => {
    let index = from;
    for (let i = 0; i < options.length; i += 1) {
      index = (index + step + options.length) % options.length;
      if (!options[index].disabled) return index;
    }
    return from;
  };

  // Mantiene visible la opción activa al moverse con el teclado
  useLayoutEffect(() => {
    if (!open || active < 0) return;
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [open, active]);

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

  const handleKeyDown = (event) => {
    if (disabled) return;
    const { key } = event;

    if (!open) {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(key)) {
        event.preventDefault();
        openList();
      }
      return;
    }

    if (key === 'ArrowDown') { event.preventDefault(); setActive((index) => move(index, 1)); return; }
    if (key === 'ArrowUp') { event.preventDefault(); setActive((index) => move(index, -1)); return; }
    if (key === 'Home') { event.preventDefault(); setActive(move(-1, 1)); return; }
    if (key === 'End') { event.preventDefault(); setActive(move(options.length, -1)); return; }
    if (key === 'Enter' || key === ' ') { event.preventDefault(); choose(active); return; }
    if (key === 'Tab') { setOpen(false); return; }

    // Escribir las primeras letras salta a la opción
    if (key.length === 1) {
      const now = Date.now();
      typed.current = {
        text: (now - typed.current.time > 700 ? '' : typed.current.text) + key.toLowerCase(),
        time: now,
      };
      const found = options.findIndex(
        (option) => !option.disabled && option.label.toLowerCase().startsWith(typed.current.text)
      );
      if (found >= 0) setActive(found);
    }
  };

  return (
    <div className={`ui-select ${open ? 'is-open' : ''}`}>
      <button
        ref={triggerRef}
        id={triggerId}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={open && active >= 0 ? `${listId}-${active}` : undefined}
        aria-label={ariaLabel}
        aria-required={required || undefined}
        className={`ui-select-trigger ${className}`}
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={handleKeyDown}
      >
        <span className={`ui-select-value ${selected ? '' : 'is-placeholder'}`}>
          {selected && selected.label ? selected.label : placeholder}
        </span>
        <Icon name="chevronDown" size={16} strokeWidth={2.4} className="ui-select-chevron" />
      </button>

      {/* Permite la validación nativa de formularios (required) */}
      <input
        className="ui-select-native"
        tabIndex={-1}
        aria-hidden="true"
        name={name}
        value={current}
        required={required}
        onChange={() => {}}
        onInvalid={() => triggerRef.current?.focus()}
      />

      {open && createPortal(
        <ul
          ref={listRef}
          id={listId}
          role="listbox"
          className="ui-popover ui-select-list"
          style={position}
          aria-labelledby={triggerId}
        >
          {options.map((option, index) => (
            <li
              key={`${option.value}-${index}`}
              id={`${listId}-${index}`}
              data-index={index}
              role="option"
              aria-selected={option.value === current}
              aria-disabled={option.disabled || undefined}
              className={`ui-select-option ${index === active ? 'is-active' : ''}`}
              onMouseEnter={() => !option.disabled && setActive(index)}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(index)}
            >
              <span>{option.label}</span>
              {option.value === current && <Icon name="check" size={16} strokeWidth={2.6} />}
            </li>
          ))}
          {options.length === 0 && <li className="ui-select-empty">Sin opciones</li>}
        </ul>,
        document.body
      )}
    </div>
  );
}

export default Select;
