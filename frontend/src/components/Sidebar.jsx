import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Trello, 
  Cpu, 
  Bell, 
  LogOut, 
  User,
  FolderOpen
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user, activeOrg, logout } = useAuth();

  return (
    <aside className="glass-panel" style={{ width: '280px', height: '100vh', display: 'flex', flexDirection: 'column', padding: '24px 16px', borderRadius: '0 24px 24px 0', borderLeft: 'none' }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', paddingLeft: '8px' }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'var(--shadow-neon)' }}>
          <FolderOpen size={20} color="white" />
        </div>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '800', background: 'linear-gradient(135deg, #fff, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Flowdesk</h2>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Automation Hub</span>
        </div>
      </div>

      {/* Workspace Display */}
      {activeOrg && (
        <div style={{ marginBottom: '28px' }}>
          <div className="glass-card" style={{ width: '100%', padding: '12px', background: 'rgba(255,255,255,0.03)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Workspace</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{activeOrg.name}</div>
          </div>
        </div>
      )}

      {/* Navigation Items */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1 }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          style={{
            display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '15px', fontWeight: '500', transition: 'all 0.2s',
            background: activeTab === 'dashboard' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))' : 'transparent',
            color: activeTab === 'dashboard' ? 'var(--text-primary)' : 'var(--text-secondary)',
            boxShadow: activeTab === 'dashboard' ? 'inset 0 0 0 1px var(--border-glass-active)' : 'none'
          }}
        >
          <LayoutDashboard size={18} /> Dashboard
        </button>

        <button
          onClick={() => setActiveTab('kanban')}
          style={{
            display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '15px', fontWeight: '500', transition: 'all 0.2s',
            background: activeTab === 'kanban' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))' : 'transparent',
            color: activeTab === 'kanban' ? 'var(--text-primary)' : 'var(--text-secondary)',
            boxShadow: activeTab === 'kanban' ? 'inset 0 0 0 1px var(--border-glass-active)' : 'none'
          }}
        >
          <Trello size={18} /> Task Board
        </button>

        <button
          onClick={() => setActiveTab('automations')}
          style={{
            display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '15px', fontWeight: '500', transition: 'all 0.2s',
            background: activeTab === 'automations' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))' : 'transparent',
            color: activeTab === 'automations' ? 'var(--text-primary)' : 'var(--text-secondary)',
            boxShadow: activeTab === 'automations' ? 'inset 0 0 0 1px var(--border-glass-active)' : 'none'
          }}
        >
          <Cpu size={18} /> Automations
        </button>

        <button
          onClick={() => setActiveTab('notifications')}
          style={{
            display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', border: 'none', borderRadius: '10px', cursor: 'pointer', fontSize: '15px', fontWeight: '500', transition: 'all 0.2s', width: '100%',
            background: activeTab === 'notifications' ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(168, 85, 247, 0.15))' : 'transparent',
            color: activeTab === 'notifications' ? 'var(--text-primary)' : 'var(--text-secondary)',
            boxShadow: activeTab === 'notifications' ? 'inset 0 0 0 1px var(--border-glass-active)' : 'none'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexGrow: 1 }}>
            <Bell size={18} /> Notifications
          </div>
          {user?.unread_notifications_count > 0 && (
            <span style={{ background: 'var(--danger)', color: 'white', fontSize: '11px', fontWeight: '700', padding: '2px 6px', borderRadius: '20px', boxShadow: '0 0 10px rgba(239, 68, 68, 0.5)' }}>
              {user.unread_notifications_count}
            </span>
          )}
        </button>
      </nav>

      {/* User info & Signout */}
      {user && (
        <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '8px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={18} color="var(--text-secondary)" />
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.first_name} {user.last_name || ''}</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.email}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="btn-secondary"
            style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px' }}
          >
            <LogOut size={16} /> Log Out
          </button>
        </div>
      )}
    </aside>
  );
}
