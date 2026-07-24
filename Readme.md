# Flowdesk - Multi-Tenant Collaborative Workflow & Project Management

Flowdesk is a high-performance, multi-tenant collaborative workflow and project management system designed with a microservices-ready layered architecture. It integrates Agile project management elements (similar to Jira and Trello) with Slack-like user mentions, real-time unread notifications, custom workflow engines, and automated SLA (Service Level Agreement) monitors.

---

## 🚀 Key System Features

### 🔐 1. Authentication & Security Hardening
* **JWT Access & Refresh Token Rotation**: Implements a secure authentication flow with short-lived access tokens (15 mins) and refresh tokens (7 days). Each token refresh rotates the active token pair, immediately invalidating old tokens to mitigate replay attacks.
* **API Service Tokens (API Keys)**: Allows automated service accounts to perform secure API interactions via hashed keys stored in the database, passed via the `X-API-Key` header.
* **Rate Limiting**: Employs Redis-backed sliding window rate limiting on all sensitive authentication endpoints (e.g., maximum 5 login attempts per minute per IP address).
* **Cryptographic Safety**: Passwords are securely hashed using `bcrypt` (cost factor 12) and token hashes are verified via constant-time string comparisons.

### 🏢 2. Multi-Tenant Isolation & Role Management
* **Strict Tenant Scoping**: Enforces tenant-level isolation. All resource queries are strictly scoped using the organization's unique identifier (`org_id`) derived from the active JWT context.
* **Role-Based Access Control (RBAC)**: Configures roles (`OWNER`, `ADMIN`, `MEMBER`) determining system permissions. Advanced exit protection is coded into membership queries to prevent leaving organizations without an owner.
* **Tokenized Invite System**: Permits admins to invite new members to their workspace via secure, time-limited cryptographic tokens.

### ⚙️ 3. Customized DB-Driven State Machine Workflows
* **Dynamic Project Statuses**: Replaces static, hardcoded enums with database-backed status configurations (`project_statuses`).
* **Custom Transition Rules**: Defines explicit status path logic (`workflow_rules`). A task can only progress along authorized status transitions (e.g., `Backlog` ➔ `In Progress` ➔ `In Review`), validating all changes at the database and service layer.

### 📝 4. Advanced Task Lifecycle & Collaboration
* **Work Management**: Supports complete task CRUD operations containing priority queues (`low`, `medium`, `high`, `urgent`), due dates, categories, and multiple assignees.
* **Collaborative Watchers**: Users can subscribe as watchers (`task_watchers`) to get automatic event streams about changes to task status, attachments, or comments.
* **Inter-Task Dependencies**: Supports linking tasks through relations (`task_links`) such as `BLOCKS`, `BLOCKED_BY`, and `RELATES_TO`.
* **Regex Mention Engine**: Automatically parses comments for organization member mentions. Validated mentions trigger instant background notifications and log database associations (`comment_mentions`).
* **Time Tracking**: Log work durations (`time_entries`) on tasks with aggregated reports on task views.

### 📁 5. Large File Chunked Uploads
* **Multiparts & Storage Backends**: Supports local storage or AWS S3 (integrated via LocalStack for dev environment).
* **Chunked Upload Session**: Allows upload sessions (`upload_sessions`, `multipart_uploads`) to slice large documents into chunks, upload them sequentially, and reconstruct them under single task attachments (`task_attachments`).

### 🤖 6. Automation Engine & SLA Escalation
* **JSONB Automation Rules**: Allows teams to create trigger-action logic (e.g., *IF Priority is "urgent" AND Status is "todo", THEN assign to ADMIN and notify OWNER*).
* **SLA Timers & Breach Monitors**: Active tasks are tracked against SLA policies (`sla_policies`, `sla_timers`). A Celery Beat background scheduler executes every minute, firing warning notifications at 75% elapsed duration and marking the task as `BREACHED` at 100% elapsed time.
* **Approval Gateways**: Enables members to request formal sign-offs (`approval_requests`) from owners/admins before transitioning sensitive tasks to final statuses.

---

## 🛠️ Architecture & Technology Stack

Flowdesk uses a robust, decoupled technology stack designed for performance, horizontal scaling, and audit integrity:

```
  Client (Vite/React Dashboard) <──> API Gateway (FastAPI / ASGI)
                                              │
                      ┌───────────────────────┼──────────────────────┐
                      ▼                       ▼                      ▼
           ┌─────────────────────┐ ┌─────────────────────┐ ┌──────────────────┐
           │     PostgreSQL      │ │     Redis Cache     │ │   Celery Queue   │
           │  (Relational DB &   │ │ (Unread counters,   │ └────────┬─────────┘
           │   JSONB Automs)     │ │  rate-limits, pub)  │          │
           └─────────────────────┘ └─────────────────────┘          ▼
                                                           ┌──────────────────┐
                                                           │   Celery Beat    │
                                                           │ & Async Workers  │
                                                           └──────────────────┘
```

