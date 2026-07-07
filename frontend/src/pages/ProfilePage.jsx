import { useEffect, useState } from 'react';
import { ShieldCheck } from 'lucide-react';

import { useAuth } from '../context/AuthContext.jsx';
import { authService } from '../services/authService.js';

function ProfilePage() {
  const { user, setUser } = useAuth();
  const [loading, setLoading] = useState(!user);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    authService
      .profile()
      .then((profile) => {
        if (active) {
          setUser(profile);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setError('Unable to load profile.');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [setUser]);

  if (loading) {
    return <p className="text-slate-300">Loading profile...</p>;
  }

  if (error) {
    return <p className="text-red-200">{error}</p>;
  }

  return (
    <section className="max-w-2xl">
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
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
            <dd className="mt-1 font-medium text-white">{user.full_name}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-400">Email</dt>
            <dd className="mt-1 font-medium text-white">{user.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-400">Role</dt>
            <dd className="mt-1 font-medium text-white">{user.role}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-400">Status</dt>
            <dd className="mt-1 font-medium text-white">
              {user.is_active ? 'Active' : 'Inactive'}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

export default ProfilePage;
