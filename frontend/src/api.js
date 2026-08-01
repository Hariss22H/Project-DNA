const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function authHeaders(token, extra = {}) {
  const headers = { ...extra }
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

function extractErrorMessage(body, status) {
  const detail = body?.detail
  const raw = Array.isArray(detail)
    ? detail.map((item) => item.msg || JSON.stringify(item)).join(', ')
    : detail
      || body?.error?.message
      || body?.message
      || ''

  if (status === 401 || /invalid.*(email|password|credentials)/i.test(raw)) {
    return 'Invalid email or password.'
  }
  if (status === 404 && /account|email|user/i.test(raw)) {
    return raw || 'No account found with this email.'
  }
  if (raw && !/^Request failed/i.test(raw)) return raw
  if (status === 422) return 'Please check your details and try again.'
  if (status >= 500) return 'Something went wrong on our side. Please try again.'
  return 'Something went wrong. Please try again.'
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
    throw new Error(extractErrorMessage(body, response.status))
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
  forgotPassword: (email) =>
    apiRequest('/api/auth/forgot-password', { method: 'POST', body: { email } }),
  resetPassword: (payload) =>
    apiRequest('/api/auth/reset-password', { method: 'POST', body: payload }),
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
