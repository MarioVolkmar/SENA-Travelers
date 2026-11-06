import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import Modal from '../../../components/Modal/Modal';
import { formatCurrency, getErrorMessage } from '../../../utils/format';

import Select from '../../../components/Select/Select';
import DatePicker from '../../../components/DatePicker/DatePicker';
const EMPTY_FORM = {
  nombre: '',
  descripcion: '',
  precio: '',
  descuento: '0',
  fecha_inicio: '',
  fecha_fin: '',
  cupo_max: '',
  ciudad_id: '',
};

/**
 * Crear (packageId = null) o editar un paquete turístico con sus productos.
 */
function PackageFormModal({ packageId, cities, products, onClose, onSaved }) {
  const isEdit = Boolean(packageId);

  const [form, setForm] = useState(EMPTY_FORM);
  const [selected, setSelected] = useState({}); // { producto_id: cantidad }
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isEdit) return;

    api.get(`/packages/admin/${packageId}`)
      .then(({ data }) => {
        setForm({
          nombre: data.nombre,
          descripcion: data.descripcion,
          precio: String(Number(data.precio)),
          descuento: String(data.descuento),
          fecha_inicio: data.fecha_inicio,
          fecha_fin: data.fecha_fin,
          cupo_max: String(data.cupo_max),
          ciudad_id: String(data.ciudad_id),
        });
        setSelected(Object.fromEntries(data.productos.map((item) => [item.producto_id, item.cantidad])));
      })
      .catch((requestError) => setError(getErrorMessage(requestError, 'No fue posible cargar el paquete.')))
      .finally(() => setLoading(false));
  }, [isEdit, packageId]);

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  const toggleProduct = (id) => {
    setSelected((current) => {
      const next = { ...current };
      if (next[id]) delete next[id];
      else next[id] = 1;
      return next;
    });
  };

  const setQuantity = (id, value) => {
    setSelected((current) => ({ ...current, [id]: Math.max(1, Number(value) || 1) }));
  };

  // Se muestran los productos activos y, al editar, también los inactivos que ya tenía
  const availableProducts = products.filter(
    (product) => product.estado === 'activo' || selected[product.id_producto]
  );

  const finalPrice = Number(form.precio || 0) * (1 - Number(form.descuento || 0) / 100);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (form.fecha_fin < form.fecha_inicio) {
      setError('La fecha de fin no puede ser anterior a la de inicio.');
      return;
    }

    const productos = Object.entries(selected).map(([producto_id, cantidad]) => ({
      producto_id: Number(producto_id),
      cantidad,
    }));

    if (productos.length === 0) {
      setError('Elige al menos un producto incluido en el paquete.');
      return;
    }

    const payload = {
      nombre: form.nombre.trim(),
      descripcion: form.descripcion.trim(),
      precio: form.precio,
      descuento: Number(form.descuento || 0),
      fecha_inicio: form.fecha_inicio,
      fecha_fin: form.fecha_fin,
      cupo_max: Number(form.cupo_max),
      ciudad_id: Number(form.ciudad_id),
      productos,
    };

    setSaving(true);

    try {
      const response = isEdit
        ? await api.patch(`/packages/${packageId}`, payload)
        : await api.post('/packages/', payload);

      onSaved(response.data, isEdit);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar el paquete.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Editar paquete' : 'Nuevo paquete'}
      subtitle={isEdit ? form.nombre : 'Los paquetes nuevos quedan activos y visibles en el catálogo.'}
      size="large"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button type="submit" form="package-form" className="btn btn-primary" disabled={saving || loading}>
            {saving ? 'Guardando...' : isEdit ? 'Guardar cambios' : 'Crear paquete'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="admin-muted">Cargando...</p>
      ) : (
        <form id="package-form" className="admin-form-grid" onSubmit={handleSubmit}>
          <div className="field field-full">
            <label htmlFor="pkg-name">Nombre</label>
            <input id="pkg-name" value={form.nombre} onChange={update('nombre')} minLength={2} maxLength={100} required />
          </div>

          <div className="field field-full">
            <label htmlFor="pkg-description">Descripción</label>
            <textarea
              id="pkg-description"
              value={form.descripcion}
              onChange={update('descripcion')}
              minLength={10}
              required
              placeholder="Escribe «Incluye alojamiento, desayunos y ...» para que se muestre la lista de lo incluido."
            />
          </div>

          <div className="field">
            <label htmlFor="pkg-city">Destino</label>
            <Select id="pkg-city" value={form.ciudad_id} onChange={update('ciudad_id')} required>
              <option value="">Selecciona</option>
              {cities.map((city) => (
                <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}, {city.departamento}</option>
              ))}
            </Select>
          </div>

          <div className="field">
            <label htmlFor="pkg-slots">Cupo máximo (personas)</label>
            <input id="pkg-slots" type="number" min="1" value={form.cupo_max} onChange={update('cupo_max')} required />
          </div>

          <div className="field">
            <label htmlFor="pkg-start">Fecha de inicio</label>
            <DatePicker id="pkg-start" value={form.fecha_inicio} onChange={update('fecha_inicio')} required />
          </div>

          <div className="field">
            <label htmlFor="pkg-end">Fecha de fin</label>
            <DatePicker
              id="pkg-end"
              min={form.fecha_inicio || undefined}
              value={form.fecha_fin}
              onChange={update('fecha_fin')}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="pkg-price">Precio por persona (COP)</label>
            <input id="pkg-price" type="number" min="1" step="1000" value={form.precio} onChange={update('precio')} required />
          </div>

          <div className="field">
            <label htmlFor="pkg-discount">Descuento (%)</label>
            <input id="pkg-discount" type="number" min="0" max="90" value={form.descuento} onChange={update('descuento')} />
            {Number(form.precio) > 0 && (
              <span className="field-hint">Precio final: {formatCurrency(finalPrice)} por persona</span>
            )}
          </div>

          <div className="field field-full">
            <span className="field-label">Productos incluidos ({Object.keys(selected).length})</span>
            {availableProducts.length === 0 ? (
              <p className="admin-muted">No hay productos activos. Créalos primero en la sección Productos.</p>
            ) : (
              <div className="admin-product-picker">
                {availableProducts.map((product) => {
                  const checked = Boolean(selected[product.id_producto]);

                  return (
                    <label
                      key={product.id_producto}
                      className={`admin-product-option ${checked ? 'selected' : ''}`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleProduct(product.id_producto)}
                      />
                      <span>
                        {product.nombre}
                        <small>
                          {product.tipo_producto} · {formatCurrency(product.costo)}
                          {product.estado !== 'activo' && ' · inactivo'}
                        </small>
                      </span>
                      {checked && (
                        <input
                          type="number"
                          min="1"
                          value={selected[product.id_producto]}
                          onChange={(event) => setQuantity(product.id_producto, event.target.value)}
                          onClick={(event) => event.preventDefault()}
                          aria-label={`Cantidad de ${product.nombre}`}
                        />
                      )}
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </form>
      )}
    </Modal>
  );
}

export default PackageFormModal;
