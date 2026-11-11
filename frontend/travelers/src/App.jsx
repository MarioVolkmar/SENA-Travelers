import { lazy, Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';

import Navbar from './components/Navbar/Navbar';
import Footer from './components/Footer/Footer';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';
import { PageSkeleton } from './components/Skeleton/Skeleton';
import WhatsAppButton from './components/WhatsAppButton/WhatsAppButton';
import { ROLE_PROVIDER } from './utils/format';

// El inicio va en el archivo principal (es lo primero que se ve).
// Las demás pantallas se descargan solo cuando se visitan, así la primera carga es más liviana.
import Home from './pages/Home/Home';

const Login = lazy(() => import('./pages/Login/Login'));
const Register = lazy(() => import('./pages/Register/Register'));
const Packages = lazy(() => import('./pages/Packages/Packages'));
const PackageDetail = lazy(() => import('./pages/PackageDetail/PackageDetail'));
const Reservations = lazy(() => import('./pages/Reservations/Reservations'));
const Profile = lazy(() => import('./pages/Profile/Profile'));
const AdminDashboard = lazy(() => import('./pages/Admin/AdminDashboard'));
const ProviderPanel = lazy(() => import('./pages/ProviderPanel/ProviderPanel'));
const VerifyEmail = lazy(() => import('./pages/VerifyEmail/VerifyEmail'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/ResetPassword/ResetPassword'));
const VerifyVoucher = lazy(() => import('./pages/VerifyVoucher/VerifyVoucher'));
const LegalPage = lazy(() => import('./pages/Legal/LegalPage'));

import './App.css';

// Pantallas que ocupan toda la ventana y no llevan pie de página
const NO_FOOTER_PATHS = ['/admin', '/proveedor', '/login', '/register', '/forgot-password', '/reset-password', '/verify-email'];

function App() {
  const location = useLocation();
  const showFooter = !NO_FOOTER_PATHS.includes(location.pathname);

  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Suspense fallback={<PageSkeleton />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/packages" element={<Packages />} />
          <Route path="/packages/:id" element={<PackageDetail />} />
          <Route path="/verificar/:codigo" element={<VerifyVoucher />} />
          <Route path="/terminos" element={<LegalPage doc="terminos" />} />
          <Route path="/privacidad" element={<LegalPage doc="privacidad" />} />
          <Route path="/cancelaciones" element={<LegalPage doc="cancelaciones" />} />
          <Route
            path="/reservations"
            element={<ProtectedRoute><Reservations /></ProtectedRoute>}
          />
          <Route
            path="/profile"
            element={<ProtectedRoute><Profile /></ProtectedRoute>}
          />
          <Route
            path="/admin"
            element={<ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>}
          />
          <Route
            path="/proveedor"
            element={<ProtectedRoute roles={[ROLE_PROVIDER]}><ProviderPanel /></ProtectedRoute>}
          />
          <Route
            path="*"
            element={<p className="page-status">Página no encontrada.</p>}
          />
        </Routes>
        </Suspense>
      </main>
      {showFooter && <Footer />}
      {showFooter && <WhatsAppButton />}
    </div>
  );
}

export default App;
