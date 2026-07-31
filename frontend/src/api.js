const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function authHeaders(token, extra = {}) {
  const headers = { ...extra }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

async function parseResponse(response) {
  const text = await response.text()
  let body = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = { detail: text }
  }
  if (!response.ok) {
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || JSON.stringify(item)).join(', ')
      : detail || body?.message || `Request failed (${response.status})`
    throw new Error(message)
  }
  return body
}

export async function apiRequest(path, { method = 'GET', token, body, formData } = {}) {
  const headers = authHeaders(token, formData ? {} : { 'Content-Type': 'application/json' })
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: formData || (body !== undefined ? JSON.stringify(body) : undefined),
  })
  return parseResponse(response)
}

export const api = {
  register: (payload) => apiRequest('/api/auth/register', { method: 'POST', body: payload }),
  login: (payload) => apiRequest('/api/auth/login', { method: 'POST', body: payload }),
  me: (token) => apiRequest('/api/auth/me', { token }),
  listProjects: (token) => apiRequest('/api/projects', { token }),
  createProject: (token, payload) => apiRequest('/api/projects', { method: 'POST', token, body: payload }),
  getDashboard: (token, projectId) => apiRequest(`/api/projects/${projectId}/dashboard`, { token }),
  connectGithub: (token, projectId, repository_url) =>
    apiRequest(`/api/projects/${projectId}/github`, {
      method: 'POST',
      token,
      body: { repository_url },
    }),
  listDocuments: (token, projectId) => apiRequest(`/api/projects/${projectId}/documents`, { token }),
  uploadDocument: (token, projectId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiRequest(`/api/projects/${projectId}/documents`, { method: 'POST', token, formData })
  },
  indexProject: (token, projectId) =>
    apiRequest(`/api/projects/${projectId}/index`, { method: 'POST', token }),
  chat: (token, projectId, question) =>
    apiRequest('/api/chat', { method: 'POST', token, body: { project_id: projectId, question } }),
  getTimeline: (token, projectId) => apiRequest(`/api/projects/${projectId}/timeline`, { token }),
  getRisks: (token, projectId) => apiRequest(`/api/projects/${projectId}/risks`, { token }),
  analyzeRisks: (token, projectId) =>
    apiRequest(`/api/projects/${projectId}/risks/analyze`, { method: 'POST', token }),
  getGraph: (token, projectId) => apiRequest(`/api/projects/${projectId}/graph`, { token }),
  generateLocalTimeline: () => apiRequest('/api/timeline/generate', { method: 'POST' }),
  generateLocalGraph: () => apiRequest('/api/graph/generate', { method: 'POST' }),
  health: () => apiRequest('/api/health'),
}
