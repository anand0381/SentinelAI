import { useCallback, useEffect, useMemo, useState } from 'react';
import { Edit3, Plus, Search, Trash2 } from 'lucide-react';

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
  INCIDENT_PRIORITIES,
  INCIDENT_STATUSES,
  incidentService,
} from '../services/incidentService.js';
import { formatDateTime } from '../utils/formatters.js';

const pageSize = 10;

const emptyForm = {
  assigned_to: '',
  description: '',
  priority: 'MEDIUM',
  related_threat_id: '',
  status: 'OPEN',
  title: '',
};

const priorityVariant = {
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

function normalizeIncidentPayload(form) {
  return {
    assigned_to: form.assigned_to.trim() || null,
    description: form.description.trim(),
    priority: form.priority,
    related_threat_id: form.related_threat_id ? Number(form.related_threat_id) : null,
    status: form.status,
    title: form.title.trim(),
  };
}

function getIncidentForm(incident) {
  if (!incident) {
    return emptyForm;
  }

  return {
    assigned_to: incident.assigned_to || '',
    description: incident.description || '',
    priority: incident.priority || 'MEDIUM',
    related_threat_id: incident.related_threat_id || '',
    status: incident.status || 'OPEN',
    title: incident.title || '',
  };
}

function IncidentsPage() {
  const { showToast } = useToast();
  const [confirmTarget, setConfirmTarget] = useState(null);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ priority: '', status: '' });
  const [form, setForm] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [incidents, setIncidents] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState('');
  const [saving, setSaving] = useState(false);
  const [editingIncident, setEditingIncident] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });

  const loadIncidents = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError('');
    try {
      const response = await incidentService.list({ page: nextPage, pageSize });
      setIncidents(response.items || []);
      setPagination({
        page: response.page || nextPage,
        pages: response.pages || 1,
        total: response.total || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load incidents.');
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadIncidents(page);
  }, [loadIncidents, page]);

  const visibleIncidents = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return incidents.filter((incident) => {
      const matchesQuery =
        !normalizedQuery ||
        [incident.title, incident.description, incident.assigned_to]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(normalizedQuery));
      const matchesStatus = !filters.status || incident.status === filters.status;
      const matchesPriority = !filters.priority || incident.priority === filters.priority;
      return matchesQuery && matchesStatus && matchesPriority;
    });
  }, [filters, incidents, query]);

  function openCreateModal() {
    setEditingIncident(null);
    setForm({ ...emptyForm });
    setFormError('');
    setIsModalOpen(true);
  }

  function openEditModal(incident) {
    setEditingIncident(incident);
    setForm(getIncidentForm(incident));
    setFormError('');
    setIsModalOpen(true);
  }

  function closeModal() {
    setEditingIncident(null);
    setFormError('');
    setIsModalOpen(false);
  }

  function handleSearch(event) {
    event.preventDefault();
  }

  function handleClearFilters() {
    setQuery('');
    setFilters({ priority: '', status: '' });
  }

  function validateForm() {
    if (!form.title.trim() || !form.description.trim()) {
      return 'Title and description are required.';
    }

    if (form.title.trim().length < 3) {
      return 'Title must be at least 3 characters.';
    }

    if (form.description.trim().length < 10) {
      return 'Description must be at least 10 characters.';
    }

    if (form.related_threat_id && Number.isNaN(Number(form.related_threat_id))) {
      return 'Related threat ID must be a number.';
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
      const payload = normalizeIncidentPayload(form);
      if (editingIncident) {
        await incidentService.update(editingIncident.id, payload);
        showToast({ message: 'Incident updated successfully.', type: 'success' });
      } else {
        await incidentService.create(payload);
        showToast({ message: 'Incident created successfully.', type: 'success' });
      }
      closeModal();
      await loadIncidents(page);
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Unable to save incident.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirmTarget) {
      return;
    }

    try {
      await incidentService.remove(confirmTarget.id);
      showToast({ message: 'Incident deleted successfully.', type: 'success' });
      setConfirmTarget(null);
      await loadIncidents(page);
    } catch (err) {
      showToast({
        message: err.response?.data?.detail || 'Unable to delete incident.',
        type: 'error',
      });
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Incident Management</h1>
          <p className="mt-1 text-sm text-slate-400">
            Track investigations, assignments, and response status.
          </p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus size={16} aria-hidden="true" />
          Create Incident
        </Button>
      </div>

      <Card className="p-4">
        <form className="grid gap-3 lg:grid-cols-[1fr_repeat(2,minmax(0,11rem))_auto]" onSubmit={handleSearch}>
          <Input
            aria-label="Search incidents"
            className="mt-0"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search title, assignee, or description"
            value={query}
          />
          <select
            aria-label="Filter by status"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}
            value={filters.status}
          >
            <option value="">All statuses</option>
            {INCIDENT_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by priority"
            className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none focus:border-cyan-400"
            onChange={(event) => setFilters((current) => ({ ...current, priority: event.target.value }))}
            value={filters.priority}
          >
            <option value="">All priorities</option>
            {INCIDENT_PRIORITIES.map((priority) => (
              <option key={priority} value={priority}>
                {priority}
              </option>
            ))}
          </select>
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
            <Spinner label="Loading incidents" />
          </div>
        ) : visibleIncidents.length === 0 ? (
          <div className="p-6">
            <EmptyState title="No incidents found" description="Create an incident or adjust the filters." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
              <thead className="bg-slate-950/60 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Incident</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Assigned To</th>
                  <th className="px-4 py-3">Threat ID</th>
                  <th className="px-4 py-3">Updated</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200">
                {visibleIncidents.map((incident) => (
                  <tr className="hover:bg-slate-800/40" key={incident.id}>
                    <td className="max-w-xs px-4 py-4">
                      <p className="font-medium text-white">{incident.title}</p>
                      <p className="mt-1 truncate text-xs text-slate-400">{incident.description}</p>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={incident.status === 'CLOSED' || incident.status === 'RESOLVED' ? 'green' : 'cyan'}>
                        {incident.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={priorityVariant[incident.priority] || 'cyan'}>{incident.priority}</Badge>
                    </td>
                    <td className="px-4 py-4">{incident.assigned_to || 'Unassigned'}</td>
                    <td className="px-4 py-4">{incident.related_threat_id || 'N/A'}</td>
                    <td className="px-4 py-4">{formatDateTime(incident.updated_at)}</td>
                    <td className="px-4 py-4">
                      <div className="flex justify-end gap-2">
                        <Button className="px-3" onClick={() => openEditModal(incident)} variant="secondary">
                          <Edit3 size={15} aria-hidden="true" />
                        </Button>
                        <Button className="px-3" onClick={() => setConfirmTarget(incident)} variant="danger">
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
          Page {pagination.page} of {pagination.pages} | {pagination.total} total incidents
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

      <Modal open={isModalOpen} title={editingIncident ? 'Edit Incident' : 'Create Incident'}>
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
              label="Status"
              onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
              value={form.status}
            >
              {INCIDENT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </SelectField>
            <SelectField
              label="Priority"
              onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}
              value={form.priority}
            >
              {INCIDENT_PRIORITIES.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </SelectField>
            <Input
              label="Assigned To"
              onChange={(event) => setForm((current) => ({ ...current, assigned_to: event.target.value }))}
              placeholder="Analyst name or email"
              value={form.assigned_to}
            />
            <Input
              label="Related Threat ID"
              min="1"
              onChange={(event) => setForm((current) => ({ ...current, related_threat_id: event.target.value }))}
              placeholder="Optional"
              type="number"
              value={form.related_threat_id}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button onClick={closeModal} type="button" variant="secondary">
              Cancel
            </Button>
            <Button disabled={saving} type="submit">
              {saving ? 'Saving...' : 'Save Incident'}
            </Button>
          </div>
        </form>
      </Modal>

      <ConfirmationDialog
        confirmLabel="Delete Incident"
        description={`Delete "${confirmTarget?.title || 'this incident'}"? This action cannot be undone.`}
        onCancel={() => setConfirmTarget(null)}
        onConfirm={handleDelete}
        open={Boolean(confirmTarget)}
        title="Delete incident"
      />
    </section>
  );
}

export default IncidentsPage;
