import { Activity, ShieldCheck, Siren, Users } from 'lucide-react';

import Card from '../components/ui/Card.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';

const stats = [
  { label: 'Threat Monitoring', value: 'Ready', icon: ShieldCheck },
  { label: 'Incident Queue', value: 'Ready', icon: Siren },
  { label: 'Analyst Workspace', value: 'Ready', icon: Users },
  { label: 'API Connection', value: 'Secured', icon: Activity },
];

function DashboardPage() {
  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.label} className="p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{item.label}</p>
                  <p className="mt-2 text-xl font-semibold text-white">{item.value}</p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-md bg-cyan-400/10 text-cyan-300">
                  <Icon size={22} aria-hidden="true" />
                </span>
              </div>
            </Card>
          );
        })}
      </div>

      <EmptyState
        title="Dashboard analytics will appear here"
        description="Charts and live operational metrics are intentionally reserved for a later sprint."
      />
    </section>
  );
}

export default DashboardPage;
