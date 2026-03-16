# AGENTS.md

## Project Overview

This is the **Customer Chatbot GSA with Voice** — a multi-agent conversational AI chatbot
supporting text and voice modalities for product discovery, customer support, and policy queries.

Built with **FastAPI + Semantic Kernel** on the backend and **React + TypeScript** on the frontend,
deployed to **Azure Container Apps**. The project follows the
[SDL with GitHub Copilot and Azure](/.github/SDL-with-Copilot-and-Azure.md) lifecycle and uses
SDL agent-driven workflows for development.

Key capabilities:

- **Multi-agent orchestration** — Chat, Product, and Policy agents via Semantic Kernel + Azure AI Foundry
- **Voice interaction** — Real-time STT/TTS via Azure Voice Live API over WebSocket
- **Product discovery** — Visual product cards with AI Search-powered recommendations
- **Policy/FAQ support** — RAG over policy documents in Blob Storage + AI Search
- **Secure auth** — Microsoft Entra ID (MSAL.js frontend, bearer token backend)
- **Data access** — Cosmos DB via `sas-cosmosdb`, Blob Storage via `sas-storage`

## Repository Structure

```
.
├── AGENTS.md                                    ← You are here (CCA guidance)
├── README.md                                    ← Project overview and deployment guide
├── azure.yaml                                   ← Azure Developer CLI configuration
├── .design/                                     ← SDL design templates and guidance
│   ├── ADR-TEMPLATE.md                          ← Standard ADR format
│   ├── DESIGN-DOC-TEMPLATE.md                   ← General design document template
│   ├── API-DOC-TEMPLATE.md                      ← API documentation template
│   └── README.template.md                       ← GSA-aligned project README template
├── docs/                                        ← Project documentation
│   ├── adr/                                     ← Architecture Decision Records
│   │   └── ADR-0002-customer-chatbot-voice-architecture.md
│   ├── api/                                     ← API endpoint documentation
│   │   └── chatbot-api.md                       ← REST + WebSocket API reference
│   └── design/                                  ← Design documents
│       └── customer-chatbot-voice-design.md     ← Full system design
├── infra/                                       ← Bicep infrastructure-as-code
│   ├── main.bicep                               ← Main deployment orchestration
│   ├── abbreviations.json                       ← Azure resource abbreviations
│   └── modules/
│       ├── ai-search.bicep                      ← Azure AI Search
│       ├── container-apps-env.bicep             ← Container Apps environment
│       ├── container-registry.bicep             ← ACR instance
│       ├── cosmos-db.bicep                      ← Cosmos DB account + database
│       ├── key-vault.bicep                      ← Key Vault
│       ├── log-analytics.bicep                  ← Log Analytics workspace
│       ├── openai.bicep                         ← Azure OpenAI
│       └── storage.bicep                        ← Storage account
├── src/
│   ├── CustomerChatbotAPI/                      ← Python FastAPI backend
│   │   ├── Dockerfile
│   │   ├── pyproject.toml                       ← Dependencies (UV)
│   │   ├── azure_cicd.yaml                      ← CI/CD pipeline
│   │   ├── app/
│   │   │   ├── main.py                          ← FastAPI entry point + lifespan
│   │   │   ├── application.py                   ← Settings (pydantic-settings)
│   │   │   ├── agents/                          ← AI agent definitions
│   │   │   │   ├── chat_agent.py                ← General conversation
│   │   │   │   ├── product_agent.py             ← Product discovery
│   │   │   │   └── policy_agent.py              ← Policy/FAQ
│   │   │   ├── domain/                          ← Entities, enums, models
│   │   │   ├── infrastructure/                  ← Repositories + auth middleware
│   │   │   ├── services/                        ← Orchestrator, voice, product, policy
│   │   │   └── routers/                         ← HTTP/WebSocket route handlers
│   │   └── tests/                               ← 63 backend tests (pytest)
│   │       ├── unit/
│   │       └── integration/
│   └── CustomerChatbotWeb/                      ← React TypeScript frontend
│       ├── Dockerfile
│       ├── package.json                         ← Dependencies (npm)
│       ├── azure_cicd.yaml                      ← CI/CD pipeline
│       └── src/
│           ├── Components/                      ← ChatPanel, MessageBubble, ProductCard, VoiceToggle
│           ├── Hooks/                           ← useAuth, useChat, useVoice
│           ├── Services/                        ← chatApi, voiceApi
│           ├── msal-auth/                       ← MSAL configuration
│           └── types/                           ← Shared TypeScript types
│       └── tests/                               ← 31 frontend tests (vitest)
├── .github/
│   ├── copilot-instructions.md                  ← Repo-level instructions (always active)
│   ├── SDL-with-Copilot-and-Azure.md            ← Full SDL definition (9 phases)
│   ├── reference-catalog.md                     ← Library & template registry
│   ├── PULL_REQUEST_TEMPLATE.md                 ← PR form
│   ├── instructions/                            ← File-based quality instructions
│   │   ├── code-quality-py.instructions.md      ← Python code quality (auto: **.py)
│   │   ├── code-quality-ts.instructions.md      ← TypeScript code quality (auto: **/*.ts)
│   │   ├── code-quality-tsx.instructions.md     ← React code quality (auto: **/*.tsx)
│   │   ├── test-quality.instructions.md         ← Python test quality (auto: tests/**)
│   │   ├── test-quality-ts.instructions.md      ← TypeScript test quality (auto: **/*.test.ts)
│   │   └── test-quality-tsx.instructions.md     ← React test quality (auto: **/*.test.tsx)
│   └── prompts/                                 ← SDL phase prompt files
└── .vscode/
    ├── mcp.json                                 ← MCP servers configuration
    └── agents/                                  ← Subagent system (14 agent files)
```

