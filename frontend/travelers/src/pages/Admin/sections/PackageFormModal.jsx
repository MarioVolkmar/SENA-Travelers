import { useEffect, useState } from 'react';

import api from '../../../api/axiosConfig';
import Icon from '../../../components/Icon/Icon';
import Modal from '../../../components/Modal/Modal';
import { formatCurrency, getErrorMessage } from '../../../utils/format';
import { LIMITS, useLimits } from '../../../utils/limits';
import { productTypeLabel, useProductTypes } from '../../../utils/productTypes';
import { matches } from '../adminShared';
import { EMPTY_INCLUDES } from '../../../utils/packageIncludes';
import IncludesPicker from './IncludesPicker';
import NumberField, { numberError } from '../../../components/NumberField/NumberField';

import Select from '../../../components/Select/Select';
import DatePicker from '../../../components/DatePicker/DatePicker';
import { laterKey, todayKey } from '../../../components/DatePicker/calendarUtils';
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
  useLimits(); // vuelve a pintar cuando llegan los límites del backend
  const isEdit = Boolean(packageId);

  const [form, setForm] = useState(EMPTY_FORM);
  const [selected, setSelected] = useState({}); // { producto_id: cantidad }
  const [includes, setIncludes] = useState(EMPTY_INCLUDES);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [providers, setProviders] = useState([]);
  const [providerFilter, setProviderFilter] = useState('');
  const [productQuery, setProductQuery] = useState('');
  const [onlySelected, setOnlySelected] = useState(false);
  const types = useProductTypes();

  useEffect(() => {
    api.get('/providers/')
      .then((response) => setProviders(response.data))
      .catch(() => setProviders([]));
  }, []);

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
        setIncludes({ tipos: data.incluye?.tipos || [], otros: data.incluye?.otros || [] });
      })
      .catch((requestError) => setError(getErrorMessage(requestError, 'No fue posible cargar el paquete.')))
      .finally(() => setLoading(false));
  }, [isEdit, packageId]);

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  // Si la nueva fecha de inicio queda después de la de fin, la de fin se borra para elegirla de nuevo
  const updateStart = (event) => {
    const start = event.target.value;
    setForm((current) => ({
      ...current,
      fecha_inicio: start,
      fecha_fin: current.fecha_fin && current.fecha_fin < start ? '' : current.fecha_fin,
    }));
  };

  const toggleProduct = (id) => {
    setSelected((current) => {
      const next = { ...current };
      if (next[id]) delete next[id];
      else next[id] = 1;
      return next;
    });
  };

  const setQuantity = (id, value) => {
    const { min, max } = LIMITS.packageProductQuantity;
    setSelected((current) => ({ ...current, [id]: Math.min(max, Math.max(min, Number(value) || min)) }));
  };

  // Se muestran los productos activos y, al editar, también los inactivos que ya tenía
  const availableProducts = products.filter(
    (product) => product.estado === 'activo' || selected[product.id_producto]
  );

  const providerName = (id) => providers.find((provider) => provider.id_proveedor === id)?.nombre_empresa || `Proveedor #${id}`;
  const cityName = (id) => cities.find((city) => city.id_ciudad === id)?.nombre || '';

  // Proveedores que tienen productos disponibles, con cuántos tiene cada uno
  const providerOptions = [...new Set(availableProducts.map((product) => product.proveedor_id))]
    .map((id) => ({
      id,
      name: providerName(id),
      count: availableProducts.filter((product) => product.proveedor_id === id).length,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  const shownProducts = availableProducts
    .filter((product) => !providerFilter || product.proveedor_id === Number(providerFilter))
    .filter((product) => !onlySelected || selected[product.id_producto])
    .filter((product) => !productQuery.trim()
      || matches(product.nombre, productQuery)
      || matches(productTypeLabel(types, product.tipo_producto), productQuery)
      || matches(cityName(product.ciudad_id), productQuery));

  const selectedCost = availableProducts
    .filter((product) => selected[product.id_producto])
    .reduce((sum, product) => sum + Number(product.costo) * selected[product.id_producto], 0);

  const finalPrice = Number(form.precio || 0) * (1 - Number(form.descuento || 0) / 100);
  // Algún número fuera de su rango: el botón de guardar queda deshabilitado
  const quantityInvalid = Object.values(selected).some((value) => numberError(value, LIMITS.packageProductQuantity));
  const numbersInvalid = Boolean(
    numberError(form.cupo_max, LIMITS.packageSlots)
    || numberError(form.precio, LIMITS.packagePrice, { money: true })
    || numberError(form.descuento, LIMITS.packageDiscount, { optional: true })
    || quantityInvalid
  );

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
      incluye: includes,
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
          <button type="submit" form="package-form" className="btn btn-primary" disabled={saving || loading || numbersInvalid}>
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
              placeholder="Cuenta de qué se trata el viaje: lugares, experiencias, para quién es..."
            />
          </div>

          <div className="field field-full">
            <span className="field-label">Qué incluye</span>
            <IncludesPicker value={includes} onChange={setIncludes} />
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

          <NumberField
            id="pkg-slots"
            label="Cupo máximo"
            placeholder="Número de personas"
            value={form.cupo_max}
            onChange={update('cupo_max')}
            range={LIMITS.packageSlots}
            unit=" personas"
            hint={`Entre ${LIMITS.packageSlots.min} y ${LIMITS.packageSlots.max} personas.`}
          />

          <div className="field">
            <label htmlFor="pkg-start">Fecha de inicio</label>
            <DatePicker id="pkg-start" value={form.fecha_inicio} onChange={updateStart} min={todayKey()} required />
          </div>

          <div className="field">
            <label htmlFor="pkg-end">Fecha de fin</label>
            <DatePicker
              id="pkg-end"
              min={laterKey(form.fecha_inicio, todayKey())}
              value={form.fecha_fin}
              onChange={update('fecha_fin')}
              required
            />
          </div>

          <NumberField
            id="pkg-price"
            label="Precio por persona (IVA incluido)"
            placeholder="En pesos (COP)"
            value={form.precio}
            onChange={update('precio')}
            range={LIMITS.packagePrice}
            money
            hint={`Entre ${formatCurrency(LIMITS.packagePrice.min)} y ${formatCurrency(LIMITS.packagePrice.max)}.`}
          />

          <NumberField
            id="pkg-discount"
            label="Descuento (%)"
            placeholder="0"
            value={form.descuento}
            onChange={update('descuento')}
            range={LIMITS.packageDiscount}
            optional
            unit=" %"
            hint={Number(form.precio) > 0
              ? `Precio final: ${formatCurrency(finalPrice)} por persona. Entre ${LIMITS.packageDiscount.min} y ${LIMITS.packageDiscount.max} %.`
              : `Entre ${LIMITS.packageDiscount.min} y ${LIMITS.packageDiscount.max} %.`}
          />

          <div className="field field-full">
            <span className="field-label">
              Productos incluidos ({Object.keys(selected).length})
              {selectedCost > 0 && <span className="admin-picker-cost"> · costo {formatCurrency(selectedCost)} por persona</span>}
            </span>
            {availableProducts.length === 0 ? (
              <p className="admin-muted">No hay productos activos. Créalos primero en la sección Productos.</p>
            ) : (
              <>
              <div className="admin-picker-filters">
                <label className="admin-search">
                  <Icon name="search" size={16} />
                  <input
                    type="search"
                    value={productQuery}
                    onChange={(event) => setProductQuery(event.target.value)}
                    placeholder="Buscar producto, tipo o ciudad"
                    aria-label="Buscar productos"
                  />
                </label>
                <Select
                  value={providerFilter}
                  onChange={(event) => setProviderFilter(event.target.value)}
                  className="admin-select"
                  aria-label="Filtrar por proveedor"
                >
                  <option value="">Todos los proveedores ({availableProducts.length})</option>
                  {providerOptions.map((option) => (
                    <option key={option.id} value={option.id}>{option.name} ({option.count})</option>
                  ))}
                </Select>
                <button
                  type="button"
                  className="chip"
                  aria-pressed={onlySelected}
                  onClick={() => setOnlySelected((value) => !value)}
                >
                  Solo elegidos
                </button>
              </div>
              {shownProducts.length === 0 && (
                <p className="admin-muted admin-picker-empty">Ningún producto coincide con esos filtros.</p>
              )}
              <div className="admin-product-picker">
                {shownProducts.map((product) => {
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
                          {productTypeLabel(types, product.tipo_producto)} · {formatCurrency(product.costo)}
                          {product.estado !== 'activo' && ' · inactivo'}
                        </small>
                        <small className="admin-product-provider">
                          {providerName(product.proveedor_id)}{cityName(product.ciudad_id) ? ` · ${cityName(product.ciudad_id)}` : ''}
                        </small>
                      </span>
                      {checked && (
                        <input
                          type="number"
                          min={LIMITS.packageProductQuantity.min}
                          max={LIMITS.packageProductQuantity.max}
                          value={selected[product.id_producto]}
                          aria-invalid={Boolean(numberError(selected[product.id_producto], LIMITS.packageProductQuantity))}
                          title={`Entre ${LIMITS.packageProductQuantity.min} y ${LIMITS.packageProductQuantity.max}`}
                          onChange={(event) => setQuantity(product.id_producto, event.target.value)}
                          onClick={(event) => event.preventDefault()}
                          aria-label={`Cantidad de ${product.nombre}`}
                        />
                      )}
                    </label>
                  );
                })}
              </div>
              </>
            )}
          </div>
        </form>
      )}
    </Modal>
  );
}

export default PackageFormModal;
