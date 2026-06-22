import React, { useState, useEffect } from 'react';

// Setup API endpoint target
const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';

interface Profile {
  id?: string;
  email: string;
  phone?: string;
  full_name?: string;
  interests?: string[];
  avg_order_value?: number;
  price_sensitivity?: string;
}

interface StepState {
  status: 'idle' | 'active' | 'completed' | 'error';
  title: string;
  description: string;
  logs: string[];
}

const INITIAL_STEPS: Record<string, StepState> = {
  CDP_STITCHING: { status: 'idle', title: 'Identity Stitching (CDP)', description: 'Resolving profiles from messy raw events.', logs: [] },
  PROMO_OPTIMIZATION: { status: 'idle', title: 'Margin/Promo Optimizer', description: 'Computing margin-safe discounts & anti-abuse checks.', logs: [] },
  CREATIVE_COPYWRITING: { status: 'idle', title: 'Creative Copywriter', description: 'Generating hyper-personalized copies.', logs: [] },
  COMPLIANCE_AUDIT: { status: 'idle', title: 'GDPR & Legal Guardrails', description: 'Verifying legal footers and zero-trust policies.', logs: [] },
  ADVISOR_SCRIPT: { status: 'idle', title: 'CS Advisor Script', description: 'Synthesizing script for client success reps.', logs: [] },
  PERSISTENCE: { status: 'idle', title: 'ROI Calculator & Save', description: 'Storing campaign logs and computing dynamic ROI.', logs: [] }
};

