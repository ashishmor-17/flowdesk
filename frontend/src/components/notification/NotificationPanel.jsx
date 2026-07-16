import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { 
  Bell, 
  Check, 
  CheckCheck, 
  Info, 
  AlertCircle, 
  Mail, 
  CheckCircle
} from 'lucide-react';

export default function NotificationPanel({ onNavigateToTask }) {
  const { refreshUserProfile } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const getTaskIdOfNotification = (n) => {
    if (n.payload && n.payload.task_id) {
      return n.payload.task_id;
    }
    if (n.entity_type === 'task' && n.entity_id) {
      return n.entity_id;
    }
    return null;
  };

  const handleNotificationClick = async (n) => {
    // 1. Mark as read if not already read
    if (!n.is_read) {
      try {
        await api.notifications.markRead(n.id);
        setNotifications(prev => 
          prev.map(item => item.id === n.id ? { ...item, is_read: true } : item)
        );
        refreshUserProfile();
      } catch (err) {
        console.error("Failed to mark notification as read:", err);
      }
    }

    // 2. Navigate if there is a target task
    const taskId = getTaskIdOfNotification(n);
    if (taskId && onNavigateToTask) {
      onNavigateToTask(taskId);
    }
  };

  const fetchNotifications = async (cursorVal = null) => {
    setLoading(true);
    try {
      const data = await api.notifications.list(20, cursorVal);
      if (cursorVal) {
        setNotifications(prev => [...prev, ...data.notifications]);
      } else {
        setNotifications(data.notifications);
      }
      setCursor(data.next_cursor);
      setHasMore(!!data.next_cursor);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleAcceptInviteInline = async (token, notificationId) => {
    try {
      await api.org.acceptInvite(token);
      await api.notifications.markRead(notificationId);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setMessage('Joined organization successfully!');
      setTimeout(() => setMessage(''), 3000);
      refreshUserProfile();
    } catch (err) {
      console.error(err);
      setMessage(err.message || 'Failed to accept invitation.');
      setTimeout(() => setMessage(''), 5000);
    }
  };

  const getNotificationDetails = (n) => {
    const p = n.payload || {};
    switch (n.type) {
      case 'task_assigned':
        return {
          title: 'Task Assigned',
          message: `${p.assigned_by_name || 'Someone'} assigned you the task "${p.task_title || 'Untitled'}"`,
        };
      case 'task_unassigned':
        return {
          title: 'Task Unassigned',
          message: `${p.unassigned_by_name || 'Someone'} unassigned you from the task "${p.task_title || 'Untitled'}"`,
        };
      case 'task_status_change':
        return {
          title: 'Status Updated',
          message: `${p.changed_by_name || 'Someone'} changed status of "${p.task_title || 'Untitled'}" to ${p.new_status ? p.new_status.toUpperCase().replace(/_/g, ' ') : ''}`,
        };
      case 'task_comment_added':
        return {
          title: 'New Comment',
          message: `${p.author_name || 'Someone'} commented on "${p.task_title || 'Untitled'}": "${p.preview || ''}"`,
        };
      case 'task_overdue':
        return {
          title: 'Task Overdue',
          message: `The task "${p.task_title || 'Untitled'}" was due on ${p.due_date}`,
        };
      case 'mention':
        return {
          title: 'Mentioned in Comment',
          message: `${p.mentioned_by_name || 'Someone'} mentioned you in a comment on "${p.task_title || 'Untitled'}": "${p.preview || ''}"`,
        };
      case 'org_invite':
        return {
          title: 'Workspace Invitation',
          message: `${p.invited_by_name || 'Someone'} invited you to join organization "${p.org_name || 'Acme'}"`,
          invitation_token: p.token,
          org_name: p.org_name
        };
      case 'automation':
        return {
          title: 'Automation Alert',
          message: p.message || `Rule "${p.rule_name}" triggered.`,
        };
      case 'sla_warning':
        return {
          title: 'SLA Warning',
          message: `SLA warning for task "${p.task_title || 'Untitled'}". Deadline: ${p.deadline ? new Date(p.deadline).toLocaleString() : ''}`,
        };
      case 'sla_breached':
        return {
          title: 'SLA Breached',
          message: `SLA breached for task "${p.task_title || 'Untitled'}". Deadline: ${p.deadline ? new Date(p.deadline).toLocaleString() : ''}`,
        };
      case 'approval_requested':
        return {
          title: 'Approval Requested',
          message: p.message || `Approval requested for task.`,
        };
      case 'approval_decided':
        return {
          title: 'Approval Decision',
          message: p.message || `Approval request decided: ${p.status}.`,
        };
      case 'role_changed':
        return {
          title: 'Role Updated',
          message: `Your role in "${p.org_name || 'Organization'}" has been updated to ${p.new_role || 'Member'} by ${p.updated_by_name || 'Owner'}.`,
        };
      default:
        return {
          title: n.type ? n.type.replace(/_/g, ' ').toUpperCase() : 'Notification',
          message: p.message || p.preview || JSON.stringify(p),
        };
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await api.notifications.markRead(id);
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
      refreshUserProfile();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.notifications.markAllRead();
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true }))
      );
      refreshUserProfile();
      setMessage('All notifications marked as read.');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error(err);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'task_assigned': return <Bell size={18} color="var(--primary)" />;
      case 'task_status_change': return <Info size={18} color="var(--secondary)" />;
      case 'task_comment_added': return <Mail size={18} color="var(--accent)" />;
      case 'task_overdue': return <AlertCircle size={18} color="var(--danger)" />;
      default: return <Bell size={18} color="var(--text-secondary)" />;
    }
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', flexGrow: 1, height: '100vh', width: '100%', overflowY: 'auto' }} className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Bell size={28} /> Notification Feed
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Stay informed on updates, comments, and task deadlines.</p>
        </div>

        {notifications.some(n => !n.is_read) && (
          <button className="btn-secondary" onClick={handleMarkAllRead} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCheck size={16} /> Mark All as Read
          </button>
        )}
      </div>

      {message && (
        <div className="glass-panel" style={{ padding: '10px 20px', background: 'rgba(16, 185, 129, 0.1)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#34d399', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} /> {message}
        </div>
      )}

      {/* List */}
      {loading && notifications.length === 0 ? (
        <div>Loading notifications...</div>
      ) : notifications.length === 0 ? (
        <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          You have no notifications yet.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '800px' }}>
          {notifications.map(n => {
            const details = getNotificationDetails(n);
            return (
              <div 
                key={n.id} 
                className="glass-card" 
                onClick={() => handleNotificationClick(n)}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between', 
                  padding: '16px 20px',
                  background: n.is_read ? 'rgba(255,255,255,0.01)' : 'rgba(99, 102, 241, 0.04)',
                  borderLeft: n.is_read ? '1px solid var(--border-glass)' : '4px solid var(--primary)',
                  opacity: n.is_read ? 0.75 : 1,
                  cursor: 'pointer',
                  transition: 'background 0.2s, transform 0.2s'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = n.is_read ? 'rgba(255,255,255,0.01)' : 'rgba(99, 102, 241, 0.04)'; }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.03)' }}>
                    {getNotificationIcon(n.type)}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '15px', fontWeight: n.is_read ? '500' : '700', color: 'var(--text-primary)' }}>{details.title}</h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>{details.message}</p>
                    {details.invitation_token && !n.is_read && (
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleAcceptInviteInline(details.invitation_token, n.id); }}
                        className="btn-primary" 
                        style={{ marginTop: '10px', padding: '6px 14px', fontSize: '12px' }}
                      >
                        Accept Invitation
                      </button>
                    )}
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '6px' }}>
                      {new Date(n.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                {!n.is_read && (
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleMarkAsRead(n.id); }}
                    style={{ background: 'transparent', border: '1px solid var(--border-glass)', borderRadius: '6px', padding: '6px', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                    title="Mark as read"
                  >
                    <Check size={16} />
                  </button>
                )}
              </div>
            );
          })}

          {hasMore && (
            <button 
              className="btn-secondary" 
              style={{ alignSelf: 'center', marginTop: '16px', padding: '10px 24px' }}
              onClick={() => fetchNotifications(cursor)}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load More Notifications'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
