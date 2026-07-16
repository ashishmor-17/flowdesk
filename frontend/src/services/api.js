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

  if (headers['Content-Type'] === undefined) {
    delete headers['Content-Type'];
  }

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
    removeMember: (userId) =>
      request(`/org/members/${userId}`, {
        method: 'DELETE'
      }),
    updateMemberRole: (userId, role, actionForPrevOwner = 'admin') =>
      request(`/org/members/${userId}/role`, {
        method: 'PATCH',
        body: JSON.stringify({ role, action_for_prev_owner: actionForPrevOwner })
      }),
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
    listTeams: () => request('/org/teams'),
    createTeam: (name) =>
      request('/org/teams', {
        method: 'POST',
        body: JSON.stringify({ name })
      }),
    addTeamMember: (teamId, userId) =>
      request(`/org/teams/${teamId}/members`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
      }),
    removeTeamMember: (teamId, userId) =>
      request(`/org/teams/${teamId}/members/${userId}`, {
        method: 'DELETE'
      }),
    deleteTeam: (teamId) =>
      request(`/org/teams/${teamId}`, {
        method: 'DELETE'
      }),
    createSLAPolicy: (policyData) =>
      request('/org/sla-policies', {
        method: 'POST',
        body: JSON.stringify(policyData)
      }),
    listSLAPolicies: () => request('/org/sla-policies'),
    getAuditLogs: () => request('/org/audit-logs'),
    delete: () => request('/org', { method: 'DELETE' }),
  },
  projects: {
    list: () => request('/projects'),
    create: (name, description, color) =>
      request('/projects', {
        method: 'POST',
        body: JSON.stringify({ name, description, color })
      }),
    get: (projectId) => request(`/projects/${projectId}`),
    update: (projectId, projectData) =>
      request(`/projects/${projectId}`, {
        method: 'PATCH',
        body: JSON.stringify(projectData)
      }),
    archive: (projectId) =>
      request(`/projects/${projectId}/archive`, { method: 'PATCH' }),
    delete: (projectId, cascade = false) =>
      request(`/projects/${projectId}?cascade=${cascade}`, { method: 'DELETE' }),
    getStatuses: (projectId) => request(`/projects/${projectId}/statuses`),
    createStatus: (projectId, statusData) =>
      request(`/projects/${projectId}/statuses`, {
        method: 'POST',
        body: JSON.stringify(statusData)
      }),
    createWorkflowRule: (projectId, ruleData) =>
      request(`/projects/${projectId}/workflow-rules`, {
        method: 'POST',
        body: JSON.stringify(ruleData)
      }),
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
    get: (taskId) => request(`/tasks/${taskId}`),
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
    assign: (taskId, userId) =>
      request(`/tasks/${taskId}/assign`, {
        method: 'PATCH',
        body: JSON.stringify({ assigned_to: userId })
      }),
    addAssignee: (taskId, assigneeData) =>
      request(`/tasks/${taskId}/assignees`, {
        method: 'POST',
        body: JSON.stringify(assigneeData)
      }),
    watch: (taskId) =>
      request(`/tasks/${taskId}/watchers`, { method: 'POST' }),
    unwatch: (taskId, userId) =>
      request(`/tasks/${taskId}/watchers/${userId}`, { method: 'DELETE' }),
    delete: (taskId) =>
      request(`/tasks/${taskId}`, { method: 'DELETE' }),
    listAttachments: (taskId) =>
      request(`/tasks/${taskId}/attachments`),
    uploadAttachment: (taskId, file) => {
      const formData = new FormData();
      formData.append('file', file);
      return request(`/tasks/${taskId}/attachments`, {
        method: 'POST',
        headers: {
          'Content-Type': undefined
        },
        body: formData
      });
    },
    deleteAttachment: (taskId, attachmentId) =>
      request(`/tasks/${taskId}/attachments/${attachmentId}`, {
        method: 'DELETE'
      }),
    getDownloadUrl: (taskId, attachmentId) =>
      `${BASE_URL}/tasks/${taskId}/attachments/${attachmentId}/download?token=${localStorage.getItem('access_token')}`,
    initiateUpload: (taskId, initiateData) =>
      request(`/tasks/${taskId}/attachments/upload/initiate`, {
        method: 'POST',
        body: JSON.stringify(initiateData)
      }),
    uploadPart: (taskId, sessionId, partNumber, file) => {
      const formData = new FormData();
      formData.append('file', file);
      return request(`/tasks/${taskId}/attachments/upload/${sessionId}/parts?part_number=${partNumber}`, {
        method: 'POST',
        headers: {
          'Content-Type': undefined
        },
        body: formData
      });
    },
    completeUpload: (taskId, sessionId) =>
      request(`/tasks/${taskId}/attachments/upload/${sessionId}/complete`, { method: 'POST' }),
    abortUpload: (taskId, sessionId) =>
      request(`/tasks/${taskId}/attachments/upload/${sessionId}/abort`, { method: 'POST' }),
    getUploadProgress: (taskId, sessionId) =>
      request(`/tasks/${taskId}/attachments/upload/${sessionId}`),
    createApproval: (taskId, approverId) =>
      request(`/tasks/${taskId}/approvals`, {
        method: 'POST',
        body: JSON.stringify({ approver_id: approverId })
      }),
    listApprovals: (taskId) =>
      request(`/tasks/${taskId}/approvals`),
    updateApproval: (taskId, approvalId, status, comment = null) =>
      request(`/tasks/${taskId}/approvals/${approvalId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status, comment })
      }),
    createTimeEntry: (taskId, minutes, description = null) =>
      request(`/tasks/${taskId}/time-entries`, {
        method: 'POST',
        body: JSON.stringify({ minutes, description })
      }),
    listTimeEntries: (taskId) =>
      request(`/tasks/${taskId}/time-entries`),
    createLink: (taskId, linkData) =>
      request(`/tasks/${taskId}/links`, {
        method: 'POST',
        body: JSON.stringify(linkData)
      }),
    deleteLink: (taskId, linkId) =>
      request(`/tasks/${taskId}/links/${linkId}`, { method: 'DELETE' }),
    getActivity: (taskId) =>
      request(`/tasks/${taskId}/activity`),
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
    update: (commentId, content) =>
      request(`/comments/${commentId}`, {
        method: 'PATCH',
        body: JSON.stringify({ content })
      }),
    delete: (commentId) =>
      request(`/comments/${commentId}`, { method: 'DELETE' }),
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
    get: (id) => request(`/automation/rules/${id}`),
    update: (id, ruleData) =>
      request(`/automation/rules/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(ruleData)
      }),
    delete: (id) => request(`/automation/rules/${id}`, { method: 'DELETE' }),
    getHistory: (id) => request(`/automation/rules/${id}/history`),
  },
  users: {
    listAll: () => request('/users'),
    getProfile: () => request('/users/me'),
    updateProfile: (profileData) =>
      request('/users/me', {
        method: 'PATCH',
        body: JSON.stringify(profileData)
      }),
    changePassword: (oldPassword, newPassword) =>
      request('/users/me/password', {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      }),
    updatePreferences: (preferences) =>
      request('/users/me', {
        method: 'PATCH',
        body: JSON.stringify({ preferences })
      })
  }
};
