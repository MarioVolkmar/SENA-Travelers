import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../../api/axiosConfig';
import PageHero from '../../components/PageHero/PageHero';
import bannerImage from '../../assets/images/banner.jpg';
import usePageTitle from '../../hooks/usePageTitle';
import { CONTACT } from '../../utils/contact';

import './LegalPage.css';

const UPDATED = '11 de noviembre de 2026';

function Contact() {
  return (
    <p>
      Escríbenos a <a href={`mailto:${CONTACT.email}`}>{CONTACT.email}</a>, llámanos o escríbenos por WhatsApp al{' '}
      {CONTACT.phoneLabel}, o visítanos en {CONTACT.address}.
    </p>
  );
}

function Terms() {
  return (
    <>
      <h2>1. Quiénes somos</h2>
      <p>
        {CONTACT.companyName} (NIT {CONTACT.nit}, Registro Nacional de Turismo {CONTACT.rnt}) es una agencia de viajes
        que vende paquetes turísticos dentro de Colombia a través de este sitio web.
      </p>

      <h2>2. Uso del sitio y de tu cuenta</h2>
      <ul>
        <li>Para reservar necesitas una cuenta con tu correo verificado y tu perfil de viajero completo.</li>
        <li>Eres responsable de que tus datos y los de tus acompañantes sean correctos y de mantener tu contraseña en secreto.</li>
        <li>Podemos suspender cuentas que hagan un uso indebido del sitio o entreguen información falsa.</li>
      </ul>

      <h2>3. Paquetes, precios y cupos</h2>
      <ul>
        <li>Los precios se muestran en pesos colombianos, por persona, e incluyen los servicios descritos en cada paquete en “Qué incluye”.</li>
        <li>Todos los precios <strong>incluyen el IVA del 19 %</strong>. En el resumen de la reserva, el pago, el voucher y los correos se muestra el desglose: valor sin IVA + IVA = total.</li>
        <li>Los cupos son limitados; el sistema solo permite reservar mientras haya cupos disponibles.</li>
        <li>Los descuentos y cupones aplican según sus condiciones y no son acumulables salvo que se indique lo contrario.</li>
      </ul>

      <h2>4. Reservas y pagos</h2>
      <ul>
        <li>Una reserva queda <strong>pendiente</strong> al crearla y se <strong>confirma</strong> cuando se registra el pago total.</li>
        <li>Las reservas pendientes tienen un plazo para pagarse (se muestra en “Mis reservas”). Antes de que venza te avisamos por correo y en la campana; si vence sin pago, la reserva se cancela automáticamente, sin ningún cobro, y sus cupos quedan libres.</li>
        <li>Con la reserva confirmada puedes descargar tu voucher, que incluye un código QR para verificar su autenticidad.</li>
        <li>Recibirás por correo la confirmación de la reserva y del pago.</li>
      </ul>

      <h2>5. Cancelaciones y reembolsos</h2>
      <p>
        Las condiciones para cancelar y los valores que se reembolsan están en nuestra{' '}
        <Link to="/cancelaciones">política de cancelación</Link>.
      </p>

      <h2>6. Responsabilidad</h2>
      <p>
        Los servicios de alojamiento, transporte, alimentación y actividades los prestan proveedores aliados. La agencia
        responde por la organización del paquete conforme a la Ley 300 de 1996 (Ley General de Turismo) y el Estatuto del
        Consumidor (Ley 1480 de 2011). No respondemos por hechos de fuerza mayor como fenómenos naturales, cierres de vías o
        decisiones de las autoridades; en esos casos buscaremos reprogramar o reembolsar según corresponda.
      </p>

      <h2>7. Reseñas</h2>
      <p>
        Solo pueden opinar viajeros con un viaje confirmado y ya realizado. Podemos ocultar reseñas con lenguaje ofensivo o
        que no correspondan a la experiencia del viaje.
      </p>

      <h2>8. Contacto</h2>
      <Contact />
    </>
  );
}

function Privacy() {
  return (
    <>
      <p>
        En cumplimiento de la Ley 1581 de 2012 y el Decreto 1377 de 2013, esta política explica cómo {CONTACT.companyName}{' '}
        trata tus datos personales.
      </p>

      <h2>1. Responsable del tratamiento</h2>
      <p>
        {CONTACT.companyName}, NIT {CONTACT.nit}, {CONTACT.address}. Correo: <a href={`mailto:${CONTACT.email}`}>{CONTACT.email}</a>.
      </p>

      <h2>2. Qué datos recogemos</h2>
      <ul>
        <li><strong>Cuenta:</strong> nombre, correo, contraseña (guardada cifrada, nunca en texto plano) y foto de perfil opcional.</li>
        <li><strong>Perfil de viajero:</strong> documento de identidad, fecha de nacimiento y ciudad.</li>
        <li><strong>Acompañantes:</strong> nombre, documento y fecha de nacimiento de quienes viajan contigo.</li>
        <li><strong>Reservas y pagos:</strong> paquetes, fechas, valores y método de pago (no guardamos números de tarjetas).</li>
        <li><strong>Proveedores:</strong> datos de la empresa y de contacto para coordinar los servicios.</li>
      </ul>

      <h2>3. Para qué los usamos</h2>
      <ul>
        <li>Crear y administrar tu cuenta y tus reservas.</li>
        <li>Enviarte confirmaciones, recordatorios de viaje y avisos sobre tus reservas.</li>
        <li>Compartir con los proveedores del paquete solo los datos necesarios para prestar el servicio (por ejemplo, el nombre de los viajeros para el hotel).</li>
        <li>Cumplir obligaciones legales, contables y tributarias.</li>
      </ul>

      <h2>4. Tus derechos</h2>
      <p>Como titular de los datos puedes:</p>
      <ul>
        <li>Conocer, actualizar y corregir tus datos (puedes hacerlo desde “Mi perfil”).</li>
        <li>Pedir prueba de la autorización que nos diste y saber cómo usamos tus datos.</li>
        <li>Revocar la autorización o pedir que eliminemos tus datos, cuando no exista una obligación legal de conservarlos.</li>
        <li>Presentar quejas ante la Superintendencia de Industria y Comercio.</li>
      </ul>

      <h2>5. Cómo ejercerlos</h2>
      <p>
        Envía tu solicitud a <a href={`mailto:${CONTACT.email}`}>{CONTACT.email}</a> indicando tu nombre, documento y lo que
        necesitas. Respondemos consultas en máximo 10 días hábiles y reclamos en máximo 15 días hábiles.
      </p>

      <h2>6. Seguridad</h2>
      <p>
        Usamos conexión cifrada (HTTPS), contraseñas cifradas, acceso por roles y límites de intentos de inicio de sesión
        para proteger tu información.
      </p>
    </>
  );
}

