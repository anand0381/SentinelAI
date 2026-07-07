import { LogOut, Menu, UserCircle } from 'lucide-react';
import { useState } from 'react';

import Button from '../ui/Button.jsx';
import Badge from '../ui/Badge.jsx';
import { useAuth } from '../../context/AuthContext.jsx';

function TopBar({ onMenuClick, title }) {
  const { logout, user } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            className="rounded-md p-2 text-slate-300 hover:bg-slate-800 hover:text-white lg:hidden"
            type="button"
            onClick={onMenuClick}
          >
            <Menu size={22} aria-hidden="true" />
          </button>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Workspace</p>
            <h1 className="text-lg font-semibold text-white">{title}</h1>
          </div>
        </div>

        <div className="relative">
          <button
            className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-left hover:border-cyan-500/60"
            type="button"
            onClick={() => setOpen((current) => !current)}
          >
            <UserCircle className="text-cyan-300" size={22} aria-hidden="true" />
            <span className="hidden sm:block">
              <span className="block text-sm font-medium text-white">
                {user?.full_name || 'User'}
              </span>
              <span className="block text-xs text-slate-500">{user?.email}</span>
            </span>
          </button>

          {open ? (
            <div className="absolute right-0 mt-2 w-64 rounded-lg border border-slate-800 bg-slate-900 p-3 shadow-xl">
              <div className="border-b border-slate-800 pb-3">
                <p className="text-sm font-medium text-white">{user?.full_name}</p>
                <p className="mt-1 text-xs text-slate-400">{user?.email}</p>
                <div className="mt-3">
                  <Badge>{user?.role || 'VIEWER'}</Badge>
                </div>
              </div>
              <Button className="mt-3 w-full" onClick={logout} variant="ghost">
                <LogOut size={16} aria-hidden="true" />
                Logout
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}

export default TopBar;
