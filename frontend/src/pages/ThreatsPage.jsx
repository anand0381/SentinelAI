import { useCallback, useEffect, useState } from 'react';
import { BrainCircuit, Edit3, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';

import Alert from '../components/ui/Alert.jsx';
import Badge from '../components/ui/Badge.jsx';
import Button from '../components/ui/Button.jsx';
import Card from '../components/ui/Card.jsx';
import ConfirmationDialog from '../components/ui/ConfirmationDialog.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import Input from '../components/ui/Input.jsx';
import Modal from '../components/ui/Modal.jsx';
import Spinner from '../components/ui/Spinner.jsx';
import { useToast } from '../hooks/useToast.js';
import {
  THREAT_CATEGORIES,
  THREAT_SEVERITIES,
  THREAT_STATUSES,
  threatService,
} from '../services/threatService.js';
import {
  currentDateTimeLocal,
  formatDateTime,
  toApiDateTime,
  toDateTimeLocal,
} from '../utils/formatters.js';

const pageSize = 10;

const emptyForm = {
  category: 'Malware',
  confidence_score: 75,
  description: '',
  detected_at: '',
  severity: 'LOW',
  source: '',
  status: 'NEW',
  title: '',
};

const badgeVariantBySeverity = {
  CRITICAL: 'red',
  HIGH: 'amber',
  LOW: 'green',
  MEDIUM: 'cyan',
};

function SelectField({ children, label, ...props }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <select
        className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-400"
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

function TextAreaField({ label, ...props }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-200">{label}</span>
      <textarea
        className="mt-2 min-h-28 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400"
        {...props}
      />
    </label>
  );
}

function normalizeThreatPayload(form) {
  return {
    category: form.category,
    confidence_score: Number(form.confidence_score),
    description: form.description.trim(),
    detected_at: toApiDateTime(form.detected_at),
    severity: form.severity,
    source: form.source.trim(),
    status: form.status,
    title: form.title.trim(),
  };
}

function getThreatForm(threat) {
  if (!threat) {
    return emptyForm;
  }

  return {
    category: threat.category || 'Malware',
    confidence_score: threat.confidence_score ?? 75,
    description: threat.description || '',
    detected_at: toDateTimeLocal(threat.detected_at),
    severity: threat.severity || 'LOW',
    source: threat.source || '',
    status: threat.status || 'NEW',
    title: threat.title || '',
  };
}

function getAnalyzeErrorMessage(error) {
  const detail = error.response?.data?.detail;

  if (typeof detail === 'string') {
    if (detail.includes('UNAVAILABLE') || detail.includes('overloaded')) {
      return 'Gemini is temporarily overloaded. Please try Analyze with AI again in a moment.';
    }

    if (detail.includes('rate limit') || detail.includes('429')) {
      return 'Gemini rate limit was reached. Please wait before running another analysis.';
    }

    return detail;
  }

  return 'Unable to analyze threat with AI.';
}

function ThreatsPage() {
  const { showToast } = useToast();
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [confirmTarget, setConfirmTarget] = useState(null);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ category: '', severity: '', source: '', status: '' });
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [intelStatus, setIntelStatus] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [syncingIntel, setSyncingIntel] = useState(false);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState('');
  const [saving, setSaving] = useState(false);
  const [threats, setThreats] = useState([]);
  const [editingThreat, setEditingThreat] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  const loadThreats = useCallback(async (nextPage = page, nextQuery = query, nextFilters = filters) => {
    setLoading(true);
    setError('');
    try {
      const hasActiveFilters = Object.values(nextFilters).some(Boolean);
      let response;
      if (nextQuery.trim()) {
        response = await threatService.search({
          page: nextPage,
          pageSize,
          query: nextQuery.trim(),
        });
      } else if (hasActiveFilters) {
        response = await threatService.filter({
          ...nextFilters,
          page: nextPage,
          pageSize,
        });
      } else {
        response = await threatService.list({ page: nextPage, pageSize });
      }

      setThreats(response.items || []);
      setPagination({
        page: response.page || nextPage,
        pages: response.pages || 1,
        total: response.total || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load threats.');
    } finally {
      setLoading(false);
    }
  }, [filters, page, query]);

  const loadIntelStatus = useCallback(async () => {
    try {
      const status = await threatService.threatIntelligenceStatus();
      setIntelStatus(status);
    } catch (err) {
      showToast({
        message: err.response?.data?.detail || 'Unable to load threat intelligence status.',
        type: 'error',
      });
    }
  }, [showToast]);

  useEffect(() => {
    loadThreats(page);
  }, [loadThreats, page]);

  useEffect(() => {
    loadIntelStatus();
  }, [loadIntelStatus]);

  function openCreateModal() {
    setEditingThreat(null);
    setForm({ ...emptyForm, detected_at: currentDateTimeLocal() });
    setFormError('');
    setIsModalOpen(true);
  }

  function openEditModal(threat) {
    setEditingThreat(threat);
    setForm(getThreatForm(threat));
    setFormError('');
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingThreat(null);
    setFormError('');
  }

  async function handleSearch(event) {
    event.preventDefault();
    setPage(1);
    await loadThreats(1);
  }

  async function handleClearFilters() {
    const clearedFilters = { category: '', severity: '', source: '', status: '' };
    setQuery('');
    setFilters(clearedFilters);
    setPage(1);
    await loadThreats(1, '', clearedFilters);
  }

  function validateForm() {
    if (!form.title.trim() || !form.description.trim() || !form.source.trim()) {
      return 'Title, description, and source are required.';
    }

    if (form.title.trim().length < 3) {
      return 'Title must be at least 3 characters.';
    }

    if (form.description.trim().length < 10) {
      return 'Description must be at least 10 characters.';
    }

    if (form.source.trim().length < 2) {
      return 'Source must be at least 2 characters.';
    }

    if (!form.detected_at) {
      return 'Detected date and time are required.';
    }

    const confidence = Number(form.confidence_score);
    if (Number.isNaN(confidence) || confidence < 0 || confidence > 100) {
      return 'Confidence score must be between 0 and 100.';
    }

    return '';
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const validationError = validateForm();
    if (validationError) {
      setFormError(validationError);
      return;
    }

    setSaving(true);
    setFormError('');
    try {
      const payload = normalizeThreatPayload(form);
      if (editingThreat) {
        await threatService.update(editingThreat.id, payload);
        showToast({ message: 'Threat updated successfully.', type: 'success' });
      } else {
        await threatService.create(payload);
        showToast({ message: 'Threat created successfully.', type: 'success' });
      }
      closeModal();
      await loadThreats(page);
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Unable to save threat.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirmTarget) {
      return;
    }

    try {
      await threatService.remove(confirmTarget.id);
      showToast({ message: 'Threat deleted successfully.', type: 'success' });
      setConfirmTarget(null);
      await loadThreats(page);
    } catch (err) {
      showToast({
        message: err.response?.data?.detail || 'Unable to delete threat.',
        type: 'error',
      });
    }
  }

  async function handleAnalyze(threat) {
    setAnalyzingId(threat.id);
    setAiAnalysis(null);
    try {
      const analysis = await threatService.analyze(threat.id);
      setAiAnalysis({ ...analysis, title: threat.title });
      showToast({ message: 'AI analysis completed successfully.', type: 'success' });
      await loadThreats(page);
    } catch (err) {
      showToast({
        message: getAnalyzeErrorMessage(err),
        type: 'error',
      });
    } finally {
      setAnalyzingId(null);
    }
  }

  async function handleSyncThreatIntelligence() {
    setSyncingIntel(true);
    setSyncResult(null);
    try {
      const result = await threatService.syncThreatIntelligence();
      setSyncResult(result);
      showToast({
        message: `Threat feeds synced: ${result.imported} imported, ${result.updated} updated.`,
        type: 'success',
      });
      await Promise.all([loadThreats(1), loadIntelStatus()]);
      setPage(1);
    } catch (err) {
      showToast({
        message: err.response?.data?.detail || 'Unable to sync threat intelligence feeds.',
        type: 'error',
      });
    } finally {
      setSyncingIntel(false);
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Threat Management</h1>
          <p className="mt-1 text-sm text-slate-400">
            Review, classify, and maintain threat intelligence records.
          </p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus size={16} aria-hidden="true" />
          Create Threat
        </Button>
      </div>

      <Card className="p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-sm font-semibold text-cyan-200">Live Threat Intelligence</p>
            <div className="mt-2 grid gap-2 text-sm text-slate-400 md:grid-cols-3">
              <span>Status: {intelStatus?.last_status || 'NOT_STARTED'}</span>
              <span>Imported: {intelStatus?.imported_total ?? 0}</span>
              <span>Last sync: {formatDateTime(intelStatus?.last_sync_at)}</span>
            </div>
            {syncResult ? (
              <p className="mt-3 text-xs text-slate-500">
                Fetched {syncResult.fetched}, imported {syncResult.imported}, updated {syncResult.updated},
                duplicates {syncResult.skipped_duplicates}, analyzed {syncResult.analyzed}, failed {syncResult.failed}.
              </p>
            ) : null}
          </div>
          <Button disabled={syncingIntel} onClick={handleSyncThreatIntelligence} variant="secondary">
            <RefreshCw className={syncingIntel ? 'animate-spin' : ''} size={16} aria-hidden="true" />
            {syncingIntel ? 'Syncing Feeds' : 'Sync Threat Feed'}
          </Button>
        </div>
      </Card>

      <Card className="p-4">
        <form className="grid gap-3 lg:grid-cols-[1fr_repeat(4,minmax(0,11rem))_auto]" onSubmit={handleSearch}>
          <Input
            aria-label="Search threats"
            className="mt-0"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search title, source, or description"
            value={query}
          />
          <select
            aria-label="Filter by category"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))}
            value={filters.category}
          >
            <option value="">All categories</option>
            {THREAT_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by severity"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value }))}
            value={filters.severity}
          >
            <option value="">All severities</option>
            {THREAT_SEVERITIES.map((severity) => (
              <option key={severity} value={severity}>
                {severity}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by status"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
            value={filters.status}
          >
            <option value="">All statuses</option>
            {THREAT_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <Input
            aria-label="Filter by source"
            className="mt-0"
            onChange={(event) => setFilters((current) => ({ ...current, source: event.target.value }))}
            placeholder="Source"
            value={filters.source}
          />
          <div className="flex gap-2">
            <Button className="px-3" type="submit">
              <Search size={16} aria-hidden="true" />
            </Button>
            <Button className="px-3" onClick={handleClearFilters} variant="secondary">
              Clear
            </Button>
          </div>
        </form>
      </Card>

      {error ? <Alert type="error">{error}</Alert> : null}

      <Card className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <Spinner label="Loading threats" />
          </div>
        ) : threats.length === 0 ? (
          <div className="p-6">
            <EmptyState title="No threats found" description="Create a threat or adjust the search filters." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
              <thead className="bg-slate-950/60 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Threat</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Detected</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200">
                {threats.map((threat) => (
                  <tr className="hover:bg-slate-800/40" key={threat.id}>
                    <td className="max-w-xs px-4 py-4">
                      <p className="font-medium text-white">{threat.title}</p>
                      <p className="mt-1 truncate text-xs text-slate-400">{threat.source}</p>
                    </td>
                    <td className="px-4 py-4">{threat.category}</td>
                    <td className="px-4 py-4">
                      <Badge variant={threat.source_feed ? 'cyan' : 'slate'}>
                        {threat.source_feed || 'Manual'}
                      </Badge>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={badgeVariantBySeverity[threat.severity] || 'cyan'}>
                        {threat.severity}
                      </Badge>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={threat.status === 'CLOSED' ? 'green' : 'cyan'}>{threat.status}</Badge>
                    </td>
                    <td className="px-4 py-4">{threat.confidence_score}%</td>
                    <td className="px-4 py-4">{formatDateTime(threat.detected_at)}</td>
                    <td className="px-4 py-4">
                      <div className="flex justify-end gap-2">
                        <Button className="px-3" onClick={() => openEditModal(threat)} variant="secondary">
                          <Edit3 size={15} aria-hidden="true" />
                        </Button>
                        <Button
                          className="px-3"
                          disabled={analyzingId === threat.id}
                          onClick={() => handleAnalyze(threat)}
                          variant="secondary"
                        >
                          {analyzingId === threat.id ? (
                            <Spinner label="" />
                          ) : (
                            <BrainCircuit size={15} aria-hidden="true" />
                          )}
                        </Button>
                        <Button className="px-3" onClick={() => setConfirmTarget(threat)} variant="danger">
                          <Trash2 size={15} aria-hidden="true" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <div className="flex flex-col gap-3 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
        <span>
          Page {pagination.page} of {pagination.pages} | {pagination.total} total threats
        </span>
        <div className="flex gap-2">
          <Button disabled={page <= 1 || loading} onClick={() => setPage((current) => current - 1)} variant="secondary">
            Previous
          </Button>
          <Button
            disabled={page >= pagination.pages || loading}
            onClick={() => setPage((current) => current + 1)}
            variant="secondary"
          >
            Next
          </Button>
        </div>
      </div>

      <Modal open={isModalOpen} title={editingThreat ? 'Edit Threat' : 'Create Threat'}>
        <form className="space-y-4" onSubmit={handleSubmit}>
          {formError ? <Alert type="error">{formError}</Alert> : null}
          <Input
            label="Title"
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            required
            value={form.title}
          />
          <TextAreaField
            label="Description"
            onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
            required
            value={form.description}
          />
          <div className="grid gap-4 md:grid-cols-2">
            <SelectField
              label="Category"
              onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
              value={form.category}
            >
              {THREAT_CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Severity"
              onChange={(event) => setForm((current) => ({ ...current, severity: event.target.value }))}
              value={form.severity}
            >
              {THREAT_SEVERITIES.map((severity) => (
                <option key={severity} value={severity}>
                  {severity}
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Status"
              onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
              value={form.status}
            >
              {THREAT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </SelectField>
            <Input
              label="Confidence Score"
              max="100"
              min="0"
              onChange={(event) => setForm((current) => ({ ...current, confidence_score: event.target.value }))}
              required
              type="number"
              value={form.confidence_score}
            />
            <Input
              label="Source"
              onChange={(event) => setForm((current) => ({ ...current, source: event.target.value }))}
              required
              value={form.source}
            />
            <Input
              label="Detected At"
              onChange={(event) => setForm((current) => ({ ...current, detected_at: event.target.value }))}
              type="datetime-local"
              value={form.detected_at}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button onClick={closeModal} type="button" variant="secondary">
              Cancel
            </Button>
            <Button disabled={saving} type="submit">
              {saving ? 'Saving...' : 'Save Threat'}
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmationDialog
        confirmLabel="Delete Threat"
        description={`Delete "${confirmTarget?.title || 'this threat'}"? This action cannot be undone.`}
        onCancel={() => setConfirmTarget(null)}
        onConfirm={handleDelete}
        open={Boolean(confirmTarget)}
        title="Delete threat"
      />

      <Modal open={Boolean(aiAnalysis)} title="AI Threat Analysis">
        {aiAnalysis ? (
          <div className="space-y-5">
            <div>
              <p className="text-xs uppercase tracking-wide text-cyan-300">Analyzed Threat</p>
              <h2 className="mt-1 text-lg font-semibold text-white">{aiAnalysis.title}</h2>
              <p className="mt-2 text-sm text-slate-300">{aiAnalysis.ai_summary}</p>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">Risk Score</p>
                <p className="mt-2 text-2xl font-semibold text-red-200">{aiAnalysis.risk_score}%</p>
              </div>
              <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">AI Confidence</p>
                <p className="mt-2 text-2xl font-semibold text-cyan-200">
                  {aiAnalysis.confidence_score}%
                </p>
              </div>
            </div>

            <div className="space-y-3 text-sm text-slate-300">
              <div>
                <p className="font-semibold text-white">Attack Vector</p>
                <p className="mt-1">{aiAnalysis.attack_vector}</p>
              </div>
              <div>
                <p className="font-semibold text-white">Business Impact</p>
                <p className="mt-1">{aiAnalysis.business_impact}</p>
              </div>
              <div>
                <p className="font-semibold text-white">MITRE ATT&CK Mapping</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {aiAnalysis.mitre_attack.map((item) => (
                    <Badge key={item} variant="cyan">
                      {item}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="font-semibold text-white">Recommendations</p>
                <ul className="mt-2 space-y-2">
                  {aiAnalysis.recommendations.map((item) => (
                    <li className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2" key={item}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <p className="text-xs text-slate-500">
                Last analyzed: {formatDateTime(aiAnalysis.last_analyzed)}
              </p>
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setAiAnalysis(null)} variant="secondary">
                Close
              </Button>
            </div>
          </div>
        ) : null}
      </Modal>
    </section>
  );
}

export default ThreatsPage;
