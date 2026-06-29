# Video Demo Script

## Multi-Agent Customer Support Assistant for SMBs
**Track:** Agents for Business  
**Duration:** Under 5 minutes

---

## SECTION 1: PROBLEM & BUSINESS VALUE (0:00 - 0:30)

### Visual: Title slide → Problem statistics slide

**NARRATION:**

> "Small businesses are drowning in customer support requests. 80% of tickets are repetitive questions—order tracking, refund requests, password resets—yet customers wait hours for answers.
>
> This project solves that problem with a multi-agent AI system that handles routine support instantly, securely, and accurately. Let me show you how it works."

### Screen Recording Checklist:
- [ ] Title slide with project name and track
- [ ] Animated stat: "80% of tickets are repetitive"
- [ ] Business value bullets appearing

---

## SECTION 2: ARCHITECTURE & COURSE CONCEPTS (0:30 - 1:15)

### Visual: Architecture diagram (Mermaid) → Code snippets

**NARRATION:**

> "The system implements key concepts from the 5-Day AI Agents course:
>
> **Multi-agent architecture** — Four specialized agents work in sequence: Intent Classifier, Data Retrieval, Response Generator, and Quality Safety. Each has a focused job, making the system modular and testable.
>
> **MCP tool server** — Six business tools are exposed following Model Context Protocol conventions—get_order_details, get_refund_policy, create_support_ticket, and more.
>
> **Session and memory** — SQLite-backed persistent sessions enable multi-turn conversations. The system remembers order IDs mentioned earlier and resolves follow-ups like 'Can I refund IT?' automatically.
>
> **Security guardrails** — PII masking, access validation, and session lockout protect customer data.
>
> **Structured outputs** — Pydantic schemas ensure type-safe data exchange between agents.
>
> **Comprehensive evaluation** — 67 automated tests validate every component.
>
> Let me show you this working live."

### Screen Recording Checklist:
- [ ] Show Mermaid architecture diagram from docs/ARCHITECTURE.md
- [ ] Briefly show `src/agents/` folder structure
- [ ] Show `src/mcp_server/server.py` tool list
- [ ] Show `src/memory/session_store.py` briefly
- [ ] Show `src/security/pii_masker.py` patterns
- [ ] Show `src/schemas/` folder for structured outputs

---

## SECTION 3: LIVE DEMO (1:15 - 3:15)

### Visual: Terminal running CLI chat

**SETUP COMMANDS:**
```bash
cd ai-agents-business-support
python -m src.cli chat --verbose
```

> 💡 **TIP:** Use `--verbose` flag to show intent classification, tools used, and processing time for each response.

### Demo Message 1: Order Status (1:15 - 1:45)

**NARRATION:**

> "Let's start the interactive CLI with verbose mode to see the agent pipeline in action. First, I'll set my email to alice.johnson@email.com, one of our sample customers.
>
> Now I ask: 'Where is my order ORD-2024-002?'
>
> Watch the verbose output—the system classifies intent as ORDER_STATUS, retrieves order data through MCP tools, validates Alice owns this order, and generates a response. You can see the tools used and processing time below the response."

**TYPE:**
```
/email alice.johnson@email.com
Where is my order ORD-2024-002?
```

**EXPECTED OUTPUT:**
- Intent: order_status
- Order details retrieved
- Response with shipping status
- **Verbose info:** Intent, Priority, Tools used, Processing time

### Demo Message 2: Refund Follow-up (1:45 - 2:15)

**NARRATION:**

> "Now here's where session memory shines. I'll ask a follow-up: 'Can I refund it?'
>
> Notice I said 'IT'—not the order number. The system remembers ORD-2024-002 from context and resolves the reference automatically. It then checks the refund policy via MCP tool and responds appropriately.
>
> Let me show the session state with /session command."

**TYPE:**
```
Can I refund it?
/session
```

