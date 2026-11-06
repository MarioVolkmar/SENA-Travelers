import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { useFavorites } from '../../context/FavoritesContext';
import Icon from '../Icon/Icon';
import './FavoriteButton.css';

/** Corazón para guardar un paquete. Funciona aunque esté dentro de un enlace. */
function FavoriteButton({ packageId, packageName, variant = 'overlay' }) {
  const { isAuthenticated } = useAuth();
  const { isFavorite, toggle } = useFavorites();
  const navigate = useNavigate();
  const location = useLocation();
  const saved = isFavorite(packageId);

  const handleClick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!isAuthenticated) {
      navigate('/login', { state: { from: location.pathname } });
      return;
    }
    toggle(packageId);
  };

  const label = saved ? `Quitar ${packageName} de favoritos` : `Guardar ${packageName} en favoritos`;

  return (
    <button
      type="button"
      className={`favorite-button favorite-button-${variant} ${saved ? 'is-saved' : ''}`}
      onClick={handleClick}
      aria-pressed={saved}
      aria-label={label}
      title={saved ? 'Quitar de favoritos' : 'Guardar en favoritos'}
    >
      <Icon name="heart" size={variant === 'inline' ? 18 : 20} strokeWidth={2.2} />
      {variant === 'inline' && <span>{saved ? 'Guardado' : 'Guardar'}</span>}
    </button>
  );
}

export default FavoriteButton;
