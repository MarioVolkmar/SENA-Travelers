import { useCallback, useRef, useState } from 'react';

import Modal from '../Modal/Modal';

/**
 * Confirmación con el estilo de la página (en lugar de window.confirm).
 *
 *   const { confirm, dialog } = useConfirm();
 *   if (!(await confirm({ title, message, confirmLabel, tone: 'danger' }))) return;
 *   ...
 *   return <>{...}{dialog}</>;
 */
export default function useConfirm() {
  const [request, setRequest] = useState(null);
  const resolver = useRef(null);

  const confirm = useCallback((options) => new Promise((resolve) => {
    resolver.current = resolve;
    setRequest(options);
  }), []);

  const finish = useCallback((answer) => {
    resolver.current?.(answer);
    resolver.current = null;
    setRequest(null);
  }, []);

  const cancel = useCallback(() => finish(false), [finish]);

  const dialog = request && (
    <Modal
      title={request.title}
      subtitle={request.subtitle}
      size="small"
      onClose={cancel}
      footer={(
        <>
          <button type="button" className="btn btn-secondary" onClick={cancel}>
            Cancelar
          </button>
          <button
            type="button"
            className={`btn ${request.tone === 'danger' ? 'btn-danger-solid' : 'btn-primary'}`}
            onClick={() => finish(true)}
            autoFocus
          >
            {request.confirmLabel || 'Confirmar'}
          </button>
        </>
      )}
    >
      <p className="confirm-message">{request.message}</p>
      {request.details?.length > 0 && (
        <ul className="confirm-details">
          {request.details.map((item) => <li key={item}>{item}</li>)}
        </ul>
      )}
    </Modal>
  );

  return { confirm, dialog };
}
