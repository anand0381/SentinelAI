import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';

import Alert from '../components/ui/Alert.jsx';
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import Input from '../components/ui/Input.jsx';
import { useAuth } from '../context/AuthContext.jsx';

function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
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
      await register(form);
      navigate('/login', {
        replace: true,
        state: { message: 'Account created. You can sign in now.' },
      });
    } catch (requestError) {
      setError(requestError.message || 'Unable to register.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <Card className="p-6">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-500/15 text-teal-300">
            <UserPlus size={22} aria-hidden="true" />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-white">Create account</h1>
            <p className="text-sm text-slate-400">Join the SentinelAI workspace</p>
          </div>
        </div>

        {error ? <Alert type="error">{error}</Alert> : null}

        <form className="mt-4 space-y-4" onSubmit={submit}>
          <Input
            label="Full name"
            minLength={2}
            name="full_name"
            onChange={updateField}
            required
            value={form.full_name}
          />

          <Input
            autoComplete="email"
            label="Email"
            name="email"
            onChange={updateField}
            required
            type="email"
            value={form.email}
          />

          <Input
            autoComplete="new-password"
            label="Password"
            minLength={8}
            name="password"
            onChange={updateField}
            required
            type="password"
            value={form.password}
          />

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

          <Button className="w-full" disabled={loading} type="submit">
            {loading ? 'Creating account...' : 'Create account'}
          </Button>
        </form>

        <p className="mt-4 text-sm text-slate-400">
          Already registered?{' '}
          <Link className="font-medium text-teal-300 hover:text-teal-200" to="/login">
            Sign in
          </Link>
        </p>
      </Card>
    </section>
  );
}

export default RegisterPage;
