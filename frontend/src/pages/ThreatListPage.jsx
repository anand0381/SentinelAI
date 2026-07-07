import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Edit, Plus, Search, Trash2 } from 'lucide-react';

import {
  THREAT_CATEGORIES,
  THREAT_SEVERITIES,
  THREAT_STATUSES,
  threatService,
} from '../services/threatService.js';

const PAGE_SIZE = 8;

function ThreatListPage() {
  const [threats, setThreats] = useState([]);
  const [meta, setMeta] = useState({ total: 0, page: 1, pages: 0 });
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    severity: '',
    status: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);

  const hasFilters = Boolean(filters.category || filters.severity || filters.status);

  const loadThreats = useCallback(
    async (page = 1) => {
      setLoading(true);
      setError('');

      try {
        let response;
        if (query.trim().length >= 2) {
          response = await threatService.search({
            query: query.trim(),
            page,
            pageSize: PAGE_SIZE,
          });
        } else if (hasFilters) {
          response = await threatService.filter({
            ...filters,
            page,
            pageSize: PAGE_SIZE,
          });
        } else {
          response = await threatService.list({ page, pageSize: PAGE_SIZE });
        }

        setThreats(response.items);
        setMeta({
          total: response.total,
          page: response.page,
          pages: response.pages,
        });
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'Unable to load threats.');
      } finally {
        setLoading(false);
      }
    },
    [filters, hasFilters, query],
  );

  useEffect(() => {
    loadThreats(1);
  }, [loadThreats]);

  const updateFilter = (event) => {
    setFilters((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const confirmDelete = async () => {
    if (!deleteTarget) {
      return;
    }

    try {
      await threatService.remove(deleteTarget.id);
      setDeleteTarget(null);
      loadThreats(meta.page);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to delete threat.');
      setDeleteTarget(null);
    }
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-teal-300">
            Threat Management
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Threats</h1>
        </div>
        <Link
          to="/threats/new"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
        >
          <Plus size={18} aria-hidden="true" />
          New threat
        </Link>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_repeat(3,180px)]">
          <label className="relative block">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
              size={18}
              aria-hidden="true"
            />
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 py-2 pl-10 pr-3 text-sm text-white outline-none focus:border-teal-400"
              placeholder="Search title, description, source"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>

          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
            name="category"
            value={filters.category}
            onChange={updateFilter}
          >
            <option value="">All categories</option>
            {THREAT_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>

          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
            name="severity"
            value={filters.severity}
            onChange={updateFilter}
          >
            <option value="">All severities</option>
            {THREAT_SEVERITIES.map((severity) => (
              <option key={severity} value={severity}>
                {severity}
              </option>
            ))}
          </select>

          <select
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-teal-400"
            name="status"
            value={filters.status}
            onChange={updateFilter}
          >
            <option value="">All statuses</option>
            {THREAT_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800">
            <thead className="bg-slate-950">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Threat
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Severity
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td className="px-4 py-6 text-sm text-slate-300" colSpan="5">
                    Loading threats...
                  </td>
                </tr>
              ) : threats.length ? (
                threats.map((threat) => (
                  <tr key={threat.id}>
                    <td className="px-4 py-4">
                      <p className="font-medium text-white">{threat.title}</p>
                      <p className="mt-1 max-w-xl truncate text-sm text-slate-400">
                        {threat.source} - Confidence {threat.confidence_score}%
                      </p>
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-300">
                      {threat.category}
                    </td>
                    <td className="px-4 py-4 text-sm font-semibold text-slate-100">
                      {threat.severity}
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-300">
                      {threat.status}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex justify-end gap-2">
                        <Link
                          to={`/threats/${threat.id}/edit`}
                          className="rounded-md border border-slate-700 p-2 text-slate-200 hover:border-slate-500 hover:text-white"
                          title="Edit threat"
                        >
                          <Edit size={16} aria-hidden="true" />
                        </Link>
                        <button
                          className="rounded-md border border-red-500/50 p-2 text-red-200 hover:border-red-400 hover:text-red-100"
                          type="button"
                          title="Delete threat"
                          onClick={() => setDeleteTarget(threat)}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-6 text-sm text-slate-300" colSpan="5">
                    No threats found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-slate-400">
          {meta.total} total threat{meta.total === 1 ? '' : 's'}
        </p>
        <div className="flex gap-2">
          <button
            className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            disabled={meta.page <= 1 || loading}
            onClick={() => loadThreats(meta.page - 1)}
          >
            Previous
          </button>
          <span className="rounded-md border border-slate-800 px-3 py-2 text-sm text-slate-300">
            Page {meta.page} of {meta.pages || 1}
          </span>
          <button
            className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
            disabled={meta.page >= meta.pages || loading}
            onClick={() => loadThreats(meta.page + 1)}
          >
            Next
          </button>
        </div>
      </div>

      {deleteTarget ? (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-slate-950/80 px-4">
          <div className="w-full max-w-md rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Delete threat</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Delete "{deleteTarget.title}"? This action cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-slate-500"
                type="button"
                onClick={() => setDeleteTarget(null)}
              >
                Cancel
              </button>
              <button
                className="rounded-md bg-red-500 px-4 py-2 text-sm font-semibold text-white hover:bg-red-400"
                type="button"
                onClick={confirmDelete}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

export default ThreatListPage;
