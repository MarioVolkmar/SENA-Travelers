import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Icon from '../../components/Icon/Icon';
import { formatLongDate } from '../../utils/format';

import './VerifyVoucher.css';
import usePageTitle from '../../hooks/usePageTitle';

const STATUS = {
  confirmada: { title: 'Reserva válida', text: 'El voucher corresponde a una reserva pagada y confirmada.', tone: 'ok' },
  pendiente: { title: 'Reserva sin pagar', text: 'La reserva existe pero todavía no se ha pagado.', tone: 'warn' },
  cancelada: { title: 'Reserva cancelada', text: 'Este voucher ya no es válido: la reserva fue cancelada.', tone: 'bad' },
};

/** Página pública que abre el código QR del voucher. */
function VerifyVoucher() {
  usePageTitle('Verificar voucher');
  const { codigo } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/vouchers/verify/${encodeURIComponent(codigo)}`)
      .then((response) => setData(response.data))
      .catch((requestError) => setError(
        requestError.response?.status === 404
          ? 'No encontramos una reserva con ese código.'
          : 'No fue posible verificar el voucher en este momento.'
      ));
  }, [codigo]);

  const status = data ? STATUS[data.estado] || STATUS.pendiente : null;

  return (
    <section className="page verify-page">
      <div className={`verify-card ${error ? 'is-bad' : status ? `is-${status.tone}` : ''}`}>
        {!data && !error && <p className="page-status">Verificando voucher...</p>}

        {error && (
          <>
            <span className="verify-icon"><Icon name="close" size={34} strokeWidth={2.4} /></span>
            <h1>Voucher no válido</h1>
            <p>{error}</p>
            <p className="verify-code">{codigo}</p>
          </>
        )}

        {data && (
          <>
            <span className="verify-icon">
              <Icon name={status.tone === 'ok' ? 'check' : status.tone === 'bad' ? 'close' : 'clock'} size={34} strokeWidth={2.4} />
            </span>
            <p className="eyebrow">Verificación Travelers</p>
            <h1>{status.title}</h1>
            <p>{status.text}</p>

            <dl className="verify-data">
              <div><dt>Código</dt><dd>{data.codigo_reserva}</dd></div>
              <div><dt>Paquete</dt><dd>{data.paquete}</dd></div>
              <div><dt>Destino</dt><dd>{data.destino}</dd></div>
              <div><dt>Fecha del viaje</dt><dd>{formatLongDate(data.fecha_reserva)}</dd></div>
              <div><dt>Viajeros</dt><dd>{data.cantidad_personas}</dd></div>
              <div><dt>Titular</dt><dd>{data.titular}</dd></div>
            </dl>
          </>
        )}

        <Link to="/" className="btn btn-secondary">Ir a Travelers</Link>
      </div>
    </section>
  );
}

export default VerifyVoucher;
