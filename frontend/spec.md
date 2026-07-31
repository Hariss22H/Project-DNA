# Frontend & Dashboard Specification
**Project:** Project DNA – AI-Powered Organizational Memory

**Module Owner:** Frontend Team

**Tech Stack**
- React + Vite
- Tailwind CSS
- React Router
- React Flow
- Recharts / Chart.js
- Axios
- Framer Motion (Optional)

---

# Objective

Develop a responsive, modern, and intuitive web application that enables users to interact with the Project DNA platform. The frontend will provide visualization, project management, AI interaction, and analytics through an easy-to-use dashboard.

---

# Scope

This module is responsible for:

- Complete UI Design
- Dashboard Development
- User Navigation
- Data Visualization
- AI Chat Interface
- Knowledge Graph Visualization
- Responsive Design
- API Integration

---

# Functional Requirements

## Authentication (Optional)

### Features

- Login Page
- Sign Up (Optional)
- JWT Authentication
- Remember Me
- Logout

### Inputs

- Email
- Password

### Outputs

- Auth Token
- Redirect to Dashboard

---

# Dashboard

## Description

Acts as the project's command center.

### Displays

- Active Projects
- Project Health Score
- Documentation Coverage
- Knowledge Graph Overview
- AI Insights
- Recent Activities
- Team Members
- Pending Risks

### Components

- Statistics Cards
- Activity Timeline
- Project Cards
- Risk Alerts
- AI Recommendations

---

# Create Project Page

## Inputs

- Project Name
- Description
- Organization
- Team Members
- Start Date

### Actions

- Create New Project
- Save Project

### Outputs

- New Project Created
- Redirect to Dashboard

---

# Connect GitHub

## Features

- Connect Repository
- Fetch Commits
- Fetch Pull Requests
- Fetch Issues
- Fetch Contributors

### Inputs

GitHub Repository URL

### Outputs

Repository Metadata

---

# Upload Documents

## Supported Files

- PDF
- DOCX
- TXT
- Markdown

### Features

- Drag & Drop Upload
- Progress Indicator
- Upload History
- Delete Documents

### Outputs

Files uploaded successfully.

---

# AI Chat

## Description

Natural language interface for querying project knowledge.

### Example Questions

Why was React selected?

Summarize Sprint 5.

Who approved the architecture?

Show project risks.

### Features

- Chat History
- Typing Indicator
- Suggested Questions
- AI Responses
- Source References

---

# Knowledge Graph

## Description

Interactive visualization of project relationships.

### Nodes

- People
- Documents
- Decisions
- Code
- Tasks
- Meetings

### Features

- Zoom
- Search
- Filter
- Expand Nodes
- Highlight Relationships

Technology

React Flow

---

# Risk Dashboard

Displays AI-generated project risks.

### Risk Categories

Documentation Gap

Knowledge Silos

Single Point Dependency

Pending Tasks

Inactive Contributors

### Charts

Risk Distribution

Documentation Coverage

Project Health Score

Knowledge Growth

---

# Project Timeline

Shows project evolution.

### Events

Project Created

Documents Uploaded

Meeting Conducted

Decision Taken

Repository Connected

Milestones

---

# Shared Components

## Navbar

Contains

- Logo
- Search
- Notifications
- User Profile

---

## Sidebar

Navigation

Dashboard

Projects

Knowledge Graph

AI Chat

Documents

Timeline

Risk Dashboard

Settings

---

## Cards

Reusable Components

Statistic Card

Project Card

Risk Card

Insight Card

Activity Card

---

## Charts

Project Health

Knowledge Growth

Documentation Coverage

Risk Analysis

Team Contributions

---

## Upload Component

Features

- Drag & Drop
- File Validation
- Upload Progress
- Retry Failed Uploads

---

## Chat Component

Features

- Message Bubble
- Code Block
- Markdown Support
- Loading Animation

---

## Graph Component

React Flow Visualization

Supports

- Dragging
- Zooming
- Node Expansion
- Relationship Highlighting

---

# API Endpoints

## Authentication

POST /login

POST /logout

---

## Projects

GET /projects

POST /projects

GET /projects/:id

DELETE /projects/:id

---

## GitHub

POST /github/connect

GET /github/repos

---

## Documents

POST /documents/upload

GET /documents

DELETE /documents/:id

---

## AI

POST /chat

GET /insights

---

## Knowledge Graph

GET /graph

---

## Risks

GET /risks

---

## Timeline

GET /timeline

---

# Expected Outcomes

Users should be able to:

✓ Create Projects

✓ Connect GitHub Repository

✓ Upload Documents

✓ Visualize Knowledge Graph

✓ Chat with AI

✓ View Project Timeline

✓ Monitor Risks

✓ Analyze Project Health

---

# Non-Functional Requirements

- Responsive Design
- Fast Page Load
- Mobile Friendly
- Accessibility Support
- Dark Mode Ready
- Secure API Communication
- Clean UI/UX

---

# Folder Structure

```
src/
│
├── assets/
├── components/
│   ├── cards/
│   ├── charts/
│   ├── chat/
│   ├── graph/
│   ├── layout/
│   └── upload/
│
├── pages/
│   ├── Dashboard.jsx
│   ├── CreateProject.jsx
│   ├── UploadDocuments.jsx
│   ├── ConnectGitHub.jsx
│   ├── AIChat.jsx
│   ├── KnowledgeGraph.jsx
│   ├── RiskDashboard.jsx
│   └── Timeline.jsx
│
├── services/
├── hooks/
├── utils/
├── App.jsx
└── main.jsx
```

---

# Deliverables

- Responsive React Application
- Modern Dashboard UI
- Fully Functional Navigation
- Knowledge Graph Visualization
- AI Chat Interface
- Document Upload Module
- Charts & Analytics Dashboard
- API Integration
- Production-ready Frontend

---

# Acceptance Criteria

- All pages render without errors.
- Responsive across desktop, tablet, and mobile.
- GitHub repository connection works.
- Document upload UI validates supported file types.
- AI Chat displays responses with loading states.
- Knowledge Graph supports zoom, pan, and node interaction.
- Dashboard updates dynamically from backend APIs.
- Reusable components follow consistent styling and accessibility practices.

---

# Future Enhancements

- Real-time updates using WebSockets.
- Theme customization (light/dark mode).
- Multi-project workspace.
- Advanced graph filtering and search.
- Notifications and activity feed.
- Offline support with Progressive Web App (PWA).