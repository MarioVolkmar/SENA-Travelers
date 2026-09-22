import { Link, useNavigate } from 'react-router-dom';

import logoTravelers from '../../assets/images/logoEscrito.png';
import { useAuth } from '../../context/AuthContext';

import './Navbar.css';

function Navbar() {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-logo">
        <img
          src={logoTravelers}
          alt="Logo Travelers"
          className="logo-icono"
        />
      </Link>

      <div className="navbar-links">
        <Link to="/">Inicio</Link>

        <Link to="/packages">
          Paquetes turísticos
        </Link>

        {isAuthenticated &&  user &&(
          <>
            <Link to="/reservations">
              Reservas
            </Link>

            <Link to="/profile">
              {user.nombre.toUpperCase()}
            </Link>
          </>
        )}

        {!isAuthenticated && (
          <Link to="/register">
            Registro
          </Link>
        )}

        {isAuthenticated ? (
          <button
            type="button"
            className="navbar-logout navbar-button"
            onClick={handleLogout}
          >
            Cerrar sesión
          </button>
        ) : (
          <Link to="/login" className="navbar-login">
            Iniciar sesión
          </Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;