## Agent Architecture

The template includes a multi-agent subagent system. **Sassy** (the SDL Agent Coordinator) is the only
user-facing agent. It delegates to phase-specific worker agents, each with scoped tool access:

| Agent                     | Phase | Tools                        | MCP Integration                                                                                  |
| ------------------------- | ----- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| Sassy (Coordinator)       | All   | agent, read, search          | GitHub MCP (issue reading + **auth gate**)                                                       |
| Analyst                   | 1-2   | read, search, fetch          | GitHub MCP (**auth required**) + awesome-copilot (planning) + Context7 + ADO MCP (wiki)          |
| Scaffolder                | 3     | read, search, edit, terminal | GitHub MCP (**auth required**) + awesome-copilot (Docker) + Context7 + ADO MCP (wiki)            |
| Deployer                  | 3+8   | read, search, edit, terminal | GitHub MCP (**auth required**) + awesome-copilot (Bicep) + Azure MCP + MS Learn + ADO MCP (wiki) |
| Implementer               | 4     | read, search, edit, terminal | GitHub MCP (**auth required**, live SDK patterns) + awesome-copilot + Context7                   |
| Documenter                | 5     | read, search, edit           | GitHub MCP (**auth required**, ADR examples) + MS Learn                                          |
| QA Coordinator            | 6     | agent, read, search          | Orchestrates 5 parallel reviewers                                                                |
| Architecture Reviewer     | 6     | read, search                 | GitHub MCP (**auth required**, cross-repo pattern search)                                        |
| Azure Compliance Reviewer | 6     | read, search                 | GitHub MCP (**auth required**, live SDK APIs) + awesome-copilot (Bicep)                          |
| Code Quality Reviewer     | 6     | read, search                 | awesome-copilot (commenting, performance, calisthenics)                                          |
| Security Reviewer         | 6     | read, search                 | awesome-copilot (OWASP — loaded fresh every review)                                              |
| Test Coverage Reviewer    | 6     | read, search, terminal       | awesome-copilot (Playwright)                                                                     |
| RAI Reviewer              | 7     | read, search                 | awesome-copilot (AI safety review)                                                               |
| Release Manager           | 8-9   | read, search, edit           | GitHub MCP (**auth required**, PR creation, commit history)                                      |

## SDL Phases

This repository follows a 9-phase Software Development Lifecycle. When working on an issue,
identify which phase(s) it maps to and follow the corresponding rules:

1. **Requirement Analysis** — Clarify problem, goals, constraints, scope
2. **Design** — Choose architecture, Azure services, patterns; reuse reference catalog
3. **Repo Structure & CI/CD** — Align repo layout with templates; update ADO pipelines
4. **Implementation & Tests** — Implement in small steps with tests; follow quality instructions
5. **Repository Documentation** — Update ADRs, API docs, README
6. **QA Activities** — Run automated tests + targeted manual QA
7. **RAI Review** — Assess AI/data risks and mitigations (if applicable)
8. **Release Script Preparation** — Create repeatable release process
9. **Publish to GitHub** — PR with Copilot + human review

## Setup Commands

```bash
# Clone the repository
git clone <REPO_URL>
cd customer-chatbot-gsa

# --- Backend (Python / FastAPI) ---
cd src/CustomerChatbotAPI

# Install dependencies
uv sync
uv sync --group dev

# Copy environment config and edit with your Azure resource values
cp .env.example .env

# Run locally
uv run uvicorn app.main:app --reload --port 8000

# Run tests (63 tests)
uv run pytest

# --- Frontend (React / TypeScript) ---
cd ../CustomerChatbotWeb

# Install dependencies
npm install

# Copy environment config
cp .env .env.local

# Run dev server
npm run dev

# Run tests (31 tests)
npm test

# --- Deploy to Azure ---
cd ../..
azd auth login
azd up
```

