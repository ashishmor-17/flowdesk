const BASE_URL = 'http://localhost:8000/api/v1';

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const orgId = localStorage.getItem('active_org_id');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(orgId && { 'X-Org-Id': orgId }),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !endpoint.includes('/auth/')) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshRes.ok) {
          const refreshData = await refreshRes.json();
          localStorage.setItem('access_token', refreshData.access_token);
          localStorage.setItem('refresh_token', refreshData.refresh_token);
          headers.Authorization = `Bearer ${refreshData.access_token}`;
          const retryRes = await fetch(`${BASE_URL}${endpoint}`, {
            ...options,
            headers,
          });
          return await handleResponse(retryRes);
        }
      } catch (err) {
        console.error('Failed to refresh token:', err);
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.reload();
  }

  return handleResponse(response);
}

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const data = await response.json();
      errorDetail = data.detail || data.message || errorDetail;
      if (typeof errorDetail === 'object') {
        errorDetail = errorDetail.message || JSON.stringify(errorDetail);
      }
    } catch (_) {}
    throw new Error(errorDetail);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  auth: {
    login: (email, password) => 
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      }),
    signup: (email, password, first_name, last_name) =>
      request('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, first_name, last_name })
      }),
    logout: (refreshToken) =>
      request('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken })
      }),
  },
  org: {
    create: (name, slug) =>
      request('/org/create', {
        method: 'POST',
        body: JSON.stringify({ name, slug })
      }),
    getMembers: () => request('/org/members'),
    invite: (email, role) =>
      request('/org/invite-user', {
        method: 'POST',
        body: JSON.stringify({ email, role })
      }),
    acceptInvite: (token) =>
      request('/org/accept-invite', {
        method: 'POST',
        body: JSON.stringify({ token })
      }),
  },
  projects: {
    list: () => request('/projects'),
    create: (name, description, color) =>
      request('/projects', {
        method: 'POST',
        body: JSON.stringify({ name, description, color })
      }),
    archive: (projectId) =>
      request(`/projects/${projectId}/archive`, { method: 'POST' }),
    delete: (projectId, cascade = false) =>
      request(`/projects/${projectId}?cascade=${cascade}`, { method: 'DELETE' }),
  },
  tasks: {
    list: (orgId, projectId, status) => {
      let query = `?org_id=${orgId}`;
      if (projectId) query += `&project_id=${projectId}`;
      if (status) query += `&status=${status}`;
      return request(`/tasks${query}`);
    },
    create: (projectId, title, description, priority, due_date) =>
      request('/tasks', {
        method: 'POST',
        body: JSON.stringify({ project_id: projectId, title, description, priority, due_date })
      }),
    update: (taskId, updateData) =>
      request(`/tasks/${taskId}`, {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      }),
    updateStatus: (taskId, status, version) =>
      request(`/tasks/${taskId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, version })
      }),
    delete: (taskId) =>
      request(`/tasks/${taskId}`, { method: 'DELETE' }),
  },
  comments: {
    list: (taskId, limit = 20, cursor = null) => {
      let query = `?limit=${limit}`;
      if (cursor) query += `&cursor=${cursor}`;
      return request(`/tasks/${taskId}/comments${query}`);
    },
    create: (taskId, content) =>
      request(`/tasks/${taskId}/comments`, {
        method: 'POST',
        body: JSON.stringify({ content })
      }),
  },
  notifications: {
    list: (limit = 20, cursor = null) => {
      let query = `?limit=${limit}`;
      if (cursor) query += `&cursor=${cursor}`;
      return request(`/notifications${query}`);
    },
    getUnreadCount: () => request('/notifications/unread'),
    markRead: (id) => request(`/notifications/${id}/read`, { method: 'PATCH' }),
    markAllRead: () => request('/notifications/read-all', { method: 'PATCH' }),
  },
  automation: {
    list: (projectId = null) => {
      const query = projectId ? `?project_id=${projectId}` : '';
      return request(`/automation/rules${query}`);
    },
    create: (ruleData) =>
      request('/automation/rules', {
        method: 'POST',
        body: JSON.stringify(ruleData)
      }),
    delete: (id) => request(`/automation/rules/${id}`, { method: 'DELETE' }),
  },
  users: {
    listAll: () => request('/users'),
  }
};
