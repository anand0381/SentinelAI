import { Outlet } from 'react-router-dom';
import { useState } from 'react';

import Sidebar from '../components/navigation/Sidebar.jsx';
import TopBar from '../components/navigation/TopBar.jsx';

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 lg:grid lg:grid-cols-[288px_1fr]">
      <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="min-w-0">
        <TopBar onMenuClick={() => setSidebarOpen(true)} title="SentinelAI" />
        <main className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900 px-5 py-4">
            <p className="text-xs uppercase tracking-wide text-cyan-300">
              SentinelAI / Console
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-white">
              Cybersecurity Threat Intelligence
            </h2>
          </div>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
