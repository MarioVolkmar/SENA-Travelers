/**
 * Datos de contacto de la agencia (pie de página, botón de WhatsApp y páginas legales).
 *
 * Son DATOS DE EJEMPLO: cámbialos aquí por los reales y se actualizan en todo el sitio.
 */
export const CONTACT = {
  companyName: 'Travelers Agencia de Viajes S.A.S.',
  nit: '900.000.000-0',
  rnt: '00000',                 // Registro Nacional de Turismo
  whatsapp: '573000000000',     // solo números, con el 57 de Colombia
  phoneLabel: '+57 300 000 0000',
  email: 'contacto@travelers.com.co',
  address: 'SENA Regional Antioquia, Medellín, Colombia',
  hours: 'Lunes a viernes de 8:00 a. m. a 6:00 p. m. · Sábados de 9:00 a. m. a 1:00 p. m.',
  social: [
    { name: 'Instagram', url: 'https://www.instagram.com/' },
  ],
};

/** Enlace de WhatsApp con un mensaje inicial ya escrito. */
export function whatsappLink(message = 'Hola, quiero información sobre un paquete de Travelers.') {
  return `https://wa.me/${CONTACT.whatsapp}?text=${encodeURIComponent(message)}`;
}
