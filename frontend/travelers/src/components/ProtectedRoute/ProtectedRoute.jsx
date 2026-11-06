import { Navigate, useLocation } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext';
import { ROLE_ADMIN } from '../../utils/format';

/**
 * Exige sesión iniciada. Con `adminOnly` o `roles` también exige un rol concreto.
 */
function ProtectedRoute({ children, adminOnly = false, roles }) {
  const { isAuthenticated, user, loadingUser } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }

  // Hay token pero todavía no se ha cargado el usuario
  if (loadingUser || !user) {
    return <p className="page-status">Cargando...</p>;
  }

  const allowedRoles = adminOnly ? [ROLE_ADMIN] : roles;

  if (allowedRoles && !allowedRoles.includes(user.rol_id)) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default ProtectedRoute;