**EXPECTED OUTPUT:**
- Intent: refund_request  
- Context resolution: "it" → ORD-2024-002
- Policy lookup via MCP tool
- Refund eligibility response
- **Session info:** Session ID, verified email, message count, intent history

### Demo Message 3: Security - Cross-Customer Access Block (2:15 - 2:40)

**NARRATION:**

> "Let me demonstrate the security guardrails. I'll try to access an order that doesn't belong to Alice.
>
> 'Show me order ORD-2024-003.' This order belongs to Bob Smith, not Alice.
>
> The system blocks access and increments the failed verification counter. Three failures would lock the session entirely. This prevents cross-customer data leakage."

**TYPE:**
```
Show me order ORD-2024-003
```

**EXPECTED OUTPUT:**
- Access denied message
- No order details leaked (no amount, no items, no tracking)
- Failed attempt counter incremented

### Demo Message 4: Security - Suspended Account (2:40 - 2:55)

**NARRATION:**

> "The system also handles edge cases. Let me switch to a suspended account—Frank Miller.
>
> Even with correct credentials, suspended accounts cannot access their order data."

**TYPE:**
```
/email frank.miller@email.com
Show me order ORD-2024-008
```

**EXPECTED OUTPUT:**
- Account suspended message
- No order access granted

### Demo Message 5: Human Escalation (2:55 - 3:15)

**NARRATION:**

> "Finally, let me switch back to Alice. If a customer asks for a human—'Let me speak to a manager'—the system creates a support ticket automatically and escalates appropriately."

**TYPE:**
```
/email alice.johnson@email.com
Let me speak to a manager
```

**EXPECTED OUTPUT:**
- Intent: human_escalation
- Ticket created with ticket ID
- Escalation acknowledgment

### Screen Recording Checklist:
- [ ] Terminal clear and readable (large font)
- [ ] Use `--verbose` flag when starting chat
- [ ] Show /email command setting context
- [ ] Show each message and response clearly
- [ ] Pause briefly after each response for viewers to read
- [ ] Show /session command to display context state
- [ ] Demonstrate both cross-customer block AND suspended account

---

## SECTION 4: SECURITY & EVALUATION (3:15 - 4:10)

### Visual: Test output → Security code

**NARRATION:**

> "Every security claim is backed by automated tests. Let me run the test suite.
>
> 67 tests covering intent classification, PII masking, access control, session management, and full orchestrator flows. All passing.
>
> For PII masking specifically—credit cards get masked showing only the last 4 digits, emails are partially redacted, phone numbers hidden, and internal IDs completely removed. These aren't just claims; they're verified in test_security.py."

**COMMANDS:**
```bash
# Quick validation
python -m src.cli test all

# Full test suite with details
pytest tests/ -v --tb=short
```

### Screen Recording Checklist:
- [ ] Run `python -m src.cli test all` showing quick validation
- [ ] Run `pytest tests/ -v` briefly showing **67 passed**
- [ ] Show tests/test_security.py file briefly
- [ ] Highlight specific test cases: `test_mask_credit_card_16_digit`, `test_mask_email`, `test_mask_internal_ids`

---

## SECTION 5: CONCLUSION & FUTURE WORK (4:10 - 4:45)

### Visual: Summary slide → Future roadmap

**NARRATION:**

> "To summarize: this Multi-Agent Customer Support Assistant demonstrates how the AI Agents course concepts combine into a real business solution.
>
> Multi-agent architecture, MCP tools, persistent sessions, security guardrails, structured outputs, and comprehensive evaluation—all working together to reduce customer wait times from hours to seconds.
>
> Future enhancements include voice integration for phone support, an analytics dashboard, and multi-channel deployment to Slack and WhatsApp.
>
> The code is fully open source on GitHub. Thanks for watching, and I welcome your feedback!"

### Screen Recording Checklist:
- [ ] Summary slide showing course concepts ✓
- [ ] Future roadmap bullets
- [ ] GitHub link displayed
- [ ] Thank you / contact slide

---

## ⏱️ TIMING BUFFER NOTES

