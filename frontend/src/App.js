import React, {useEffect, useMemo, useState} from 'react';
import axios from 'axios';

export default function App(){
  const [view, setView] = useState('analysis'); // 'analysis' or 'dashboard'
  const [ticket, setTicket] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [message, setMessage] = useState('');

  const [tickets, setTickets] = useState([]);
  const [kbArticles, setKbArticles] = useState([]);
  const [gapData, setGapData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // Local fallback; Railway should set REACT_APP_BACKEND_URL.
  const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

  const fetchTickets = async () => {
    try {
      const res = await axios.get(`${API_BASE}/tickets`);
      setTickets(res.data.tickets || []);
    } catch (e) {
      console.warn('Failed to load tickets:', e.message);
      setTickets([]);
    }
  };

  const fetchKbArticles = async () => {
    try {
      const res = await axios.get(`${API_BASE}/kb-articles`);
      setKbArticles(res.data.articles || []);
    } catch (e) {
      console.warn('Failed to load KB articles:', e.message);
      setKbArticles([]);
    }
  };

  const fetchGapAnalysis = async () => {
    try {
      const res = await axios.get(`${API_BASE}/gap-analysis`);
      setGapData(res.data);
    } catch (e) {
      console.warn('Failed to load gap analysis:', e.message);
      setGapData(null);
    }
  };

  const loadDashboardData = async () => {
    setDashboardLoading(true);
    await Promise.all([fetchTickets(), fetchKbArticles(), fetchGapAnalysis()]);
    setDashboardLoading(false);
  };

  useEffect(() => {
    if (view === 'dashboard') {
      loadDashboardData();
    }
  }, [view]);

  function derivePriority(category) {
    const high = new Set(['Payment', 'Authentication', 'API', 'Security']);
    const medium = new Set(['Performance', 'Integration', 'Data Export']);
    if (high.has(category)) return 'High';
    if (medium.has(category)) return 'Medium';
    return 'Low';
  }

  function deriveStatus(ticketId) {
    // Simple stable status based on ticketId hash
    const num = ticketId.replace(/\D/g, '');
    const n = Number(num) || 0;
    const states = ['Open', 'In Progress', 'Resolved'];
    return states[n % states.length];
  }

  function parseTicketDate(dateString) {
    // Normalize "YYYY-MM-DD HH:mm:ss" into a parseable Date.
    // If parsing fails, return null.
    if (!dateString) return null;
    const normalized = dateString.replace(' ', 'T');
    const parsed = new Date(normalized);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  const ticketStats = useMemo(() => {
    const total = tickets.length;
    const withPriority = tickets.map(t => ({
      ...t,
      priority: derivePriority(t.category || ''),
      status: deriveStatus(t.ticket_id || ''),
      created_at_date: parseTicketDate(t.created_at),
    }));
    const open = withPriority.filter(t => t.status !== 'Resolved').length;
    const resolved = total - open;
    const highPriority = withPriority.filter(t => t.priority === 'High').length;
    const aiClassified = analysis ? 1 : 0; // placeholder: track last analysis

    const byCategory = withPriority.reduce((acc, t) => {
      const cat = t.category || 'Unknown';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});

    const byPriority = withPriority.reduce((acc, t) => {
      acc[t.priority] = (acc[t.priority] || 0) + 1;
      return acc;
    }, {});

    const ticketsOverTime = withPriority
      .filter(t => t.created_at_date)
      .map(t => ({
        ...t,
        created_at: t.created_at_date
      }));

    const timeSeries = ticketsOverTime.reduce((acc, t) => {
      const key = t.created_at.toISOString().slice(0, 10);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    const timeSeriesArray = Object.entries(timeSeries)
      .map(([date, count]) => ({date, count}))
      .sort((a, b) => a.date.localeCompare(b.date));

    const recent = [...withPriority]
      .filter(t => t.created_at_date)
      .sort((a, b) => {
        const aTime = a.created_at_date?.getTime() ?? 0;
        const bTime = b.created_at_date?.getTime() ?? 0;
        return bTime - aTime;
      })
      .slice(0, 7);

    const similarTickets = recent.filter(t => t.category === analysis?.classification?.category).slice(0, 5);

    return {
      total,
      open,
      resolved,
      highPriority,
      aiClassified,
      byCategory,
      byPriority,
      timeSeries: timeSeriesArray,
      recent,
      similarTickets,
    };
  }, [tickets, analysis]);

  async function analyze(){
    setLoading(true);
    setAnalysis(null);
    setMessage('');
    try{
      const res = await axios.post(`${API_BASE}/analyze-ticket`, {ticket_text: ticket});
      setAnalysis(res.data);
    }catch(e){
      setMessage('Error: ' + (e.response?.data?.detail || e.message));
    }finally{
      setLoading(false);
    }
  }

  async function buildIndex(){
    setMessage('Building index...');
    try{
      const res = await axios.post(`${API_BASE}/build-index`);
      setMessage('Index build started: ' + (res.data?.message || 'ok'));
    }catch(e){
      setMessage('Index build failed: ' + (e.response?.data?.detail || e.message));
    }
  }

  const renderDashboard = () => {
    return (
      <div className="dashboard">
        <section className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Tickets</div>
            <div className="stat-value">{ticketStats.total}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Open Tickets</div>
            <div className="stat-value">{ticketStats.open}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Resolved Tickets</div>
            <div className="stat-value">{ticketStats.resolved}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">High Priority</div>
            <div className="stat-value">{ticketStats.highPriority}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">AI Classified</div>
            <div className="stat-value">{ticketStats.aiClassified}</div>
          </div>
        </section>

        <section className="card">
          <h3>Tickets Over Time</h3>
          {ticketStats.timeSeries.length > 0 ? (
            <div className="chart">
              {ticketStats.timeSeries.map(pt => (
                <div key={pt.date} className="chart-bar">
                  <div className="bar" style={{height: `${Math.max(4, pt.count * 10)}px`}} />
                  <div className="bar-label">{pt.date.slice(5)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty">No ticket data to show.</div>
          )}
        </section>

        <section className="card grid-2">
          <div>
            <h3>Category Breakdown</h3>
            {Object.keys(ticketStats.byCategory).length ? (
              <div className="chart-list">
                {Object.entries(ticketStats.byCategory).map(([cat, count]) => (
                  <div key={cat} className="chart-row">
                    <div className="chart-label">{cat}</div>
                    <div className="chart-bar-row">
                      <div className="bar-fill" style={{width: `${(count / ticketStats.total) * 100}%`}} />
                    </div>
                    <div className="chart-value">{count}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty">No category data available.</div>
            )}
          </div>

          <div>
            <h3>Priority Distribution</h3>
            {Object.keys(ticketStats.byPriority).length ? (
              <div className="chart-list">
                {Object.entries(ticketStats.byPriority).map(([prio, count]) => (
                  <div key={prio} className="chart-row">
                    <div className="chart-label">{prio}</div>
                    <div className="chart-bar-row">
                      <div className="bar-fill" style={{width: `${(count / ticketStats.total) * 100}%`}} />
                    </div>
                    <div className="chart-value">{count}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty">No priority data available.</div>
            )}
          </div>
        </section>

        <section className="card">
          <h3>Recent Tickets</h3>
          {ticketStats.recent.length ? (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Ticket ID</th>
                    <th>Message</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {ticketStats.recent.map(t => (
                    <tr key={t.ticket_id}>
                      <td>{t.ticket_id}</td>
                      <td className="message-cell">{t.ticket_text}</td>
                      <td>{t.category}</td>
                      <td>{t.priority}</td>
                      <td>{t.status}</td>
                      <td>{t.created_at_date ? t.created_at_date.toLocaleDateString() : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty">No recent tickets available.</div>
          )}
        </section>

        <section className="card grid-2">
          <div>
            <h3>AI Insights</h3>
            {analysis ? (
              <div className="insights">
                <div><strong>Detected category:</strong> {analysis.classification?.category}</div>
                <div><strong>Confidence:</strong> {Math.round((analysis.classification?.confidence||0)*100)}%</div>
                <div><strong>Suggested KB article:</strong> {analysis.recommendations?.[0]?.title || '—'}</div>
                <div><strong>Similar tickets:</strong></div>
                <ul>
                  {ticketStats.similarTickets.length ? (
                    ticketStats.similarTickets.map(t => (
                      <li key={t.ticket_id}>{t.ticket_id} — {t.ticket_text.slice(0, 60)}...</li>
                    ))
                  ) : (
                    <li>None found.</li>
                  )}
                </ul>
              </div>
            ) : (
              <div className="empty">Run a ticket analysis to see AI insights here.</div>
            )}
          </div>

          <div>
            <h3>Knowledge Gap Analysis</h3>
            {gapData ? (
              <div className="insights">
                <div><strong>Low performing articles:</strong></div>
                <ul>
                  {(gapData.low_performers || []).slice(0, 4).map((item, idx) => (
                    <li key={idx}>{item.title} ({Math.round(item.ctr*100)}% CTR)</li>
                  ))}
                </ul>

                <div style={{marginTop: '1rem'}}><strong>Low coverage questions:</strong></div>
                <ul>
                  {(gapData.low_coverage || []).slice(0, 4).map((item, idx) => (
                    <li key={idx}>{item.title || item.question || 'Unnamed'}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="empty">Gap analysis data unavailable. Build the index to enable.</div>
            )}
          </div>
        </section>
      </div>
    );
  };

  const renderAnalysis = () => {
    return (
      <>
        <section className="hero">
          <h1>Intelligent Ticket Analysis</h1>
          <p className="sub">Automatically analyze tickets, apply tags, and classify</p>
        </section>

        <section className="card">
          <h2>Enter Support Ticket</h2>
          <textarea value={ticket} onChange={e=>setTicket(e.target.value)} placeholder="Paste a support ticket..." rows={6}></textarea>
          <div className="row">
            <button className="btn primary" onClick={analyze} disabled={loading || !ticket}>Analyze Ticket</button>
            <div className="status">{loading ? 'Analyzing...' : message}</div>
          </div>
        </section>

        {analysis && (
          <section className="card result">
            <h3>Classification Results</h3>
            <div className="grid">
              <div className="box">
                <div className="label">Category</div>
                <div className="value">{analysis.classification?.category || '—'}</div>
              </div>
              <div className="box center">
                <div className="label">Confidence</div>
                <div className="confidence-large">{Math.round((analysis.classification?.confidence||0)*100)}%</div>
              </div>
              <div className="box">
                <div className="label">Status</div>
                <div className={"status-badge " + (analysis.classification?.status === 'success' ? 'ok' : 'warn')}>{analysis.classification?.status || '—'}</div>
              </div>
            </div>

            <div className="tags">
              {(analysis.classification?.tags || []).map((t,i)=> (
                <span key={i} className="tag">{t}</span>
              ))}
            </div>

            <h3>Recommended KB Articles</h3>
            <div className="recommendations">
              {(analysis.recommendations && analysis.recommendations.length>0) ? (
                analysis.recommendations.map((r,idx)=> (
                  <div key={idx} className="kb">
                    <div className="kb-left">
                      <div className="kb-title">#{idx+1} {r.title}</div>
                      <div className="kb-meta">Article ID: {r.article_id} • {r.category}</div>
                      <div className="kb-content">{r.content}</div>
                    </div>
                    <div className="kb-right">
                      <div className="similarity">{Math.round((r.similarity_score||0)*100)}%</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty">No recommendations. Build the index first.</div>
              )}
            </div>
          </section>
        )}
      </>
    );
  };

  return (
    <div className="app-root">
      <header className="topbar">
        <div className="brand"><span className="brand-icon">🤖</span>AI Support Ticket Helper</div>
        <div className="actions">
          <button className="btn outline" onClick={buildIndex}>Build Index</button>
          <button
            className={"btn outline" + (view === 'dashboard' ? ' active' : '')}
            onClick={() => setView('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={"btn outline" + (view === 'analysis' ? ' active' : '')}
            onClick={() => setView('analysis')}
          >
            Analyze
          </button>
        </div>
      </header>

      <main className="container">
        {view === 'dashboard' ? renderDashboard() : renderAnalysis()}
      </main>

      <footer className="footer">Powered by LLaMA & FAISS</footer>
    </div>
  );
}