## Development Workflow

### Working with Issues

When assigned an issue, you can use either the **agent-driven** or **manual prompt** approach:

**Agent-driven (recommended):**
1. Open Copilot Chat and select the **Sassy** agent.
2. Describe the task — the Coordinator identifies the SDL phase and delegates to the right worker agent.
3. Worker agents fetch live patterns from MCP servers, implement changes, and run quality checks.
4. The QA Coordinator runs 5 parallel reviewers automatically.

**Manual prompt approach:**
1. **Identify SDL phase(s)** — Read the issue and determine which SDL phase it falls under.
2. **Follow the matching prompt file** — Each phase has a prompt file with steps and exit criteria.
3. **Apply quality standards** — The `.github/*-quality*.instructions.md` files auto-apply when editing matching files.
4. **Use reference catalog libraries** — Check `.github/reference-catalog.md` before introducing new dependencies.

### Key Rules

- **GitHub MCP authentication**: All agents that access `mcaps-microsoft` reference repos (sas-cosmosdb, sas-storage, templates)
  require GitHub MCP authentication. Before any workflow, agents perform a lightweight probe call. If authentication fails,
  the agent stops and asks the user to sign in with an account that has `mcaps-microsoft` org access. Agents will not
  proceed with invented or stale patterns — they fall back to local `.github/reference-catalog.md` with a warning.
- **Azure SDK choices**: Use `sas-cosmosdb` (PyPI) for Cosmos DB, `sas-storage` (PyPI) for Blob/Queue.
  Do NOT use raw Azure SDK clients when these libraries cover the use case.
- **Scaffolding**: When creating new services, follow the templates in the reference catalog:
  - General app → `python_application_template`
  - REST API → `python_api_application_template`
  - AI agent → `python_agent_framework_dev_template`
- **Testing**: Always generate tests alongside code. Follow the test-quality instruction files.
- **Documentation**: Every significant change needs at least one doc artifact (ADR, API doc, or README update).
- **Architecture**: Respect layering rules (API → Application → Domain; Infrastructure depends on Domain, not vice versa).

### Reusable Libraries

| Library                                                                                         | PyPI Package   | Use for                                         |
| ----------------------------------------------------------------------------------------------- | -------------- | ----------------------------------------------- |
| [python_cosmosdb_helper](https://github.com/mcaps-microsoft/python_cosmosdb_helper)             | `sas-cosmosdb` | Cosmos DB SQL + MongoDB with Repository Pattern |
| [python_storageaccount_helper](https://github.com/mcaps-microsoft/python_storageaccount_helper) | `sas-storage`  | Azure Blob Storage + Queue operations           |

### Scaffolding Templates

| Template                                                                                                      | Use for                                                                           |
| ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| [python_application_template](https://github.com/mcaps-microsoft/python_application_template)                 | Base app (console, worker, pipeline, CLI) with AppContext + DI + Azure App Config |
| [python_api_application_template](https://github.com/mcaps-microsoft/python_api_application_template)         | FastAPI service                                                                   |
| [python_agent_framework_dev_template](https://github.com/mcaps-microsoft/python_agent_framework_dev_template) | AI agent with Azure AI Foundry + MCP                                              |

## Quality Standards

Quality instruction files auto-apply when editing matching files:

- **Code quality**: Copyright headers, docstrings, naming conventions, comment cleanup, dead code removal, compile/type-check
- **Test quality**: Test sanitization, naming conventions, mocking patterns, assertion style, coverage config

### Python
- Code: `.github/instructions/code-quality-py.instructions.md`
- Tests: `.github/instructions/test-quality.instructions.md`
- Framework: pytest (no pytest-asyncio)

### TypeScript
- Code: `.github/instructions/code-quality-ts.instructions.md`
- Tests: `.github/instructions/test-quality-ts.instructions.md`
- Framework: Vitest

### React (TSX)
- Code: `.github/instructions/code-quality-tsx.instructions.md`
- Tests: `.github/instructions/test-quality-tsx.instructions.md`
- Framework: Vitest + React Testing Library

## Pull Request Guidelines

When creating a pull request:

1. Reference the SDL phase and any design/ADR documents
2. Ensure all quality standards are met (copyright, docstrings, naming, tests)
3. Include at least one documentation update for significant changes
4. Run tests locally before submitting
5. Respond to Copilot code review comments

## Contributing

- Follow the SDL phases for any changes to this template repo
- When adding new instruction files, follow the `.instructions.md` format with `applyTo` front matter
- When adding new prompt files, include SDL phase reference and exit criteria
- When adding new reference catalog entries, follow the format in `.github/reference-catalog.md` Section 3
