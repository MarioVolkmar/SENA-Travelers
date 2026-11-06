import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Icon from '../Icon/Icon';
import './NotificationBell.css';

const REFRESH_MS = 60_000;

const TYPE_ICONS = {
  reserva_creada: 'ticket',
  reserva_confirmada: 'check',
  pago_aprobado: 'card',
  reserva_cancelada: 'close',
  recordatorio_viaje: 'calendar',
  solicitud_proveedor: 'building',
  proveedor_verificado: 'building',
  orden_pago: 'card',
  orden_pagada: 'dollar',
};

function timeAgo(value) {
  if (!value) return '';
  const seconds = Math.max(0, (Date.now() - new Date(value).getTime()) / 1000);
  if (seconds < 60) return 'ahora';
  if (seconds < 3600) return `hace ${Math.floor(seconds / 60)} min`;
  if (seconds < 86400) return `hace ${Math.floor(seconds / 3600)} h`;
  const days = Math.floor(seconds / 86400);
  if (days < 7) return days === 1 ? 'ayer' : `hace ${days} días`;
  return new Date(value).toLocaleDateString('es-CO', { day: 'numeric', month: 'short' });
}

/** Campana de avisos de la barra de navegación. */
function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ no_leidas: 0, notificaciones: [] });
  const wrapperRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const response = await api.get('/notifications/app');
      setData(response.data);
    } catch {
      // Si falla, la campana simplemente no muestra nada nuevo
    }
  }, []);

  useEffect(() => {
    load();
    const timer = window.setInterval(load, REFRESH_MS);
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('focus', onFocus);
    };
  }, [load]);

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (event) => {
      if (!wrapperRef.current?.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const openItem = async (item) => {
    setOpen(false);
    if (!item.leida) {
      setData((current) => ({
        no_leidas: Math.max(0, current.no_leidas - 1),
        notificaciones: current.notificaciones.map((n) => (
          n.id_notificacion === item.id_notificacion ? { ...n, leida: true } : n
        )),
      }));
      api.patch(`/notifications/app/${item.id_notificacion}/read`).catch(() => {});
    }
    if (item.enlace) navigate(item.enlace);
  };

  const markAll = async () => {
    try {
      const response = await api.patch('/notifications/app/read-all');
      setData(response.data);
    } catch {
      // sin cambios
    }
  };

  const count = data.no_leidas;

  return (
    <div className="bell" ref={wrapperRef}>
      <button
        type="button"
        className={`bell-button ${count > 0 ? 'has-unread' : ''}`}
        aria-label={count > 0 ? `Notificaciones: ${count} sin leer` : 'Notificaciones'}
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => {
          setOpen((value) => !value);
          if (!open) load();
        }}
      >
        <Icon name="bell" size={20} />
        {count > 0 && <span className="bell-count" aria-hidden="true">{count > 9 ? '9+' : count}</span>}
      </button>

      {open && (
        <div className="bell-panel" role="dialog" aria-label="Notificaciones">
          <div className="bell-header">
            <p>Notificaciones</p>
            {count > 0 && (
              <button type="button" className="bell-mark-all" onClick={markAll}>
                Marcar todas como leídas
              </button>
            )}
          </div>

          {data.notificaciones.length === 0 ? (
            <div className="bell-empty">
              <Icon name="bell" size={28} />
              <p>No tienes notificaciones todavía.</p>
            </div>
          ) : (
            <ul className="bell-list">
              {data.notificaciones.map((item) => (
                <li key={item.id_notificacion}>
                  <button
                    type="button"
                    className={`bell-item ${item.leida ? '' : 'is-unread'}`}
                    onClick={() => openItem(item)}
                  >
                    <span className="bell-item-icon">
                      <Icon name={TYPE_ICONS[item.tipo] || 'bell'} size={17} />
                    </span>
                    <span className="bell-item-text">
                      <strong>{item.titulo}</strong>
                      <span>{item.mensaje}</span>
                      <small>{timeAgo(item.fecha)}</small>
                    </span>
                    {!item.leida && <span className="bell-dot" aria-label="Sin leer" />}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
