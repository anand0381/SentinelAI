import { useEffect, useMemo, useState } from 'react';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import { Activity, AlertTriangle, ShieldAlert, Siren, TrendingUp } from 'lucide-react';

import Alert from '../components/ui/Alert.jsx';
import Card from '../components/ui/Card.jsx';
import EmptyState from '../components/ui/EmptyState.jsx';
import Spinner from '../components/ui/Spinner.jsx';
import { dashboardService } from '../services/dashboardService.js';

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
);

const palette = ['#22d3ee', '#38bdf8', '#f59e0b', '#ef4444', '#a78bfa', '#34d399', '#f472b6'];

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#cbd5e1',
        boxWidth: 12,
      },
    },
  },
  scales: {
    x: {
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(148, 163, 184, 0.12)' },
    },
    y: {
      beginAtZero: true,
      ticks: { color: '#94a3b8', precision: 0 },
      grid: { color: 'rgba(148, 163, 184, 0.12)' },
    },
  },
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#cbd5e1',
        boxWidth: 12,
      },
    },
  },
};

function withColors(chartData) {
  return {
    labels: chartData?.labels || [],
    datasets: (chartData?.datasets || []).map((dataset) => ({
      ...dataset,
      backgroundColor: palette,
      borderColor: palette,
      borderWidth: 1,
    })),
  };
}

function withLineColors(chartData) {
  return {
    labels: chartData?.labels || [],
    datasets: (chartData?.datasets || []).map((dataset, index) => ({
      ...dataset,
      backgroundColor: index === 0 ? 'rgba(34, 211, 238, 0.14)' : 'rgba(245, 158, 11, 0.14)',
      borderColor: index === 0 ? '#22d3ee' : '#f59e0b',
      borderWidth: 2,
      tension: 0.35,
    })),
  };
}

function hasChartData(chartData) {
  return (chartData?.datasets || []).some((dataset) =>
    (dataset.data || []).some((value) => Number(value) > 0),
  );
}

function ChartPanel({ children, title }) {
  return (
    <Card className="p-5">
      <h2 className="text-base font-semibold text-white">{title}</h2>
      <div className="mt-4 h-72">{children}</div>
    </Card>
  );
}

function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    async function loadDashboard() {
      setLoading(true);
      setError('');
      try {
        const response = await dashboardService.overview();
        if (!ignore) {
          setData(response);
        }
      } catch (err) {
        if (!ignore) {
          setError(err.response?.data?.detail || 'Unable to load dashboard analytics.');
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      ignore = true;
    };
  }, []);

  const kpis = useMemo(
    () => [
      {
        icon: ShieldAlert,
        label: 'Total Threats',
        value: data?.summary?.total_threats ?? 0,
      },
      {
        icon: Siren,
        label: 'Total Incidents',
        value: data?.summary?.total_incidents ?? 0,
      },
      {
        icon: AlertTriangle,
        label: 'Critical Threats',
        value: data?.summary?.critical_threats ?? 0,
      },
      {
        icon: TrendingUp,
        label: 'Open Incidents',
        value: data?.summary?.open_incidents ?? 0,
      },
      {
        icon: Activity,
        label: 'High Priority Incidents',
        value: data?.summary?.high_priority_incidents ?? 0,
      },
    ],
    [data],
  );

  if (loading) {
    return (
      <Card className="p-6">
        <Spinner label="Loading dashboard analytics" />
      </Card>
    );
  }

  if (error) {
    return <Alert type="error">{error}</Alert>;
  }

  return (
    <section className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {kpis.map((item) => {
          const Icon = item.icon;
          return (
            <Card className="p-5" key={item.label}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-400">{item.label}</p>
                  <p className="mt-2 text-2xl font-semibold text-white">{item.value}</p>
                </div>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-cyan-400/10 text-cyan-300">
                  <Icon size={22} aria-hidden="true" />
                </span>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <ChartPanel title="Threat Severity">
          {hasChartData(data?.threatSeverity) ? (
            <Bar data={withColors(data.threatSeverity)} options={chartOptions} />
          ) : (
            <EmptyState title="No severity data" description="Threat severity metrics will appear here." />
          )}
        </ChartPanel>

        <ChartPanel title="Threat Categories">
          {hasChartData(data?.threatCategory) ? (
            <Doughnut data={withColors(data.threatCategory)} options={doughnutOptions} />
          ) : (
            <EmptyState title="No category data" description="Threat category metrics will appear here." />
          )}
        </ChartPanel>

        <ChartPanel title="Incident Status">
          {hasChartData(data?.incidentStatus) ? (
            <Doughnut data={withColors(data.incidentStatus)} options={doughnutOptions} />
          ) : (
            <EmptyState title="No incident data" description="Incident status metrics will appear here." />
          )}
        </ChartPanel>

        <ChartPanel title="Threat Timeline">
          {hasChartData(data?.monthlyTrends) ? (
            <Line data={withLineColors(data.monthlyTrends)} options={chartOptions} />
          ) : (
            <EmptyState title="No trend data" description="Monthly threat and incident trends will appear here." />
          )}
        </ChartPanel>
      </div>
    </section>
  );
}

export default DashboardPage;
