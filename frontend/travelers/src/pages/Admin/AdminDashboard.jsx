import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Avatar from '../../components/Avatar/Avatar';
import Icon from '../../components/Icon/Icon';
import { useAuth } from '../../context/AuthContext';

import SummarySection from './sections/SummarySection';
import ReservationsSection from './sections/ReservationsSection';
import PaymentsSection from './sections/PaymentsSection';
import PackagesSection from './sections/PackagesSection';
import ProductsSection from './sections/ProductsSection';
import ProvidersSection from './sections/ProvidersSection';
import UsersSection from './sections/UsersSection';
import CitiesSection from './sections/CitiesSection';
import ProviderPaymentsSection from './sections/ProviderPaymentsSection';
import SettingsSection from './sections/SettingsSection';
import CouponsSection from './sections/CouponsSection';
import ReviewsAdminSection from './sections/ReviewsAdminSection';
import ReportsSection from './sections/ReportsSection';
import AuditSection from './sections/AuditSection';

import './AdminDashboard.css';

const SECTIONS = [
  { key: 'resumen', label: 'Resumen', icon: 'home', component: SummarySection },
  { key: 'reportes', label: 'Reportes', icon: 'chart', component: ReportsSection },
  { key: 'reservas', label: 'Reservas', icon: 'ticket', component: ReservationsSection, badge: 'reservas' },
  { key: 'pagos', label: 'Pagos', icon: 'card', component: PaymentsSection },
  { key: 'paquetes', label: 'Paquetes', icon: 'box', component: PackagesSection },
  { key: 'productos', label: 'Productos', icon: 'grid', component: ProductsSection },
  { key: 'proveedores', label: 'Proveedores', icon: 'building', component: ProvidersSection, badge: 'proveedores' },
  { key: 'pagos-proveedores', label: 'Pagos a proveedores', icon: 'card', component: ProviderPaymentsSection, badge: 'ordenes' },
  { key: 'cupones', label: 'Cupones', icon: 'tag', component: CouponsSection },
  { key: 'resenas', label: 'Reseñas', icon: 'star', component: ReviewsAdminSection },
  { key: 'usuarios', label: 'Usuarios', icon: 'users', component: UsersSection },
  { key: 'ciudades', label: 'Ciudades', icon: 'pin', component: CitiesSection },
  { key: 'configuracion', label: 'Configuración', icon: 'sparkle', component: SettingsSection },
  { key: 'bitacora', label: 'Bitácora', icon: 'history', component: AuditSection },
];

function AdminDashboard() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [pending, setPending] = useState({ reservas: 0, proveedores: 0, ordenes: 0 });

  const requested = searchParams.get('seccion');
  const active = SECTIONS.find((section) => section.key === requested) || SECTIONS[0];
  const ActiveSection = active.component;

  // Contadores de pendientes para el menú
  const refreshPending = useCallback(async () => {
    try {
      const [reservations, providers, orders] = await Promise.all([
        api.get('/reservations/'),
        api.get('/providers/pending'),
        api.get('/provider-payments/?estado=aprobada'),
      ]);

      setPending({
        reservas: reservations.data.filter((item) => item.estado === 'pendiente').length,
        proveedores: providers.data.length,
        ordenes: orders.data.length, // aprobadas, listas para transferir
      });
    } catch {
      // Los contadores son informativos: si fallan, la consola sigue funcionando
    }
  }, []);

  useEffect(() => {
    refreshPending();
  }, [refreshPending]);

  const goTo = (key, extra = {}) => {
    setSearchParams(key === 'resumen' ? extra : { seccion: key, ...extra });
  };

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-identity">
          <Avatar user={user} size={44} />
          <div>
            <p className="admin-identity-name">{user.nombre}</p>
            <p className="admin-identity-role">Administrador</p>
          </div>
        </div>

        <p className="admin-sidebar-title">Consola</p>
        <nav className="admin-menu" aria-label="Secciones de la consola">
          {SECTIONS.map((section) => {
            const count = section.badge ? pending[section.badge] : 0;

            return (
              <button
                key={section.key}
                type="button"
                aria-current={active.key === section.key ? 'page' : undefined}
                className={`admin-menu-item ${active.key === section.key ? 'active' : ''}`}
                onClick={() => goTo(section.key)}
              >
                <Icon name={section.icon} size={20} />
                <span>{section.label}</span>
                {count > 0 && <span className="admin-menu-badge">{count}</span>}
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="admin-main">
        <ActiveSection
          key={active.key}
          user={user}
          goTo={goTo}
          searchParams={searchParams}
          onDataChanged={refreshPending}
        />
      </section>
    </div>
  );
}

export default AdminDashboard;