* **FastAPI Backend (Python 3.12)**: ASGI-first REST API exposing auto-generated Swagger documentation (`/docs`) and ReDoc (`/redoc`).
* **Vite + React Frontend**: Single Page Application dashboard using modern, responsive styling and Lucide icons.
* **PostgreSQL 15**: Relational backend utilizing JSONB column formats for dynamic automation criteria and metadata preference storage.
* **SQLAlchemy & Alembic**: Asynchronous database interaction paired with version-controlled migrations.
* **Redis**: Acts as the caching layer, Celery task broker, and high-speed memory database for atomic unread notification counts (`user:{id}:unread_count`).
* **Celery & Celery Beat**: Asynchronous task workers executing notification fan-outs, file assembly, and background SLA polling.
* **LocalStack**: Emulates S3 object storage for local testing of task attachments and multipart upload assemblies.
* **Mailpit**: Emulates SMTP mail transfer for testing invitation emails and notifications locally.

---

## 📂 Codebase Structure

```
flowdesk/
├── app/                      # Backend FastAPI Source Code
│   ├── api/                  # API Routers & Endpoint Controllers
│   │   └── v1/               # Versioned routes (auth, orgs, tasks, comments, etc.)
│   ├── core/                 # App config, database session, safety handlers
│   ├── middleware/           # Rate limiting and request interception
│   ├── models/               # SQLAlchemy Declarative Models
│   ├── repositories/         # Database query abstractions
│   ├── schemas/              # Pydantic v2 request/response serializers
│   ├── services/             # Core business rules & RBAC validators
│   ├── utils/                # S3 connection, mention parsers, email senders
│   └── workers/              # Celery instance, Beat configs, background tasks
├── frontend/                 # Frontend React Application
│   ├── src/
│   │   ├── components/       # UI Components (Auth, TaskBoard, Automations, etc.)
│   │   ├── context/          # Auth Context & global state
│   │   └── services/         # API HTTP Client wrappers
│   └── vite.config.js        # Vite compilation configurations
├── migrations/               # Alembic database migration revisions
├── scripts/                  # End-to-end flow test suite
├── docker-compose.yml        # Orchestration file for all services
├── pyproject.toml            # Python backend dependencies
└── Readme.md                 # This document
```

## ⚡ Setup & Installation

### Prerequisite Check
Ensure you have the following installed on your system:
* [Docker & Docker Compose](https://www.docker.com/)
* [Python 3.12+](https://www.python.org/)
* [Node.js v18+](https://nodejs.org/)

---

### Step 1: Clone the Repository & Configure Environment
1. Clone the project and navigate into the `flowdesk` folder.
2. Duplicate `.env.example` to create a `.env` file:
   ```bash
   cp .env.example .env
   ```
3. The default settings in `.env` are pre-configured to connect directly to the services defined in `docker-compose.yml`.

---

### Step 2: Start Services via Docker Compose
Run the following command to boot the backing databases, cache stores, workers, and frontend:
```bash
docker-compose up --build -d
```

This starts the following services:
* **PostgreSQL**: Accessible on port `5432`
* **Redis**: Accessible on port `6379`
* **LocalStack (S3)**: Accessible on port `4566`
* **Mailpit (SMTP mock)**: Web Interface on port `8025`, SMTP on port `1025`
* **FastAPI Server**: Running at `http://localhost:8000`
* **React Frontend**: Running at `http://localhost:3000`

The API startup command automatically runs `alembic upgrade head` to run all database schema migrations.

---

### Step 3: Run Backend Locally (Optional / Development Mode)
If you prefer running the Python API server outside of Docker for active debugging:
1. Ensure Postgres, Redis, and LocalStack are running via Docker.
2. Initialize virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   
   pip install -r pyproject.toml
   ```
   ```
   If UV is installed and active, use the following command:
   uv sync -- creates virtual environment and installs dependencies.
   ```
3. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   or
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

---

### Step 4: Run Celery Worker & Beat Locally (Optional)
If running the backend manually, you also need to start Celery to process asynchronous tasks (notifications, SLA timer cron check, file attachments assembly):
```bash
# Start worker
celery -A app.workers.celery_app worker --loglevel=info -P solo

# Start cron beat scheduler (in a separate terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

---

### Step 5: Start Frontend Locally (Optional)
If running the frontend outside of Docker:
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Boot Vite's hot-reloading dev server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:5173` (or the port specified in console).

---

## 🧪 Testing the Flowdesk System

The project features a suite of detailed flow integration tests verifying authentication, organization boundaries, workflows, task lifecycles, and automation triggers.

### Running with Pytest
Run the full test suite using `pytest`:
```bash
pytest
```

### Running Individual Flow Tests
You can run specific test scripts located in the `scripts/` directory:
```bash
# Test SLA warning and breach escalation triggers
pytest scripts/test_sla_flow.py -v

# Test Multi-Tenant Organization logic and invitation tokens
pytest scripts/test_org_flow.py -v

# Test Task status state machine transitions
pytest scripts/test_workflow_flow.py -v

# Test Automation Rules and execution history logs
pytest scripts/test_automation_engine_flow.py -v
```
