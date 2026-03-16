# Contributing

Thank you for your interest in contributing to the Customer Chatbot GSA!

## Getting Started

1. Fork the repository
2. Create a feature branch from `main`
3. Follow the SDL phases outlined in `AGENTS.md`
4. Ensure all tests pass before submitting a PR
5. Fill out the PR template completely

## Development Setup

### Backend (Python)
```bash
cd src/CustomerChatbotAPI
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

### Frontend (React/TypeScript)
```bash
cd src/CustomerChatbotWeb
npm install
npm run dev
```

## Code Quality

- Python: Follow `.github/instructions/code-quality-py.instructions.md`
- TypeScript: Follow `.github/instructions/code-quality-ts.instructions.md`
- React: Follow `.github/instructions/code-quality-tsx.instructions.md`
- Tests: Follow the test-quality instruction files

## Pull Request Guidelines

- Reference the SDL phase and related design/ADR documents
- Include tests for all non-trivial changes
- Update documentation as needed
- Respond to code review comments promptly
