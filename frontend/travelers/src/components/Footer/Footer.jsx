import { Link } from 'react-router-dom';

import Icon from '../Icon/Icon';
import { CONTACT, whatsappLink } from '../../utils/contact';

import './Footer.css';

function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <p className="footer-logo">travelers<span>.</span></p>
          <p>Paquetes turísticos por Colombia con alojamiento, transporte y tours. Reserva, paga y viaja en un solo lugar.</p>

          <ul className="footer-contact">
            <li>
              <Icon name="chat" size={16} />
              <a href={whatsappLink()} target="_blank" rel="noopener noreferrer">WhatsApp {CONTACT.phoneLabel}</a>
            </li>
            <li>
              <Icon name="mail" size={16} />
              <a href={`mailto:${CONTACT.email}`}>{CONTACT.email}</a>
            </li>
            <li>
              <Icon name="pin" size={16} />
              <span>{CONTACT.address}</span>
            </li>
            <li>
              <Icon name="clock" size={16} />
              <span>{CONTACT.hours}</span>
            </li>
          </ul>
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
          <div className="footer-column">
            <p className="footer-title">Legal</p>
            <Link to="/terminos">Términos y condiciones</Link>
            <Link to="/privacidad">Política de privacidad</Link>
            <Link to="/cancelaciones">Política de cancelación</Link>
          </div>
          <div className="footer-column">
            <p className="footer-title">Síguenos</p>
            {CONTACT.social.map((network) => (
              <a key={network.name} href={network.url} target="_blank" rel="noopener noreferrer">
                {network.name}
              </a>
            ))}
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>
          © {year} {CONTACT.companyName} · NIT {CONTACT.nit} · RNT {CONTACT.rnt}
        </p>
        <p>Proyecto Técnico en Programación de Software · SENA</p>
      </div>
    </footer>
  );
}

export default Footer;
