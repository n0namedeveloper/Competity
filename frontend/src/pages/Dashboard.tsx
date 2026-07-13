import { useState, useEffect } from 'react';
import { TargetIcon, ExternalLinkIcon, ExclamationTriangleIcon, LightningBoltIcon, ActivityLogIcon } from '@radix-ui/react-icons';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalCompetitors: 0,
    newLaunches: 0,
    activeAlerts: 0,
  });

  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    setTimeout(() => {
      setStats({
        totalCompetitors: 5,
        newLaunches: 12,
        activeAlerts: 3,
      });
      setChartData([
        { name: 'Acme', activity: 45 },
        { name: 'Globex', activity: 80 },
        { name: 'Soylent', activity: 20 },
        { name: 'Initech', activity: 90 },
        { name: 'Umbrella', activity: 10 },
      ]);
    }, 500);
  }, []);

  return (
    <div>
      <header style={{ marginBottom: '2rem' }}>
        <h1>Overview</h1>
        <p>Real-time competitive landscape and AI-driven insights.</p>
      </header>

      <div className="dashboard-grid">
        <div className="flat-panel stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-info">
              <p>Monitored</p>
              <h3>{stats.totalCompetitors}</h3>
            </div>
            <TargetIcon width={20} height={20} color="var(--text-secondary)" />
          </div>
        </div>
        
        <div className="flat-panel stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-info">
              <p>New Launches</p>
              <h3>{stats.newLaunches}</h3>
            </div>
            <LightningBoltIcon width={20} height={20} color="var(--text-secondary)" />
          </div>
        </div>

        <div className="flat-panel stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div className="stat-info">
              <p>Active Alerts</p>
              <h3>{stats.activeAlerts}</h3>
            </div>
            <ExclamationTriangleIcon width={20} height={20} color="var(--text-secondary)" />
          </div>
        </div>
      </div>

      <div className="flat-panel" style={{ marginTop: '1.5rem', padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.5rem' }}>
          <ActivityLogIcon width={18} height={18} color="var(--text-primary)" />
          <h2 style={{ margin: 0, fontSize: '1rem' }}>Activity Timeline</h2>
        </div>
        
        <div style={{ height: '300px', width: '100%' }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} dy={10} />
              <YAxis stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} axisLine={false} tickLine={false} dx={-10} />
              <Tooltip 
                cursor={{ fill: 'var(--bg-panel-hover)' }}
                contentStyle={{ 
                  background: 'var(--bg-panel)', 
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '12px',
                  boxShadow: 'var(--shadow-apple)',
                  color: 'var(--text-primary)'
                }} 
              />
              <Bar dataKey="activity" fill="var(--accent-primary)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
