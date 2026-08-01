import { useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  Activity, AlertTriangle, Bell, Bot, ChevronDown, CircleHelp, FileText,
  FolderKanban, GitBranch, LayoutDashboard, Menu, MoreHorizontal, Plus,
  Search, Settings, ShieldAlert, Sparkles, Upload, Users, X, LockKeyhole, Mail
} from 'lucide-react'
import { api } from './api'

const navigation = [
  ['Dashboard', LayoutDashboard], ['Projects', FolderKanban], ['Knowledge Graph', GitBranch],
  ['AI Chat', Bot], ['Documents', FileText], ['Timeline', Activity], ['Risk Dashboard', ShieldAlert],
]

const SESSION_KEY = 'project-dna-session'
const PROJECT_KEY = 'project-dna-active-project'
const CHAT_EXAMPLES = [
  'Explain the authentication flow.',
  'Summarize the project architecture.',
  'Which APIs handle user authentication?',
  'What technologies are used?',
  'What risks exist in this project?',
]

function initialsFrom(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
}

function sessionFromAuth(data) {
  const user = data.user
  return {
    token: data.access_token,
    name: user.full_name,
    email: user.email,
    initials: user.initials || initialsFrom(user.full_name),
    role: user.role || 'Project manager',
    userId: user.id,
  }
}

function formatRelativeTime(ts) {
  const diff = Math.max(0, Date.now() - ts)
  if (diff < 60_000) return 'Just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return new Date(ts).toLocaleDateString()
}

function enhanceAnswerMarkdown(text = '') {
  const trimmed = text.trim()
  if (!trimmed) return '_No answer returned._'
  if (/^#{1,3}\s|^\s*[-*•]\s|^\s*\d+\.\s/m.test(trimmed)) return trimmed

  const paragraphs = trimmed
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean)

  if (paragraphs.length > 1) {
    return paragraphs.map((p) => p.replace(/\n/g, ' ')).join('\n\n')
  }

  const sentences = trimmed
    .replace(/\n+/g, ' ')
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean)

  if (sentences.length <= 2) return trimmed

  const intro = sentences.slice(0, 2).join(' ')
  const points = sentences.slice(2, 6)
  return `${intro}\n\n### Key Points\n\n${points.map((point) => `- ${point}`).join('\n')}`
}

