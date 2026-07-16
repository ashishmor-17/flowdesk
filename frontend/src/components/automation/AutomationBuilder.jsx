import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { 
  Cpu, 
  Plus, 
  Trash2, 
  AlertTriangle, 
  CheckCircle,
  Settings
} from 'lucide-react';

export default function AutomationBuilder() {
  const { user, activeOrg } = useAuth();
  const isAuthorized = user?.role?.toUpperCase() === 'OWNER' || user?.role?.toUpperCase() === 'ADMIN';
  const [projects, setProjects] = useState([]);
  const [selectedProjId, setSelectedProjId] = useState('');
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(false);

  const [name, setName] = useState('');
  const [triggerEvent, setTriggerEvent] = useState('STATUS_CHANGED');
  const [actionType, setActionType] = useState('NOTIFY_ROLE');
  
  const [conds, setConds] = useState([]);
  const [newCondKey, setNewCondKey] = useState('status');
  const [newCondVal, setNewCondVal] = useState('in_progress');

  const [notifyUserId, setNotifyUserId] = useState('');
  const [notifyRole, setNotifyRole] = useState('admin');
  const [changeStatus, setChangeStatus] = useState('todo');
  const [sendEmail, setSendEmail] = useState('');

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const fetchProjects = async () => {
    try {
      const projs = await api.projects.list();
      const list = projs?.projects || [];
      setProjects(list);
      if (list.length > 0) {
        setSelectedProjId(list[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRules = async () => {
    if (!selectedProjId) return;
    setLoading(true);
    try {
      const data = await api.automation.list(selectedProjId);
      setRules(data?.rules || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeOrg]);

  useEffect(() => {
    fetchRules();
  }, [selectedProjId]);

  const handleAddCondition = () => {
    if (!newCondKey.trim() || !newCondVal.trim()) return;
    if (conds.some(c => c.key === newCondKey)) {
      setError(`Condition for '${newCondKey}' already added.`);
      return;
    }
    setConds(prev => [...prev, { key: newCondKey, value: newCondVal }]);
    setError('');
  };

  const handleRemoveCondition = (index) => {
    setConds(prev => prev.filter((_, i) => i !== index));
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    const conditionsObj = {};
    conds.forEach(c => {
      conditionsObj[c.key] = c.value;
    });

    let actionPayload = {};
    if (actionType === 'NOTIFY_USER') {
      actionPayload = { recipient_id: notifyUserId };
    } else if (actionType === 'NOTIFY_ROLE') {
      actionPayload = { role: notifyRole };
    } else if (actionType === 'CHANGE_STATUS') {
      actionPayload = { status: changeStatus };
    } else if (actionType === 'SEND_EMAIL') {
      actionPayload = { email: sendEmail };
    }

    try {
      await api.automation.create({
        project_id: selectedProjId,
        name,
        trigger_event: triggerEvent,
        conditions: Object.keys(conditionsObj).length > 0 ? conditionsObj : null,
        action_type: actionType,
        action_payload: actionPayload
      });

      setName('');
      setConds([]);
      fetchRules();
      setMessage('Automation rule created successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to create automation rule');
    }
  };

  const handleDeleteRule = async (id) => {
    setError('');
    try {
      await api.automation.delete(id);
      fetchRules();
      setMessage('Rule deleted.');
      setTimeout(() => setMessage(''), 2000);
    } catch (err) {
      setError(err.message || 'Failed to delete rule');
    }
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', flexGrow: 1, height: '100vh', width: '100%', overflowY: 'auto' }} className="animate-fade-in">
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800' }}>Automation Rules Builder</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Define triggers, condition rules, and automated event actions.</p>
        </div>

        {projects.length > 0 && (
          <select
            className="input-field"
            style={{ width: '220px' }}
            value={selectedProjId}
            onChange={(e) => setSelectedProjId(e.target.value)}
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        )}
      </div>

      {message && (
        <div className="glass-panel" style={{ padding: '10px 20px', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} /> {message}
        </div>
      )}

      {error && (
        <div className="glass-panel" style={{ padding: '10px 20px', background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Main Builder Grid */}
      {!selectedProjId ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Create a project first in the Dashboard to map automation rules.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: isAuthorized ? '1.2fr 1fr' : '1fr', gap: '28px' }}>
          
          {/* Rules List */}
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Active Rules</h3>
            {loading ? (
              <div>Loading rules...</div>
            ) : rules.length === 0 ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                {isAuthorized 
                  ? "No automation rules defined for this project yet. Use the composer on the right to build one."
                  : "No automation rules defined for this project yet."}
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {rules.map(rule => (
                  <div key={rule.id} className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Cpu size={16} color="var(--primary)" />
                        <h4 style={{ fontSize: '15px', fontWeight: '600' }}>{rule.name}</h4>
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '12px' }}>
                        <span style={{ background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--border-glass)' }}>
                          <strong>Trigger:</strong> {rule.trigger_event}
                        </span>
                        
                        <span style={{ background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--border-glass)' }}>
                          <strong>Action:</strong> {rule.action_type}
                        </span>
                      </div>

                      {rule.conditions && Object.keys(rule.conditions).length > 0 && (
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          <strong>Conditions:</strong> {JSON.stringify(rule.conditions)}
                        </div>
                      )}

                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        <strong>Action Payload:</strong> {JSON.stringify(rule.action_payload)}
                      </div>
                    </div>

                    {isAuthorized && (
                      <button 
                        onClick={() => handleDeleteRule(rule.id)}
                        style={{ background: 'transparent', border: 'none', color: 'rgba(239, 68, 68, 0.7)', cursor: 'pointer', padding: '6px' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Creation Form */}
          {isAuthorized && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={18} /> New Automation Wizard
              </h3>

              <form onSubmit={handleCreateRule} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Rule Name</label>
                  <input
                    type="text"
                    required
                    className="input-field"
                    placeholder="e.g. Notify Owner on High Priority"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Trigger Event</label>
                  <select
                    className="input-field"
                    value={triggerEvent}
                    onChange={(e) => setTriggerEvent(e.target.value)}
                  >
                    <option value="STATUS_CHANGED">Status Changed</option>
                    <option value="TASK_CREATED">Task Created</option>
                    <option value="TASK_ASSIGNED">Task Assigned</option>
                    <option value="TASK_OVERDUE">Task Overdue</option>
                  </select>
                </div>

                <div style={{ border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', marginBottom: '10px' }}>Conditions</div>
                  
                  <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                    <select
                      className="input-field"
                      style={{ flex: 1, padding: '6px 12px' }}
                      value={newCondKey}
                      onChange={(e) => setNewCondKey(e.target.value)}
                    >
                      <option value="status">status</option>
                      <option value="priority">priority</option>
                    </select>

                    <select
                      className="input-field"
                      style={{ flex: 1.2, padding: '6px 12px' }}
                      value={newCondVal}
                      onChange={(e) => setNewCondVal(e.target.value)}
                    >
                      {newCondKey === 'status' ? (
                        <>
                          <option value="todo">To Do</option>
                          <option value="in_progress">In Progress</option>
                          <option value="review">Review</option>
                          <option value="done">Done</option>
                        </>
                      ) : (
                        <>
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="urgent">Urgent</option>
                        </>
                      )}
                    </select>

                    <button 
                      type="button" 
                      className="btn-secondary" 
                      style={{ padding: '6px 12px' }}
                      onClick={handleAddCondition}
                    >
                      Add
                    </button>
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {conds.map((c, index) => (
                      <div key={index} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-glass)', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span><strong>{c.key}:</strong> {c.value}</span>
                        <button 
                          type="button" 
                          onClick={() => handleRemoveCondition(index)}
                          style={{ border: 'none', background: 'transparent', color: 'var(--danger)', cursor: 'pointer', fontWeight: '700' }}
                        >
                          ×
                        </button>
                      </div>
                    ))}
                    {conds.length === 0 && (
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>No conditions set. Rule will run on all triggers.</span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Action Type</label>
                  <select
                    className="input-field"
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value)}
                  >
                    <option value="NOTIFY_ROLE">Notify Role</option>
                    <option value="NOTIFY_USER">Notify Specific User</option>
                    <option value="CHANGE_STATUS">Auto Change Status</option>
                    <option value="SEND_EMAIL">Send Email (Simulation)</option>
                  </select>
                </div>

                {actionType === 'NOTIFY_ROLE' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Role</label>
                    <select
                      className="input-field"
                      value={notifyRole}
                      onChange={(e) => setNotifyRole(e.target.value)}
                    >
                      <option value="owner">Owner</option>
                      <option value="admin">Admin</option>
                      <option value="member">Member</option>
                    </select>
                  </div>
                )}

                {actionType === 'NOTIFY_USER' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target User ID (UUID)</label>
                    <input
                      type="text"
                      required
                      className="input-field"
                      placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                      value={notifyUserId}
                      onChange={(e) => setNotifyUserId(e.target.value)}
                    />
                  </div>
                )}

                {actionType === 'CHANGE_STATUS' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Target Task Status</label>
                    <select
                      className="input-field"
                      value={changeStatus}
                      onChange={(e) => setChangeStatus(e.target.value)}
                    >
                      <option value="todo">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="review">Review</option>
                      <option value="done">Done</option>
                    </select>
                  </div>
                )}

                {actionType === 'SEND_EMAIL' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Recipient Email</label>
                    <input
                      type="email"
                      required
                      className="input-field"
                      placeholder="manager@example.com"
                      value={sendEmail}
                      onChange={(e) => setSendEmail(e.target.value)}
                    />
                  </div>
                )}

                <button type="submit" className="btn-primary" style={{ marginTop: '8px' }}>
                  Create Automation Rule
                </button>

              </form>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
