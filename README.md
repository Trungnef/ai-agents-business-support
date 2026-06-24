# Multi-Agent Customer Support Assistant for SMBs

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-66%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-ready multi-agent system for automating customer support in small and medium businesses. Built for the **Kaggle Capstone "5-Day Gen AI Intensive"** competition.

**🏆 Track:** Agents for Business  
**📺 Demo Video:** [YouTube Link](https://youtu.be/YOUR_VIDEO_ID)  
**📝 Kaggle Writeup:** [docs/KAGGLE_WRITEUP_DRAFT.md](docs/KAGGLE_WRITEUP_DRAFT.md)

## 🎯 Project Overview

This system demonstrates real AI agent concepts by handling customer support requests through a coordinated multi-agent pipeline:

1. **Intent Classification** - Understands what the customer needs
2. **Data Retrieval** - Fetches relevant order/account information securely
3. **Response Generation** - Creates helpful, accurate replies
4. **Quality Assurance** - Ensures safety and compliance

### Business Value

- ⏱️ **Reduces response time** from hours to seconds
- 🎯 **Accurate routing** of requests by intent and priority
- 🔒 **Security-first design** protects customer data
- 📊 **Audit trail** for compliance and improvement

## 🏗️ Architecture

```
User Message → Orchestrator → Intent Classifier → MCP Tools → Data Retrieval 
                                                      ↓
            Final Response ← Quality Agent ← Response Generator ← Security Check
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams and component descriptions.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google AI API key (optional - system works with rule-based fallback)

### Installation

```bash
# Clone the repository
git clone https://github.com/Trungnef/ai-agents-business-support.git
cd ai-agents-business-support

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Run the Demo

```bash
# Interactive chat mode
python -m src.cli chat

# Single query
python -m src.cli ask "Where is my order ORD-2024-002?" --email alice.johnson@email.com

# Run with verbose output
python -m src.cli ask "I want a refund for order ORD-2024-005" --email carol.white@email.com --verbose

# Quick validation tests
python -m src.cli test all
```

### Run FastAPI Server

```bash
# Start the REST API server
uvicorn src.api.app:app --reload --port 8000

# Or use Python directly
python -m src.api.app

# Then access:
# - API docs: http://localhost:8000/docs
# - Chat endpoint: POST http://localhost:8000/chat
```

### Run Tests

```bash
# All tests (66 tests)
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test categories
pytest tests/test_intent.py -v
pytest tests/test_security.py -v
```

## 📁 Project Structure

```
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── intent_classifier.py
│   │   ├── data_retrieval.py
│   │   ├── response_generator.py
│   │   └── quality_safety.py
│   ├── tools/            # Business logic tools
│   ├── mcp_server/       # MCP tool server
│   ├── orchestrator/     # Agent coordination
│   ├── memory/           # Session persistence (SQLite)
│   ├── api/              # FastAPI REST endpoints
│   ├── security/         # PII masking, validation
│   ├── schemas/          # Pydantic models
│   ├── eval/             # Evaluation framework
│   └── cli.py            # CLI entrypoint
├── data/                 # Sample datasets
├── tests/                # Test suite
├── docs/                 # Documentation
└── requirements.txt
```

## 🔧 Supported Intents

| Intent | Description | Example |
|--------|-------------|---------|
| `refund_request` | Customer wants money back | "I'd like a refund for my order" |
| `order_status` | Checking order/delivery | "Where is my package?" |
| `billing_issue` | Payment problems | "I was charged twice" |
| `account_access` | Login issues | "I can't access my account" |
| `shipping_issue` | Delivery problems | "Package shows delivered but I didn't get it" |
| `human_escalation` | Wants human agent | "Let me speak to a manager" |
| `other` | Unclassified | General questions |

## 🛡️ Security Features

- **PII Masking**: Credit cards, emails, phone numbers automatically masked
- **Access Validation**: Orders only accessible by verified owner
- **Session Security**: Lockout after failed verification attempts
- **Audit Logging**: All operations logged for compliance

## 📚 Course Concepts Implemented

| Concept | Location | Description |
|---------|----------|-------------|
| ADK Multi-Agent | `src/agents/` | 4 specialized agents with rule-based fallback |
| MCP Server | `src/mcp_server/` | 6 business tools exposed via MCP-compatible API |
| Skills/CLI | `src/cli.py` | Interactive demo with chat mode and testing |
| Session State | `src/memory/`, `src/orchestrator/` | SQLite persistence + multi-turn memory |
| Security | `src/security/` | PII masking, access control, guardrails |
| Evaluation | `src/eval/`, `tests/` | 66 behavioral tests covering all components |
| REST API | `src/api/app.py` | FastAPI endpoint for integration |

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and Mermaid diagrams
- [Kaggle Writeup](docs/KAGGLE_WRITEUP_DRAFT.md) - Competition submission (~2,100 words)
- [Video Script](docs/VIDEO_SCRIPT.md) - Demo video outline with narration
- [Demo Commands](docs/DEMO_COMMANDS.md) - Quick reference for all commands
- [Submission Checklist](docs/SUBMISSION_CHECKLIST.md) - Pre-submission verification
- [Evaluation](docs/EVALUATION.md) - Test results and metrics

## 🧪 Sample Data

The `data/` folder contains realistic sample data:

- `customers.csv` - 10 customer profiles
- `orders.csv` - 15 orders with various statuses
- `refund_policies.json` - Refund eligibility rules
- `support_tickets.csv` - Existing tickets

## 🤝 Contributing

This is a competition project, but feedback is welcome! Please open an issue for bugs or suggestions.

## � Quick Validation

```bash
# Verify everything works in one command
python -m src.cli test all

# Expected output:
# ✓ Intent classification tests passed
# ✓ PII masking tests passed
# ✓ Order authorization tests passed
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Google AI for the 5-Day Gen AI Intensive course
- Kaggle for hosting the Capstone competition
- The MCP community for protocol specifications

---

**Built with ❤️ for the Kaggle AI Agents Capstone 2026**


