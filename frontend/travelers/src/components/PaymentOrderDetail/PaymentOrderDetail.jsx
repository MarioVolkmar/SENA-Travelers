import Modal from '../Modal/Modal';
import { formatCurrency, formatDate } from '../../utils/format';
import { ORDER_BADGE, ORDER_STATUS_LABELS } from '../../utils/paymentOrders';
import { unitShortLabel } from '../../utils/productTypes';

import './PaymentOrderDetail.css';

/** Detalle de una orden de pago a proveedor: reserva, líneas y estado del pago. */
function PaymentOrderDetail({ order, onClose, footer }) {
  return (
    <Modal
      title={`Orden ${order.codigo}`}
      subtitle={`${order.nombre_proveedor} · ${order.paquete}`}
      size="large"
      onClose={onClose}
      footer={footer}
    >
      <div className="order-facts">
        <div><span>Estado</span><strong><span className={`badge badge-${ORDER_BADGE[order.estado]}`}>{ORDER_STATUS_LABELS[order.estado]}</span></strong></div>
        <div><span>Reserva</span><strong>{order.codigo_reserva}</strong></div>
        <div><span>Viaje</span><strong>{formatDate(order.fecha_viaje)} · {order.viajeros} viajeros</strong></div>
        <div><span>Vence</span><strong>{formatDate(order.fecha_vencimiento)}</strong></div>
      </div>

      <div className="table-wrapper">
        <table className="data-table order-lines">
          <thead>
            <tr>
              <th>Servicio</th>
              <th>Costo</th>
              <th>Cantidad</th>
              <th>Viajeros</th>
              <th>Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {order.detalles.map((line) => (
              <tr key={line.producto_id}>
                <td className="admin-strong">{line.descripcion}</td>
                <td>{formatCurrency(line.costo_unitario)} <span className="admin-muted">{unitShortLabel(line.unidad_cobro)}</span></td>
                <td>{line.cantidad}</td>
                <td>{line.unidad_cobro === 'servicio' ? '—' : line.viajeros}</td>
                <td className="admin-strong">{formatCurrency(line.subtotal)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={4}>Total de la orden</td>
              <td>{formatCurrency(order.monto)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {(order.referencia_pago || order.nota) && (
        <div className="order-notes">
          {order.referencia_pago && (
            <p><strong>Pagada</strong> el {formatDate(order.fecha_pago)} · referencia <strong>{order.referencia_pago}</strong></p>
          )}
          {order.nota && <p><strong>Nota:</strong> {order.nota}</p>}
        </div>
      )}
    </Modal>
  );
}

export default PaymentOrderDetail;
