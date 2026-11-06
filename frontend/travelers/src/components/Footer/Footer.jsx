import { Link } from 'react-router-dom';

import './Footer.css';

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <p className="footer-logo">travelers<span>.</span></p>
          <p>Agencia de viajes · Proyecto Técnico en Programación de Software, SENA 2026.</p>
        </div>

        <div className="footer-columns">
          <div className="footer-column">
            <p className="footer-title">Explora</p>
            <Link to="/packages">Paquetes</Link>
            <Link to="/reservations">Mis reservas</Link>
          </div>
          <div className="footer-column">
            <p className="footer-title">Cuenta</p>
            <Link to="/login">Iniciar sesión</Link>
            <Link to="/register">Registro</Link>
            <Link to="/profile">Mi perfil</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
