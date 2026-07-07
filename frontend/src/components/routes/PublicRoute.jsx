import { Navigate, Outlet } from 'react-router-dom';

import Spinner from '../ui/Spinner.jsx';
import { useAuth } from '../../context/AuthContext.jsx';

function PublicRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <Spinner label="Restoring session" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default PublicRoute;
