import { useMemo, useState } from 'react'
import {
  Activity, AlertTriangle, Bell, Bot, ChevronDown, CircleHelp, FileText,
  FolderKanban, GitBranch, LayoutDashboard, Menu, MoreHorizontal, Plus,
  Search, Settings, ShieldAlert, Sparkles, Upload, Users, X, LockKeyhole, Mail
} from 'lucide-react'

const navigation = [
  ['Dashboard', LayoutDashboard], ['Projects', FolderKanban], ['Knowledge Graph', GitBranch],
  ['AI Chat', Bot], ['Documents', FileText], ['Timeline', Activity], ['Risk Dashboard', ShieldAlert],
]

const activities = [
  { icon: Upload, tone: 'purple', title: 'Architecture Decision Record uploaded', detail: 'by Priya Sharma · 12 minutes ago' },
  { icon: GitBranch, tone: 'blue', title: 'Repository connected to Project DNA', detail: 'github.com/acme/nova-web · 2 hours ago' },
  { icon: Users, tone: 'green', title: 'Alex Chen joined the project', detail: 'Added as Engineering Lead · Yesterday' },
]

const risks = [
  { level: 'High', title: 'Undocumented deployment process', detail: 'No runbook has been found for production releases.', color: 'red' },
  { level: 'Medium', title: 'Single point dependency', detail: 'Authentication knowledge is concentrated with one contributor.', color: 'amber' },
  { level: 'Low', title: 'Stale decision record', detail: 'One architecture decision has not been reviewed in 90 days.', color: 'blue' },
]

