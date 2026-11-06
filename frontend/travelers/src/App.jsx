import { Routes, Route, useLocation } from 'react-router-dom';

import Navbar from './components/Navbar/Navbar';
import Footer from './components/Footer/Footer';
import ProtectedRoute from './components/ProtectedRoute/ProtectedRoute';

import Home from './pages/Home/Home';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import Packages from './pages/Packages/Packages';
import PackageDetail from './pages/PackageDetail/PackageDetail';
import Reservations from './pages/Reservations/Reservations';
import Profile from './pages/Profile/Profile';
import AdminDashboard from './pages/Admin/AdminDashboard';
import ProviderPanel from './pages/ProviderPanel/ProviderPanel';
import { ROLE_PROVIDER } from './utils/format';
import VerifyEmail from './pages/VerifyEmail/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword/ForgotPassword';
import ResetPassword from './pages/ResetPassword/ResetPassword';
import VerifyVoucher from './pages/VerifyVoucher/VerifyVoucher';

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
      </main>
      {showFooter && <Footer />}
    </div>
  );
}

export default App;
