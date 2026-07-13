import React, { createContext, useState, useEffect, useContext } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [activeOrg, setActiveOrg] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProfileAndOrgs = async () => {
    try {
      // Fetch /me profile details directly
      const res = await fetch('http://localhost:8000/api/v1/me', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (!res.ok) throw new Error('Unauthenticated');
      const profile = await res.json();

      setUser(profile);

      if (profile.org_id) {
        const orgInfo = { id: profile.org_id, name: profile.org_name || 'My Organization' };
        setActiveOrg(orgInfo);
        localStorage.setItem('active_org_id', profile.org_id);
      } else {
        setActiveOrg(null);
        localStorage.removeItem('active_org_id');
      }
    } catch (err) {
      console.error('Session verification failed:', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchProfileAndOrgs();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const data = await api.auth.login(email, password);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      await fetchProfileAndOrgs();
      return data;
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const signup = async (email, password, firstName, lastName) => {
    setLoading(true);
    try {
      const data = await api.auth.signup(email, password, firstName, lastName);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      await fetchProfileAndOrgs();
      return data;
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await api.auth.logout(refreshToken);
      } catch (_) {}
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_org_id');
    setUser(null);
    setActiveOrg(null);
    setLoading(false);
  };

  const createOrg = async (name, slug) => {
    const newOrg = await api.org.create(name, slug);
    const orgInfo = { id: newOrg.id, name: newOrg.name };
    setActiveOrg(orgInfo);
    localStorage.setItem('active_org_id', newOrg.id);
    
    // Refresh user profile to ensure the database link is fully synced on the user state
    await fetchProfileAndOrgs();
    return newOrg;
  };

  return (
    <AuthContext.Provider value={{ user, activeOrg, loading, login, signup, logout, createOrg, refreshUserProfile: fetchProfileAndOrgs }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
