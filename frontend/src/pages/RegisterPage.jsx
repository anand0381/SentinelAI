import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';

import { authService } from '../services/authService.js';

function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'VIEWER',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const updateField = (event) => {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.register(form);
      navigate('/login', { replace: true });
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || 'Unable to register.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="mx-auto max-w-md">
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-500/15 text-teal-300">
            <UserPlus size={22} aria-hidden="true" />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-white">Create account</h1>
            <p className="text-sm text-slate-400">Join the SentinelAI workspace</p>
          </div>
        </div>

        {error ? (
          <div className="mb-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        <form className="space-y-4" onSubmit={submit}>
          <label className="block">
            <span className="text-sm font-medium text-slate-200">Full name</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="full_name"
              value={form.full_name}
              onChange={updateField}
              minLength={2}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Email</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              type="email"
              name="email"
              value={form.email}
              onChange={updateField}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Password</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              type="password"
              name="password"
              value={form.password}
              onChange={updateField}
              minLength={8}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Role</span>
            <select
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="role"
              value={form.role}
              onChange={updateField}
            >
              <option value="VIEWER">Viewer</option>
              <option value="ANALYST">Analyst</option>
            </select>
          </label>

          <button
            className="inline-flex w-full items-center justify-center rounded-md bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-70"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="mt-4 text-sm text-slate-400">
          Already registered?{' '}
          <Link className="font-medium text-teal-300 hover:text-teal-200" to="/login">
            Sign in
          </Link>
        </p>
      </div>
    </section>
  );
}

export default RegisterPage;
