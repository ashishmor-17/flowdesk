import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';
import Auth from './components/auth/Auth';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './components/dashboard/Dashboard';
import TaskBoard from './components/task/TaskBoard';
import AutomationBuilder from './components/automation/AutomationBuilder';
import NotificationPanel from './components/notification/NotificationPanel';
import Settings from './components/settings/Settings';
import AdminPortal from './components/admin/AdminPortal';
import { Briefcase } from 'lucide-react';

function AppContent() {
  const { user, activeOrg, loading, createOrg, refreshUserProfile } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [initialOpenTaskId, setInitialOpenTaskId] = useState(null);
  
  const [orgName, setOrgName] = useState('');
  const [orgSlug, setOrgSlug] = useState('');
  const [inviteToken, setInviteToken] = useState('');
  const [orgError, setOrgError] = useState('');
  const [orgLoading, setOrgLoading] = useState(false);
  const [pendingInvites, setPendingInvites] = useState([]);

  React.useEffect(() => {
    if (user && !activeOrg) {
      api.notifications.list(10)
        .then(data => {
          const invites = (data.notifications || []).filter(n => n.type === 'org_invite' && !n.is_read);
          setPendingInvites(invites);
        })
        .catch(err => console.error('Failed to load pending invitations:', err));
    }
  }, [user, activeOrg]);

  const handleCreateInitialOrg = async (e) => {
    e.preventDefault();
    setOrgError('');
    setOrgLoading(true);
    try {
      await createOrg(orgName, orgSlug);
    } catch (err) {
      setOrgError(err.message || 'Failed to create workspace');
    } finally {
      setOrgLoading(false);
    }
  };

  const handleAcceptInvite = async (e) => {
    e.preventDefault();
    setOrgError('');
    setOrgLoading(true);
    try {
      await api.org.acceptInvite(inviteToken);
      await refreshUserProfile();
    } catch (err) {
      setOrgError(err.message || 'Failed to accept invitation. Please check the token.');
    } finally {
      setOrgLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-dark)' }}>
        <div style={{ width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.05)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '16px' }} />
        <span style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Initializing Flowdesk...</span>
      </div>
    );
  }

  if (!user) {
    return <Auth />;
  }

  if (!activeOrg) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(circle at top right, rgba(99, 102, 241, 0.1), transparent 60%), var(--bg-dark)' }}>
        <div className="glass-panel" style={{ width: '450px', padding: '40px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto', boxShadow: 'var(--shadow-neon)' }}>
              <Briefcase size={28} color="white" />
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: '800' }}>Setup Your Workspace</h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px' }}>To start automating tasks, you need to create your first organization workspace.</p>
          </div>

          {orgError && <div style={{ color: 'var(--danger)', fontSize: '13px' }}>{orgError}</div>}

          <form onSubmit={handleCreateInitialOrg} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Organization Name</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="e.g. Acme Corporation"
                value={orgName}
                onChange={(e) => {
                  setOrgName(e.target.value);
                  setOrgSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''));
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Slug / URL key</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="e.g. acme-corporation"
                value={orgSlug}
                onChange={(e) => setOrgSlug(e.target.value)}
              />
            </div>

            <button type="submit" className="btn-primary" style={{ padding: '12px', marginTop: '8px' }} disabled={orgLoading}>
              {orgLoading ? 'Creating Workspace...' : 'Create Workspace'}
            </button>
          </form>

          {pendingInvites.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '16px', borderRadius: '8px', marginTop: '8px' }}>
              <div style={{ fontSize: '13px', fontWeight: '750', color: 'var(--primary)' }}>Pending Workspace Invitations</div>
              {pendingInvites.map(n => {
                const p = n.payload || {};
                return (
                  <div key={n.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                    <div>
                      {p.invited_by_name || 'Someone'} invited you to join <strong>{p.org_name || 'Organization'}</strong>.
                    </div>
                    <button
                      type="button"
                      className="btn-primary"
                      style={{ padding: '6px 12px', fontSize: '12px', alignSelf: 'flex-start' }}
                      onClick={async () => {
                        setOrgLoading(true);
                        setOrgError('');
                        try {
                          await api.org.acceptInvite(p.token);
                          await api.notifications.markRead(n.id);
                          await refreshUserProfile();
                        } catch (err) {
                          setOrgError(err.message || 'Failed to accept invitation.');
                        } finally {
                          setOrgLoading(false);
                        }
                      }}
                    >
                      Accept and Join
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          <div style={{ textAlign: 'center', margin: '8px 0', color: 'var(--text-muted)', fontSize: '13px' }}>— OR —</div>

          <form onSubmit={handleAcceptInvite} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Have an Invite Token?</label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="Enter One-Time Invite Token (OTP)"
                value={inviteToken}
                onChange={(e) => setInviteToken(e.target.value)}
              />
            </div>

            <button type="submit" className="btn-secondary" style={{ padding: '12px', marginTop: '8px' }} disabled={orgLoading}>
              {orgLoading ? 'Joining...' : 'Join Organization'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'kanban':
        return (
          <TaskBoard 
            initialOpenTaskId={initialOpenTaskId} 
            onClearInitialOpenTaskId={() => setInitialOpenTaskId(null)} 
          />
        );
      case 'automations':
        return <AutomationBuilder />;
      case 'notifications':
        return (
          <NotificationPanel 
            onNavigateToTask={(taskId) => {
              setInitialOpenTaskId(taskId);
              setActiveTab('kanban');
            }} 
          />
        );
      case 'settings':
        return <Settings />;
      case 'admin':
        return (user?.role?.toUpperCase() === 'OWNER' || user?.role?.toUpperCase() === 'ADMIN') ? <AdminPortal /> : <Dashboard />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', background: 'var(--bg-dark)', overflow: 'hidden' }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {renderTabContent()}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
