import { ShieldCheck } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { useAuth } from '../../context/AuthContext.jsx';

function TopNav() {
  const { isAuthenticated, clearAuthSession, user } = useAuth();

  return (
    <header className="border-b border-slate-800 bg-slate-950/95">
      <nav className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <NavLink to="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-teal-500/15 text-teal-300">
            <ShieldCheck size={22} aria-hidden="true" />
          </span>
          <span>
            <span className="block text-base font-semibold leading-5">
              SentinelAI
            </span>
            <span className="block text-xs text-slate-400">
              Threat Intelligence Platform
            </span>
          </span>
        </NavLink>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <NavLink
                to="/threats"
                className="text-sm font-medium text-slate-300 hover:text-white"
              >
                Threats
              </NavLink>
              <NavLink
                to="/profile"
                className="text-sm font-medium text-slate-300 hover:text-white"
              >
                {user?.role || 'Profile'}
              </NavLink>
              <button
                className="rounded-md border border-slate-700 px-3 py-2 text-sm font-medium text-slate-200 hover:border-slate-500 hover:text-white"
                type="button"
                onClick={clearAuthSession}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className="text-sm font-medium text-slate-300 hover:text-white"
              >
                Sign in
              </NavLink>
              <NavLink
                to="/register"
                className="rounded-md bg-teal-500 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
              >
                Register
              </NavLink>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}

export default TopNav;
