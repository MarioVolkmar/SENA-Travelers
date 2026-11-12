import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import Icon from '../../../components/Icon/Icon';
import { formatCurrency, formatDateRange, getErrorMessage } from '../../../utils/format';
import { productTypeIcon, productTypeLabel, unitShortLabel, useProductTypes } from '../../../utils/productTypes';

function Field({ label, children }) {
  return (
    <div className="user-file-field">
      <dt>{label}</dt>
      <dd>{children || <span className="admin-muted">—</span>}</dd>
    </div>
  );
}

/** Ficha de un producto dentro de la consola, con los paquetes que lo incluyen. */
function ProductAdminView({ product, cityName, provider, goTo, onBack, onEdit, onToggleStatus, busy }) {
  const types = useProductTypes();
  const [packages, setPackages] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/products/admin/${product.id_producto}/packages`)
      .then((response) => setPackages(response.data))
      .catch((requestError) => {
        setPackages([]);
        setError(getErrorMessage(requestError, 'No fue posible cargar los paquetes del producto.'));
      });
  }, [product.id_producto]);

  const isActive = product.estado === 'activo';

  return (
    <>
      <button type="button" className="btn btn-secondary btn-small user-file-back" onClick={onBack}>
        <Icon name="arrowLeft" size={16} /> Volver a productos
      </button>

      <header className="user-file-header surface">
        <span className="product-file-icon"><Icon name={productTypeIcon(product.tipo_producto)} size={40} /></span>
        <div className="user-file-identity">
          <p className="eyebrow">Producto #{product.id_producto}</p>
          <h1>{product.nombre}</h1>
          <p className="admin-muted">{productTypeLabel(types, product.tipo_producto)} · {cityName(product.ciudad_id)}</p>
          <div className="user-file-badges">
            <span className={`badge badge-${product.estado}`}>{product.estado}</span>
          </div>
        </div>
        <div className="user-file-actions">
          <button type="button" className="btn btn-secondary btn-small" onClick={onEdit}>Editar</button>
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

      <div className="admin-two-columns">
        <section className="surface">
          <h2 className="user-file-title"><Icon name="tag" size={18} /> Detalle</h2>
          <dl className="user-file-fields">
            <Field label="Costo del proveedor">
              {formatCurrency(product.costo)} <span className="admin-muted">{unitShortLabel(product.unidad_cobro)}</span>
            </Field>
            <Field label="Tipo">{productTypeLabel(types, product.tipo_producto)}</Field>
            <Field label="Ciudad">{cityName(product.ciudad_id)}</Field>
            <Field label="Estado">{product.estado}</Field>
          </dl>
          <h2 className="user-file-title user-file-spaced"><Icon name="compass" size={18} /> Descripción</h2>
          <p className="package-file-description">{product.descripcion}</p>
        </section>

        <section className="surface">
          <h2 className="user-file-title"><Icon name="building" size={18} /> Proveedor</h2>
          {provider ? (
            <>
              <dl className="user-file-fields">
                <Field label="Empresa">{provider.nombre_empresa}</Field>
                <Field label="RUT">{provider.rut}</Field>
                <Field label="Teléfono">{provider.telefono}</Field>
                <Field label="Verificación">{provider.estado_verificacion}</Field>
              </dl>
              <button
                type="button"
                className="btn btn-secondary btn-small user-file-spaced"
                onClick={() => goTo('proveedores', { ficha: provider.usuario_id })}
              >
                Ver ficha del proveedor
              </button>
            </>
          ) : (
            <p className="admin-empty">Proveedor no encontrado.</p>
          )}
        </section>
      </div>

      <section className="surface user-file-spaced">
        <h2 className="user-file-title"><Icon name="grid" size={18} /> Paquetes que lo incluyen ({packages?.length ?? 0})</h2>
        {error && <div className="alert alert-error">{error}</div>}
        {packages === null ? (
          <p className="page-status">Cargando...</p>
        ) : packages.length === 0 ? (
          <p className="admin-empty">Ningún paquete lo incluye todavía.</p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Paquete</th>
                  <th>Fechas</th>
                  <th>Cantidad</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {packages.map((item) => (
                  <tr key={item.id_paquete_turistico}>
                    <td>
                      <button
                        type="button"
                        className="link-button admin-strong"
                        onClick={() => goTo('paquetes', { paquete: item.id_paquete_turistico })}
                      >
                        {item.nombre}
                      </button>
                    </td>
                    <td className="admin-muted">{formatDateRange(item.fecha_inicio, item.fecha_fin)}</td>
                    <td>{item.cantidad}</td>
                    <td><span className={`badge badge-${item.estado}`}>{item.estado}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

export default ProductAdminView;
