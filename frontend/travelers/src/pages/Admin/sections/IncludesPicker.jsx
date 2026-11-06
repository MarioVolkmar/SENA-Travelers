import { useState } from 'react';

import Icon from '../../../components/Icon/Icon';
import { PACKAGE_INCLUDES } from '../../../utils/packageIncludes';

const MAX_EXTRAS = 10;
const MAX_LENGTH = 80;

/** Selector de lo que incluye el paquete: catálogo con íconos + elementos propios.
 *  `onChange` debe ser un setter de useState (acepta una función). */
function IncludesPicker({ value, onChange }) {
  const [draft, setDraft] = useState('');
  const { tipos, otros } = value;

  // onChange es el setter de estado del formulario: se usa la forma con función
  // para no perder cambios si se marcan varias opciones seguidas
  const toggle = (key) => {
    onChange((current) => ({
      ...current,
      tipos: current.tipos.includes(key) ? current.tipos.filter((item) => item !== key) : [...current.tipos, key],
    }));
  };

  const addExtra = () => {
    const text = draft.replace(/\s+/g, ' ').trim();
    if (!text || otros.length >= MAX_EXTRAS) return;
    onChange((current) => (
      current.otros.some((item) => item.toLowerCase() === text.toLowerCase())
        ? current
        : { ...current, otros: [...current.otros, text] }
    ));
    setDraft('');
  };

  const removeExtra = (text) => onChange((current) => ({ ...current, otros: current.otros.filter((item) => item !== text) }));

  return (
    <div className="includes-picker">
      <div className="includes-grid" role="group" aria-label="Qué incluye el paquete">
        {PACKAGE_INCLUDES.map((item) => {
          const active = tipos.includes(item.key);
          return (
            <button
              key={item.key}
              type="button"
              className={`includes-option ${active ? 'is-active' : ''}`}
              aria-pressed={active}
              onClick={() => toggle(item.key)}
            >
              <span className="includes-option-icon"><Icon name={item.icon} size={18} /></span>
              <span>{item.label}</span>
              <span className="includes-option-check" aria-hidden="true"><Icon name="check" size={14} strokeWidth={3} /></span>
            </button>
          );
        })}
      </div>

      <div className="includes-extra">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              addExtra();
            }
          }}
          maxLength={MAX_LENGTH}
          placeholder="Otro elemento: «Cena de bienvenida», «Kit de snorkel»..."
          aria-label="Agregar otro elemento incluido"
          disabled={otros.length >= MAX_EXTRAS}
        />
        <button type="button" className="btn btn-secondary btn-small" onClick={addExtra} disabled={!draft.trim() || otros.length >= MAX_EXTRAS}>
          + Agregar
        </button>
      </div>

      {otros.length > 0 && (
        <ul className="includes-extras-list">
          {otros.map((text) => (
            <li key={text}>
              <Icon name="check" size={14} />
              <span>{text}</span>
              <button type="button" onClick={() => removeExtra(text)} aria-label={`Quitar ${text}`}>
                <Icon name="close" size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="field-hint">
        {tipos.length + otros.length === 0
          ? 'Si no eliges nada, la página del paquete muestra los productos incluidos.'
          : `${tipos.length + otros.length} ${tipos.length + otros.length === 1 ? 'elemento' : 'elementos'} en «Qué incluye».`}
      </p>
    </div>
  );
}

export default IncludesPicker;
