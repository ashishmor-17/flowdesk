import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { 
  Settings as SettingsIcon, 
  User, 
  Lock, 
  CheckCircle, 
  AlertCircle,
  Sliders
} from 'lucide-react';

export default function Settings() {
  const { user, refreshUserProfile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  // Account Settings state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [theme, setTheme] = useState(user?.profile?.preferences?.theme || 'dark');
  const [timezone, setTimezone] = useState(user?.profile?.preferences?.timezone || 'UTC');

  const showFeedback = (text, type = 'success') => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 4000);
  };

  // Account Handlers
  const handlePasswordChange = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      showFeedback('New passwords do not match!', 'error');
      return;
    }
    setLoading(true);
    try {
      await api.users.changePassword(oldPassword, newPassword);
      showFeedback('Password changed successfully!');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      showFeedback(err.message || 'Failed to change password', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePreferencesSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.users.updatePreferences({ theme, timezone });
      await refreshUserProfile();
      showFeedback('Preferences updated successfully!');
    } catch (err) {
      showFeedback(err.message || 'Failed to update preferences', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', flexGrow: 1, height: '100vh', width: '100%', overflowY: 'auto' }} className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '800', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <SettingsIcon size={28} /> Account Settings
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Manage your personal account profile, interface theme, and password security.
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

      {/* Grid of Preferences and Password */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '32px', maxWidth: '1000px' }} className="animate-fade-in">
        {/* Preferences Form */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={18} /> Preferences Settings
          </h3>

          <form onSubmit={handlePreferencesSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Display Theme</label>
              <select 
                value={theme} 
                onChange={e => setTheme(e.target.value)} 
                className="input-field"
                style={{ background: 'var(--bg-dark)' }}
              >
                <option value="dark">Dark Theme</option>
                <option value="light">Light Theme</option>
                <option value="glass">Glassmorphism</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Timezone</label>
              <select 
                value={timezone} 
                onChange={e => setTimezone(e.target.value)} 
                className="input-field"
                style={{ background: 'var(--bg-dark)' }}
              >
                <option value="UTC">UTC / Coordinated Universal Time</option>
                <option value="EST">EST / Eastern Standard Time</option>
                <option value="PST">PST / Pacific Standard Time</option>
                <option value="GMT">GMT / Greenwich Mean Time</option>
              </select>
            </div>

            <button type="submit" className="btn-primary" style={{ marginTop: '8px', alignSelf: 'flex-start', padding: '10px 20px' }} disabled={loading}>
              Save Preferences
            </button>
          </form>
        </div>

        {/* Password Form */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Lock size={18} /> Change Password
          </h3>

          <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Current Password</label>
              <input 
                type="password" 
                required 
                className="input-field"
                value={oldPassword} 
                onChange={e => setOldPassword(e.target.value)} 
                placeholder="Enter current password"
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>New Password</label>
              <input 
                type="password" 
                required 
                className="input-field"
                value={newPassword} 
                onChange={e => setNewPassword(e.target.value)} 
                placeholder="Enter new password"
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Confirm New Password</label>
              <input 
                type="password" 
                required 
                className="input-field"
                value={confirmPassword} 
                onChange={e => setConfirmPassword(e.target.value)} 
                placeholder="Confirm new password"
              />
            </div>

            <button type="submit" className="btn-primary" style={{ marginTop: '8px', alignSelf: 'flex-start', padding: '10px 20px' }} disabled={loading}>
              Change Password
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
