import { Route, Routes } from 'react-router-dom';

import ProtectedRoute from './components/routes/ProtectedRoute.jsx';
import AppLayout from './layouts/AppLayout.jsx';
import HomePage from './pages/HomePage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import ProfilePage from './pages/ProfilePage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import ThreatFormPage from './pages/ThreatFormPage.jsx';
import ThreatListPage from './pages/ThreatListPage.jsx';

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="profile" element={<ProfilePage />} />
          <Route path="threats" element={<ThreatListPage />} />
          <Route path="threats/new" element={<ThreatFormPage />} />
          <Route path="threats/:id/edit" element={<ThreatFormPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
