import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { formatDate } from '../../utils/format';
import { 
  FolderPlus, 
  Users, 
  Trash2, 
  Activity, 
  Mail, 
  CheckCircle,
  Briefcase,
  AlertTriangle,
  Settings,
  Sliders,
  Archive,
  X
} from 'lucide-react';

export default function Dashboard() {
  const { activeOrg, user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [showProjModal, setShowProjModal] = useState(false);
  const [projName, setProjName] = useState('');
  const [projDesc, setProjDesc] = useState('');
  const [projColor, setProjColor] = useState('#6366f1');
  
  const [deleteConfirmProj, setDeleteConfirmProj] = useState(null);
  const [cascadeDelete, setCascadeDelete] = useState(false);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [showConfigProj, setShowConfigProj] = useState(null);

  const role = user?.role || 'MEMBER';
  const isOwnerOrAdmin = ['OWNER', 'ADMIN'].includes(role.toUpperCase());

  const colors = ['#6366f1', '#a855f7', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

  const fetchData = async () => {
    if (!activeOrg) return;
    setLoading(true);
    try {
      const projList = await api.projects.list();
      setProjects(projList?.projects || []);

      const memberList = await api.org.getMembers();
      setMembers(memberList?.members || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeOrg]);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.projects.create(projName, projDesc, projColor);
      setShowProjModal(false);
      setProjName('');
      setProjDesc('');
      setProjColor('#6366f1');
      fetchData();
      setMessage('Project created successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to create project');
    }
  };

  const handleDeleteProject = async () => {
    if (!deleteConfirmProj) return;
    setError('');
    try {
      await api.projects.delete(deleteConfirmProj.id, cascadeDelete);
      setDeleteConfirmProj(null);
      setCascadeDelete(false);
      fetchData();
      setMessage('Project deleted successfully.');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to delete project. If it has tasks, you must choose cascade delete.');
    }
  };

  const handleInviteUser = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.org.invite(inviteEmail, inviteRole);
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('member');
      setMessage('Invitation sent successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to send invitation');
    }
  };

  if (!activeOrg) {
    return (
      <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
        <Briefcase size={64} color="var(--text-muted)" style={{ marginBottom: '20px' }} />
        <h2>No Organization Active</h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Please create or join an organization to get started.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '32px', overflowY: 'auto', flexGrow: 1, height: '100vh', width: '100%' }} className="animate-fade-in">
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800' }}>Workspace Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Manage projects, team members, and overall operations for {activeOrg.name}.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-secondary" onClick={() => setShowInviteModal(true)}>
            <Users size={16} /> Invite Member
          </button>
          <button className="btn-primary" onClick={() => setShowProjModal(true)}>
            <FolderPlus size={16} /> New Project
          </button>
        </div>
      </div>

      {message && (
        <div className="glass-panel" style={{ padding: '12px 20px', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} /> {message}
        </div>
      )}

      {error && (
        <div className="glass-panel" style={{ padding: '12px 20px', background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#f87171', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary)' }}>
            <Briefcase size={24} />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Projects</div>
            <div style={{ fontSize: '24px', fontWeight: '700' }}>{projects.length}</div>
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(168, 85, 247, 0.1)', color: 'var(--secondary)' }}>
            <Users size={24} />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Team Members</div>
            <div style={{ fontSize: '24px', fontWeight: '700' }}>{members.length}</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Projects & Members */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '28px' }}>
        {/* Projects Column */}
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Active Projects <span style={{ fontSize: '12px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '20px', color: 'var(--text-secondary)' }}>{projects.length}</span>
          </h3>

          {loading ? (
            <div>Loading projects...</div>
          ) : projects.length === 0 ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No projects created yet. Click "New Project" to start organizing tasks!
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {projects.map(proj => (
                <div key={proj.id} className="glass-card" style={{ borderLeft: `4px solid ${proj.color || 'var(--primary)'}`, position: 'relative', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '140px' }}>
                  <div>
                    <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {proj.name}
                      {proj.status === 'ARCHIVED' && (
                        <span style={{ fontSize: '10px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: '700' }}>
                          Archived
                        </span>
                      )}
                    </h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>{proj.description || 'No description provided.'}</p>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Created {formatDate(proj.created_at)}</span>
                    {isOwnerOrAdmin && (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          onClick={() => setShowConfigProj(proj)}
                          style={{ background: 'transparent', border: 'none', color: 'rgba(255, 255, 255, 0.6)', cursor: 'pointer', padding: '4px' }}
                          title="Project Settings"
                        >
                          <Settings size={16} />
                        </button>
                        {role.toUpperCase() === 'OWNER' && (
                          <button 
                            onClick={() => setDeleteConfirmProj(proj)}
                            style={{ background: 'transparent', border: 'none', color: 'rgba(239, 68, 68, 0.7)', cursor: 'pointer', padding: '4px' }}
                            title="Delete Project"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Team Members Column */}
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Workspace Members <span style={{ fontSize: '12px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '20px', color: 'var(--text-secondary)' }}>{members.length}</span>
          </h3>

          <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {members.map(member => (
              <div key={member.user_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{member.full_name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{member.email}</div>
                </div>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', background: member.role === 'OWNER' ? 'rgba(168, 85, 247, 0.15)' : member.role === 'ADMIN' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255,255,255,0.05)', color: member.role === 'OWNER' ? 'var(--secondary)' : member.role === 'ADMIN' ? 'var(--primary)' : 'var(--text-secondary)', padding: '2px 8px', borderRadius: '4px', fontWeight: '600' }}>
                  {member.role}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* New Project Modal */}
      {showProjModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
          <form onSubmit={handleCreateProject} className="glass-panel" style={{ padding: '28px', width: '450px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>Create New Project</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Project Name</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="e.g. Phase 2 Automation"
                value={projName}
                onChange={(e) => setProjName(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Description</label>
              <textarea
                className="input-field"
                rows={3}
                placeholder="Brief description of project goals..."
                value={projDesc}
                onChange={(e) => setProjDesc(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Theme Color</label>
              <div style={{ display: 'flex', gap: '12px' }}>
                {colors.map(c => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setProjColor(c)}
                    style={{ width: '28px', height: '28px', borderRadius: '50%', background: c, border: projColor === c ? '2px solid white' : 'none', cursor: 'pointer', boxShadow: projColor === c ? '0 0 10px rgba(255,255,255,0.4)' : 'none', transition: 'all 0.1s' }}
                  />
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
              <button type="button" className="btn-secondary" onClick={() => setShowProjModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Create Project</button>
            </div>
          </form>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
          <form onSubmit={handleInviteUser} className="glass-panel" style={{ padding: '28px', width: '400px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>Invite Team Member</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Email Address</label>
              <input
                type="email"
                required
                className="input-field"
                placeholder="colleague@example.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Organization Role</label>
              <select
                className="input-field"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
                <option value="guest">Guest</option>
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
              <button type="button" className="btn-secondary" onClick={() => setShowInviteModal(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Send Invitation</button>
            </div>
          </form>
        </div>
      )}

      {/* Delete Project Confirm Modal */}
      {deleteConfirmProj && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="glass-panel" style={{ padding: '28px', width: '420px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle /> Delete Project
            </h3>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Are you sure you want to delete project <strong>{deleteConfirmProj.name}</strong>? This action is permanent.</p>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              <input
                type="checkbox"
                id="cascade"
                checked={cascadeDelete}
                onChange={(e) => setCascadeDelete(e.target.checked)}
                style={{ cursor: 'pointer', width: '16px', height: '16px' }}
              />
              <label htmlFor="cascade" style={{ fontSize: '13px', cursor: 'pointer', userSelect: 'none' }}>
                Cascade Delete (Delete all tasks in project)
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
              <button className="btn-secondary" onClick={() => { setDeleteConfirmProj(null); setCascadeDelete(false); }}>Cancel</button>
              <button className="btn-danger" onClick={handleDeleteProject}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Project Settings Modal */}
      {showConfigProj && (
        <ProjectSettingsModal 
          project={showConfigProj} 
          onClose={() => { setShowConfigProj(null); fetchData(); }} 
        />
      )}
    </div>
  );
}

function ProjectSettingsModal({ project, onClose }) {
  const { activeOrg } = useAuth();
  const [activeTab, setActiveTab] = useState('general');
  
  // General Info states
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || '');
  const [color, setColor] = useState(project.color || '#6366f1');
  const [statusVal, setStatusVal] = useState(project.status || 'ACTIVE');

  // Statuses states
  const [statuses, setStatuses] = useState([]);
  const [statusName, setStatusName] = useState('');
  const [statusColor, setStatusColor] = useState('#6366f1');
  const [statusPosition, setStatusPosition] = useState(0);
  const [loadingStatuses, setLoadingStatuses] = useState(false);

  // Workflow Rules states
  const [fromStatus, setFromStatus] = useState('');
  const [toStatus, setToStatus] = useState('');
  const [workflowRules, setWorkflowRules] = useState([]); // local session list of created rules

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const colors = ['#6366f1', '#a855f7', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

  const fetchStatuses = async () => {
    setLoadingStatuses(true);
    try {
      const data = await api.projects.getStatuses(project.id);
      setStatuses(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingStatuses(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'statuses' || activeTab === 'workflow') {
      fetchStatuses();
    }
  }, [activeTab]);

  const handleUpdateDetails = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await api.projects.update(project.id, { name, description, color });
      setMessage('Project details updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to update project details');
    }
  };

  const handleToggleArchive = async () => {
    setError('');
    setMessage('');
    try {
      const result = await api.projects.archive(project.id);
      setStatusVal(result.status);
      setMessage(`Project ${result.status === 'ARCHIVED' ? 'archived' : 'activated'} successfully!`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to archive/unarchive project');
    }
  };

  const handleCreateStatus = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (!statusName.trim()) return;
    try {
      await api.projects.createStatus(project.id, {
        name: statusName,
        color: statusColor,
        position: parseInt(statusPosition) || 0
      });
      setStatusName('');
      setStatusPosition(0);
      fetchStatuses();
      setMessage('Board column status added successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to create custom status');
    }
  };

  const handleCreateWorkflowRule = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    if (!fromStatus || !toStatus) return;
    try {
      const result = await api.projects.createWorkflowRule(project.id, {
        from_status: fromStatus,
        to_status: toStatus
      });
      setWorkflowRules(prev => [...prev, result]);
      setFromStatus('');
      setToStatus('');
      setMessage('Workflow rule created successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err.message || 'Failed to create workflow rule');
    }
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)' }}>
      <div className="glass-panel" style={{ width: '800px', height: '80vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', borderBottom: '1px solid var(--border-glass)', flexShrink: 0 }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }}>Project Settings: {project.name}</h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Configure columns, rules, and general settings</span>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <X size={20} />
          </button>
        </div>

        {/* Body content (split left sidebar tabs / right panel) */}
        <div style={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
          
          {/* Sidebar Tabs */}
          <div style={{ width: '200px', borderRight: '1px solid var(--border-glass)', background: 'rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', padding: '12px', gap: '4px' }}>
            <button
              onClick={() => setActiveTab('general')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                padding: '10px 12px',
                background: activeTab === 'general' ? 'rgba(255,255,255,0.05)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: activeTab === 'general' ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'general' ? '600' : '400',
                textAlign: 'left',
                cursor: 'pointer'
              }}
            >
              <Settings size={16} /> General Info
            </button>
            <button
              onClick={() => setActiveTab('statuses')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                padding: '10px 12px',
                background: activeTab === 'statuses' ? 'rgba(255,255,255,0.05)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: activeTab === 'statuses' ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'statuses' ? '600' : '400',
                textAlign: 'left',
                cursor: 'pointer'
              }}
            >
              <Sliders size={16} /> Board Columns
            </button>
            <button
              onClick={() => setActiveTab('workflow')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: '100%',
                padding: '10px 12px',
                background: activeTab === 'workflow' ? 'rgba(255,255,255,0.05)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                color: activeTab === 'workflow' ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: activeTab === 'workflow' ? '600' : '400',
                textAlign: 'left',
                cursor: 'pointer'
              }}
            >
              <Sliders size={16} /> Workflow Rules
            </button>
          </div>

          {/* Right Panel Contents */}
          <div style={{ flexGrow: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {message && <div style={{ color: 'var(--success)', fontSize: '13px' }}>{message}</div>}
            {error && <div style={{ color: 'var(--danger)', fontSize: '13px', lineHeight: '1.4' }}>{error}</div>}

            {activeTab === 'general' && (
              <form onSubmit={handleUpdateDetails} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Project Name</label>
                  <input
                    type="text"
                    required
                    className="input-field"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Description</label>
                  <textarea
                    className="input-field"
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Theme Color</label>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="color"
                      value={color}
                      onChange={(e) => setColor(e.target.value)}
                      style={{ border: 'none', background: 'transparent', width: '36px', height: '36px', cursor: 'pointer' }}
                    />
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {colors.map((c) => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setColor(c)}
                          style={{
                            width: '24px',
                            height: '24px',
                            borderRadius: '50%',
                            background: c,
                            border: color === c ? '2px solid white' : 'none',
                            cursor: 'pointer'
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', borderTop: '1px solid var(--border-glass)', paddingTop: '20px' }}>
                  <button
                    type="button"
                    onClick={handleToggleArchive}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      background: 'rgba(245, 158, 11, 0.15)',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      borderRadius: '6px',
                      padding: '8px 16px',
                      color: '#fbbf24',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '600'
                    }}
                  >
                    <Archive size={14} />
                    {statusVal === 'ARCHIVED' ? 'Unarchive Project' : 'Archive Project'}
                  </button>
                  
                  <button type="submit" className="btn-primary">Save Changes</button>
                </div>
              </form>
            )}

            {activeTab === 'statuses' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <form onSubmit={handleCreateStatus} style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600' }}>Add Custom Column/Status</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 100px', gap: '12px' }}>
                    <input
                      type="text"
                      required
                      placeholder="e.g. In Review"
                      className="input-field"
                      value={statusName}
                      onChange={(e) => setStatusName(e.target.value)}
                    />
                    <input
                      type="number"
                      required
                      placeholder="Position (0, 1, 2...)"
                      className="input-field"
                      value={statusPosition}
                      onChange={(e) => setStatusPosition(e.target.value)}
                    />
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <input
                        type="color"
                        value={statusColor}
                        onChange={(e) => setStatusColor(e.target.value)}
                        style={{ border: 'none', background: 'transparent', width: '36px', height: '36px', cursor: 'pointer' }}
                      />
                    </div>
                  </div>
                  <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-start' }}>Add Column</button>
                </form>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600' }}>Current Columns</h4>
                  {loadingStatuses ? (
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Loading statuses...</div>
                  ) : statuses.length === 0 ? (
                    <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No custom statuses. Standard statuses are used.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {statuses.map(st => (
                        <div key={st.id} className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderLeft: `4px solid ${st.color || 'var(--primary)'}` }}>
                          <div>
                            <span style={{ fontWeight: '600', fontSize: '14px' }}>{st.name}</span>
                            <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: '12px' }}>Pos: {st.position}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'workflow' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <form onSubmit={handleCreateWorkflowRule} style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600' }}>Create State Transition Restriction Rule</h4>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>By default, tasks can transition from any status to any other status. Creating rules restricts task transitions only to the configured paths.</p>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>From Status</label>
                      <select
                        className="input-field"
                        required
                        value={fromStatus}
                        onChange={(e) => setFromStatus(e.target.value)}
                      >
                        <option value="">Select status...</option>
                        {/* Always include defaults + custom statuses */}
                        <option value="backlog">Backlog</option>
                        <option value="todo">To Do</option>
                        <option value="in_progress">In Progress</option>
                        <option value="review">Review</option>
                        <option value="done">Done</option>
                        {statuses.map(st => (
                          <option key={st.id} value={st.name.toLowerCase().replace(' ', '_')}>{st.name}</option>
                        ))}
                      </select>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <label style={{ fontSize: '12.5px', color: 'var(--text-secondary)' }}>Allowed To Status</label>
                      <select
                        className="input-field"
                        required
                        value={toStatus}
                        onChange={(e) => setToStatus(e.target.value)}
                      >
                        <option value="">Select status...</option>
                        <option value="backlog">Backlog</option>
                        <option value="todo">To Do</option>
                        <option value="in_progress">In Progress</option>
                        <option value="review">Review</option>
                        <option value="done">Done</option>
                        {statuses.map(st => (
                          <option key={st.id} value={st.name.toLowerCase().replace(' ', '_')}>{st.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-start' }} disabled={!fromStatus || !toStatus}>Create Rule</button>
                </form>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600' }}>Session Configured Rules</h4>
                  {workflowRules.length === 0 ? (
                    <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No workflow rules created in this session.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {workflowRules.map((rule, idx) => (
                        <div key={idx} className="glass-card" style={{ padding: '10px 14px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontWeight: '600', color: 'var(--primary)' }}>{rule.from_status.toUpperCase()}</span>
                          <span style={{ color: 'var(--text-muted)' }}>&rarr;</span>
                          <span style={{ fontWeight: '600', color: 'var(--success)' }}>{rule.to_status.toUpperCase()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