function App() {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem('project-dna-session')
    return saved ? JSON.parse(saved) : null
  })
  const [active, setActive] = useState('Dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [notice, setNotice] = useState('')
  const restrictedForMember = ['Risk Dashboard']
  const visibleNavigation = navigation.filter(([label]) => auth?.role !== 'Team member' || !restrictedForMember.includes(label))

  const pageSubtitle = useMemo(() => active === 'Dashboard' ? 'Here is what is happening across your organization.' : `Manage your ${active.toLowerCase()} in one place.`, [active])
  const showNotice = (message) => { setNotice(message); window.setTimeout(() => setNotice(''), 2800) }
  const sendMessage = (text = query) => {
    if (!text.trim()) return
    setMessages((current) => [...current, { role: 'user', text }, { role: 'ai', text: 'I found relevant project context. Connect your API to return grounded answers and source references here.' }])
    setQuery('')
  }

  if (!auth) return <Auth onLogin={(session) => {
    localStorage.setItem('project-dna-session', JSON.stringify(session))
    setAuth(session)
  }}/>

  return <div className="app-shell">
    <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
      <div className="brand"><div className="brand-mark"><Sparkles size={18}/></div><span>Project DNA</span><button className="icon-button mobile-only" onClick={() => setSidebarOpen(false)} aria-label="Close navigation"><X /></button></div>
      <nav aria-label="Main navigation">
        <p className="nav-label">WORKSPACE</p>
        {visibleNavigation.map(([label, Icon]) => <button key={label} className={`nav-item ${active === label ? 'active' : ''}`} onClick={() => { setActive(label); setSidebarOpen(false) }}><Icon size={19}/><span>{label}</span></button>)}
        <p className="nav-label lower">PREFERENCES</p>
        <button className="nav-item" onClick={() => showNotice('Settings will be available shortly.')}><Settings size={19}/><span>Settings</span></button>
      </nav>
      <div className="sidebar-help"><div className="help-icon"><CircleHelp size={18}/></div><div><strong>Need a hand?</strong><span>Visit our help center</span></div></div>
      <div className="profile"><div className="avatar">{auth.initials}</div><div><strong>{auth.name}</strong><span>{auth.role}</span></div><ChevronDown size={16}/></div>
      <button className="logout-button" onClick={() => { localStorage.removeItem('project-dna-session'); setAuth(null) }}>Log out</button>
    </aside>

    <main className="main-content">
      <header className="topbar">
        <button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu /></button>
        <label className="search"><Search size={19}/><input placeholder="Search projects, documents, people..." /></label>
        <div className="top-actions"><button className="icon-button notification" aria-label="Notifications"><Bell size={20}/><i /></button>{auth.role !== 'Team member' && <button className="create-button" onClick={() => showNotice('Create project flow opened.')}><Plus size={18}/> <span>New project</span></button>}</div>
      </header>
      <section className="content">
        <div className="page-heading"><div><p className="eyebrow">OVERVIEW</p><h1>{active}</h1><p>{pageSubtitle}</p></div><button className="outline-button" onClick={() => showNotice('Report export is being prepared.')}><FileText size={17}/> Export report</button></div>
        {active === 'Dashboard' ? <Dashboard onAction={showNotice} /> : <PlaceholderPage name={active} onAction={showNotice}/>} 
      </section>
    </main>
    {sidebarOpen && <button className="scrim" onClick={() => setSidebarOpen(false)} aria-label="Close navigation" />}
    <button className="ai-launcher" onClick={() => setChatOpen(true)} aria-label="Open AI assistant"><Bot size={24}/></button>
    {chatOpen && <div className="chat-panel"><div className="chat-title"><div><div className="bot-icon"><Bot size={18}/></div><span><strong>DNA Assistant</strong><small>Project intelligence</small></span></div><button className="icon-button" onClick={() => setChatOpen(false)} aria-label="Close chat"><X /></button></div><div className="chat-messages">{messages.length ? messages.map((m, i) => <div key={i} className={`message ${m.role}`}>{m.text}</div>) : <><p className="chat-greeting">What would you like to know?</p><button onClick={() => sendMessage('Summarize project risks')}>Summarize project risks</button><button onClick={() => sendMessage('What decisions were made recently?')}>Recent decisions</button></>}</div><form className="chat-input" onSubmit={(e) => {e.preventDefault(); sendMessage()}}><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Ask about this project..."/><button aria-label="Send message">↑</button></form></div>}
    {notice && <div className="toast">{notice}</div>}
  </div>
}

function Auth({ onLogin }) {
  const [signup, setSignup] = useState(false)
  if (signup) return <Signup onLogin={onLogin} onBack={() => setSignup(false)} />
  return <><Login onLogin={onLogin}/><button className="auth-switch" onClick={() => setSignup(true)}>New to Project DNA? <strong>Create account</strong></button></>
}

function Signup({ onLogin, onBack }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('Project manager')
  const [error, setError] = useState('')
  const submit = (event) => {
    event.preventDefault()
    if (!name.trim() || !email.includes('@') || password.length < 4) { setError('Complete all fields and use a password with at least 4 characters.'); return }
    const initials = name.split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()
    const accounts = JSON.parse(localStorage.getItem('project-dna-accounts') || '[]')
    if (accounts.some((item) => item.email.toLowerCase() === email.toLowerCase())) { setError('An account already exists with this email. Please sign in instead.'); return }
    const account = { name: name.trim(), email: email.trim(), password, initials, role }
    localStorage.setItem('project-dna-accounts', JSON.stringify([...accounts, account]))
    onLogin({ token: `demo-jwt-${Date.now()}`, name: account.name, initials, role })
  }
  return <main className="login-page"><section className="login-panel"><div className="login-brand"><div className="brand-mark"><Sparkles size={19}/></div>Project DNA</div><div className="login-copy signup-copy"><p className="eyebrow">CREATE YOUR ACCOUNT</p><h1>Start building your organization’s memory.</h1><p>Set up your profile and choose the access level that matches your work.</p></div><form onSubmit={submit} className="login-form"><label>Full name<div className="input-wrap"><Users size={17}/><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" autoComplete="name"/></div></label><label>Email address<div className="input-wrap"><Mail size={17}/><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email"/></div></label><label>Password<div className="input-wrap"><LockKeyhole size={17}/><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Create a password" autoComplete="new-password"/></div></label><label>Role<select value={role} onChange={(e) => setRole(e.target.value)}><option>Organization admin</option><option>Project manager</option><option>Team member</option></select></label>{error && <p className="form-error">{error}</p>}<button className="login-button" type="submit">Create account and continue →</button><button className="back-button" type="button" onClick={onBack}>Already have an account? Sign in</button></form></section><section className="login-visual"><div className="orb orb-one"/><div className="orb orb-two"/><div className="visual-content"><div className="visual-logo"><Sparkles/> Project DNA</div><h2>One shared memory for the entire team.</h2><p>Admins, project managers and contributors get the tools relevant to their role.</p><div className="visual-stats"><span><strong>Admin</strong> Full workspace access</span><span><strong>Member</strong> Project collaboration</span></div></div></section></main>
}

function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const submit = (event) => {
    event.preventDefault()
    if (!email.includes('@') || password.length < 4) { setError('Enter a valid email and a password of at least 4 characters.'); return }
    const accounts = JSON.parse(localStorage.getItem('project-dna-accounts') || '[]')
    const account = accounts.find((item) => item.email.toLowerCase() === email.toLowerCase() && item.password === password)
    if (!account) { setError('No matching account was found. Create an account or check your email and password.'); return }
    onLogin({ token: `demo-jwt-${Date.now()}`, name: account.name, initials: account.initials, role: account.role })
  }
  return <main className="login-page"><section className="login-panel"><div className="login-brand"><div className="brand-mark"><Sparkles size={19}/></div>Project DNA</div><div className="login-copy"><p className="eyebrow">WELCOME BACK</p><h1>Your project memory, connected.</h1><p>Sign in to access your organization’s knowledge and insights.</p></div><form onSubmit={submit} className="login-form"><label>Email address<div className="input-wrap"><Mail size={17}/><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email"/></div></label><label>Password<div className="input-wrap"><LockKeyhole size={17}/><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password"/></div></label>{error && <p className="form-error">{error}</p>}<div className="login-options"><label className="remember"><input type="checkbox" defaultChecked/> Remember me</label><button type="button">Forgot password?</button></div><button className="login-button" type="submit">Sign in to dashboard →</button></form><p className="login-footer">Secure access powered by Project DNA</p></section><section className="login-visual"><div className="orb orb-one"/><div className="orb orb-two"/><div className="visual-content"><div className="visual-logo"><Sparkles/> Project DNA</div><h2>Bring clarity to every project decision.</h2><p>Turn your team’s scattered knowledge into an intelligent, searchable memory.</p><div className="visual-stats"><span><strong>12</strong> Active projects</span><span><strong>2.4k</strong> Knowledge items</span></div></div></section></main>
}

