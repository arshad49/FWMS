# 🚀 Freelancer CRM — AI-Powered Business Management Platform

> A full-stack CRM for freelancers and small agencies to manage clients, projects, tasks, quotations, invoices, payments, and business workflows — with an AI assistant accessible through Telegram and the web dashboard.

![Status](https://img.shields.io/badge/Status-Production--Oriented-success)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E)
![AI](https://img.shields.io/badge/AI-LLM%20%2B%20Tool%20Calling-purple)

---

## 📌 Overview

Freelancers and small agencies often manage their business across multiple tools — spreadsheets for clients, messaging apps for communication, documents for quotations, and separate systems for invoices and tasks.

**Freelancer CRM** brings these workflows into a single platform.

The system combines a traditional CRM dashboard with an **AI-powered business assistant** that allows users to perform CRM operations using natural language.

For example:

> **"Create a quote for ABC Technologies for a website project worth ₹75,000."**

The AI assistant understands the request, extracts the required information, calls the appropriate CRM tools, creates the quotation, and returns the result through Telegram.

---

# ✨ Key Features

## 🤖 AI Business Assistant

Interact with the CRM using natural language instead of manually navigating through multiple screens.

### Capabilities

- Create and manage clients
- Create projects
- Create quotations
- Generate invoices
- Create and update tasks
- Check payment status
- Query project information
- Retrieve client information
- Track deadlines
- Extract project requirements from messages
- Maintain short-term conversation context
- Execute CRM actions through tool calling

### Example

```text
User:
Create a project for Acme Solutions called "E-commerce Website"
with a budget of ₹80,000 and deadline December 20.

AI:
✓ Client identified
✓ Project created
✓ Budget recorded
✓ Deadline added
```

---

# 📱 Telegram CRM

The CRM can be operated directly through Telegram.

Instead of opening the dashboard for every operation, users can send messages such as:

```text
Show my pending projects
```

```text
Create a task for Ahmed:
Finish homepage UI by Friday.
Budget ₹5,000.
```

```text
How much money is pending from ABC Technologies?
```

```text
Send me the latest invoice for Acme Solutions.
```

The Telegram assistant processes the request and interacts with the CRM backend using structured tools.

---

# 🧠 AI Architecture

The AI assistant follows a **tool-calling architecture** rather than allowing the LLM to directly manipulate the database.

```text
                    ┌───────────────────┐
                    │       User        │
                    └─────────┬─────────┘
                              │
                    Telegram / Web
                              │
                              ▼
                    ┌───────────────────┐
                    │   AI Assistant    │
                    │                   │
                    │ LLM + LangChain   │
                    └─────────┬─────────┘
                              │
                         Tool Calling
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
        Client Tools    Project Tools    Finance Tools
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                    ┌───────────────────┐
                    │     FastAPI       │
                    │      Backend      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ PostgreSQL/Supabase│
                    └───────────────────┘
```

This approach keeps the AI layer separate from the core business logic and makes CRM operations more predictable and controllable.

---

# 💼 Client Management

Manage complete client information from a centralized dashboard.

### Features

- Client profiles
- Contact information
- Project history
- Revenue tracking
- Payment history
- Client-specific documents
- Active and completed projects

---

# 📁 Project Management

Track projects from initial requirements through completion.

### Features

- Project creation
- Project status tracking
- Budget management
- Deadline tracking
- Requirements checklist
- Progress calculation
- Task management
- Client association

### Project Lifecycle

```text
Pending
   ↓
In Progress
   ↓
Completed
```

---

# ✅ Task Management

Create and track tasks across projects.

### Features

- Task assignment
- Team member assignment
- Task budgets
- Due dates
- Project filtering
- Status tracking
- Payment status

Supported statuses:

```text
To Do → In Progress → Done
```

---

# 💰 Financial Management

Manage quotations, invoices, and payments from one place.

### Quotations

- Custom quotation templates
- Automatic quotation numbering
- Client/project association
- Line-item pricing
- Total calculation
- PDF generation
- Telegram delivery

### Invoices

- Automatic invoice numbering
- Invoice generation
- Payment tracking
- Outstanding balance calculation
- PDF generation
- Telegram delivery

### Payment Methods

- UPI
- Bank Transfer
- Cash

---

# 📊 Business Dashboard

The dashboard provides an overview of the business in real time.

### Analytics

- Total revenue
- Outstanding payments
- Active projects
- Completed projects
- Task completion rate
- Top clients
- Upcoming deadlines
- Revenue trends

### Screenshots

Add your actual screenshots under `docs/`:

```text
docs/
├── dashboard.png
├── projects.png
├── clients.png
├── invoices.png
└── telegram-ai.png
```

Then reference them in this README:

```markdown
![Dashboard](docs/dashboard.png)
```

---

# 🧠 AI Features

The project focuses on practical AI integration rather than simply adding a chatbot.

## 1. Natural Language → Business Action

```text
"Create a quote for John for a website worth ₹50,000"
```

↓

```text
LLM
  ↓
Intent detection
  ↓
Tool selection
  ↓
Structured parameters
  ↓
CRM operation
  ↓
Confirmation
```

## 2. Tool Calling

The AI assistant can call structured backend tools such as:

```text
create_client()
create_project()
create_task()
create_quote()
create_invoice()
get_project()
get_client()
get_payment_status()
```

## 3. Context Memory

The assistant maintains useful short-term context.

For example:

```text
User:
Create a quote for ABC Technologies.

AI:
Quote created.

User:
Make it ₹10,000 more.

AI:
Updated the latest quote by ₹10,000.
```

## 4. Zero-Token Fast Handlers

Common deterministic queries can bypass the LLM and execute directly.

This reduces:

- AI API usage
- Response latency
- Unnecessary model calls
- Operating costs

---

# 🏗️ Technology Stack

## Backend

| Technology | Purpose |
|---|---|
| **Python** | Core backend language |
| **FastAPI** | REST API and backend services |
| **PostgreSQL** | Relational database |
| **Supabase** | Hosted PostgreSQL infrastructure |
| **LangChain** | AI tool calling and orchestration |
| **OpenRouter** | LLM API integration |
| **psycopg2** | PostgreSQL connectivity |
| **PDFShift** | PDF generation |

## Frontend

| Technology | Purpose |
|---|---|
| **React 18** | Frontend application |
| **Vite** | Development/build tooling |
| **Tailwind CSS** | UI styling |
| **React Router** | Application routing |
| **Recharts** | Analytics and charts |
| **Lucide React** | UI icons |

## Integrations

- Telegram Bot API
- OpenRouter
- Supabase
- PDFShift

## Deployment

Designed for deployment using:

- **Vercel** — Frontend
- **Render** — Backend
- **Supabase** — Database

---

# 📂 Project Architecture

```text
freelancer-crm/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── tools/
│   ├── models/
│   ├── database/
│   ├── telegram/
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   └── package.json
│
├── docs/
│   ├── dashboard.png
│   ├── projects.png
│   ├── clients.png
│   └── telegram-ai.png
│
├── .env.example
├── requirements.txt
└── README.md
```

> Adjust the structure above if your actual repository structure is different.

---

# 🚀 Getting Started

## Prerequisites

Make sure you have:

- Python 3.12+
- Node.js 18+
- npm
- PostgreSQL / Supabase
- OpenRouter API key
- Telegram Bot Token
- PDFShift API key

---

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/freelancer-crm.git
cd freelancer-crm
```

---

## 2. Backend Setup

```bash
cd backend

python -m venv venv
```

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file:

```env
DATABASE_URL=your_supabase_database_url
OPENROUTER_API_KEY=your_openrouter_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
PDFSHIFT_API_KEY=your_pdfshift_api_key
```

**Never commit your `.env` file to GitHub.**

---

## 4. Start the Backend

```bash
uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## 5. Start the Frontend

```bash
cd frontend

npm install
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

---

# 🔐 Security Considerations

The project is designed with separation between the AI layer and core business operations.

Important production considerations include:

- Environment-based secrets
- Database access control
- API authentication
- Input validation
- Tool-level permissions
- Telegram user authorization
- Rate limiting
- Secure webhook configuration
- Database backups
- Error logging and monitoring

---

# 🧪 Example AI Workflow

### Creating a project through Telegram

```text
User
 │
 │ "Create a project for XYZ"
 ▼
Telegram Bot
 │
 ▼
FastAPI
 │
 ▼
AI Assistant
 │
 ├── Understand request
 ├── Extract project details
 ├── Select create_project tool
 │
 ▼
CRM Tool
 │
 ▼
PostgreSQL
 │
 ▼
AI Response
 │
 ▼
Telegram
```

---

# 🎯 Why I Built This

This project was built to explore how **AI can interact with real business systems instead of functioning only as a conversational chatbot**.

The main goal was to combine:

- AI agents
- Tool calling
- Natural language interfaces
- CRM workflows
- Financial management
- Document generation
- Telegram automation
- Full-stack application development

It demonstrates how an LLM can act as an interface to structured business operations while keeping the actual business logic inside the backend.

---

# 🔮 Future Improvements

- [ ] Multi-user authentication
- [ ] Role-based access control
- [ ] Advanced AI memory
- [ ] Email integration
- [ ] WhatsApp integration
- [ ] Automated payment reminders
- [ ] Recurring invoices
- [ ] Expense management
- [ ] Client portal
- [ ] Advanced financial analytics
- [ ] AI-generated business reports
- [ ] Workflow automation
- [ ] Agent evaluation and monitoring
- [ ] Audit logs
- [ ] Automated testing
- [ ] Docker deployment

---

# 📸 Screenshots

Add actual screenshots from your application here.

### Dashboard

![Dashboard](docs/dashboard.png)

### Project Management

![Projects](docs/projects.png)

### AI Telegram Assistant

![Telegram AI](docs/telegram-ai.png)

### Invoice Management

![Invoices](docs/invoices.png)

---

# 📈 Project Highlights

### Full-Stack Engineering

- React frontend
- FastAPI backend
- PostgreSQL database
- REST APIs

### AI Engineering

- LLM integration
- Tool calling
- Natural language → structured actions
- Context-aware interactions
- Deterministic AI fallbacks

### Automation

- Telegram integration
- Automated document generation
- CRM workflow automation

### Business Systems

- CRM
- Project management
- Quotation management
- Invoice management
- Payment tracking

---

# 👨‍💻 Author

**Arshad**

AI Engineer & Automation Developer

Interested in building practical AI systems, agentic workflows, business automation, and AI-powered applications.

---

## ⭐ If you find this project useful

Give the repository a ⭐ and feel free to explore the implementation.
