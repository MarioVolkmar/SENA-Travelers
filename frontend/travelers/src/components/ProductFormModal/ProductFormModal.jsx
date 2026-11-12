import { useState } from 'react';

import api from '../../api/axiosConfig';
import { formatCurrency, getErrorMessage } from '../../utils/format';
import { LIMITS, useLimits } from '../../utils/limits';
import { productTypeIcon, unitShortLabel, useProductUnits } from '../../utils/productTypes';
import Icon from '../Icon/Icon';
import Modal from '../Modal/Modal';
import NumberField, { numberError } from '../NumberField/NumberField';

import './ProductFormModal.css';

import Select from '../Select/Select';
// Usa clases de la consola (admin-*); se importa aquí porque la consola se carga aparte
import '../../pages/Admin/AdminDashboard.css';
/**
 * Crear o editar un producto.
 * - Consola: recibe `providers` y permite elegir (o cambiar) el proveedor.
 * - Panel del proveedor: recibe `fixedProviderId` y el producto siempre es suyo.
 */
function ProductFormModal({ product, cities, types, providers = [], fixedProviderId, onClose, onSaved }) {
  useLimits(); // vuelve a pintar cuando llegan los límites del backend
  const isEdit = Boolean(product);
  const units = useProductUnits();
  const [form, setForm] = useState({
    nombre: product?.nombre || '',
    descripcion: product?.descripcion || '',
    tipo_producto: product?.tipo_producto || '',
    costo: product ? String(Number(product.costo)) : '',
    unidad_cobro: product?.unidad_cobro || 'persona',
    ciudad_id: product ? String(product.ciudad_id) : '',
    proveedor_id: product ? String(product.proveedor_id) : fixedProviderId ? String(fixedProviderId) : '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });
  const selectedType = types.find((type) => type.clave === form.tipo_producto);
  const legacyType = form.tipo_producto && !selectedType;

  const providerOptions = providers.filter(
    (provider) => provider.estado_verificacion === 'aprobado' || String(provider.id_proveedor) === form.proveedor_id
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    if (!selectedType) {
      setError('Elige el tipo de producto.');
      return;
    }

    setSaving(true);

    const data = {
      nombre: form.nombre.trim(),
      descripcion: form.descripcion.trim(),
      tipo_producto: form.tipo_producto,
      costo: form.costo,
      unidad_cobro: form.unidad_cobro,
      ciudad_id: Number(form.ciudad_id),
    };

    try {
      let saved;

      if (isEdit) {
        saved = (await api.patch(`/products/${product.id_producto}`, data)).data;

        if (!fixedProviderId && form.proveedor_id !== String(product.proveedor_id)) {
          saved = (await api.patch(`/products/${product.id_producto}/provider`, {
            proveedor_id: Number(form.proveedor_id),
          })).data;
        }
      } else {
        saved = (await api.post('/products/', { ...data, proveedor_id: Number(form.proveedor_id) })).data;
      }

      onSaved(saved, isEdit);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar el producto.'));
    } finally {
      setSaving(false);
    }
  };

  const costInvalid = Boolean(numberError(form.costo, LIMITS.productCost, { money: true }));

  return (
    <Modal
      title={isEdit ? 'Editar producto' : 'Nuevo producto'}
      subtitle="Un servicio que se puede incluir en los paquetes turísticos."
      size="large"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>Cancelar</button>
          <button type="submit" form="product-form" className="btn btn-primary" disabled={saving || costInvalid}>
            {saving ? 'Guardando...' : isEdit ? 'Guardar cambios' : 'Crear producto'}
          </button>
        </>
      )}
    >
      {error && <div className="alert alert-error">{error}</div>}

      <form id="product-form" className="admin-form-grid" onSubmit={handleSubmit}>
        <fieldset className="field field-full product-types">
          <legend className="field-label">Tipo de producto</legend>
          {legacyType && (
            <p className="field-hint">
              Este producto tiene el tipo antiguo «{form.tipo_producto}». Elige uno del catálogo para guardarlo.
            </p>
          )}
          <div className="product-type-grid">
            {types.map((type) => (
              <label
                key={type.clave}
                className={`product-type-option ${form.tipo_producto === type.clave ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="tipo_producto"
                  value={type.clave}
                  checked={form.tipo_producto === type.clave}
                  onChange={update('tipo_producto')}
                />
                <span className="product-type-icon"><Icon name={productTypeIcon(type.clave)} size={22} /></span>
                <span className="product-type-text">
                  <strong>{type.nombre}</strong>
                  <small>{type.ejemplos}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="field field-full">
          <label htmlFor="prod-name">Nombre</label>
          <input
            id="prod-name"
            value={form.nombre}
            onChange={update('nombre')}
            minLength={2}
            maxLength={100}
            placeholder={selectedType ? `Ej.: ${selectedType.ejemplos.split(',')[0]}` : 'Ej.: Hotel Casa San Agustín'}
            required
          />
        </div>

        <div className="field field-full">
          <label htmlFor="prod-description">Descripción</label>
          <textarea
            id="prod-description"
            value={form.descripcion}
            onChange={update('descripcion')}
            minLength={10}
            placeholder="Qué incluye, horarios, capacidad, condiciones..."
            required
          />
        </div>

        <div className="field">
          <label htmlFor="prod-unit">Cómo cobras</label>
          <Select id="prod-unit" value={form.unidad_cobro} onChange={update('unidad_cobro')}>
            {units.map((unit) => (
              <option key={unit.clave} value={unit.clave}>{unit.nombre}</option>
            ))}
          </Select>
        </div>

        <NumberField
          id="prod-cost"
          label={`Costo (COP) ${unitShortLabel(form.unidad_cobro)}`}
          value={form.costo}
          onChange={update('costo')}
          range={LIMITS.productCost}
          money
          hint={`${form.unidad_cobro === 'servicio'
            ? 'Se paga una vez por reserva, sin importar cuántos viajeros.'
            : 'Se multiplica por los viajeros (y por las noches o días incluidos).'} Entre ${formatCurrency(LIMITS.productCost.min)} y ${formatCurrency(LIMITS.productCost.max)}.`}
        />

        <div className="field">
          <label htmlFor="prod-city">Ciudad donde se presta</label>
          <Select id="prod-city" value={form.ciudad_id} onChange={update('ciudad_id')} required>
            <option value="">Selecciona</option>
            {cities.map((city) => (
              <option key={city.id_ciudad} value={city.id_ciudad}>{city.nombre}</option>
            ))}
          </Select>
        </div>

        {!fixedProviderId && (
          <div className="field field-full">
            <label htmlFor="prod-provider">Proveedor</label>
            <Select id="prod-provider" value={form.proveedor_id} onChange={update('proveedor_id')} required>
              <option value="">Selecciona</option>
              {providerOptions.map((provider) => (
                <option key={provider.id_proveedor} value={provider.id_proveedor}>{provider.nombre_empresa}</option>
              ))}
            </Select>
            {providerOptions.length === 0 && <span className="field-hint">No hay proveedores aprobados todavía.</span>}
          </div>
        )}
      </form>
    </Modal>
  );
}

export default ProductFormModal;
