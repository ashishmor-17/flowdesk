import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { 
  Shield, 
  User, 
  Users, 
  Clock, 
  FileText, 
  Trash2, 
  UserPlus, 
  UserMinus, 
  Plus, 
  CheckCircle, 
  AlertCircle,
  Mail,
  ShieldCheck
} from 'lucide-react';

export default function AdminPortal() {
  const { user, activeOrg, refreshUserProfile } = useAuth();
  const [activeTab, setActiveTab] = useState('members');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // State collections
  const [members, setMembers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [slaPolicies, setSlaPolicies] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);

  // Form states
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [newTeamName, setNewTeamName] = useState('');
  const [newSlaName, setNewSlaName] = useState('');
  const [newSlaPriority, setNewSlaPriority] = useState('medium');
  const [newSlaDuration, setNewSlaDuration] = useState(60);

  // Selection states for team membership additions
  const [selectedTeamForUser, setSelectedTeamForUser] = useState({});

  const showFeedback = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 4000);
  };

  // Determine current user's role in the organization
  const currentUserRole = (user?.role || 'MEMBER').toUpperCase();

  // Fetch initial data based on active tab
  useEffect(() => {
    if (activeTab === 'members') {
      fetchMembersAndTeams();
    } else if (activeTab === 'teams') {
      fetchTeamsAndMembers();
    } else if (activeTab === 'sla') {
      fetchSlaPolicies();
    } else if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab]);

  const fetchMembersAndTeams = async () => {
    setLoading(true);
    try {
      const [membersData, teamsData] = await Promise.all([
        api.org.getMembers(),
        api.org.listTeams()
      ]);
      setMembers(membersData.members || membersData);
      setTeams(teamsData);
    } catch (err) {
      console.error(err);
      showFeedback(err.message || 'Failed to load member and team details', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamsAndMembers = async () => {
    setLoading(true);
    try {
      const [teamsData, membersData] = await Promise.all([
        api.org.listTeams(),
        api.org.getMembers()
      ]);
      setTeams(teamsData);
      setMembers(membersData.members || membersData);
    } catch (err) {
      console.error(err);
      showFeedback(err.message || 'Failed to load team data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchSlaPolicies = async () => {
    setLoading(true);
    try {
      const data = await api.org.listSLAPolicies();
      setSlaPolicies(data);
    } catch (err) {
      console.error(err);
      showFeedback(err.message || 'Failed to load SLA policies', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const data = await api.org.getAuditLogs();
      setAuditLogs(data);
    } catch (err) {
      console.error(err);
      showFeedback(err.message || 'Failed to load audit logs', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Member Handlers
  const handleInviteUser = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setLoading(true);
    try {
      await api.org.invite(inviteEmail, inviteRole);
      setInviteEmail('');
      setInviteRole('member');
      showFeedback('Invitation sent successfully!');
      fetchMembersAndTeams();
    } catch (err) {
      showFeedback(err.message || 'Failed to send invitation', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (userId, userEmail, userRole) => {
    if (userId === user.id) {
      showFeedback('You cannot remove yourself. To leave, please contact another owner.', 'error');
      return;
    }

    const targetRole = (userRole || '').toUpperCase();

    // Role-based validations
    if (currentUserRole === 'ADMIN' && (targetRole === 'OWNER' || targetRole === 'ADMIN')) {
      showFeedback('Admins cannot remove Owners or other Admins.', 'error');
      return;
    }

    if (targetRole === 'OWNER') {
      const ownerCount = members.filter(m => (m.role || '').toUpperCase() === 'OWNER').length;
      if (ownerCount <= 1) {
        showFeedback('The organization must have at least one Owner.', 'error');
        return;
      }
    }

    if (!confirm(`Are you sure you want to remove ${userEmail} from this organization?`)) return;

    setLoading(true);
    try {
      await api.org.removeMember(userId);
      showFeedback('Member removed successfully.');
      fetchMembersAndTeams();
    } catch (err) {
      showFeedback(err.message || 'Failed to remove member', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUserToTeam = async (userId, teamId) => {
    if (!teamId) return;
    setLoading(true);
    try {
      await api.org.addTeamMember(teamId, userId);
      showFeedback('User added to team.');
      fetchMembersAndTeams();
    } catch (err) {
      showFeedback(err.message || 'Failed to add user to team', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUserFromTeam = async (userId, teamId) => {
    setLoading(true);
    try {
      await api.org.removeTeamMember(teamId, userId);
      showFeedback('User removed from team.');
      fetchMembersAndTeams();
    } catch (err) {
      showFeedback(err.message || 'Failed to remove user from team', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Teams Handlers
  const handleCreateTeam = async (e) => {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    setLoading(true);
    try {
      await api.org.createTeam(newTeamName);
      setNewTeamName('');
      await fetchTeamsAndMembers();
      showFeedback('Team created successfully!');
    } catch (err) {
      showFeedback(err.message || 'Failed to create team', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTeam = async (teamId) => {
    if (!confirm('Are you sure you want to delete this team?')) return;
    setLoading(true);
    try {
      await api.org.deleteTeam(teamId);
      await fetchTeamsAndMembers();
      showFeedback('Team deleted.');
    } catch (err) {
      showFeedback(err.message || 'Failed to delete team', 'error');
    } finally {
      setLoading(false);
    }
  };

  // SLA Handlers
  const handleCreateSla = async (e) => {
    e.preventDefault();
    if (!newSlaName.trim()) return;
    setLoading(true);
    try {
      await api.org.createSLAPolicy({
        name: newSlaName,
        priority: newSlaPriority,
        duration_minutes: parseInt(newSlaDuration)
      });
      setNewSlaName('');
      setNewSlaDuration(60);
      await fetchSlaPolicies();
      showFeedback('SLA Policy created successfully!');
    } catch (err) {
      showFeedback(err.message || 'Failed to create SLA Policy', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', flexGrow: 1, height: '100vh', width: '100%', overflowY: 'auto' }} className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield size={28} color="var(--primary)" /> Workspace Admin Portal
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Manage workspace members, role definitions, team rosters, operational SLAs, and audit history.
        </p>
      </div>

      {message.text && (
        <div 
          className="glass-panel animate-fade-in" 
          style={{ 
            padding: '12px 20px', 
            background: message.type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', 
            borderColor: message.type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)', 
            color: message.type === 'error' ? '#f87171' : '#34d399', 
            borderRadius: '8px', 
            marginBottom: '24px', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '10px' 
          }}
        >
          {message.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
          <span style={{ fontSize: '14px', fontWeight: '500' }}>{message.text}</span>
        </div>
      )}

      {/* Admin Tab Switcher */}
      <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', marginBottom: '28px' }}>
        <button 
          onClick={() => setActiveTab('members')} 
          className={`btn-secondary ${activeTab === 'members' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', background: activeTab === 'members' ? 'rgba(255,255,255,0.08)' : 'transparent', borderColor: activeTab === 'members' ? 'var(--primary)' : 'transparent' }}
        >
          <User size={16} /> Members
        </button>

        <button 
          onClick={() => setActiveTab('teams')} 
          className={`btn-secondary ${activeTab === 'teams' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', background: activeTab === 'teams' ? 'rgba(255,255,255,0.08)' : 'transparent', borderColor: activeTab === 'teams' ? 'var(--primary)' : 'transparent' }}
        >
          <Users size={16} /> Teams
        </button>

        <button 
          onClick={() => setActiveTab('sla')} 
          className={`btn-secondary ${activeTab === 'sla' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', background: activeTab === 'sla' ? 'rgba(255,255,255,0.08)' : 'transparent', borderColor: activeTab === 'sla' ? 'var(--primary)' : 'transparent' }}
        >
          <Clock size={16} /> SLA Targets
        </button>

        <button 
          onClick={() => setActiveTab('audit')} 
          className={`btn-secondary ${activeTab === 'audit' ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', background: activeTab === 'audit' ? 'rgba(255,255,255,0.08)' : 'transparent', borderColor: activeTab === 'audit' ? 'var(--primary)' : 'transparent' }}
        >
          <FileText size={16} /> Audit Trail
        </button>
      </div>

      {/* Tab Panels */}
      <div style={{ flexGrow: 1 }}>
        {/* MEMBERS PANEL */}
        {activeTab === 'members' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '32px', alignItems: 'start' }} className="animate-fade-in">
            {/* Members List */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', marginBottom: '16px' }}>
                Workspace Roster
              </h3>
              {loading && members.length === 0 ? (
                <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>Loading members...</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {members.map(m => {
                    // Find teams this member belongs to
                    const userTeams = teams.filter(t => t.member_ids?.includes(m.user_id || m.id));
                    
                    return (
                      <div 
                        key={m.user_id || m.id} 
                        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border-glass)' }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontWeight: '600', fontSize: '15px' }}>{m.full_name || 'No Name'}</span>
                            {currentUserRole === 'OWNER' && (m.user_id || m.id) !== user.id ? (
                              <select
                                value={(m.role || '').toLowerCase()}
                                onChange={async (e) => {
                                  const targetRole = e.target.value;
                                  if (targetRole === 'owner') {
                                    const transferConfirm = window.confirm(`Are you sure you want to transfer ownership to ${m.full_name || m.email}? This will make them the Owner of the organization.`);
                                    if (!transferConfirm) return;
                                    
                                    const leaveChoice = window.confirm(`Do you want to remain in the organization as an Admin? \n\nClick OK to stay as Admin, or click Cancel to leave the organization.`);
                                    const action = leaveChoice ? 'admin' : 'leave';
                                    
                                    setLoading(true);
                                    try {
                                      await api.org.updateMemberRole(m.user_id || m.id, 'owner', action);
                                      showFeedback('Ownership transferred successfully!');
                                      await refreshUserProfile();
                                      fetchMembersAndTeams();
                                    } catch (err) {
                                      showFeedback(err.message || 'Failed to transfer ownership', 'error');
                                    } finally {
                                      setLoading(false);
                                    }
                                  } else {
                                    setLoading(true);
                                    try {
                                      await api.org.updateMemberRole(m.user_id || m.id, targetRole);
                                      showFeedback(`Role updated to ${targetRole.toUpperCase()}!`);
                                      fetchMembersAndTeams();
                                    } catch (err) {
                                      showFeedback(err.message || 'Failed to update role', 'error');
                                    } finally {
                                      setLoading(false);
                                    }
                                  }
                                }}
                                className="input-field"
                                style={{ padding: '2px 8px', fontSize: '11px', background: 'var(--bg-dark)', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', height: '24px' }}
                              >
                                <option value="member">MEMBER</option>
                                <option value="admin">ADMIN</option>
                                <option value="owner">OWNER</option>
                              </select>
                            ) : (
                              <span style={{ fontSize: '10px', textTransform: 'uppercase', background: (m.role || '').toUpperCase() === 'OWNER' ? 'rgba(168, 85, 247, 0.15)' : (m.role || '').toUpperCase() === 'ADMIN' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255,255,255,0.05)', color: (m.role || '').toUpperCase() === 'OWNER' ? 'var(--secondary)' : (m.role || '').toUpperCase() === 'ADMIN' ? 'var(--primary)' : 'var(--text-secondary)', padding: '2px 8px', borderRadius: '4px', fontWeight: '600' }}>
                                {m.role}
                              </span>
                            )}
                          </div>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{m.email}</span>
                          
                          {/* User's Teams list */}
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                            {userTeams.map(t => (
                              <span 
                                key={t.id} 
                                style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)', color: 'var(--primary)', padding: '2px 6px', borderRadius: '4px' }}
                              >
                                {t.name}
                                <button 
                                  onClick={() => handleRemoveUserFromTeam(m.user_id || m.id, t.id)}
                                  style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: 0, fontSize: '9px', display: 'flex', alignItems: 'center' }}
                                  title="Remove from Team"
                                >
                                  ×
                                </button>
                              </span>
                            ))}
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          {/* Manage Teams dropdown */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <select 
                              value={selectedTeamForUser[m.user_id || m.id] || ''}
                              onChange={e => setSelectedTeamForUser(prev => ({ ...prev, [m.user_id || m.id]: e.target.value }))}
                              className="input-field"
                              style={{ width: '150px', padding: '6px 10px', fontSize: '12px', background: 'var(--bg-dark)' }}
                            >
                              <option value="">Add to team...</option>
                              {teams.map(t => {
                                if (t.member_ids?.includes(m.user_id || m.id)) return null;
                                return <option key={t.id} value={t.id}>{t.name}</option>;
                              })}
                            </select>
                            <button 
                              onClick={() => {
                                const tId = selectedTeamForUser[m.user_id || m.id];
                                handleAddUserToTeam(m.user_id || m.id, tId);
                                setSelectedTeamForUser(prev => ({ ...prev, [m.user_id || m.id]: '' }));
                              }}
                              className="btn-secondary"
                              style={{ padding: '6px 10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                              disabled={!selectedTeamForUser[m.user_id || m.id]}
                            >
                              <Plus size={14} />
                            </button>
                          </div>

                          {/* Delete Member button */}
                          {(m.user_id || m.id) !== user.id && (
                            <button 
                              onClick={() => handleRemoveMember(m.user_id || m.id, m.email, m.role)}
                              style={{ 
                                background: 'transparent', 
                                border: '1px solid rgba(239, 68, 68, 0.2)', 
                                padding: '8px', 
                                color: '#f87171', 
                                borderRadius: '8px', 
                                cursor: 'pointer', 
                                display: 'flex', 
                                alignItems: 'center',
                                opacity: (currentUserRole === 'ADMIN' && ((m.role || '').toUpperCase() === 'OWNER' || (m.role || '').toUpperCase() === 'ADMIN')) ? 0.3 : 1
                              }}
                              disabled={currentUserRole === 'ADMIN' && ((m.role || '').toUpperCase() === 'OWNER' || (m.role || '').toUpperCase() === 'ADMIN')}
                              title="Remove Member from Org"
                            >
                              <Trash2 size={15} />
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Invite Panel */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <UserPlus size={18} color="var(--primary)" /> Invite Member
              </h3>
              <form onSubmit={handleInviteUser} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Email Address</label>
                  <div style={{ position: 'relative' }}>
                    <Mail size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input 
                      type="email" 
                      required 
                      className="input-field" 
                      placeholder="teammate@company.com" 
                      value={inviteEmail} 
                      onChange={e => setInviteEmail(e.target.value)}
                      style={{ paddingLeft: '38px' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Organization Role</label>
                  <select 
                    value={inviteRole} 
                    onChange={e => setInviteRole(e.target.value)} 
                    className="input-field"
                    style={{ background: 'var(--bg-dark)' }}
                  >
                    <option value="member">Member (Regular Access)</option>
                    <option value="admin">Admin (Manage Ops/SLA/Teams)</option>
                  </select>
                </div>

                <button type="submit" className="btn-primary" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px' }} disabled={loading}>
                  <UserPlus size={16} /> Send Invitation
                </button>
              </form>
            </div>
          </div>
        )}

        {/* TEAMS PANEL */}
        {activeTab === 'teams' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px' }} className="animate-fade-in">
            {/* Create Team Card */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={18} /> Create New Operational Team
              </h3>
              <form onSubmit={handleCreateTeam} style={{ display: 'flex', gap: '12px' }}>
                <input 
                  type="text" 
                  required 
                  className="input-field" 
                  placeholder="e.g. Frontend Engineering, Customer Support" 
                  value={newTeamName}
                  onChange={e => setNewTeamName(e.target.value)}
                  style={{ maxWidth: '400px' }}
                />
                <button type="submit" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} disabled={loading}>
                  Create Team
                </button>
              </form>
            </div>

            {/* Teams List */}
            {teams.length === 0 ? (
              <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No teams configured in this organization.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {teams.map(team => (
                  <div key={team.id} className="glass-panel" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', marginBottom: '16px' }}>
                      <div>
                        <h4 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)' }}>{team.name}</h4>
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          Created: {new Date(team.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <button 
                        onClick={() => handleDeleteTeam(team.id)} 
                        style={{ background: 'transparent', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '8px', color: '#f87171', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>

                    {/* Members List */}
                    <div>
                      <h5 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '8px' }}>Roster ({team.member_ids?.length || 0})</h5>
                      {!team.member_ids || team.member_ids.length === 0 ? (
                        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No members assigned to this team.</p>
                      ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {team.member_ids.map(mid => {
                            const u = members.find(member => (member.user_id || member.id) === mid);
                            if (!u) return null;
                            return (
                              <div 
                                key={mid} 
                                style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-glass)' }}
                              >
                                <span style={{ fontSize: '12px' }}>{u.full_name || u.email}</span>
                                <button 
                                  onClick={() => handleRemoveUserFromTeam(mid, team.id)} 
                                  style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
                                  title="Remove from Team"
                                >
                                  <UserMinus size={13} />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SLA PANEL */}
        {activeTab === 'sla' && (
          <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '32px', maxWidth: '1100px' }} className="animate-fade-in">
            {/* Create SLA Policy */}
            <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', height: 'fit-content' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Plus size={18} /> New SLA Target
              </h3>
              <form onSubmit={handleCreateSla} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Policy Label</label>
                  <input 
                    type="text" 
                    required 
                    className="input-field" 
                    value={newSlaName} 
                    onChange={e => setNewSlaName(e.target.value)} 
                    placeholder="e.g. Urgent Incident SLA"
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Trigger Priority</label>
                  <select 
                    value={newSlaPriority} 
                    onChange={e => setNewSlaPriority(e.target.value)} 
                    className="input-field"
                    style={{ background: 'var(--bg-dark)' }}
                  >
                    <option value="low">Low Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="high">High Priority</option>
                  </select>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Target Resolution (Minutes)</label>
                  <input 
                    type="number" 
                    required 
                    min="1" 
                    className="input-field" 
                    value={newSlaDuration} 
                    onChange={e => setNewSlaDuration(e.target.value)}
                  />
                </div>

                <button type="submit" className="btn-primary" style={{ marginTop: '8px' }} disabled={loading}>
                  Save SLA Target
                </button>
              </form>
            </div>

            {/* SLA Policies List */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', marginBottom: '16px' }}>
                Active SLA Targets
              </h3>
              {slaPolicies.length === 0 ? (
                <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No SLA rules configured.
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'left' }}>
                      <th style={{ padding: '12px' }}>Policy Name</th>
                      <th style={{ padding: '12px' }}>Priority Trigger</th>
                      <th style={{ padding: '12px' }}>Resolution Target</th>
                      <th style={{ padding: '12px' }}>Created Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {slaPolicies.map(policy => (
                      <tr key={policy.id} style={{ borderBottom: '1px solid var(--border-glass)', fontSize: '14px' }}>
                        <td style={{ padding: '12px', fontWeight: '600' }}>{policy.name}</td>
                        <td style={{ padding: '12px' }}>
                          <span style={{ 
                            padding: '4px 8px', 
                            borderRadius: '4px', 
                            fontSize: '11px', 
                            fontWeight: '700', 
                            textTransform: 'uppercase',
                            background: policy.priority === 'high' ? 'rgba(239, 68, 68, 0.15)' : policy.priority === 'medium' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: policy.priority === 'high' ? '#f87171' : policy.priority === 'medium' ? '#fbbf24' : '#34d399'
                          }}>
                            {policy.priority}
                          </span>
                        </td>
                        <td style={{ padding: '12px' }}>{policy.duration_minutes} mins</td>
                        <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{new Date(policy.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* AUDIT LOG PANEL */}
        {activeTab === 'audit' && (
          <div className="glass-panel animate-fade-in" style={{ padding: '24px', maxWidth: '1000px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} /> Organization Audit Log
            </h3>
            {auditLogs.length === 0 ? (
              <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No events recorded in the workspace audit logs.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-secondary)', fontSize: '13px', textAlign: 'left' }}>
                      <th style={{ padding: '12px' }}>Timestamp</th>
                      <th style={{ padding: '12px' }}>Actor</th>
                      <th style={{ padding: '12px' }}>Action</th>
                      <th style={{ padding: '12px' }}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map(log => (
                      <tr key={log.id} style={{ borderBottom: '1px solid var(--border-glass)', fontSize: '13px' }}>
                        <td style={{ padding: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', fontWeight: '600' }}>
                          {log.actor_email || log.actor_id || 'System Event'}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', fontSize: '11px', fontFamily: 'monospace' }}>
                            {log.action}
                          </span>
                        </td>
                        <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>
                          {log.description || JSON.stringify(log.payload)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
