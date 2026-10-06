# 🤖 AI-Powered Freelancer CRM

A full-stack CRM project built to explore how **LLMs, tool calling, and automation can be integrated into real business workflows**.

The system allows freelancers and small teams to manage **clients, projects, tasks, quotations, invoices, and payments** through a web dashboard, while an AI assistant provides a natural-language interface through **Telegram**.

**This is a learning and portfolio project focused on practical AI engineering, agentic workflows, and full-stack development.**

---

## 🧩 What Is This?

Traditional CRM systems require users to manually navigate through dashboards to perform everyday operations.

This project explores a different approach:

**What if you could simply tell the CRM what you want to do?**

For example:

```text
"Create a project for ABC Technologies with a budget of ₹80,000."
```

The AI assistant can:

```text
User
  ↓
Natural Language Request
  ↓
LLM
  ↓
Tool Selection
  ↓
CRM Tool
  ↓
Database
  ↓
Result
  ↓
Telegram Response
```

Instead of allowing the LLM to directly access the database, the assistant uses **structured tools** to perform specific CRM operations.

---

# ✨ Main Features

### 🤖 AI Assistant

* Natural-language CRM interaction
* LLM-based intent understanding
* Tool/function calling
* Structured parameter extraction
* Short-term conversational context
* AI-assisted CRM operations

### 📱 Telegram Integration

Manage CRM operations directly from Telegram.

Examples:

```text
Show my pending projects
```

```text
Create a task for Ahmed to finish the homepage by Friday.
```

```text
How much payment is pending from ABC Technologies?
```

```text
Create a quotation for John for ₹50,000.
```

---

### 👥 Client Management

* Create and manage clients
* Store contact information
* View client history
* Track associated projects
* Track revenue and payments

---

### 📁 Project Management

* Create projects
* Track project status
* Set budgets
* Set deadlines
* Maintain requirements
* Track project progress
* Connect projects with clients and tasks

Project lifecycle:

```text
Pending → In Progress → Completed
```

---

### ✅ Task Management

* Create tasks
* Assign tasks
* Set deadlines
* Track task status
* Assign budgets
* Filter tasks by project

```text
To Do → In Progress → Done
```

---

### 💰 Quotes & Invoices

The project also explores basic financial workflows:

* Create quotations
* Generate invoices
* Automatic numbering
* Track payments
* Calculate outstanding balances
* Generate PDF documents
* Deliver documents through Telegram

---

### 📊 Dashboard

The web dashboard provides an overview of:

* Projects
* Clients
* Tasks
* Revenue
* Payments
* Upcoming deadlines
* Project status
* Task completion

---

# 🧠 AI Architecture

The core idea of the project is **LLM → Tools → Business Logic → Database**.

```text
                         ┌──────────────┐
                         │     User     │
                         └──────┬───────┘
                                │
                    Telegram / Web Interface
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Assistant  │
                       │                 │
                       │  LLM + Tools    │
                       └────────┬────────┘
                                │
                         Tool Selection
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       Client Tools       Project Tools     Finance Tools
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     FastAPI     │
                       │    Backend      │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ PostgreSQL /    │
                       │    Supabase     │
                       └─────────────────┘
```

### Why use tools?

The LLM does **not** directly modify the database.

Instead, it decides which structured operation is required.

For example:

```text
User:
"Create a project for ABC Technologies."

        ↓

AI decides:

create_project(
    client="ABC Technologies",
    project_name="...",
    budget="..."
)

        ↓

Backend validates the request

        ↓

Database operation

        ↓

Result returned to the AI

        ↓

User receives confirmation
```

This provides a cleaner separation between **AI reasoning and application logic**.

---

# 🛠️ Technology Stack

## Backend

* **Python**
* **FastAPI**
* **PostgreSQL**
* **Supabase**
* **LangChain**
* **OpenRouter**
* **psycopg2**

## Frontend

* **React 18**
* **Vite**
* **Tailwind CSS**
* **React Router**
* **Recharts**
* **Lucide React**

## Integrations

* Telegram Bot API
* OpenRouter API
* Supabase
* PDFShift

---

# 📂 Project Structure

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
│   └── screenshots/
│
├── .env.example
├── requirements.txt
└── README.md
```

---

# 🚀 Running the Project

## Requirements

* Python 3.12+
* Node.js 18+
* PostgreSQL / Supabase
* OpenRouter API key
* Telegram Bot Token
* PDFShift API key

### Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

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

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔐 Environment Variables

Create a `.env` file:

```env
DATABASE_URL=your_database_url
OPENROUTER_API_KEY=your_openrouter_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
PDFSHIFT_API_KEY=your_pdfshift_api_key
```

> Never commit API keys or secrets to GitHub.

---

# 📚 What I Explored Through This Project

This project was primarily built as a practical way to understand how AI systems connect with real applications.

### AI Engineering

* LLM API integration
* Prompt design
* Tool/function calling
* Structured outputs
* Context handling
* AI-driven decision making

### Agentic AI Concepts

* AI → tool selection
* Tool execution
* Business action workflows
* Separation of AI reasoning from application logic
* Deterministic handlers for simple operations

### Backend Engineering

* REST APIs
* FastAPI
* PostgreSQL
* Database operations
* Service-layer architecture

### Full-Stack Development

* React
* API integration
* Dashboard development
* State management
* Data visualization

### Automation

* Telegram bot integration
* Automated document generation
* AI-powered CRM workflows

---

# 🎯 Project Goal

The goal was not simply to build another CRUD application.

The main goal was to understand how to build a system where:

> **Natural language can become a controlled business action.**

For example:

```text
"Create a quotation for ABC Technologies."

                ↓

        AI understands intent

                ↓

        Selects CRM tool

                ↓

        Backend validates request

                ↓

        Database is updated

                ↓

        User receives result
```

This project helped me understand the connection between **LLMs, agents, APIs, databases, and real-world automation**.

---

# 🔮 Future Improvements

Possible improvements include:

* [ ] Authentication and authorization
* [ ] Role-based access control
* [ ] Better AI memory
* [ ] WhatsApp integration
* [ ] Email integration
* [ ] Automated payment reminders
* [ ] AI-generated business reports
* [ ] Workflow automation
* [ ] Agent evaluation
* [ ] Better error handling
* [ ] Docker support
* [ ] Automated testing

---

# 📸 Screenshots

Add screenshots here to show the project visually.

### Dashboard

```text
docs/screenshots/dashboard.png
```

### Project Management

```text
docs/screenshots/projects.png
```

### AI Telegram Assistant

```text
docs/screenshots/telegram-ai.png
```

### Invoice Management

```text
docs/screenshots/invoices.png
```

---

# 👨‍💻 Author

**Arshad**

AI Engineer & Automation Developer

Focused on building practical applications using **AI, LLMs, agentic workflows, automation, Python, and modern web technologies.**

---

## ⭐ About This Repository

This repository is primarily a **learning and portfolio project** created to experiment with AI-powered business applications and understand how modern AI systems can interact with structured software systems.
