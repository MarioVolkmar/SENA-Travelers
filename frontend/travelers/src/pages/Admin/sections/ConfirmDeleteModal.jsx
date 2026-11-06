import Modal from '../../../components/Modal/Modal';
import { useAdminAction } from '../adminShared';

/**
 * Confirmación para eliminar definitivamente. Si el backend lo impide
 * (409: tiene reservas, productos...), el motivo se muestra aquí mismo.
 */
function ConfirmDeleteModal({ title, name, consequences = [], request, onClose, onDeleted }) {
  const { busy, error, run } = useAdminAction();

  const handleDelete = async () => {
    const { ok } = await run(request, null, 'No fue posible eliminar.');
    if (ok) onDeleted();
  };

  return (
    <Modal
      title={title}
      subtitle={name}
      size="small"
      onClose={onClose}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={busy}>
            {error ? 'Cerrar' : 'Cancelar'}
          </button>
          {!error && (
            <button type="button" className="btn btn-danger-solid" onClick={handleDelete} disabled={busy}>
              {busy ? 'Eliminando...' : 'Eliminar definitivamente'}
            </button>
          )}
        </>
      )}
    >
      {error ? (
        <div className="alert alert-error">{error}</div>
      ) : (
        <>
          <p className="confirm-delete-text">Esta acción no se puede deshacer.</p>
          {consequences.length > 0 && (
            <ul className="confirm-delete-list">
              {consequences.map((item) => <li key={item}>{item}</li>)}
            </ul>
          )}
        </>
      )}
    </Modal>
  );
}

export default ConfirmDeleteModal;
