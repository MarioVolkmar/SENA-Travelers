import { useCallback, useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import { Paged } from '../../../components/Pagination/Pagination';
import useConfirm from '../../../components/ConfirmDialog/useConfirm';
import Toast from '../../../components/Toast/Toast';
import Icon from '../../../components/Icon/Icon';
import IconButton from '../../../components/IconButton/IconButton';
import ProductFormModal from '../../../components/ProductFormModal/ProductFormModal';
import { formatCurrency } from '../../../utils/format';
import { productTypeIcon, productTypeLabel, useProductTypes } from '../../../utils/productTypes';
import { matches, useAdminAction } from '../adminShared';
import ConfirmDeleteModal from './ConfirmDeleteModal';

import Select from '../../../components/Select/Select';
function ProductsSection() {
  const types = useProductTypes();
  const [products, setProducts] = useState(null);
  const [cities, setCities] = useState([]);
  const [providers, setProviders] = useState([]);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [editing, setEditing] = useState(null); // 'new' | producto
  const [deleting, setDeleting] = useState(null);
  const { busy, message, error, run, clear } = useAdminAction();
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    const [productsResponse, citiesResponse, providersResponse] = await Promise.all([
      api.get('/products/admin'),
      api.get('/cities/'),
      api.get('/providers/'),
    ]);

    setProducts([...productsResponse.data].sort((a, b) => a.nombre.localeCompare(b.nombre)));
    setCities(citiesResponse.data);
    setProviders(providersResponse.data);
  }, []);

  useEffect(() => {
    load().catch(() => setProducts([]));
  }, [load]);

  const cityName = (id) => cities.find((city) => city.id_ciudad === id)?.nombre || '';
  const providerName = (id) => providers.find((provider) => provider.id_proveedor === id)?.nombre_empresa || `#${id}`;

  const toggleStatus = async (product) => {
    const estado = product.estado === 'activo' ? 'inactivo' : 'activo';
    const accepted = await confirm({
      title: estado === 'activo' ? 'Activar producto' : 'Desactivar producto',
      subtitle: product.nombre,
      message: estado === 'activo'
        ? 'El producto vuelve a estar disponible para armar paquetes.'
        : 'El producto no se podrá agregar a nuevos paquetes.',
      confirmLabel: estado === 'activo' ? 'Activar' : 'Desactivar',
      tone: estado === 'activo' ? 'primary' : 'danger',
    });
    if (!accepted) return;
    const { ok } = await run(
      () => api.patch(`/products/${product.id_producto}/status`, { estado }),
      `«${product.nombre}» ${estado === 'activo' ? 'activado' : 'desactivado'}.`
    );
    if (ok) await load();
  };

  if (!products) return <p className="page-status">Cargando productos...</p>;

  const visible = products
    .filter((product) => !typeFilter || product.tipo_producto === typeFilter)
    .filter(
      (product) => !query
        || matches(product.nombre, query)
        || matches(providerName(product.proveedor_id), query)
        || matches(cityName(product.ciudad_id), query)
    );

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Productos</h1>
          <p>Servicios de los proveedores (hospedaje, comidas, transporte...) que se combinan en los paquetes.</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={() => { clear(); setEditing('new'); }}>
          + Nuevo producto
        </button>
      </div>

      <Toast text={message} />
      <Toast text={error} tone="error" />

      <div className="surface">
        <div className="admin-toolbar">
          <label className="admin-search">
            <Icon name="search" size={16} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar por nombre, proveedor o ciudad"
              aria-label="Buscar productos"
            />
          </label>
          <label className="admin-search" style={{ maxWidth: 220 }}>
            <Icon name="grid" size={16} />
            <Select
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value)}
              aria-label="Filtrar por tipo"
            >
              <option value="">Todos los tipos</option>
              {types.map((type) => (
                <option key={type.clave} value={type.clave}>{type.nombre}</option>
              ))}
            </Select>
          </label>
        </div>

        <div className="table-wrapper">
          <Paged items={visible} label="productos">{(rows) => (
          <table className="data-table">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Tipo</th>
                <th>Costo</th>
                <th>Proveedor</th>
                <th>Estado</th>
                <th><span className="visually-hidden">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((product) => (
                <tr key={product.id_producto}>
                  <td>
                    <span className="admin-strong">{product.nombre}</span>
                    <br />
                    <span className="admin-muted">{cityName(product.ciudad_id)}</span>
                  </td>
                  <td>
                    <span className="admin-thumb-cell">
                      <Icon name={productTypeIcon(product.tipo_producto)} size={18} />
                      {productTypeLabel(types, product.tipo_producto)}
                    </span>
                  </td>
                  <td className="admin-strong">{formatCurrency(product.costo)}</td>
                  <td>{providerName(product.proveedor_id)}</td>
                  <td><span className={`badge badge-${product.estado}`}>{product.estado}</span></td>
                  <td>
                    <div className="admin-actions">
                      <IconButton icon="edit" label="Editar" onClick={() => { clear(); setEditing(product); }} />
                      <IconButton
                        icon={product.estado === 'activo' ? 'pause' : 'play'}
                        label={product.estado === 'activo' ? 'Desactivar' : 'Activar'}
                        variant={product.estado === 'activo' ? 'warning' : 'success'}
                        disabled={busy}
                        onClick={() => toggleStatus(product)}
                      />
                      <IconButton icon="trash" label="Eliminar" variant="danger" onClick={() => setDeleting(product)} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}</Paged>
          {visible.length === 0 && <p className="admin-empty">No hay productos con esos filtros.</p>}
        </div>
      </div>

      {deleting && (
        <ConfirmDeleteModal
          title="Eliminar producto"
          name={`${deleting.nombre} · ${providerName(deleting.proveedor_id)}`}
          consequences={[
            'Solo se puede si no está incluido en ningún paquete ni en órdenes de pago.',
            'Si está en uso, quítalo del paquete o desactívalo.',
          ]}
          request={() => api.delete(`/products/${deleting.id_producto}`)}
          onClose={() => setDeleting(null)}
          onDeleted={async () => {
            const name = deleting.nombre;
            setDeleting(null);
            await run(() => load(), `«${name}» eliminado.`);
          }}
        />
      )}

      {editing && (
        <ProductFormModal
          product={editing === 'new' ? null : editing}
          cities={cities}
          types={types}
          providers={providers}
          onClose={() => setEditing(null)}
          onSaved={async (saved, wasEdit) => {
            setEditing(null);
            await run(() => load(), `«${saved.nombre}» ${wasEdit ? 'actualizado' : 'creado'}.`);
          }}
        />
      )}
      {dialog}
    </>
  );
}

export default ProductsSection;
