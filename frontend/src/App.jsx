import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Auth from './components/Auth';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import KanbanBoard from './components/KanbanBoard';
import AutomationBuilder from './components/AutomationBuilder';
import NotificationPanel from './components/NotificationPanel';
import { Briefcase } from 'lucide-react';

function AppContent() {
  const { user, activeOrg, loading, createOrg } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  
  const [orgName, setOrgName] = useState('');
  const [orgSlug, setOrgSlug] = useState('');
  const [orgError, setOrgError] = useState('');
  const [orgLoading, setOrgLoading] = useState(false);

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
        </div>
      </div>
    );
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'kanban':
        return <KanbanBoard />;
      case 'automations':
        return <AutomationBuilder />;
      case 'notifications':
        return <NotificationPanel />;
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
