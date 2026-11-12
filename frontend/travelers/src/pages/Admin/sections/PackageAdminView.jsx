import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import fallbackImage from '../../../assets/images/fondo.png';
import Icon from '../../../components/Icon/Icon';
import { finalPrice, formatCurrency, formatDate, formatDateRange, getErrorMessage, tripLength } from '../../../utils/format';
import { describedIncludes, includeItems } from '../../../utils/packageIncludes';
import { productTypeIcon, productTypeLabel, unitShortLabel, useProductTypes } from '../../../utils/productTypes';
import { IVA_PERCENT, splitIva } from '../../../utils/taxes';

function Field({ label, children }) {
  return (
    <div className="user-file-field">
      <dt>{label}</dt>
      <dd>{children || <span className="admin-muted">—</span>}</dd>
    </div>
  );
}

function Empty({ children }) {
  return <p className="admin-empty">{children}</p>;
}

/**
 * Ficha de un paquete dentro de la consola (como la ficha de usuario):
 * se ve aunque el paquete esté inactivo y tiene botón para volver a la lista.
 */
function PackageAdminView({ packageId, version, cityName, products, onBack, onEdit, onImages, onToggleStatus, busy }) {
  const types = useProductTypes();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('resumen');
  const [activePhoto, setActivePhoto] = useState(0);

  const load = useCallback(async () => {
    try {
      const [detail, images, availability, reservations] = await Promise.all([
        api.get(`/packages/admin/${packageId}`),
        api.get(`/packages/${packageId}/images`).catch(() => ({ data: [] })),
        api.get(`/reservations/availability/${packageId}`).catch(() => ({ data: null })),
        api.get('/reservations/').catch(() => ({ data: [] })),
      ]);
      setData({
        paquete: detail.data,
        fotos: images.data.filter((image) => image.imagen_url),
        disponibilidad: availability.data,
        reservas: reservations.data
          .filter((item) => item.id_paquete_turistico === packageId)
          .sort((a, b) => String(b.fecha_compra || '').localeCompare(String(a.fecha_compra || ''))),
      });
      setError('');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible cargar el paquete.'));
    }
  }, [packageId]);

  // "version" cambia cuando la lista se recarga (tras editar, cambiar fotos o el estado)
  useEffect(() => {
    load();
  }, [load, version]);

  const back = (
    <button type="button" className="btn btn-secondary btn-small user-file-back" onClick={onBack}>
      <Icon name="arrowLeft" size={16} /> Volver a paquetes
    </button>
  );

  if (error) {
    return (
      <>
        {back}
        <div className="alert alert-error">{error}</div>
      </>
    );
  }

  if (!data) return <p className="page-status">Cargando paquete...</p>;

  const { paquete, fotos, disponibilidad, reservas } = data;
  const isActive = paquete.estado === 'activo';
  const price = finalPrice(paquete);
  const { base, iva } = splitIva(price);
  const days = tripLength(paquete.fecha_inicio, paquete.fecha_fin);
  const photo = fotos[activePhoto]?.imagen_url || fotos[0]?.imagen_url || fallbackImage;

  const productRows = (paquete.productos || []).map((item) => ({
    ...item,
    producto: products.find((product) => product.id_producto === item.producto_id),
  }));

  // «Qué incluye», igual que en la página pública: lo elegido en el formulario,
  // si no la frase «Incluye ...» de la descripción y si no los productos
  const chosen = includeItems(paquete.incluye);
  const described = describedIncludes(paquete.descripcion);
  const includes = chosen.length > 0
    ? chosen
    : described.length > 0
    ? described.map((text) => ({ key: text, text, icon: 'check' }))
    : productRows.filter((item) => item.producto).map((item) => ({
      key: `producto-${item.producto_id}`,
      text: item.cantidad > 1 ? `${item.producto.nombre} (×${item.cantidad})` : item.producto.nombre,
      icon: productTypeIcon(item.producto.tipo_producto),
    }));

  const active = reservas.filter((item) => item.estado !== 'cancelada');
  const confirmed = reservas.filter((item) => item.estado === 'confirmada');
  const travelers = active.reduce((sum, item) => sum + item.cantidad_personas, 0);
  const sales = confirmed.reduce((sum, item) => sum + Number(item.total_reserva || 0), 0);

  const tabs = [
    { key: 'resumen', label: 'Resumen' },
    { key: 'fotos', label: 'Fotos', count: fotos.length },
    { key: 'productos', label: 'Productos', count: productRows.length },
    { key: 'reservas', label: 'Reservas', count: reservas.length },
  ];

  return (
    <>
      {back}

      <header className="user-file-header surface">
        <img className="package-file-cover" src={fotos[0]?.imagen_url || fallbackImage} alt="" />
        <div className="user-file-identity">
          <p className="eyebrow">Paquete #{paquete.id_paquete_turistico}</p>
          <h1>{paquete.nombre}</h1>
          <p className="admin-muted">{cityName(paquete.ciudad_id)} · {formatDateRange(paquete.fecha_inicio, paquete.fecha_fin)}</p>
          <div className="user-file-badges">
            <span className={`badge badge-${paquete.estado}`}>{paquete.estado}</span>
            {paquete.descuento > 0 && <span className="badge badge-pendiente">−{paquete.descuento} %</span>}
            {!isActive && <span className="badge badge-inactivo">no se ve en el sitio</span>}
          </div>
        </div>

        <div className="user-file-actions">
          <button type="button" className="btn btn-secondary btn-small" onClick={onEdit}>Editar</button>
          <button type="button" className="btn btn-secondary btn-small" onClick={onImages}>Fotos</button>
          <button
            type="button"
            className={`btn btn-small ${isActive ? 'btn-danger' : 'btn-primary'}`}
            disabled={busy}
            onClick={onToggleStatus}
          >
            {isActive ? 'Desactivar' : 'Activar'}
          </button>
        </div>
      </header>

      <div className="admin-summary">
        <div className="admin-stat highlight">
          <span>Precio por persona</span>
          <strong>{formatCurrency(price)}</strong>
        </div>
        <div className="admin-stat">
          <span>Cupos disponibles</span>
          <strong>{disponibilidad ? `${disponibilidad.cupos_disponibles} / ${disponibilidad.cupo_max}` : paquete.cupo_max}</strong>
        </div>
        <div className="admin-stat">
          <span>Viajeros (reservas activas)</span>
          <strong>{travelers}</strong>
        </div>
        <div className="admin-stat">
          <span>Ventas confirmadas</span>
          <strong>{formatCurrency(sales)}</strong>
        </div>
      </div>

      <div className="user-file-tabs" role="tablist" aria-label="Información del paquete">
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={tab === item.key}
            className="chip"
            aria-pressed={tab === item.key}
            onClick={() => setTab(item.key)}
          >
            {item.label}
            {item.count > 0 && <span className="user-file-count">{item.count}</span>}
          </button>
        ))}
      </div>

      {tab === 'resumen' && (
        <>
          <div className="admin-two-columns">
            <section className="surface">
              <h2 className="user-file-title"><Icon name="calendar" size={18} /> Viaje</h2>
              <dl className="user-file-fields">
                <Field label="Destino">{cityName(paquete.ciudad_id)}</Field>
                <Field label="Salida">{formatDate(paquete.fecha_inicio)}</Field>
                <Field label="Regreso">{formatDate(paquete.fecha_fin)}</Field>
                <Field label="Duración">{days}</Field>
                <Field label="Cupo máximo">{paquete.cupo_max}</Field>
                <Field label="Estado">{paquete.estado}</Field>
              </dl>
            </section>

            <section className="surface">
              <h2 className="user-file-title"><Icon name="card" size={18} /> Precio por persona</h2>
              <dl className="user-file-fields">
                <Field label="Precio de lista">{formatCurrency(paquete.precio)}</Field>
                <Field label="Descuento">{paquete.descuento > 0 ? `${paquete.descuento} %` : 'Sin descuento'}</Field>
                <Field label="Valor sin IVA">{formatCurrency(base)}</Field>
                <Field label={`IVA (${IVA_PERCENT} %)`}>{formatCurrency(iva)}</Field>
                <Field label="Precio final (IVA incluido)">{formatCurrency(price)}</Field>
              </dl>
            </section>
          </div>

          <section className="surface user-file-spaced">
            <h2 className="user-file-title"><Icon name="compass" size={18} /> Descripción</h2>
            <p className="package-file-description">{paquete.descripcion}</p>

            <h2 className="user-file-title user-file-spaced"><Icon name="check" size={18} /> Qué incluye</h2>
            {includes.length === 0 ? <Empty>No se ha indicado qué incluye.</Empty> : (
              <ul className="package-file-includes">
                {includes.map((item) => (
                  <li key={item.key}><Icon name={item.icon} size={16} /> {item.text}</li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {tab === 'fotos' && (
        <div className="surface">
          {fotos.length === 0 ? (
            <Empty>El paquete no tiene fotos. Usa «Fotos» para agregarlas.</Empty>
          ) : (
            <>
              <img className="package-file-photo" src={photo} alt={`Foto de ${paquete.nombre}`} />
              <div className="package-file-thumbs">
                {fotos.map((image, index) => (
                  <button
                    key={image.id_imagen}
                    type="button"
                    className={index === activePhoto ? 'is-active' : ''}
                    aria-label={`Ver foto ${index + 1}`}
                    onClick={() => setActivePhoto(index)}
                  >
                    <img src={image.imagen_url} alt="" loading="lazy" />
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {tab === 'productos' && (
        <div className="surface">
          {productRows.length === 0 ? <Empty>No tiene productos.</Empty> : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Tipo</th>
                    <th>Cantidad</th>
                    <th>Costo del proveedor</th>
                  </tr>
                </thead>
                <tbody>
                  {productRows.map((item) => (
                    <tr key={item.producto_id}>
                      <td className="admin-strong">{item.producto?.nombre || `#${item.producto_id}`}</td>
                      <td className="admin-muted">{item.producto ? productTypeLabel(types, item.producto.tipo_producto) : ''}</td>
                      <td>{item.cantidad}</td>
                      <td>
                        {item.producto ? (
                          <>
                            {formatCurrency(item.producto.costo)}{' '}
                            <span className="admin-muted">{unitShortLabel(item.producto.unidad_cobro)}</span>
                          </>
                        ) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'reservas' && (
        <div className="surface">
          {reservas.length === 0 ? <Empty>Este paquete aún no tiene reservas.</Empty> : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Reserva</th>
                    <th>Comprada</th>
                    <th>Viajeros</th>
                    <th>Total</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {reservas.map((item) => (
                    <tr key={item.id_reserva}>
                      <td className="admin-strong">{item.codigo_reserva}</td>
                      <td className="admin-muted">{formatDate(item.fecha_compra)}</td>
                      <td>{item.cantidad_personas}</td>
                      <td>{formatCurrency(item.total_reserva)}</td>
                      <td><span className={`badge badge-${item.estado}`}>{item.estado}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  );
}

export default PackageAdminView;
