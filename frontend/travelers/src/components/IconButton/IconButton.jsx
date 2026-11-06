import Icon from '../Icon/Icon';
import './IconButton.css';

/**
 * Botón de acción con ícono y texto emergente.
 * Con `hidden` deja el hueco vacío para que los demás botones
 * de la fila no cambien de posición.
 */
function IconButton({ icon, label, variant = 'neutral', hidden = false, disabled, onClick }) {
  if (hidden) return <span className="action-icon action-icon-placeholder" aria-hidden="true" />;

  return (
    <button
      type="button"
      className={`action-icon action-icon-${variant}`}
      data-tip={label}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon name={icon} size={18} />
    </button>
  );
}

export default IconButton;
