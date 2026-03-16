# Release Checklist — Customer Chatbot GSA with Voice

> Use this checklist for every release. Copy into the release PR body or track
> progress directly in this file on a release branch.

## Version

- **Release version:** `0.1.0`
- **Release date:** _TBD_
- **Target environment:** _dev / staging / prod_
- **Release manager:** _@handle_

---

## Pre-Release Checks

### 1. Code Completeness

- [ ] All planned features for this release are merged
- [ ] No open blockers or critical issues
- [ ] Feature branches have been merged into the release branch

### 2. Testing (113 tests total)

| Suite | Command | Count | Status |
|-------|---------|-------|--------|
| Backend unit | `cd src/CustomerChatbotAPI && uv run pytest tests/unit/ -q` | 72 | ⬜ |
| Backend integration | `cd src/CustomerChatbotAPI && uv run pytest tests/integration/ -q` | 10 | ⬜ |
| Frontend | `cd src/CustomerChatbotWeb && npx vitest run` | 31 | ⬜ |

- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Test coverage is acceptable (`uv run pytest --cov`)

### 3. Code Quality

- [ ] Python code quality verified (`.github/instructions/code-quality-py.instructions.md`)
- [ ] TypeScript code quality verified (`.github/instructions/code-quality-ts.instructions.md`)
- [ ] React/TSX code quality verified (`.github/instructions/code-quality-tsx.instructions.md`)
- [ ] Copyright headers present on all source files
- [ ] No secrets, credentials, or PII in code
- [ ] No dead code, unused imports, or commented-out blocks

### 4. Docker Builds

- [ ] API image builds: `docker build -t customer-chatbot-api -f src/CustomerChatbotAPI/Dockerfile src/CustomerChatbotAPI`
- [ ] Web image builds: `docker build -t customer-chatbot-web -f src/CustomerChatbotWeb/Dockerfile src/CustomerChatbotWeb`

### 5. Documentation

- [ ] [README.md](../README.md) is up to date
- [ ] [Design doc](../docs/design/customer-chatbot-voice-design.md) reflects current state
- [ ] [ADR-0002](../docs/adr/ADR-0002-customer-chatbot-voice-architecture.md) is current
- [ ] [API docs](../docs/api/chatbot-api.md) match implemented endpoints
- [ ] Component READMEs updated (`src/CustomerChatbotAPI/README.md`, `src/CustomerChatbotWeb/README.md`)

### 6. Infrastructure

- [ ] `azure.yaml` services (`api`, `web`) are correctly configured
- [ ] All 8 Bicep modules present in `infra/modules/`
- [ ] `infra/main.bicep` provisions all required resources:
  - Log Analytics, Container Registry, Container Apps Environment
  - Cosmos DB, Storage Account, AI Search
  - Azure OpenAI, Key Vault

### 7. RAI Review

- [ ] RAI review completed (or explicitly deferred with justification)

---

## Deployment

### Automated (recommended)

```powershell
# Dry run — validates everything without deploying
.\scripts\deploy.ps1 -DryRun

# Full deployment
.\scripts\deploy.ps1

# Deploy to a specific environment
.\scripts\deploy.ps1 -Environment staging
```

### Manual

```bash
# 1. Authenticate
azd auth login

# 2. Select environment
azd env select <environment-name>

# 3. Provision infrastructure + deploy apps
azd up
```

---

## Post-Deployment Verification

- [ ] API health probe responds: `GET <api-url>/healthz`
- [ ] Frontend loads in browser
- [ ] Chat conversation works end-to-end (text)
- [ ] Voice interaction works (if deployed with Voice Live API)
- [ ] Product search returns results
- [ ] Policy FAQ returns answers
- [ ] Application Insights shows no new errors
- [ ] Cosmos DB RU consumption is within expected range
- [ ] Container App readiness/liveness probes passing

---

## Rollback Plan

If issues are detected post-deployment:

1. **Redeploy previous version:** `azd deploy --from-package <previous-version>`
2. **Or rollback via Container Apps revision management** in Azure Portal
3. **Feature flags:** Disable new features if available
4. **Notify:** Comment on the release PR with findings
5. **Post-mortem:** Create a work item to document the issue

---

## SDL Exit Criteria (Phases 8-9)

| Criterion | Status |
|-----------|--------|
| All automated tests pass | ⬜ |
| Code quality verified by QA | ⬜ |
| Documentation updated | ⬜ |
| RAI review completed (or deferred) | ⬜ |
| PR follows `.github/PULL_REQUEST_TEMPLATE.md` | ⬜ |
| Release checklist completed | ⬜ |
| Deployment repeatable via `azd up` | ⬜ |

---

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Release Manager | | | ⬜ |
| QA Lead | | | ⬜ |
| Tech Lead | | | ⬜ |
