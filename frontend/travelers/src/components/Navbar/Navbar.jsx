import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';

import logoTravelers from '../../assets/images/logoEscrito.png';
import { useAuth } from '../../context/AuthContext';
import { ROLE_ADMIN, ROLE_PROVIDER } from '../../utils/format';
import Avatar from '../Avatar/Avatar';
import Icon from '../Icon/Icon';
import NotificationBell from '../NotificationBell/NotificationBell';

import './Navbar.css';

function Navbar() {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);

  // En el inicio la barra flota sobre la foto principal
  const isHome = location.pathname === '/';
  const isAdmin = user?.rol_id === ROLE_ADMIN;
  const isProvider = user?.rol_id === ROLE_PROVIDER;

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const linkClass = ({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`;

  return (
    <header className={`navbar ${isHome ? 'navbar-floating' : ''}`}>
      <nav className="navbar-inner" aria-label="Principal">
        <Link to="/" className="navbar-logo">
          <img src={logoTravelers} alt="Travelers" />
        </Link>

        <button
          type="button"
          className="navbar-toggle"
          aria-expanded={open}
          aria-controls="navbar-menu"
          aria-label={open ? 'Cerrar menú' : 'Abrir menú'}
          onClick={() => setOpen((value) => !value)}
        >
          <Icon name={open ? 'close' : 'menu'} size={22} />
        </button>

        <div id="navbar-menu" className={`navbar-menu ${open ? 'open' : ''}`}>
          <div className="navbar-links">
            <NavLink to="/" end className={linkClass}>Inicio</NavLink>
            <NavLink to="/packages" className={linkClass}>Paquetes</NavLink>
            {isAuthenticated && user && (
              isAdmin
                ? <NavLink to="/admin" className={linkClass}>Consola</NavLink>
                : isProvider
                  ? <NavLink to="/proveedor" className={linkClass}>Mi panel</NavLink>
                  : <NavLink to="/reservations" className={linkClass}>Mis reservas</NavLink>
            )}
          </div>

          <div className="navbar-actions">
            {isAuthenticated && user ? (
              <>
                <NotificationBell />
                <Link to="/profile" className="navbar-user">
                  <Avatar user={user} size={36} />
                  <span className="navbar-user-name">{user.nombre.split(' ')[0]}</span>
                </Link>
                <button
                  type="button"
                  className="navbar-logout"
                  onClick={handleLogout}
                  aria-label="Cerrar sesión"
                  title="Cerrar sesión"
                >
                  <Icon name="logout" size={20} />
                </button>
              </>
            ) : (
              <>
                <Link to="/register" className="navbar-register">Registro</Link>
                <Link to="/login" className="navbar-login">Iniciar sesión</Link>
              </>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}

export default Navbar;
