import Icon from '../Icon/Icon';
import { whatsappLink } from '../../utils/contact';

import './WhatsAppButton.css';

/** Botón flotante para escribirle a la agencia por WhatsApp. */
function WhatsAppButton() {
  return (
    <a
      className="whatsapp-button"
      href={whatsappLink()}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Escríbenos por WhatsApp"
    >
      <Icon name="chat" size={24} />
      <span className="whatsapp-button-text">¿Dudas? Escríbenos</span>
    </a>
  );
}

export default WhatsAppButton;