| Section | Target | Buffer | Notes |
|---------|--------|--------|-------|
| Section 1: Problem | 0:30 | ±5s | Keep tight, avoid rambling |
| Section 2: Architecture | 0:45 | ±10s | Can trim if running long |
| Section 3: Live Demo | 2:00 | ±15s | **Highest variance** - practice commands |
| Section 4: Tests | 0:55 | ±10s | Can skip full pytest output if short on time |
| Section 5: Conclusion | 0:35 | ±5s | Fixed closing |
| **Total** | **4:45** | Buffer to 5:00 | **15 seconds safety margin** |

> ⚠️ **If running over 4:45:** Skip Demo Message 4 (suspended account) and reduce test output display.

---

## SCREEN RECORDING MASTER CHECKLIST

### Before Recording:
- [ ] Terminal font size: 16pt minimum
- [ ] Clear terminal history
- [ ] Fresh virtual environment activated
- [ ] Sample data loaded (data/*.csv exists)
- [ ] No API key needed (rule-based fallback works)

### Recording Software Settings:
- [ ] Resolution: 1920x1080 or 1280x720
- [ ] Frame rate: 30fps
- [ ] Audio: Clear microphone, minimal background noise
- [ ] Cursor highlight enabled

### Files to Have Open:
- [ ] `docs/ARCHITECTURE.md` (for diagram)
- [ ] `src/agents/` folder
- [ ] `src/mcp_server/server.py`
- [ ] `src/security/pii_masker.py`
- [ ] Terminal ready in project root

### Demo Commands Quick Reference:
```bash
# Start demo (USE VERBOSE!)
python -m src.cli chat --verbose

# In chat:
/email alice.johnson@email.com
Where is my order ORD-2024-002?
Can I refund it?
/session
Show me order ORD-2024-003
/email frank.miller@email.com
Show me order ORD-2024-008
/email alice.johnson@email.com
Let me speak to a manager
/quit

# Run tests
python -m src.cli test all
pytest tests/ -v
```

### Sample Data Quick Reference:
| Customer | Email | Notes |
|----------|-------|-------|
| Alice Johnson | alice.johnson@email.com | Active, Gold tier, owns ORD-2024-002 |
| Bob Smith | bob.smith@email.com | Active, owns ORD-2024-003 |
| Frank Miller | frank.miller@email.com | **SUSPENDED**, owns ORD-2024-008 |

| Order ID | Owner | Status | Demo Use |
|----------|-------|--------|----------|
| ORD-2024-002 | Alice | shipped | Order status + refund |
| ORD-2024-003 | Bob | processing | Cross-customer block |
| ORD-2024-008 | Frank | cancelled | Suspended account demo |

---

## BACKUP DEMO COMMANDS (if CLI has issues)

```bash
# Single query mode (non-interactive)
python -m src.cli ask "Where is my order ORD-2024-002?" --email alice.johnson@email.com --verbose

# FastAPI server (alternative demo)
uvicorn src.api.app:app --reload --port 8000
# Then show Swagger docs at http://localhost:8000/docs
```

---

## 🎬 PRE-RECORDING CHECKLIST

### 1 Hour Before:
- [ ] Run full test suite to ensure everything passes
- [ ] Practice the demo flow 2-3 times
- [ ] Clear terminal history
- [ ] Close unnecessary applications

### 10 Minutes Before:
- [ ] Open VS Code with project loaded
- [ ] Open terminal in project root
- [ ] Open docs/ARCHITECTURE.md for diagram
- [ ] Set terminal font to 16pt+
- [ ] Test microphone audio levels

### During Recording:
- [ ] Speak slowly and clearly
- [ ] Pause 2-3 seconds after each response for viewers to read
- [ ] If you make a mistake, pause and re-record that section

---

**Video Length Target:** 4:30 - 4:45 (with 15s buffer)  
**Upload:** YouTube (Public or Unlisted per competition rules)  
**Deadline:** July 6, 2026 23:59 PT