export default function App() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  
  // Custom touchpoint inputs
  const [customEmail, setCustomEmail] = useState('');
  const [customInterest, setCustomInterest] = useState('Premium Gym Gear');
  const [customPrice, setCustomPrice] = useState('120');
  const [customEvent, setCustomEvent] = useState('cart_abandonment');
  const [isIngesting, setIsIngesting] = useState(false);

  // Execution states
  const [steps, setSteps] = useState<Record<string, StepState>>(INITIAL_STEPS);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<'email' | 'coupon' | 'advisor' | 'compliance'>('email');

  // Outputs
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [couponCode, setCouponCode] = useState('');
  const [couponDiscount, setCouponDiscount] = useState(0);
  const [advisorScript, setAdvisorScript] = useState('');
  const [complianceReport, setComplianceReport] = useState<any>(null);
  
  // P&L metrics
  const [opexSaved, setOpexSaved] = useState<number>(0);
  const [convProb, setConvProb] = useState<number>(0);

  // Load profiles on mount
  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/profiles`);
      const data = await res.json();
      if (data.profiles) {
        setProfiles(data.profiles);
        if (data.profiles.length > 0 && !selectedProfile) {
          setSelectedProfile(data.profiles[0]);
        }
      }
    } catch (err) {
      console.error("Failed to load profiles:", err);
    }
  };

  const handleResetDB = async () => {
    try {
      await fetch(`${API_BASE}/api/reset-db`, { method: 'POST' });
      await fetchProfiles();
      alert("Database reset and mock profiles reloaded!");
    } catch (err) {
      console.error(err);
    }
  };

  // Ingest Custom Touchpoint
  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customEmail) return alert("Please enter an email");

    setIsIngesting(true);
    try {
      const payload = {
        email: customEmail,
        event_type: customEvent,
        event_data: {
          product_category: customInterest,
          price: parseFloat(customPrice),
          timestamp: new Date().toISOString()
        }
      };

      const res = await fetch(`${API_BASE}/api/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await res.json();
      setIsIngesting(false);
      setCustomEmail('');
      await fetchProfiles();

      // Auto-select the newly added or updated profile
      if (data.profiling_details?.profile) {
        setSelectedProfile(data.profiling_details.profile);
      }
      alert("Raw touchpoint ingested! Customer identity resolves in real-time.");
    } catch (err) {
      console.error("Failed to ingest:", err);
      setIsIngesting(false);
    }
  };

  // Run Campaign pipeline (SSE)
  const handleTriggerCampaign = () => {
    if (!selectedProfile) return;
    
    setIsRunning(true);
    setSteps(JSON.parse(JSON.stringify(INITIAL_STEPS))); // deep copy reset
    setEmailSubject('');
    setEmailBody('');
    setCouponCode('');
    setCouponDiscount(0);
    setAdvisorScript('');
    setComplianceReport(null);
    setOpexSaved(0);
    setConvProb(0);

    const email = selectedProfile.email;
    const sseUrl = `${API_BASE}/api/stream-campaign?email=${encodeURIComponent(email)}`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      const parsed = JSON.parse(event.data);
      const { event: evtType, data } = parsed;

      if (evtType === 'step_start') {
        setSteps(prev => ({
          ...prev,
          [data.step]: {
            ...prev[data.step],
            status: 'active',
            logs: [...prev[data.step].logs, `Started: ${data.message}`]
          }
        }));
      } 
      
      else if (evtType === 'log') {
        setSteps(prev => ({
          ...prev,
          [data.step]: {
            ...prev[data.step],
            logs: [...prev[data.step].logs, data.log]
          }
        }));
      } 
      
      else if (evtType === 'step_complete') {
        setSteps(prev => ({
          ...prev,
          [data.step]: {
            ...prev[data.step],
            status: 'completed',
            logs: [...prev[data.step].logs, "Completed successfully."]
          }
        }));

        // Dynamically capture results as they are finalized by specific agents
        if (data.step === 'CDP_STITCHING') {
          setSelectedProfile(data.profile);
        } else if (data.step === 'PROMO_OPTIMIZATION') {
          setCouponCode(data.coupon_code);
          setCouponDiscount(data.discount_percent);
        } else if (data.step === 'CREATIVE_COPYWRITING') {
          setEmailSubject(data.subject);
          setEmailBody(data.body);
        } else if (data.step === 'COMPLIANCE_AUDIT') {
          setComplianceReport(data.report);
        } else if (data.step === 'ADVISOR_SCRIPT') {
          setAdvisorScript(data.script);
        } else if (data.step === 'PERSISTENCE') {
          setOpexSaved(data.total_cost_saved);
          setConvProb(data.conversion_probability);
        }
      } 
      
      else if (evtType === 'pipeline_complete') {
        eventSource.close();
        setIsRunning(false);
      } 
      
      else if (evtType === 'error') {
        eventSource.close();
        setIsRunning(false);
        alert(data.message);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE Connection Error:", err);
      eventSource.close();
      setIsRunning(false);
    };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header>
        <div className="brand">
          <div className="brand-logo">
            <span>Aura</span>
            <span className="badge demo">Agentic CDP</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={handleResetDB}>Reset Mock Database</button>
          <a href="https://github.com" target="_blank" rel="noreferrer" className="btn btn-secondary">System Docs</a>
        </div>
      </header>

      <div className="container">
        {/* Sidebar */}
        <div className="sidebar">
          <div>
            <div className="sidebar-title">Select Customer Profile</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {profiles.map(p => (
                <div
                  key={p.email}
                  className={`persona-card ${selectedProfile?.email === p.email ? 'selected' : ''}`}
                  onClick={() => !isRunning && setSelectedProfile(p)}
                >
                  <div className="persona-name">{p.full_name || p.email}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{p.email}</div>
                  <div className="persona-meta">
                    <span className="persona-tag">Spend: £{p.avg_order_value}</span>
                    <span className="persona-tag">Sensitivity: {p.price_sensitivity}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '1.25rem' }}>
            <div className="sidebar-title" style={{ marginBottom: '1rem' }}>Ingest Raw Touchpoint</div>
            <form onSubmit={handleIngest} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                  Customer Email
                </label>
                <input
                  type="email"
                  placeholder="customer@email.com"
                  value={customEmail}
                  onChange={e => setCustomEmail(e.target.value)}
                  style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-light)', fontSize: '0.85rem' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                  User Action / Event
                </label>
                <select
                  value={customEvent}
                  onChange={e => setCustomEvent(e.target.value)}
                  style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-light)', fontSize: '0.85rem' }}
                >
                  <option value="cart_abandonment">Cart Abandonment</option>
                  <option value="page_view">Web Page View</option>
                  <option value="zero_party_survey">Zero Party Survey</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                  Product Category Interest
                </label>
                <input
                  type="text"
                  placeholder="e.g. Premium Running Shoes"
                  value={customInterest}
                  onChange={e => setCustomInterest(e.target.value)}
                  style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-light)', fontSize: '0.85rem' }}
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.025em', marginBottom: '4px' }}>
                  Event Value (£)
                </label>
                <input
                  type="number"
                  placeholder="e.g. 150"
                  value={customPrice}
                  onChange={e => setCustomPrice(e.target.value)}
                  style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--border-light)', fontSize: '0.85rem' }}
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.25rem' }} disabled={isIngesting || isRunning}>
                {isIngesting ? 'Ingesting...' : 'Ingest & Stitch'}
              </button>
            </form>
          </div>
        </div>

        {/* Dashboard Main Content */}
        <div className="dashboard-content">
          {/* Top Hero Stats */}
          <div className="hero-stats">
            <div className="stat-card">
              <div className="stat-label">Automation ROI</div>
              <div className="stat-value">£{opexSaved > 0 ? opexSaved.toFixed(2) : '--'}</div>
              <div className="stat-desc">OPEX saved vs. human copywriting cycles</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Conversion Likelihood</div>
              <div className="stat-value">{convProb > 0 ? `${(convProb * 100).toFixed(0)}%` : '--'}</div>
              <div className="stat-desc">Projected conversion uplift after optimization</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Compliance Shield</div>
              <div className="stat-value" style={{ color: complianceReport?.approved ? 'var(--accent-green)' : 'var(--text-primary)' }}>
                {complianceReport ? (complianceReport.approved ? 'Passed' : 'Flagged') : '--'}
              </div>
              <div className="stat-desc">Zero-trust and legal boundary validation state</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <h2 style={{ margin: 0 }}>Omni-Campaign Strategy Sandbox</h2>
            <button
              onClick={handleTriggerCampaign}
              className="btn btn-primary"
              disabled={isRunning || !selectedProfile}
            >
              {isRunning ? 'Orchestrator Executing...' : 'Trigger Campaign Suite'}
            </button>
          </div>

          {/* Timeline and Outputs Grid */}
          <div className="workspace-grid">
            {/* Steps Timeline Panel */}
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">Agent Telemetry Logs</div>
              </div>
              <div className="panel-body">
                <div className="timeline">
                  {Object.entries(steps).map(([key, value], idx) => (
                    <div key={key} className={`timeline-node ${value.status}`}>
                      <div className="timeline-dot">{idx + 1}</div>
                      <div className="timeline-content">
                        <div className="timeline-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>{value.title}</span>
                          <span style={{ fontSize: '0.75rem', textTransform: 'capitalize', fontWeight: 'normal' }}>
                            {value.status}
                          </span>
                        </div>
                        <div className="timeline-desc">{value.description}</div>
                        {value.logs.length > 0 && (
                          <div className="timeline-logs">
                            {value.logs.map((log, lidx) => (
                              <div key={lidx}>{log}</div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Campaign Output Preview Panel */}
            <div className="panel">
              <div className="tabs">
                <div className={`tab ${activeTab === 'email' ? 'active' : ''}`} onClick={() => setActiveTab('email')}>
                  Dynamic Email Copy
                </div>
                <div className={`tab ${activeTab === 'coupon' ? 'active' : ''}`} onClick={() => setActiveTab('coupon')}>
                  Promo & Fraud Guard
                </div>
                <div className={`tab ${activeTab === 'advisor' ? 'active' : ''}`} onClick={() => setActiveTab('advisor')}>
                  Advisor Script
                </div>
                <div className={`tab ${activeTab === 'compliance' ? 'active' : ''}`} onClick={() => setActiveTab('compliance')}>
                  GDPR Audit
                </div>
              </div>

              <div className="panel-body">
                {activeTab === 'email' && (
                  <div>
                    {emailBody ? (
                      <div className="email-preview">
                        <div className="email-header">
                          <div><strong>From:</strong> Aura Offers &lt;offers@auraretail.com&gt;</div>
                          <div><strong>To:</strong> {selectedProfile?.email}</div>
                          <div><strong>Subject:</strong> {emailSubject}</div>
                        </div>
                        <div className="email-body" dangerouslySetInnerHTML={{ __html: emailBody }} />
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                        Trigger the Campaign Suite to view the personalized email draft.
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'coupon' && (
                  <div>
                    {couponCode ? (
                      <div className="coupon-preview">
                        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                          Allocated Dynamic Margin Discount
                        </div>
                        <div className="coupon-badge">{couponCode}</div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', textAlign: 'center' }}>
                          Discount Value: <strong>{couponDiscount}% OFF</strong>
                          <br />
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                            Automatically protected against database coupon loop abuse checks.
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                        Trigger the Campaign Suite to view optimized coupons.
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'advisor' && (
                  <div>
                    {advisorScript ? (
                      <div className="script-box">{advisorScript}</div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                        Trigger the Campaign Suite to generate customized phone script guides.
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'compliance' && (
                  <div>
                    {complianceReport ? (
                      <div>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '1rem' }}>
                          <span className={`badge ${complianceReport.approved ? 'active' : ''}`}>
                            {complianceReport.approved ? 'PASSED AUDIT' : 'FLAGGED'}
                          </span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                            Checked at {complianceReport.audit_timestamp}
                          </span>
                        </div>
                        <div className="audit-grid">
                          <div className="audit-item">
                            <span>Opt-out Link Footer</span>
                            <span style={{ color: complianceReport.checks.has_opt_out_disclaimer ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 'bold' }}>
                              {complianceReport.checks.has_opt_out_disclaimer ? 'PASS' : 'FAIL'}
                            </span>
                          </div>
                          <div className="audit-item">
                            <span>Zero-Trust Leak Check</span>
                            <span style={{ color: complianceReport.checks.zero_trust_data_exposure ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 'bold' }}>
                              {complianceReport.checks.zero_trust_data_exposure ? 'PASS' : 'FAIL'}
                            </span>
                          </div>
                          <div className="audit-item">
                            <span>Channel Consent</span>
                            <span style={{ color: complianceReport.checks.gdpr_compliant_channel ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 'bold' }}>
                              {complianceReport.checks.gdpr_compliant_channel ? 'PASS' : 'FAIL'}
                            </span>
                          </div>
                          <div className="audit-item">
                            <span>Proper Branding</span>
                            <span style={{ color: complianceReport.checks.has_proper_branding ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 'bold' }}>
                              {complianceReport.checks.has_proper_branding ? 'PASS' : 'FAIL'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-tertiary)' }}>
                        Trigger the Campaign Suite to view the legal privacy audit details.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
