import { ShieldCheck } from 'lucide-react';

import Badge from '../components/ui/Badge.jsx';
import Card from '../components/ui/Card.jsx';
import { useAuth } from '../context/AuthContext.jsx';

function ProfilePage() {
  const { user } = useAuth();

  return (
    <section className="max-w-2xl">
      <Card className="p-6">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-500/15 text-teal-300">
            <ShieldCheck size={22} aria-hidden="true" />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-white">User profile</h1>
            <p className="text-sm text-slate-400">Authenticated account details</p>
          </div>
        </div>

        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-slate-400">Full name</dt>
            <dd className="mt-1 font-medium text-white">{user?.full_name || 'User'}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-400">Email</dt>
            <dd className="mt-1 font-medium text-white">{user?.email || 'Unavailable'}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-400">Role</dt>
            <dd className="mt-1">
              <Badge>{user?.role || 'VIEWER'}</Badge>
            </dd>
          </div>
          <div>
            <dt className="text-sm text-slate-400">Status</dt>
            <dd className="mt-1 font-medium text-white">
              {user?.is_active ? 'Active' : 'Inactive'}
            </dd>
          </div>
        </dl>
      </Card>
    </section>
  );
}

export default ProfilePage;
