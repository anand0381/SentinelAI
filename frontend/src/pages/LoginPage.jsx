import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';

import Alert from '../components/ui/Alert.jsx';
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import Input from '../components/ui/Input.jsx';
import { useAuth } from '../context/AuthContext.jsx';

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [form, setForm] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [success] = useState(location.state?.message || '');
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

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
      await login(form);
      navigate(from, { replace: true });
    } catch (requestError) {
      setError(requestError.message || 'Unable to sign in with those credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <Card className="p-6">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-500/15 text-teal-300">
            <LogIn size={22} aria-hidden="true" />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-white">Sign in</h1>
            <p className="text-sm text-slate-400">Access SentinelAI</p>
          </div>
        </div>

        {success ? <Alert type="success">{success}</Alert> : null}
        {error ? <Alert type="error">{error}</Alert> : null}

        <form className="mt-4 space-y-4" onSubmit={submit}>
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
            autoComplete="current-password"
            label="Password"
            name="password"
            onChange={updateField}
            required
            type="password"
            value={form.password}
          />

          <Button className="w-full" disabled={loading} type="submit">
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        <p className="mt-4 text-sm text-slate-400">
          Need an account?{' '}
          <Link className="font-medium text-teal-300 hover:text-teal-200" to="/register">
            Register
          </Link>
        </p>
      </Card>
    </section>
  );
}

export default LoginPage;
