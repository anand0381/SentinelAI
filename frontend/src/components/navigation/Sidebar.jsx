import {
  BarChart3,
  Bug,
  LayoutDashboard,
  Settings,
  ShieldAlert,
  UserCircle,
  X,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Threats', to: '/threats', icon: Bug },
  { label: 'Incidents', to: '/incidents', icon: ShieldAlert },
  { label: 'Analytics', to: '/dashboard', icon: BarChart3 },
  { label: 'Profile', to: '/profile', icon: UserCircle },
  { label: 'Settings', to: '/settings', icon: Settings },
];

function Sidebar({ mobileOpen, onClose }) {
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-slate-950/70 lg:hidden ${
          mobileOpen ? 'block' : 'hidden'
        }`}
        onClick={onClose}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 border-r border-slate-800 bg-slate-950 transition-transform lg:static lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-5">
          <div>
            <p className="text-lg font-semibold text-white">SentinelAI</p>
            <p className="text-xs text-slate-500">Cyber Defense Console</p>
          </div>
          <button
            className="rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
            type="button"
            onClick={onClose}
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <nav className="space-y-1 px-3 py-5">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.label}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ${
                    isActive
                      ? 'bg-cyan-400/10 text-cyan-200'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-white'
                  }`
                }
              >
                <Icon size={18} aria-hidden="true" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
    </>
  );
}

export default Sidebar;
