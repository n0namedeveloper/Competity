import { useState, useEffect } from 'react';
import { DownloadIcon, CalendarIcon, ArrowRightIcon, LoopIcon, UpdateIcon, TrashIcon } from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';

interface Report {
  id: number;
  period_start: string;
  period_end: string;
  content_markdown: string;
  content_json: any;
  status: string;
}

export default function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const fetchReports = async () => {
    try {
      const res = await fetch('/api/v1/reports/');
      if (res.ok) {
        const data = await res.json();
        setReports(data);
        // Clear selection if some selected items were removed or on refresh
        setSelectedIds(new Set());
      }
    } catch (err) {
      console.error('Failed to fetch reports', err);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch('/api/v1/reports/generate', { method: 'POST' });
      if (res.ok) {
        alert('Report generation started in the background. It may take a few minutes.');
      } else {
        alert('Failed to start generation.');
      }
    } catch (err) {
      console.error('Failed to generate report', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.size} report(s)?`)) return;

    setIsDeleting(true);
    try {
      const res = await fetch('/api/v1/reports/', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_ids: Array.from(selectedIds) })
      });
      if (res.ok) {
        await fetchReports();
      } else {
        alert('Failed to delete reports.');
      }
    } catch (err) {
      console.error('Failed to delete reports', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const toggleSelection = (id: number) => {
    const newSelection = new Set(selectedIds);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedIds(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === reports.length && reports.length > 0) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(reports.map(r => r.id)));
    }
  };

  return (
    <div>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Reports</h1>
          <p>Weekly summaries and insights.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" onClick={fetchReports} title="Refresh reports">
            <UpdateIcon width={14} height={14} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? <LoopIcon className="animate-spin" width={14} height={14} /> : null}
            {isGenerating ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </header>

      <div className="list-container">
        {/* Bulk Action Toolbar */}
        {reports.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', padding: '16px 24px', background: 'var(--bg-panel-hover)', borderBottom: '1px solid var(--border-strong)' }}>
            <input 
              type="checkbox" 
              checked={selectedIds.size === reports.length && reports.length > 0}
              onChange={toggleSelectAll}
              style={{ marginRight: '16px', cursor: 'pointer', transform: 'scale(1.2)' }}
            />
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 500, flex: 1 }}>
              {selectedIds.size > 0 ? `${selectedIds.size} selected` : 'Select All'}
            </span>
            {selectedIds.size > 0 && (
              <button 
                className="btn btn-danger" 
                onClick={handleDeleteSelected} 
                disabled={isDeleting}
                style={{ padding: '6px 12px', fontSize: '0.85rem' }}
              >
                <TrashIcon width={14} height={14} />
                {isDeleting ? 'Deleting...' : 'Delete Selected'}
              </button>
            )}
          </div>
        )}

        {reports.length === 0 && (
          <div style={{ textAlign: 'center', padding: '3rem 2rem', color: 'var(--text-secondary)' }}>
            <p>No reports generated yet. Click "Generate" to create your first report.</p>
          </div>
        )}
        
        {reports.map((report) => {
          const summary = report.content_json?.executive_summary || 'Report content ready.';
          const isExpanded = expandedId === report.id;
          const isSelected = selectedIds.has(report.id);

          return (
            <div key={report.id} style={{ display: 'flex', flexDirection: 'column', borderBottom: '1px solid var(--border-subtle)', background: isSelected ? 'rgba(0, 113, 227, 0.03)' : 'transparent' }}>
              <div className="list-item" style={{ borderBottom: 'none', background: 'transparent' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                  <input 
                    type="checkbox" 
                    checked={isSelected}
                    onChange={() => toggleSelection(report.id)}
                    style={{ marginTop: '4px', cursor: 'pointer', transform: 'scale(1.2)' }}
                  />
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <CalendarIcon width={14} height={14} color="var(--text-secondary)" />
                      <h3 style={{ margin: 0, fontSize: '0.9rem', color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
                        Week of {new Date(report.period_start).toLocaleDateString()}
                      </h3>
                      <span className={`badge ${report.status === 'sent' ? 'badge-active' : 'badge-inactive'}`} style={{ marginLeft: '8px' }}>
                        {report.status}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {summary}
                    </p>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-secondary" title="Download PDF" onClick={() => alert('PDF download not implemented yet. Try viewing instead.')}>
                    <DownloadIcon width={14} height={14} /> PDF
                  </button>
                  <button className="btn btn-secondary" title="View Full Report" onClick={() => setExpandedId(isExpanded ? null : report.id)}>
                    {isExpanded ? 'Hide' : 'View'} <ArrowRightIcon width={14} height={14} style={{ transform: isExpanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }} />
                  </button>
                </div>
              </div>
              
              {isExpanded && (
                <div style={{ padding: '0 24px 24px 52px', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                  <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '0 0 16px 0' }} />
                  <div style={{ marginTop: '12px', lineHeight: '1.6' }}>
                    {report.content_markdown ? (
                      <ReactMarkdown>{report.content_markdown}</ReactMarkdown>
                    ) : (
                      'No markdown content available.'
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