function MarkdownBody({ content }) {
  return (
    <ReactMarkdown
      components={{
        a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer">{children}</a>,
        pre: ({ children }) => <pre className="code-block">{children}</pre>,
        code: ({ className, children }) => (
          className
            ? <code className={className}>{children}</code>
            : <code className="inline-code">{children}</code>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

function App() {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem(SESSION_KEY)
    return saved ? JSON.parse(saved) : null
  })
  const [active, setActive] = useState('Dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [chatLoading, setChatLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [projects, setProjects] = useState([])
  const [projectId, setProjectId] = useState(() => localStorage.getItem(PROJECT_KEY) || '')
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState('')
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifications, setNotifications] = useState([
    { id: 'welcome', text: 'Welcome to Project DNA.', createdAt: Date.now(), read: false },
  ])
  const notifRef = useRef(null)

  const restrictedForMember = ['Risk Dashboard']
  const visibleNavigation = navigation.filter(([label]) => auth?.role !== 'Team member' || !restrictedForMember.includes(label))
  const activeProject = projects.find((p) => p.id === projectId) || projects[0] || null
  const unreadCount = notifications.filter((n) => !n.read).length

  const pageSubtitle = useMemo(() => {
    if (!activeProject) return 'Create a project to connect GitHub, documents, and AI chat.'
    if (active === 'Dashboard') return `Live intelligence for ${activeProject.project_name}.`
    return `Manage ${active.toLowerCase()} for ${activeProject.project_name}.`
  }, [active, activeProject])

  const showNotice = (message) => {
    setNotice(message)
    window.setTimeout(() => setNotice(''), 3200)
  }

  const pushNotification = (text) => {
    setNotifications((current) => [
      { id: `${Date.now()}-${Math.random()}`, text, createdAt: Date.now(), read: false },
      ...current,
    ].slice(0, 12))
  }

  const persistSession = (session) => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    setAuth(session)
  }

  const logout = () => {
    localStorage.removeItem(SESSION_KEY)
    setAuth(null)
    setProjects([])
    setDashboard(null)
    setMessages([])
    setNotifOpen(false)
  }

  const selectProject = (id) => {
    setProjectId(id)
    localStorage.setItem(PROJECT_KEY, id)
  }

  const refreshWorkspace = async (token = auth?.token, preferredId = projectId) => {
    if (!token) return
    setLoading(true)
    try {
      const listRes = await api.listProjects(token)
      const list = listRes.data || []
      setProjects(list)
      const nextId = list.some((p) => p.id === preferredId) ? preferredId : list[0]?.id || ''
      if (nextId !== projectId) selectProject(nextId)
      if (nextId) {
        const dash = await api.getDashboard(token, nextId)
        setDashboard(dash.data)
      } else {
        setDashboard(null)
      }
    } catch (error) {
      showNotice(error.message)
      if (/credentials|unauthorized|401|signed in|sign in/i.test(error.message)) logout()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (auth?.token) refreshWorkspace(auth.token, projectId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth?.token])

  useEffect(() => {
    if (!auth?.token || !projectId) return
    api.getDashboard(auth.token, projectId)
      .then((res) => setDashboard(res.data))
      .catch((error) => showNotice(error.message))
  }, [auth?.token, projectId])

  useEffect(() => {
    if (!notifOpen) return undefined
    const onPointerDown = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setNotifOpen(false)
      }
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [notifOpen])

  const runAction = async (label, fn, successNotice) => {
    setBusy(label)
    try {
      await fn()
      const message = successNotice || `${label} complete.`
      showNotice(message)
      pushNotification(message)
    } catch (error) {
      showNotice(error.message)
    } finally {
      setBusy('')
    }
  }

  const sendMessage = async (text = query) => {
    if (!text.trim() || chatLoading) return
    if (!auth?.token || !activeProject) {
      showNotice('Select or create a project before chatting.')
      return
    }
    const question = text.trim()
    const now = Date.now()
    setMessages((current) => [...current, { id: `u-${now}`, role: 'user', text: question, createdAt: now }])
    setQuery('')
    setChatLoading(true)
    try {
      const res = await api.chat(auth.token, activeProject.id, question)
      const answer = res.data?.answer || 'No answer returned.'
      const sources = (res.data?.sources || [])
        .slice(0, 5)
        .map((s) => s.file_name || s.title || s.id)
        .filter(Boolean)
      setMessages((current) => [...current, {
        id: `a-${Date.now()}`,
        role: 'ai',
        text: answer,
        sources,
        confidence: Math.round(res.data?.confidence || 0),
        model: res.data?.model_used || 'model',
        createdAt: Date.now(),
      }])
      pushNotification('AI analysis completed.')
    } catch (error) {
      setMessages((current) => [...current, {
        id: `e-${Date.now()}`,
        role: 'ai',
        text: `I couldn't complete that request.\n\n${error.message}`,
        error: true,
        createdAt: Date.now(),
      }])
    } finally {
      setChatLoading(false)
    }
  }

  if (!auth) {
    return (
      <Auth
        onLogin={(session) => {
          persistSession(session)
        }}
        showNotice={showNotice}
        notice={notice}
      />
    )
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Sparkles size={18} /></div>
          <span>Project DNA</span>
          <button className="icon-button mobile-only" onClick={() => setSidebarOpen(false)} aria-label="Close navigation"><X /></button>
        </div>
        <nav aria-label="Main navigation">
          <p className="nav-label">WORKSPACE</p>
          {visibleNavigation.map(([label, Icon]) => (
            <button key={label} className={`nav-item ${active === label ? 'active' : ''}`} onClick={() => { setActive(label); setSidebarOpen(false) }}>
              <Icon size={19} /><span>{label}</span>
            </button>
          ))}
          <p className="nav-label lower">PREFERENCES</p>
          <button className="nav-item" onClick={() => showNotice('Settings stay local for this hackathon demo.')}>
            <Settings size={19} /><span>Settings</span>
          </button>
        </nav>
        <div className="sidebar-help">
          <div className="help-icon"><CircleHelp size={18} /></div>
          <div><strong>{loading ? 'Syncing…' : busy || 'API connected'}</strong><span>{activeProject?.project_name || 'No project yet'}</span></div>
        </div>
        <div className="profile">
          <div className="avatar">{auth.initials}</div>
          <div><strong>{auth.name}</strong><span>{auth.role}</span></div>
          <ChevronDown size={16} />
        </div>
        <button className="logout-button" onClick={logout}>Log out</button>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu /></button>
          <label className="search"><Search size={19} /><input placeholder="Search is UI-only in MVP" /></label>
          <div className="top-actions">
            {projects.length > 0 && (
              <select
                className="project-select"
                value={activeProject?.id || ''}
                onChange={(e) => selectProject(e.target.value)}
                aria-label="Active project"
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.project_name}</option>
                ))}
              </select>
            )}
            <div className="notif-wrap" ref={notifRef}>
              <button
                className="icon-button notification"
                aria-label="Notifications"
                aria-expanded={notifOpen}
                onClick={() => {
                  setNotifOpen((open) => !open)
                  setNotifications((current) => current.map((item) => ({ ...item, read: true })))
                }}
              >
                <Bell size={20} />
                {unreadCount > 0 && <i />}
              </button>
              {notifOpen && (
                <div className="notif-dropdown" role="menu">
                  <div className="notif-header">
                    <strong>Notifications</strong>
                    <span>{notifications.length ? `${notifications.length} recent` : 'Inbox'}</span>
                  </div>
                  {notifications.length ? (
                    <ul className="notif-list">
                      {notifications.map((item) => (
                        <li key={item.id}>
                          <p>{item.text}</p>
                          <small>{formatRelativeTime(item.createdAt)}</small>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="notif-empty">No new notifications.</p>
                  )}
                </div>
              )}
            </div>
            {auth.role !== 'Team member' && (
              <button
                className="create-button"
                onClick={() => setActive('Projects')}
              >
                <Plus size={18} /> <span>New project</span>
              </button>
            )}
          </div>
        </header>
        <section className="content">
          <div className="page-heading">
            <div>
              <p className="eyebrow">OVERVIEW</p>
              <h1>{active}</h1>
              <p>{pageSubtitle}</p>
            </div>
            <button className="outline-button" onClick={() => refreshWorkspace()}>
              <FileText size={17} /> Refresh data
            </button>
          </div>
          {active === 'Dashboard' && (
            <Dashboard
              dashboard={dashboard}
              project={activeProject}
              onOpen={(page) => setActive(page)}
            />
          )}
          {active === 'Projects' && (
            <ProjectsPage
              token={auth.token}
              projects={projects}
              activeId={activeProject?.id}
              onSelect={selectProject}
              onRefresh={() => refreshWorkspace()}
              onNotice={showNotice}
              runAction={runAction}
            />
          )}
          {active === 'Knowledge Graph' && (
            <GraphPage token={auth.token} project={activeProject} onNotice={showNotice} />
          )}
          {active === 'AI Chat' && (
            <ChatPage
              messages={messages}
              query={query}
              setQuery={setQuery}
              onSend={sendMessage}
              project={activeProject}
              loading={chatLoading}
            />
          )}
          {active === 'Documents' && (
            <DocumentsPage token={auth.token} project={activeProject} onNotice={showNotice} onRefresh={() => refreshWorkspace()} runAction={runAction} />
          )}
          {active === 'Timeline' && (
            <TimelinePage token={auth.token} project={activeProject} onNotice={showNotice} />
          )}
          {active === 'Risk Dashboard' && (
            <RisksPage token={auth.token} project={activeProject} onNotice={showNotice} runAction={runAction} />
          )}
        </section>
      </main>
      {sidebarOpen && <button className="scrim" onClick={() => setSidebarOpen(false)} aria-label="Close navigation" />}
      <button className="ai-launcher" onClick={() => setChatOpen(true)} aria-label="Open AI assistant"><Bot size={24} /></button>
      {chatOpen && (
        <MiniChatPanel
          project={activeProject}
          messages={messages}
          query={query}
          setQuery={setQuery}
          onSend={sendMessage}
          loading={chatLoading}
          onClose={() => setChatOpen(false)}
        />
      )}
      {notice && <div className="toast">{notice}</div>}
    </div>
  )
}

function Auth({ onLogin, showNotice, notice }) {
  const [mode, setMode] = useState('login')
  if (mode === 'signup') {
    return (
      <>
        <Signup onLogin={onLogin} onBack={() => setMode('login')} showNotice={showNotice} />
        {notice && <div className="toast">{notice}</div>}
      </>
    )
  }
  if (mode === 'forgot') {
    return (
      <>
        <ForgotPassword onBack={() => setMode('login')} showNotice={showNotice} />
        {notice && <div className="toast">{notice}</div>}
      </>
    )
  }
  return (
    <>
      <Login
        onLogin={onLogin}
        showNotice={showNotice}
        onCreateAccount={() => setMode('signup')}
        onForgotPassword={() => setMode('forgot')}
      />
      {notice && <div className="toast">{notice}</div>}
    </>
  )
}

function Signup({ onLogin, onBack, showNotice }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('Project manager')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    if (!name.trim() || !email.includes('@') || password.length < 6) {
      setError('Complete all fields and use a password with at least 6 characters.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await api.register({
        full_name: name.trim(),
        email: email.trim(),
        password,
        role,
      })
      onLogin(sessionFromAuth(res.data))
      showNotice('Account created.')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-brand"><div className="brand-mark"><Sparkles size={19} /></div>Project DNA</div>
        <div className="login-copy signup-copy">
          <p className="eyebrow">CREATE YOUR ACCOUNT</p>
          <h1>Start building your organization’s memory.</h1>
          <p>Register against the live FastAPI backend (MongoDB + JWT).</p>
        </div>
        <form onSubmit={submit} className="login-form">
          <label>Full name<div className="input-wrap"><Users size={17} /><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" autoComplete="name" /></div></label>
          <label>Email address<div className="input-wrap"><Mail size={17} /><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email" /></div></label>
          <label>Password<div className="input-wrap"><LockKeyhole size={17} /><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" autoComplete="new-password" /></div></label>
          <label>Role
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option>Organization admin</option>
              <option>Project manager</option>
              <option>Team member</option>
            </select>
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="login-button" type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create account and continue →'}</button>
          <button className="back-button" type="button" onClick={onBack}>Already have an account? Sign in</button>
        </form>
      </section>
      <AuthVisual />
    </main>
  )
}

function Login({ onLogin, showNotice, onCreateAccount, onForgotPassword }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [showSignupHint, setShowSignupHint] = useState(false)
  const [loading, setLoading] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    if (!email.includes('@') || password.length < 6) {
      setError('Enter a valid email and a password of at least 6 characters.')
      setShowSignupHint(false)
      return
    }
    setLoading(true)
    setError('')
    setShowSignupHint(false)
    try {
      const res = await api.login({ email: email.trim(), password })
      onLogin(sessionFromAuth(res.data))
      showNotice('Signed in.')
    } catch (err) {
      const message = err.message || 'Invalid email or password.'
      setError(message)
      if (/invalid email or password/i.test(message)) {
        setShowSignupHint(true)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-brand"><div className="brand-mark"><Sparkles size={19} /></div>Project DNA</div>
        <div className="login-copy">
          <p className="eyebrow">WELCOME BACK</p>
          <h1>Your project memory, connected.</h1>
          <p>Sign in with your Project DNA API account.</p>
        </div>
        <form onSubmit={submit} className="login-form">
          <label>Email address<div className="input-wrap"><Mail size={17} /><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email" /></div></label>
          <label>Password<div className="input-wrap"><LockKeyhole size={17} /><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password" /></div></label>
          {error && (
            <div className="form-error-block">
              <p className="form-error">{error}</p>
              {showSignupHint && <p className="form-error-hint">Don&apos;t have an account? Create one to continue.</p>}
            </div>
          )}
          <div className="login-options">
            <label className="remember"><input type="checkbox" defaultChecked /> Remember me</label>
            <button type="button" onClick={onForgotPassword}>Forgot password?</button>
          </div>
          <button className="login-button" type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in to dashboard →'}</button>
          <div className="auth-cta">
            <p>Don&apos;t have an account?</p>
            <button type="button" className="auth-cta-link" onClick={onCreateAccount}>Create Account</button>
          </div>
        </form>
        <p className="login-footer">Secure access powered by Project DNA</p>
      </section>
      <AuthVisual />
    </main>
  )
}

function ForgotPassword({ onBack, showNotice }) {
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const verifyEmail = async (event) => {
    event.preventDefault()
    if (!email.includes('@')) {
      setError('Enter the email associated with your account.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.forgotPassword(email.trim())
      setStep(2)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const resetPassword = async (event) => {
    event.preventDefault()
    if (password.length < 6) {
      setError('Use a password with at least 6 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.resetPassword({
        email: email.trim(),
        new_password: password,
        confirm_password: confirm,
      })
      showNotice('Password updated. You can sign in now.')
      onBack()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-brand"><div className="brand-mark"><Sparkles size={19} /></div>Project DNA</div>
        <div className="login-copy signup-copy">
          <p className="eyebrow">RESET PASSWORD</p>
          <h1>{step === 1 ? 'Find your account.' : 'Choose a new password.'}</h1>
          <p>
            {step === 1
              ? 'Enter your registered email to continue.'
              : `Set a new password for ${email}.`}
          </p>
        </div>
        {step === 1 ? (
          <form onSubmit={verifyEmail} className="login-form">
            <label>Email address<div className="input-wrap"><Mail size={17} /><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email" /></div></label>
            {error && <p className="form-error">{error}</p>}
            <button className="login-button" type="submit" disabled={loading}>{loading ? 'Checking…' : 'Continue →'}</button>
            <button className="back-button" type="button" onClick={onBack}>Back to sign in</button>
          </form>
        ) : (
          <form onSubmit={resetPassword} className="login-form">
            <label>New password<div className="input-wrap"><LockKeyhole size={17} /><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" autoComplete="new-password" /></div></label>
            <label>Confirm password<div className="input-wrap"><LockKeyhole size={17} /><input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Re-enter password" autoComplete="new-password" /></div></label>
            {error && <p className="form-error">{error}</p>}
            <button className="login-button" type="submit" disabled={loading}>{loading ? 'Updating…' : 'Update password →'}</button>
            <button className="back-button" type="button" onClick={() => { setStep(1); setError('') }}>Use a different email</button>
          </form>
        )}
      </section>
      <AuthVisual />
    </main>
  )
}

function AuthVisual() {
  return (
    <section className="login-visual">
      <div className="orb orb-one" />
      <div className="orb orb-two" />
      <div className="visual-content">
        <div className="visual-logo"><Sparkles /> Project DNA</div>
        <h2>Bring clarity to every project decision.</h2>
        <p>Turn your team’s scattered knowledge into an intelligent, searchable memory.</p>
        <div className="visual-stats">
          <span><strong>Live</strong> FastAPI backend</span>
          <span><strong>RAG</strong> grounded chat</span>
        </div>
      </div>
    </section>
  )
}

function Dashboard({ dashboard, project, onOpen }) {
  if (!project) {
    return <PlaceholderPage name="Dashboard" hint="Create a project on the Projects page to load live KPIs." />
  }
  if (!dashboard) {
    return <PlaceholderPage name="Dashboard" hint="Loading project intelligence…" />
  }

  const risks = dashboard.risks || []
  const timeline = dashboard.timeline || []
  const health = Math.round(dashboard.health_score || 0)
  const coverage = Math.round(dashboard.knowledge_coverage || 0)
  const insight = dashboard.ai_insights?.[0]

  return (
    <>
      <section className="stats-grid">
        <Stat icon={FolderKanban} label="Project status" value={dashboard.project_status} change={dashboard.github_connected ? 'GitHub connected' : 'No GitHub yet'} tone="purple" />
        <Stat icon={Activity} label="Project health" value={`${health}%`} change={dashboard.health_label || '—'} tone="green" />
        <Stat icon={FileText} label="Docs indexed" value={String(dashboard.indexed_documents_count || 0)} change={`${dashboard.chunks_indexed || 0} chunks`} tone="blue" />
        <Stat icon={ShieldAlert} label="Open risks" value={String(dashboard.risk_count || 0)} change={`${dashboard.high_risk_count || 0} high`} tone="amber" />
      </section>
      <section className="dashboard-grid">
        <div className="card project-overview">
          <div className="card-title"><div><h2>Project health</h2><p>{dashboard.project_name}</p></div><button className="more"><MoreHorizontal size={20} /></button></div>
          <div className="health-content">
            <div className="health-ring" style={{ background: `radial-gradient(closest-side,#fff 76%,transparent 77% 100%),conic-gradient(#5acb8a ${health}%,#f0eef2 0)` }}>
              <span>{health}<small>%</small></span>
            </div>
            <div className="health-bars">
              <Bar label="Coverage" value={`${coverage}%`} width={String(coverage)} color="green" />
              <Bar label="AI confidence" value={`${Math.round(dashboard.ai_confidence || 0)}%`} width={String(Math.round(dashboard.ai_confidence || 0))} color="amber" />
              <Bar label="Sources" value={String(dashboard.connected_sources_count || 0)} width={String(Math.min(100, (dashboard.connected_sources_count || 0) * 25))} color="amber" />
            </div>
          </div>
          <button className="text-button" onClick={() => onOpen('Projects')}>Manage project →</button>
        </div>
        <div className="card knowledge-card">
          <div className="card-title"><div><h2>Knowledge graph preview</h2><p>{dashboard.knowledge_graph_preview?.entity_count || 0} entities</p></div><span className="badge positive">{coverage}% coverage</span></div>
          <div className="mini-list">
            {(dashboard.knowledge_graph_preview?.nodes || []).slice(0, 6).map((node) => (
              <div key={node.id || node.label} className="mini-row"><strong>{node.label || node.id}</strong><span>{node.type || 'node'}</span></div>
            ))}
            {!dashboard.knowledge_graph_preview?.nodes?.length && <p className="muted">Index the project to populate graph entities.</p>}
          </div>
          <button className="text-button" onClick={() => onOpen('Knowledge Graph')}>Open knowledge graph →</button>
        </div>
        <div className="card activity-card">
          <div className="card-title"><div><h2>Recent activity</h2><p>Timeline from project memory</p></div></div>
          <div className="activity-list">
            {timeline.slice(0, 5).map((event, index) => (
              <div className="activity-item" key={`${event.title || event.event}-${index}`}>
                <div className="activity-icon purple"><Activity size={17} /></div>
                <div>
                  <strong>{event.title || event.event || 'Activity'}</strong>
                  <span>{event.description || event.source || event.created_at || event.date || ''}</span>
                </div>
              </div>
            ))}
            {!timeline.length && <p className="muted">No timeline events yet. Connect GitHub or upload docs.</p>}
          </div>
          <button className="text-button" onClick={() => onOpen('Timeline')}>View all activity →</button>
        </div>
        <div className="card risks-card">
          <div className="card-title"><div><h2>Risk alerts</h2><p>Rule-based project risks</p></div><span className="badge alert">{dashboard.risk_count || 0} open</span></div>
          <div className="risk-list">
            {risks.slice(0, 4).map((risk) => {
              const color = String(risk.severity || risk.level || 'low').toLowerCase().includes('high')
                ? 'red'
                : String(risk.severity || risk.level || '').toLowerCase().includes('medium')
                  ? 'amber'
                  : 'blue'
              return (
                <div className="risk" key={risk.id || risk.title}>
                  <span className={`risk-dot ${color}`} />
                  <div>
                    <div><span className={`level ${color}`}>{risk.severity || risk.level || 'Low'}</span><strong>{risk.title}</strong></div>
                    <p>{risk.description || risk.detail || ''}</p>
                  </div>
                </div>
              )
            })}
            {!risks.length && <p className="muted">Run risk analysis from the Risk Dashboard.</p>}
          </div>
          <button className="text-button" onClick={() => onOpen('Risk Dashboard')}>View risk dashboard →</button>
        </div>
      </section>
      {insight && (
        <section className="insight-banner">
          <div className="insight-icon"><Sparkles size={21} /></div>
          <div><strong>{insight.title || 'AI insight'}</strong><p>{insight.detail || insight.body || insight.text}</p></div>
          <button onClick={() => onOpen('AI Chat')}>Ask AI</button>
        </section>
      )}
    </>
  )
}

function ProjectsPage({ token, projects, activeId, onSelect, onRefresh, onNotice, runAction }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [repoUrl, setRepoUrl] = useState('')

  return (
    <div className="workspace-grid">
      <div className="card">
        <div className="card-title"><div><h2>Create project</h2><p>Starts a new knowledge twin workspace</p></div></div>
        <form
          className="stack-form"
          onSubmit={(e) => {
            e.preventDefault()
            runAction('Create project', async () => {
              const res = await api.createProject(token, {
                project_name: name.trim(),
                description: description.trim(),
              })
              setName('')
              setDescription('')
              onSelect(res.data.id)
              await onRefresh()
            }, 'Project created successfully.')
          }}
        >
          <label>Project name<input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Nova Web" /></label>
          <label>Description<textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What should the twin remember?" rows={3} /></label>
          <button className="create-button" type="submit"><Plus size={16} /> Create</button>
        </form>
      </div>
      <div className="card">
        <div className="card-title"><div><h2>Your projects</h2><p>{projects.length} workspace(s)</p></div></div>
        <div className="mini-list">
          {projects.map((project) => (
            <button
              key={project.id}
              className={`mini-row clickable ${project.id === activeId ? 'selected' : ''}`}
              onClick={() => onSelect(project.id)}
            >
              <strong>{project.project_name}</strong>
              <span>{project.project_status}{project.github_repository ? ` · ${project.github_repository}` : ''}</span>
            </button>
          ))}
          {!projects.length && <p className="muted">No projects yet.</p>}
        </div>
      </div>
      <div className="card wide">
        <div className="card-title"><div><h2>Connect GitHub</h2><p>Uses Member 1 orchestration (`POST /projects/{'{id}'}/github`)</p></div></div>
        <form
          className="stack-form horizontal"
          onSubmit={(e) => {
            e.preventDefault()
            if (!activeId) {
              onNotice('Select a project first.')
              return
            }
            runAction('Connect GitHub', async () => {
              await api.connectGithub(token, activeId, repoUrl.trim())
              setRepoUrl('')
              await onRefresh()
            }, 'Repository connected.')
          }}
        >
          <label className="grow">Repository URL<input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} required placeholder="https://github.com/owner/repo" /></label>
          <button className="create-button" type="submit"><GitBranch size={16} /> Connect</button>
          <button
            className="outline-button"
            type="button"
            onClick={() => {
              if (!activeId) {
                onNotice('Select a project first.')
                return
              }
              runAction('Index project', async () => {
                await api.indexProject(token, activeId)
                await onRefresh()
              }, 'Knowledge indexed.')
            }}
          >
            Index knowledge
          </button>
        </form>
      </div>
    </div>
  )
}

function DocumentsPage({ token, project, onNotice, onRefresh, runAction }) {
  const [docs, setDocs] = useState([])

  useEffect(() => {
    if (!token || !project) return
    api.listDocuments(token, project.id)
      .then((res) => setDocs(res.data || []))
      .catch((error) => onNotice(error.message))
  }, [token, project, onNotice])

  if (!project) return <PlaceholderPage name="Documents" hint="Create a project first." />

  return (
    <div className="workspace-grid">
      <div className="card">
        <div className="card-title"><div><h2>Upload document</h2><p>PDF, DOCX, MD, TXT</p></div></div>
        <label className="upload-box">
          <Upload size={22} />
          <span>Choose a file to extract into project memory</span>
          <input
            type="file"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (!file) return
              runAction('Upload document', async () => {
                await api.uploadDocument(token, project.id, file)
                const res = await api.listDocuments(token, project.id)
                setDocs(res.data || [])
                await onRefresh()
              }, 'Document uploaded successfully.')
              e.target.value = ''
            }}
          />
        </label>
      </div>
      <div className="card">
        <div className="card-title"><div><h2>Project documents</h2><p>{docs.length} file(s)</p></div></div>
        <div className="mini-list">
          {docs.map((doc) => (
            <div className="mini-row" key={doc.id}>
              <strong>{doc.file_name || doc.filename || doc.title}</strong>
              <span>{doc.status || doc.content_type || 'uploaded'}</span>
            </div>
          ))}
          {!docs.length && <p className="muted">No documents uploaded yet.</p>}
        </div>
      </div>
    </div>
  )
}

function TimelinePage({ token, project, onNotice }) {
  const [events, setEvents] = useState([])
  const [localEvents, setLocalEvents] = useState([])

  useEffect(() => {
    if (!token || !project) return
    api.getTimeline(token, project.id)
      .then((res) => setEvents(res.data || []))
      .catch((error) => onNotice(error.message))
    api.generateLocalTimeline()
      .then((res) => setLocalEvents(Array.isArray(res) ? res : []))
      .catch(() => setLocalEvents([]))
  }, [token, project, onNotice])

  if (!project) return <PlaceholderPage name="Timeline" hint="Create a project first." />

  const merged = [
    ...events.map((e) => ({
      date: e.created_at,
      event: e.title,
      source: e.event_type || 'Project',
      detail: e.description,
    })),
    ...localEvents,
  ].sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')))

  return (
    <div className="card">
      <div className="card-title"><div><h2>Timeline</h2><p>Project events + Member 3 local/GitHub generator</p></div></div>
      <div className="activity-list">
        {merged.map((event, index) => (
          <div className="activity-item" key={`${event.event}-${index}`}>
            <div className="activity-icon blue"><Activity size={17} /></div>
            <div>
              <strong>{event.event || event.title}</strong>
              <span>{[event.source, event.author, event.date, event.detail].filter(Boolean).join(' · ')}</span>
            </div>
          </div>
        ))}
        {!merged.length && <p className="muted">No timeline events yet.</p>}
      </div>
    </div>
  )
}

function RisksPage({ token, project, onNotice, runAction }) {
  const [risks, setRisks] = useState([])

  const load = async () => {
    if (!token || !project) return
    const res = await api.getRisks(token, project.id)
    setRisks(res.data || [])
  }

  useEffect(() => {
    load().catch((error) => onNotice(error.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, project])

  if (!project) return <PlaceholderPage name="Risk Dashboard" hint="Create a project first." />

  return (
    <div className="card">
      <div className="card-title">
        <div><h2>Risk Dashboard</h2><p>Rule-based knowledge risks</p></div>
        <button
          className="create-button"
          onClick={() => runAction('Analyze risks', async () => {
            const res = await api.analyzeRisks(token, project.id)
            setRisks(res.data || [])
          }, 'Risk analysis generated.')}
        >
          <AlertTriangle size={16} /> Analyze
        </button>
      </div>
      <div className="risk-list">
        {risks.map((risk) => {
          const color = String(risk.severity || '').toLowerCase().includes('high')
            ? 'red'
            : String(risk.severity || '').toLowerCase().includes('medium')
              ? 'amber'
              : 'blue'
          return (
            <div className="risk" key={risk.id || risk.title}>
              <span className={`risk-dot ${color}`} />
              <div>
                <div><span className={`level ${color}`}>{risk.severity || 'Low'}</span><strong>{risk.title}</strong></div>
                <p>{risk.description}</p>
              </div>
            </div>
          )
        })}
        {!risks.length && <p className="muted">No risks yet. Click Analyze after connecting sources.</p>}
      </div>
    </div>
  )
}

function GraphPage({ token, project, onNotice }) {
  const [graph, setGraph] = useState(null)
  const [localGraph, setLocalGraph] = useState(null)

  useEffect(() => {
    if (!token || !project) return
    api.getGraph(token, project.id)
      .then((res) => setGraph(res.data))
      .catch((error) => onNotice(error.message))
    api.generateLocalGraph()
      .then((res) => setLocalGraph(res))
      .catch(() => setLocalGraph(null))
  }, [token, project, onNotice])

  if (!project) return <PlaceholderPage name="Knowledge Graph" hint="Create a project first." />

  const nodes = graph?.nodes?.length ? graph.nodes : localGraph?.nodes || []
  const edges = graph?.edges?.length ? graph.edges : localGraph?.edges || []

  return (
    <div className="workspace-grid">
      <div className="card">
        <div className="card-title"><div><h2>Nodes</h2><p>{nodes.length} entities</p></div></div>
        <div className="mini-list scroll">
          {nodes.slice(0, 40).map((node) => (
            <div className="mini-row" key={node.id}>
              <strong>{node.label || node.id}</strong>
              <span>{node.type || node.data?.type || 'node'}</span>
            </div>
          ))}
          {!nodes.length && <p className="muted">No graph nodes yet. Index the project or generate the local graph.</p>}
        </div>
      </div>
      <div className="card">
        <div className="card-title"><div><h2>Edges</h2><p>{edges.length} relations</p></div></div>
        <div className="mini-list scroll">
          {edges.slice(0, 40).map((edge, index) => (
            <div className="mini-row" key={`${edge.source}-${edge.target}-${index}`}>
              <strong>{edge.source} → {edge.target}</strong>
              <span>{edge.relation || edge.label || 'related'}</span>
            </div>
          ))}
          {!edges.length && <p className="muted">No edges yet.</p>}
        </div>
      </div>
    </div>
  )
}

function ChatMessage({ message }) {
  if (message.role === 'user') {
    return (
      <article className="chat-bubble user">
        <div className="chat-meta"><span>You</span></div>
        <div className="chat-bubble-body">{message.text}</div>
      </article>
    )
  }

  return (
    <article className={`chat-bubble ai ${message.error ? 'error' : ''}`}>
      <div className="chat-meta">
        <span className="ai-label"><Bot size={14} /> Project DNA</span>
      </div>
      <div className="chat-bubble-body ai-body">
        <div className="ai-section">
          <h3>Answer</h3>
          <MarkdownBody content={enhanceAnswerMarkdown(message.text)} />
        </div>
        {!!message.sources?.length && (
          <div className="ai-section">
            <h3>Sources</h3>
            <ul className="source-list">
              {message.sources.map((source) => (
                <li key={source}><FileText size={14} /> {source}</li>
              ))}
            </ul>
          </div>
        )}
        {(message.confidence != null || message.model) && !message.error && (
          <div className="ai-meta-row">
            {message.confidence != null && (
              <span className="ai-chip confidence">Confidence · {message.confidence}%</span>
            )}
            {message.model && (
              <span className="ai-chip model">Model · {message.model}</span>
            )}
          </div>
        )}
      </div>
    </article>
  )
}

function ChatComposer({ query, setQuery, onSend, loading, disabled }) {
  return (
    <form
      className="chat-composer"
      onSubmit={(e) => {
        e.preventDefault()
        onSend()
      }}
    >
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask anything about your connected project…"
        rows={2}
        disabled={disabled || loading}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            onSend()
          }
        }}
      />
      <button className="create-button ask-button" type="submit" disabled={disabled || loading || !query.trim()}>
        {loading ? 'Thinking…' : 'Ask'}
      </button>
    </form>
  )
}

function ChatPage({ messages, query, setQuery, onSend, project, loading }) {
  const scrollerRef = useRef(null)

  useEffect(() => {
    const node = scrollerRef.current
    if (node) node.scrollTop = node.scrollHeight
  }, [messages, loading])

  if (!project) return <PlaceholderPage name="AI Chat" hint="Create and index a project first." />

  return (
    <div className="card chat-page modern">
      <div className="card-title chat-page-title">
        <div>
          <h2>AI Knowledge Twin</h2>
          <p>Grounded answers for {project.project_name}</p>
        </div>
      </div>
      <div className="chat-thread" ref={scrollerRef}>
        {!messages.length && !loading && (
          <div className="chat-welcome">
            <div className="welcome-icon"><Bot size={28} /></div>
            <h3>Welcome to Project DNA AI Knowledge Twin</h3>
            <p>Ask anything about your connected project.</p>
            <div className="example-grid">
              {CHAT_EXAMPLES.map((example) => (
                <button key={example} type="button" onClick={() => onSend(example)}>{example}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((message) => (
          <ChatMessage key={message.id || `${message.role}-${message.createdAt}`} message={message} />
        ))}
        {loading && (
          <div className="typing-indicator">
            <span className="typing-dots" aria-hidden="true"><i /><i /><i /></span>
            <p>Project DNA is analyzing your knowledge base…</p>
          </div>
        )}
      </div>
      <ChatComposer query={query} setQuery={setQuery} onSend={onSend} loading={loading} />
    </div>
  )
}

function MiniChatPanel({ project, messages, query, setQuery, onSend, loading, onClose }) {
  const scrollerRef = useRef(null)

  useEffect(() => {
    const node = scrollerRef.current
    if (node) node.scrollTop = node.scrollHeight
  }, [messages, loading])

  return (
    <div className="chat-panel">
      <div className="chat-title">
        <div>
          <div className="bot-icon"><Bot size={18} /></div>
          <span><strong>DNA Assistant</strong><small>{project?.project_name || 'Select a project'}</small></span>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Close chat"><X /></button>
      </div>
      <div className="chat-messages" ref={scrollerRef}>
        {messages.length ? messages.map((m) => (
          <ChatMessage key={m.id || `${m.role}-${m.createdAt}`} message={m} />
        )) : (
          <>
            <p className="chat-greeting">Ask about this project’s knowledge twin.</p>
            <button type="button" onClick={() => onSend('Summarize project risks')}>Summarize project risks</button>
            <button type="button" onClick={() => onSend('What decisions were made recently?')}>Recent decisions</button>
          </>
        )}
        {loading && (
          <div className="typing-indicator compact">
            <span className="typing-dots" aria-hidden="true"><i /><i /><i /></span>
            <p>Analyzing…</p>
          </div>
        )}
      </div>
      <ChatComposer query={query} setQuery={setQuery} onSend={onSend} loading={loading} disabled={!project} />
    </div>
  )
}

function Stat({ icon: Icon, label, value, change, tone }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${tone}`}><Icon size={20} /></div>
      <div><p>{label}</p><strong>{value}</strong><span>{change}</span></div>
    </div>
  )
}

function Bar({ label, value, width, color }) {
  return (
    <div className="bar-row">
      <span className={`bar-label ${color}`}>{label}</span>
      <div className="bar"><i className={color} style={{ width: `${width}%` }} /></div>
      <strong className={`bar-value ${color}`}>{value}</strong>
    </div>
  )
}

function PlaceholderPage({ name, hint }) {
  return (
    <div className="empty-page card">
      <div className="empty-icon"><Sparkles size={30} /></div>
      <h2>{name}</h2>
      <p>{hint || 'This section is ready for its data integration.'}</p>
    </div>
  )
}

export default App
