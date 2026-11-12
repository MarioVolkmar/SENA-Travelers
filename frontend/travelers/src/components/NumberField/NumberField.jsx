import { formatCurrency } from '../../utils/format';

/**
 * Mensaje de error de un número según su rango, o null si está bien.
 * - optional: vacío es válido (campos como "usos máximos" o "compra mínima").
 * - decimals: acepta decimales (latitud/longitud); si no, solo enteros.
 * - money: muestra el rango en pesos.
 */
export function numberError(value, range, { optional = false, decimals = false, money = false, unit = '' } = {}) {
  const empty = value === '' || value === null || value === undefined;
  if (empty) return optional ? null : 'Este campo es obligatorio.';

  const number = Number(value);
  const show = (amount) => (money ? formatCurrency(amount) : amount.toLocaleString('es-CO'));
  const rangeText = `entre ${show(range.min)} y ${show(range.max)}${unit}`;

  if (!Number.isFinite(number)) return `Escribe un número ${rangeText}.`;
  if (!decimals && !Number.isInteger(number)) return `Escribe un número entero ${rangeText}.`;
  if (number < range.min || number > range.max) return `El valor debe estar ${rangeText}.`;
  return null;
}

/**
 * Campo numérico con su rango: mientras se escribe, si el valor se sale del rango
 * aparece en rojo el mensaje con los valores permitidos (y el formulario debe
 * deshabilitar su botón usando numberError con los mismos datos).
 */
function NumberField({
  id,
  label,
  value,
  onChange,
  range,
  hint,
  optional = false,
  decimals = false,
  money = false,
  unit = '',
  placeholder,
  className = 'field',
  inputProps = {},
}) {
  const error = numberError(value, range, { optional, decimals, money, unit });
  // El mensaje de obligatorio solo aparece al enviar (lo muestra el navegador); el de rango, siempre
  const visibleError = value === '' || value === null || value === undefined ? null : error;

  return (
    <div className={className}>
      {label && <label htmlFor={id}>{label}</label>}
      <input
        id={id}
        type="number"
        min={range.min}
        max={range.max}
        step={decimals ? 'any' : '1'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={!optional}
        aria-invalid={Boolean(visibleError)}
        aria-describedby={`${id}-hint`}
        {...inputProps}
      />
      {visibleError ? (
        <span id={`${id}-hint`} className="field-hint field-error" role="alert">{visibleError}</span>
      ) : (
        hint && <span id={`${id}-hint`} className="field-hint">{hint}</span>
      )}
    </div>
  );
}

export default NumberField;
