import { useCallback, useEffect, useRef, useState } from 'react';

import api from '../../../api/axiosConfig';
import Icon from '../../../components/Icon/Icon';
import Modal from '../../../components/Modal/Modal';
import { getErrorMessage } from '../../../utils/format';
import { ACCEPTED_IMAGE_TYPES, resizeToJpeg } from '../../../utils/image';

/**
 * Galería de un paquete: subir fotos a S3, elegir portada y quitar fotos.
 */
function PackageImagesModal({ touristPackage, onClose, onChanged }) {
  const packageId = touristPackage.id_paquete_turistico;
  const inputRef = useRef(null);

  const [images, setImages] = useState(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState('');
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);

  const load = useCallback(async () => {
    try {
      const response = await api.get(`/packages/${packageId}/images`);
      setImages(response.data);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible cargar las imágenes.'));
      setImages([]);
    }
  }, [packageId]);

  useEffect(() => {
    load();
  }, [load]);

  const uploadFiles = async (fileList) => {
    const files = [...fileList];
    if (files.length === 0) return;

    setBusy(true);
    setError('');

    let hasCover = images.some((image) => image.es_portada);
    let order = images.length;

    try {
      for (const [index, file] of files.entries()) {
        setProgress(`Subiendo ${index + 1} de ${files.length}...`);

        const blob = await resizeToJpeg(file);
        const formData = new FormData();
        formData.append('file', blob, 'foto.jpg');
        formData.append('es_portada', String(!hasCover));
        formData.append('orden', String(order));

        await api.post(`/packages/${packageId}/images/upload`, formData);

        hasCover = true;
        order += 1;
      }
    } catch (uploadError) {
      setError(uploadError.response ? getErrorMessage(uploadError, 'No fue posible subir la imagen.') : uploadError.message);
    } finally {
      setProgress('');
      setBusy(false);
      await load();
      onChanged();
    }
  };

  const runAction = async (request, fallback) => {
    setBusy(true);
    setError('');

    try {
      await request();
      await load();
      onChanged();
    } catch (requestError) {
      setError(getErrorMessage(requestError, fallback));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      title="Fotos del paquete"
      subtitle={touristPackage.nombre}
      size="large"
      onClose={onClose}
      footer={<button type="button" className="btn btn-primary" onClick={onClose}>Listo</button>}
    >
      {error && <div className="alert alert-error">{error}</div>}

      <button
        type="button"
        className={`admin-dropzone ${dragging ? 'dragging' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          if (!busy) uploadFiles(event.dataTransfer.files);
        }}
        disabled={busy}
        style={{ width: '100%', font: 'inherit' }}
      >
        <Icon name="image" size={28} />
        <strong>{progress || 'Arrastra fotos aquí o haz clic para elegirlas'}</strong>
        <span>JPG, PNG o WEBP · se reducen a 1600 px y se guardan en S3</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_IMAGE_TYPES.join(',')}
        multiple
        className="visually-hidden"
        tabIndex={-1}
        onChange={(event) => {
          uploadFiles(event.target.files);
          event.target.value = '';
        }}
      />

      {images === null ? (
        <p className="admin-muted">Cargando...</p>
      ) : images.length === 0 ? (
        <p className="admin-empty">Este paquete todavía no tiene fotos. La primera que subas será la portada.</p>
      ) : (
        <div className="admin-images-grid">
          {images.map((image) => (
            <figure key={image.id_imagen} className={`admin-image ${image.es_portada ? 'cover' : ''}`}>
              {image.imagen_url ? (
                <img src={image.imagen_url} alt="" loading="lazy" />
              ) : (
                <div className="admin-image-missing">Sin CLOUDFRONT_URL</div>
              )}
              <figcaption>
                {image.es_portada ? (
                  <span className="badge badge-activo">Portada</span>
                ) : (
                  <button
                    type="button"
                    className="btn btn-secondary btn-small"
                    disabled={busy}
                    onClick={() => runAction(
                      () => api.patch(`/packages/${packageId}/images/${image.id_imagen}/cover`),
                      'No fue posible cambiar la portada.'
                    )}
                  >
                    Usar de portada
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-danger btn-small"
                  disabled={busy}
                  aria-label="Quitar foto"
                  onClick={() => {
                    if (window.confirm('¿Quitar esta foto del paquete?')) {
                      runAction(
                        () => api.delete(`/packages/${packageId}/images/${image.id_imagen}`),
                        'No fue posible quitar la foto.'
                      );
                    }
                  }}
                >
                  Quitar
                </button>
              </figcaption>
            </figure>
          ))}
        </div>
      )}
    </Modal>
  );
}

export default PackageImagesModal;
