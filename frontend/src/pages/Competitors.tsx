import { useState, useEffect } from 'react';
import { PlusIcon, TrashIcon, Pencil1Icon, ExternalLinkIcon } from '@radix-ui/react-icons';

interface Competitor {
  id: number;
  name: string;
  domain: string;
  github_org: string;
  keywords: string[];
  is_active: boolean;
}

export default function Competitors() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [formData, setFormData] = useState({ name: '', domain: '', github_org: '', keywords: '' });

  const fetchCompetitors = async () => {
    try {
      const res = await fetch('/api/v1/competitors/');
      if (res.ok) {
        const data = await res.json();
        setCompetitors(data);
      }
    } catch (err) {
      console.error('Failed to fetch competitors', err);
    }
  };

  useEffect(() => {
    fetchCompetitors();
  }, []);

  const handleSave = async () => {
    try {
      const payload = {
        name: formData.name,
        domain: formData.domain || null,
        github_org: formData.github_org || null,
        keywords: formData.keywords ? formData.keywords.split(',').map(k => k.trim()) : []
      };
      const res = await fetch('/api/v1/competitors/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsAdding(false);
        setFormData({ name: '', domain: '', github_org: '', keywords: '' });
        fetchCompetitors();
      }
    } catch (err) {
      console.error('Failed to save', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this?')) return;
    try {
      const res = await fetch(`/api/v1/competitors/${id}`, { method: 'DELETE' });
      if (res.ok) fetchCompetitors();
    } catch (err) {
      console.error('Failed to delete', err);
    }
  };

  return (
    <div>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Competitors</h1>
          <p>Manage your tracked companies.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsAdding(!isAdding)}>
          <PlusIcon width={14} height={14} /> New
        </button>
      </header>

      {isAdding && (
        <div className="flat-panel" style={{ marginBottom: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>New Competitor</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="input-group">
              <label className="input-label">Name</label>
              <input type="text" className="input-field" placeholder="Acme" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
            </div>
            <div className="input-group">
              <label className="input-label">Domain</label>
              <input type="text" className="input-field" placeholder="acme.com" value={formData.domain} onChange={e => setFormData({...formData, domain: e.target.value})} />
            </div>
            <div className="input-group">
              <label className="input-label">GitHub</label>
              <input type="text" className="input-field" placeholder="acme-corp" value={formData.github_org} onChange={e => setFormData({...formData, github_org: e.target.value})} />
            </div>
            <div className="input-group">
              <label className="input-label">Keywords</label>
              <input type="text" className="input-field" placeholder="acme, acmecorp" value={formData.keywords} onChange={e => setFormData({...formData, keywords: e.target.value})} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '1rem' }}>
            <button className="btn btn-primary" onClick={handleSave} disabled={!formData.name}>Save</button>
            <button className="btn btn-secondary" onClick={() => setIsAdding(false)}>Cancel</button>
          </div>
        </div>
      )}

      <div className="list-container">
        {competitors.length === 0 && !isAdding && (
          <div style={{ textAlign: 'center', padding: '3rem 2rem', color: 'var(--text-secondary)' }}>
            <p>No competitors added yet.</p>
          </div>
        )}
        
        {competitors.map((comp) => (
          <div key={comp.id} className="list-item">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                <h3 style={{ margin: 0 }}>{comp.name}</h3>
                <span className={`badge ${comp.is_active ? 'badge-active' : 'badge-inactive'}`}>
                  {comp.is_active ? 'Active' : 'Paused'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: '16px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {comp.domain && (
                  <a href={`https://${comp.domain}`} target="_blank" rel="noreferrer" style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ExternalLinkIcon width={12} height={12} /> {comp.domain}
                  </a>
                )}
                {comp.github_org && (
                  <span>GH: {comp.github_org}</span>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-secondary" style={{ padding: '6px' }}>
                <Pencil1Icon width={14} height={14} />
              </button>
              <button className="btn btn-danger" style={{ padding: '6px' }} onClick={() => handleDelete(comp.id)}>
                <TrashIcon width={14} height={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
