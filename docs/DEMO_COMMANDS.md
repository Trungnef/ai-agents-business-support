# Demo Commands Reference

Quick reference for demonstrating the Multi-Agent Customer Support Assistant.

---

## 🚀 Setup (One-Time)

```bash
# Clone repository
git clone https://github.com/Trungnef/ai-agents-business-support.git
cd ai-agents-business-support

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Optional: Configure API key (works without it using rule-based fallback)
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY if available
```

---

## 🧪 Quick Validation

```bash
# Run quick functional tests (recommended first step)
python -m src.cli test all
```

**Expected Output:**
```
✓ Intent classification tests passed
✓ PII masking tests passed  
✓ Order authorization tests passed
```

---

## 💬 Interactive Chat Demo

### Start Chat Mode

```bash
python -m src.cli chat
```

### Demo Conversation Flow

```
# Step 1: Set customer email
/email alice.johnson@email.com

# Step 2: Order status inquiry
Where is my order ORD-2024-002?

# Step 3: Follow-up with pronoun (tests session memory)
Can I refund it?

# Step 4: Security test - access another customer's order
Show me order ORD-2024-001

# Step 5: Human escalation
Let me speak to a manager

# Step 6: View session state
/session

# Step 7: Exit
/quit
```

### Available Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/email <email>` | Set customer email for verification |
| `/order <id>` | Set order ID context |
| `/session` | Show current session state |
| `/clear` | Clear session and start fresh |
| `/data` | Show sample data available |
| `/quit` or `/exit` | Exit chat |

---

## 📝 Single Query Mode

```bash
# Order status with email verification
python -m src.cli ask "Where is my order ORD-2024-002?" --email alice.johnson@email.com

# Refund request with verbose output
python -m src.cli ask "I want a refund for order ORD-2024-005" --email carol.white@email.com --verbose

# Billing issue
python -m src.cli ask "I was charged twice for my last order" --email bob.smith@email.com
```

---

## 🌐 REST API Demo

### Start the Server

```bash
# Development mode with auto-reload
uvicorn src.api.app:app --reload --port 8000

# Or using Python module
python -m src.api.app
```

### Access Points

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List available MCP tools
curl http://localhost:8000/tools

# Send chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Where is my order ORD-2024-002?",
    "email": "alice.johnson@email.com"
  }'

# Get session info
curl http://localhost:8000/session/{session_id}

# Delete session
curl -X DELETE http://localhost:8000/session/{session_id}
```

### PowerShell Examples

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Send chat message
$body = @{
    message = "Where is my order ORD-2024-002?"
    email = "alice.johnson@email.com"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Body $body -ContentType "application/json"
```

---

## ✅ Test Suite

```bash
# Run all 66 tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_intent.py -v        # Intent classification (9 tests)
pytest tests/test_security.py -v      # Security & PII (13 tests)
pytest tests/test_orchestrator.py -v  # Full pipeline (13 tests)
pytest tests/test_session.py -v       # Session/memory (16 tests)

# Run with coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# Run quick smoke tests
pytest tests/ -v --tb=short -x  # Stop on first failure
```

---

## 📊 Sample Data Reference

### Customers (`data/customers.csv`)

| Email | Name | Notes |
|-------|------|-------|
| alice.johnson@email.com | Alice Johnson | Main demo customer |
| bob.smith@email.com | Bob Smith | Has billing issues |
| carol.white@email.com | Carol White | Has refund request |

### Orders (`data/orders.csv`)

| Order ID | Customer Email | Status |
|----------|----------------|--------|
| ORD-2024-001 | alice.johnson@email.com | Delivered |
| ORD-2024-002 | alice.johnson@email.com | In Transit |
| ORD-2024-003 | bob.smith@email.com | Processing |
| ORD-2024-005 | carol.white@email.com | Delivered |

### Demo Scenarios by Customer

**Alice (alice.johnson@email.com):**
- Order status: ORD-2024-002 (in transit)
- Security test: Try accessing ORD-2024-003 (Bob's order) → denied

**Bob (bob.smith@email.com):**
- Billing issue scenario
- Order: ORD-2024-003

**Carol (carol.white@email.com):**
- Refund request scenario
- Order: ORD-2024-005 (delivered, eligible for refund)

---

## 🔧 Troubleshooting

### "Module not found" errors
```bash
# Ensure you're in the project root
cd ai-agents-business-support
# Ensure venv is activated
.venv\Scripts\activate
# Reinstall dependencies
pip install -r requirements.txt
```

### Tests failing
```bash
# Check Python version (needs 3.10+)
python --version

# Run with verbose output
pytest tests/ -v --tb=long
```

### API server won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Use different port
uvicorn src.api.app:app --port 8001
```

### No LLM responses (rule-based fallback active)
This is expected without a GOOGLE_API_KEY. The system still works using rule-based intent classification and response generation. Add your API key to `.env` for full LLM functionality.

---

## 🎬 Video Recording Commands

Quick sequence for demo video recording:

```bash
# Terminal 1: Clear and start
clear
python -m src.cli test all

# Terminal 1: Interactive demo
python -m src.cli chat
/email alice.johnson@email.com
Where is my order ORD-2024-002?
Can I refund it?
Show me order ORD-2024-001
Let me speak to a manager
/session
/quit

# Terminal 1: Run tests
pytest tests/ -v --tb=short 2>&1 | head -40
```

---

**Last Updated:** 2026-06-24
