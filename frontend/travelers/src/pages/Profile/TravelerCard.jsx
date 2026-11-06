import cardImage from '../../assets/images/banner.jpg';
import Avatar from '../../components/Avatar/Avatar';

function memberSince(date) {
  if (!date) return '—';

  return new Date(date)
    .toLocaleDateString('es-CO', { month: 'short', year: 'numeric' })
    .replace('.', '');
}

/**
 * Carnet de viajero: muestra los datos del cliente como una tarjeta.
 * Recibe los valores ya resueltos para poder mostrarse "en vivo"
 * mientras el usuario llena el formulario.
 */
function TravelerCard({ user, identificacion, ciudad, complete }) {
  const number = `TR-${String(user.id_usuario).padStart(6, '0')}`;

  return (
    <div className={`traveler-card ${complete ? 'is-complete' : ''}`}>
      <img src={cardImage} alt="" className="traveler-card-photo" />

      <div className="traveler-card-content">
        <div className="traveler-card-top">
          <div>
            <p className="traveler-card-brand">travelers<span>.</span></p>
            <p className="traveler-card-kind">Carnet de viajero</p>
          </div>
          <Avatar user={user} size={58} className="traveler-card-avatar" />
        </div>

        <div>
          <p className="traveler-card-name">{user.nombre}</p>
          <dl className="traveler-card-data">
            <div>
              <dt>Documento</dt>
              <dd>{identificacion || '— — —'}</dd>
            </div>
            <div>
              <dt>Ciudad</dt>
              <dd>{ciudad || '— — —'}</dd>
            </div>
            <div>
              <dt>Desde</dt>
              <dd>{memberSince(user.fecha_creacion)}</dd>
            </div>
          </dl>
          <p className="traveler-card-number">{number}</p>
        </div>
      </div>
    </div>
  );
}

export default TravelerCard;
