import { Routes, Route } from 'react-router-dom';

import Navbar from './components/Navbar/Navbar';

import Home from './pages/Home/Home';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import Packages from './pages/Packages/Packages';
import Reservations from './pages/Reservations/Reservations';
import Profile from './pages/Profile/Profile';
import AdminDashboard from './pages/Admin/AdminDashboard';
import VerifyEmail from './pages/VerifyEmail/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword/ForgotPassword';
import ResetPassword from './pages/ResetPassword/ResetPassword';

import './App.css';

function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/packages" element={<Packages />} />
          <Route path="/reservations" element={<Reservations />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;