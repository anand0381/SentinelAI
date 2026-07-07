import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Save } from 'lucide-react';

import {
  THREAT_CATEGORIES,
  THREAT_SEVERITIES,
  THREAT_STATUSES,
  threatService,
} from '../services/threatService.js';

function createEmptyForm() {
  return {
    title: '',
    description: '',
    category: 'Malware',
    severity: 'LOW',
    source: '',
    status: 'NEW',
    confidence_score: 75,
    detected_at: new Date().toISOString().slice(0, 16),
  };
}

function toDateTimeLocal(value) {
  return new Date(value).toISOString().slice(0, 16);
}

function toApiPayload(form) {
  return {
    ...form,
    confidence_score: Number(form.confidence_score),
    detected_at: new Date(form.detected_at).toISOString(),
  };
}

function ThreatFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);
  const [form, setForm] = useState(() => createEmptyForm());
  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isEditing) {
      return;
    }

    let active = true;
    threatService
      .get(id)
      .then((threat) => {
        if (active) {
          setForm({
            title: threat.title,
            description: threat.description,
            category: threat.category,
            severity: threat.severity,
            source: threat.source,
            status: threat.status,
            confidence_score: threat.confidence_score,
            detected_at: toDateTimeLocal(threat.detected_at),
          });
          setLoading(false);
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(requestError.response?.data?.detail || 'Unable to load threat.');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [id, isEditing]);

  const updateField = (event) => {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSaving(true);

    try {
      if (isEditing) {
        await threatService.update(id, toApiPayload(form));
      } else {
        await threatService.create(toApiPayload(form));
      }
      navigate('/threats', { replace: true });
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || 'Unable to save threat.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="text-slate-300">Loading threat...</p>;
  }

  return (
    <section className="mx-auto max-w-3xl">
      <div className="mb-6">
        <p className="text-sm font-medium uppercase tracking-wide text-teal-300">
          Threat Management
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          {isEditing ? 'Edit threat' : 'Create threat'}
        </h1>
      </div>

      {error ? (
        <div className="mb-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      <form className="rounded-lg border border-slate-800 bg-slate-900 p-6" onSubmit={submit}>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block sm:col-span-2">
            <span className="text-sm font-medium text-slate-200">Title</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="title"
              value={form.title}
              onChange={updateField}
              minLength={3}
              required
            />
          </label>

          <label className="block sm:col-span-2">
            <span className="text-sm font-medium text-slate-200">Description</span>
            <textarea
              className="mt-2 min-h-32 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="description"
              value={form.description}
              onChange={updateField}
              minLength={10}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Category</span>
            <select
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="category"
              value={form.category}
              onChange={updateField}
            >
              {THREAT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Severity</span>
            <select
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="severity"
              value={form.severity}
              onChange={updateField}
            >
              {THREAT_SEVERITIES.map((severity) => (
                <option key={severity} value={severity}>
                  {severity}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Source</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="source"
              value={form.source}
              onChange={updateField}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Status</span>
            <select
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              name="status"
              value={form.status}
              onChange={updateField}
            >
              {THREAT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Confidence score</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              type="number"
              name="confidence_score"
              value={form.confidence_score}
              onChange={updateField}
              min="0"
              max="100"
              step="0.1"
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-200">Detected at</span>
            <input
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
              type="datetime-local"
              name="detected_at"
              value={form.detected_at}
              onChange={updateField}
              required
            />
          </label>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Link
            to="/threats"
            className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500"
          >
            Cancel
          </Link>
          <button
            className="inline-flex items-center gap-2 rounded-md bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-70"
            type="submit"
            disabled={saving}
          >
            <Save size={18} aria-hidden="true" />
            {saving ? 'Saving...' : 'Save threat'}
          </button>
        </div>
      </form>
    </section>
  );
}

export default ThreatFormPage;