function Cancellations() {
  const [policy, setPolicy] = useState(null);

  useEffect(() => {
    api.get('/reservations/cancellation-policy')
      .then((response) => setPolicy(response.data))
      .catch(() => setPolicy(null));
  }, []);

  // Valores por defecto mientras llegan (o si no se pueden consultar)
  const freeDays = policy?.dias_sin_penalidad ?? 7;
  const penalty = policy?.porcentaje_penalidad ?? 30;

  return (
    <>
      <div className="legal-highlight">
        <div>
          <strong>{freeDays} días</strong>
          <span>antes del viaje puedes cancelar sin costo</span>
        </div>
        <div>
          <strong>{penalty} %</strong>
          <span>de penalidad sobre lo pagado si cancelas después</span>
        </div>
      </div>

      <h2>1. Cómo cancelar</h2>
      <p>
        Entra a <Link to="/reservations">Mis reservas</Link>, elige la reserva y pulsa “Cancelar”. Antes de confirmar verás
        cuánto se te reembolsa. Puedes cancelar reservas pendientes o confirmadas hasta el día anterior al viaje.
      </p>

      <h2>2. Cuánto se reembolsa</h2>
      <ul>
        <li><strong>Hasta {freeDays} días antes del viaje:</strong> se devuelve el 100 % de lo pagado.</li>
        <li><strong>Después de esa fecha:</strong> se cobra una penalidad del {penalty} % sobre lo pagado y se devuelve el resto.</li>
        <li><strong>Reservas pendientes (sin pago):</strong> se cancelan sin ningún cobro. Si no se pagan en {policy?.horas_para_pagar ?? 24} horas, se cancelan solas.</li>
        <li><strong>El día del viaje o después:</strong> la reserva ya no se puede cancelar.</li>
      </ul>

      <h2>3. Ejemplo</h2>
      <p>
        Pagaste $1.000.000 por un viaje que sale el 20 de diciembre. Si cancelas hasta el{' '}
        {20 - freeDays > 0 ? `${20 - freeDays} de diciembre` : 'límite'}, se te devuelven $1.000.000. Si cancelas después,
        se descuentan ${(10000 * penalty).toLocaleString('es-CO')} y se te devuelven ${(10000 * (100 - penalty)).toLocaleString('es-CO')}.
      </p>

      <h2>4. Derecho de retracto</h2>
      <p>
        Por ser una compra en línea, el Estatuto del Consumidor (Ley 1480 de 2011, artículo 47) te permite retractarte dentro
        de los 5 días hábiles siguientes a la compra, siempre que el servicio no haya empezado a prestarse.
      </p>

      <h2>5. Cancelaciones de la agencia</h2>
      <p>
        Si la agencia o un proveedor debe cancelar el paquete, te ofreceremos otra fecha o el reembolso total de lo pagado.
      </p>

      <h2>6. Dudas</h2>
      <Contact />
    </>
  );
}

const DOCUMENTS = {
  terminos: { title: 'Términos y condiciones', Body: Terms },
  privacidad: { title: 'Política de privacidad', Body: Privacy },
  cancelaciones: { title: 'Política de cancelación', Body: Cancellations },
};

/** Páginas legales: términos, privacidad y cancelaciones. */
function LegalPage({ doc }) {
  const { title, Body } = DOCUMENTS[doc];
  usePageTitle(title);

  return (
    <>
      <PageHero image={bannerImage} eyebrow="Información legal" title={title}>
        <p>Última actualización: {UPDATED}</p>
      </PageHero>

      <section className="page page-after-hero">
        <article className="legal-content">
          <Body />
        </article>

        <nav className="legal-nav" aria-label="Otros documentos legales">
          {Object.entries(DOCUMENTS)
            .filter(([key]) => key !== doc)
            .map(([key, item]) => (
              <Link key={key} to={`/${key}`} className="btn btn-secondary">{item.title}</Link>
            ))}
        </nav>
      </section>
    </>
  );
}

export default LegalPage;