function Dashboard({ onAction }) { return <>
  <section className="stats-grid">
    <Stat icon={FolderKanban} label="Active projects" value="12" change="+2 this month" tone="purple" />
    <Stat icon={Activity} label="Project health" value="82%" change="↑ 6% vs last month" tone="green" />
    <Stat icon={FileText} label="Documentation" value="74%" change="18 documents this week" tone="blue" />
    <Stat icon={ShieldAlert} label="Open risks" value="7" change="2 require attention" tone="amber" />
  </section>
  <section className="dashboard-grid">
    <div className="card project-overview"><div className="card-title"><div><h2>Project health</h2><p>Across all active projects</p></div><button className="more"><MoreHorizontal size={20}/></button></div><div className="health-content"><div className="health-ring"><span>82<small>%</small></span></div><div className="health-bars"><Bar label="On track" value="8" width="67" color="green"/><Bar label="At risk" value="3" width="25" color="amber"/><Bar label="Needs attention" value="1" width="8" color="red"/></div></div><button className="text-button" onClick={() => onAction('Opening project health report.')}>View all projects →</button></div>
    <div className="card knowledge-card"><div className="card-title"><div><h2>Knowledge growth</h2><p>Information captured this month</p></div><span className="badge positive">+24%</span></div><div className="chart"><svg viewBox="0 0 520 160" preserveAspectRatio="none" aria-label="Knowledge growth chart"><defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#8b5cf6" stopOpacity=".28"/><stop offset="1" stopColor="#8b5cf6" stopOpacity="0"/></linearGradient></defs><path d="M0,135 C42,128 58,108 94,116 S150,84 192,96 S242,66 280,77 S325,45 360,61 S414,25 452,37 S492,12 520,18 L520,160 L0,160Z" fill="url(#fill)"/><path d="M0,135 C42,128 58,108 94,116 S150,84 192,96 S242,66 280,77 S325,45 360,61 S414,25 452,37 S492,12 520,18" fill="none" stroke="#8b5cf6" strokeWidth="3"/></svg><div className="chart-labels"><span>Week 1</span><span>Week 2</span><span>Week 3</span><span>Week 4</span></div></div></div>
    <div className="card activity-card"><div className="card-title"><div><h2>Recent activity</h2><p>Latest updates from your workspace</p></div><button className="more"><MoreHorizontal size={20}/></button></div><div className="activity-list">{activities.map(({icon: Icon,tone,title,detail}) => <div className="activity-item" key={title}><div className={`activity-icon ${tone}`}><Icon size={17}/></div><div><strong>{title}</strong><span>{detail}</span></div></div>)}</div><button className="text-button" onClick={() => onAction('Opening full activity timeline.')}>View all activity →</button></div>
    <div className="card risks-card"><div className="card-title"><div><h2>Risk alerts</h2><p>AI-detected items needing review</p></div><span className="badge alert">7 open</span></div><div className="risk-list">{risks.map((risk) => <div className="risk" key={risk.title}><span className={`risk-dot ${risk.color}`}/><div><div><span className={`level ${risk.color}`}>{risk.level}</span><strong>{risk.title}</strong></div><p>{risk.detail}</p></div></div>)}</div><button className="text-button" onClick={() => onAction('Opening the risk dashboard.')}>View risk dashboard →</button></div>
  </section>
  <section className="insight-banner"><div className="insight-icon"><Sparkles size={21}/></div><div><strong>AI insight</strong><p>Project Nova’s documentation coverage has improved 18% this week. Consider reviewing the new architecture decision record.</p></div><button onClick={() => onAction('Opening AI insight details.')}>View insight</button></section>
</> }

function Stat({ icon: Icon, label, value, change, tone }) { return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={20}/></div><div><p>{label}</p><strong>{value}</strong><span>{change}</span></div></div> }
function Bar({ label, value, width, color }) { return <div className="bar-row"><span>{label}</span><div className="bar"><i className={color} style={{width: `${width}%`}}/></div><strong>{value}</strong></div> }
function PlaceholderPage({ name, onAction }) { return <div className="empty-page card"><div className="empty-icon"><Sparkles size={30}/></div><h2>{name} workspace</h2><p>This section is ready for its data integration. It will connect to the corresponding Project DNA API endpoint.</p><button className="create-button" onClick={() => onAction(`${name} setup started.`)}><Plus size={18}/> Get started</button></div> }

export default App
