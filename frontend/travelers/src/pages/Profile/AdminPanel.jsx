import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Avatar from '../../components/Avatar/Avatar';
import Icon from '../../components/Icon/Icon';
// Usa clases de la consola (admin-*); se importa aquí porque la consola se carga aparte
import '../Admin/AdminDashboard.css';

const SHORTCUTS = [
  { section: 'paquetes', extra: '&nuevo=1', icon: 'plus', title: 'Nuevo paquete', text: 'Crea un paquete y súbele fotos' },
  { section: 'paquetes', icon: 'box', title: 'Paquetes', text: 'Edita precios, fechas y productos' },
  { section: 'productos', icon: 'grid', title: 'Productos', text: 'Servicios de los proveedores' },
  { section: 'reservas', icon: 'ticket', title: 'Reservas', text: 'Estados, cancelaciones y penalidades' },
  { section: 'usuarios', icon: 'users', title: 'Usuarios', text: 'Roles, accesos y contraseñas' },
  { section: 'ciudades', icon: 'pin', title: 'Ciudades', text: 'Agrega nuevos destinos' },
];

/**
 * Sección "Administración" del perfil: identidad del administrador,
 * pendientes del día y accesos directos a la consola.
 */
function AdminPanel({ user }) {
  const [pending, setPending] = useState(null);

  useEffect(() => {
    Promise.all([api.get('/reservations/'), api.get('/providers/pending'), api.get('/packages/admin')])
      .then(([reservations, providers, packages]) => {
        setPending({
          reservas: reservations.data.filter((item) => item.estado === 'pendiente').length,
          proveedores: providers.data.length,
          inactivos: packages.data.filter((item) => item.estado !== 'activo').length,
        });
      })
      .catch(() => setPending(null));
  }, []);

  const tasks = pending
    ? [
        { count: pending.proveedores, label: 'proveedores esperan aprobación', section: 'proveedores' },
        { count: pending.reservas, label: 'reservas pendientes de pago', section: 'reservas' },
        { count: pending.inactivos, label: 'paquetes inactivos (no visibles en el catálogo)', section: 'paquetes' },
      ].filter((task) => task.count > 0)
    : [];

  return (
    <>
      <div className="admin-card">
        <Avatar user={user} size={72} />
        <div className="admin-card-text">
          <span className="admin-card-badge">
            <Icon name="check" size={14} strokeWidth={2.4} />
            Administrador
          </span>
          <h2>{user.nombre}</h2>
          <p>Tienes acceso completo a la consola de Travelers.</p>
        </div>
        <Link to="/admin" className="btn btn-primary">
          Abrir consola
          <Icon name="arrowRight" size={18} />
        </Link>
      </div>

      <div className="account-panel admin-tasks">
        <h2>Pendientes</h2>
        {pending === null ? (
          <p className="account-muted">Cargando...</p>
        ) : tasks.length === 0 ? (
          <p className="account-muted">Todo al día: no hay nada pendiente.</p>
        ) : (
          <ul className="account-rows">
            {tasks.map((task) => (
              <li key={task.section} className="account-row">
                <p className="account-row-value admin-task-text">
                  <strong>{task.count}</strong> {task.label}
                </p>
                <Link to={`/admin?seccion=${task.section}`} className="btn btn-secondary btn-small">Revisar</Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <h2 className="admin-shortcuts-title">Accesos directos</h2>
      <div className="admin-shortcuts">
        {SHORTCUTS.map((shortcut) => (
          <Link
            key={shortcut.title}
            to={`/admin?seccion=${shortcut.section}${shortcut.extra || ''}`}
            className="admin-shortcut"
          >
            <span className="admin-shortcut-icon"><Icon name={shortcut.icon} size={22} /></span>
            <span>
              <strong>{shortcut.title}</strong>
              <small>{shortcut.text}</small>
            </span>
          </Link>
        ))}
      </div>
    </>
  );
}

export default AdminPanel;
