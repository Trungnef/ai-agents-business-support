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

## SECTION 2: ARCHITECTURE & COURSE CONCEPTS (0:30 - 1:20)

### Visual: Architecture diagram (Mermaid) → Code snippets

**NARRATION:**

> "The system implements all seven course concepts from the 5-Day AI Agents course.
>
> First, **multi-agent architecture**. Four specialized agents work in sequence: Intent Classifier, Data Retrieval, Response Generator, and Quality Safety. Each has a focused job, making the system modular and testable.
>
> Second, **MCP tool server**. Six business tools are exposed following Model Context Protocol conventions—get_order_details, get_refund_policy, create_support_ticket, and more.
>
> Third, **session and memory**. SQLite-backed persistent sessions enable multi-turn conversations. The system remembers order IDs mentioned earlier and resolves follow-ups like 'Can I refund IT?' automatically.
>
> Fourth, **security guardrails**. PII masking, access validation, and session lockout protect customer data. Let me show you this working live."

### Screen Recording Checklist:
- [ ] Show Mermaid architecture diagram from docs/ARCHITECTURE.md
- [ ] Briefly show `src/agents/` folder structure
- [ ] Show `src/mcp_server/server.py` tool list
- [ ] Show `src/memory/session_store.py` briefly
- [ ] Show `src/security/pii_masker.py` patterns

---

## SECTION 3: LIVE DEMO (1:20 - 3:20)

### Visual: Terminal running CLI chat

**SETUP COMMANDS:**
```bash
cd ai-agents-business-support
python -m src.cli chat
```

### Demo Message 1: Order Status (1:20 - 1:50)

**NARRATION:**

> "Let's start the interactive CLI. First, I'll set my email to alice.johnson@email.com, one of our sample customers.
>
> Now I ask: 'Where is my order ORD-2024-002?'
>
> Watch the system classify the intent as ORDER_STATUS, retrieve the order data through MCP tools, validate that Alice owns this order, and generate a response—all in under a second."

**TYPE:**
```
/email alice.johnson@email.com
Where is my order ORD-2024-002?
```

**EXPECTED OUTPUT:**
- Intent: order_status
- Order details retrieved
- Response with shipping status

### Demo Message 2: Refund Follow-up (1:50 - 2:30)

**NARRATION:**

> "Now here's where session memory shines. I'll ask a follow-up: 'Can I refund it?'
>
> Notice I said 'IT'—not the order number. The system remembers ORD-2024-002 from context and resolves the reference automatically. It then checks the refund policy and responds appropriately."

**TYPE:**
```
Can I refund it?
```

**EXPECTED OUTPUT:**
- Intent: refund_request  
- Context resolution: "it" → ORD-2024-002
- Policy lookup via MCP tool
- Refund eligibility response

### Demo Message 3: Security Demonstration (2:30 - 3:00)

**NARRATION:**

> "Let me demonstrate the security guardrails. I'll try to access an order that doesn't belong to Alice.
>
> 'Show me order ORD-2024-001.' This order belongs to a different customer.
>
> The system blocks access and increments the failed verification counter. Three failures would lock the session entirely. This prevents cross-customer data leakage."

**TYPE:**
```
Show me order ORD-2024-001
```

**EXPECTED OUTPUT:**
- Access denied message
- No order details leaked

### Demo Message 4: Human Escalation (3:00 - 3:20)

**NARRATION:**

> "Finally, if a customer asks for a human—'Let me speak to a manager'—the system creates a support ticket automatically and escalates appropriately."

**TYPE:**
```
Let me speak to a manager
```

**EXPECTED OUTPUT:**
- Intent: human_escalation
- Ticket created
- Escalation acknowledgment

### Screen Recording Checklist:
- [ ] Terminal clear and readable (large font)
- [ ] Show /email command setting context
- [ ] Show each message and response clearly
- [ ] Pause briefly after each response for viewers to read
- [ ] Show /session command to display context state

---

## SECTION 4: SECURITY & EVALUATION (3:20 - 4:20)

### Visual: Test output → Security code

**NARRATION:**

> "Every security claim is backed by automated tests. Let me run the test suite.
>
> 66 tests covering intent classification, PII masking, access control, session management, and full orchestrator flows. All passing.
>
> For PII masking specifically—credit cards get masked showing only the last 4 digits, emails are partially redacted, internal IDs are completely hidden. These aren't just claims; they're verified in test_security.py."

**COMMANDS:**
```bash
python -m src.cli test all
pytest tests/test_security.py -v --tb=short
```

### Screen Recording Checklist:
- [ ] Run `python -m src.cli test all` showing quick validation
- [ ] Run `pytest tests/ -v` briefly showing 66 passed
- [ ] Show tests/test_security.py file briefly
- [ ] Highlight PII masking test cases

---

## SECTION 5: CONCLUSION & FUTURE WORK (4:20 - 5:00)

### Visual: Summary slide → Future roadmap

**NARRATION:**

> "To summarize: this Multi-Agent Customer Support Assistant demonstrates how the AI Agents course concepts combine into a real business solution.
>
> ADK-style agents, MCP tools, persistent sessions, security guardrails, and comprehensive testing—all working together to reduce customer wait times from hours to seconds.
>
> Future enhancements include voice integration for phone support, an analytics dashboard, and multi-channel deployment to Slack and WhatsApp.
>
> The code is fully open source on GitHub. Thanks for watching, and I welcome your feedback!"

### Screen Recording Checklist:
- [ ] Summary slide showing 7 course concepts ✓
- [ ] Future roadmap bullets
- [ ] GitHub link displayed
- [ ] Thank you / contact slide

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
# Start demo
python -m src.cli chat

# In chat:
/email alice.johnson@email.com
Where is my order ORD-2024-002?
Can I refund it?
Show me order ORD-2024-001
Let me speak to a manager
/session
/quit

# Run tests
python -m src.cli test all
pytest tests/ -v
```

---

## BACKUP DEMO COMMANDS (if CLI has issues)

```bash
# Single query mode
python -m src.cli ask "Where is my order ORD-2024-002?" --email alice.johnson@email.com --verbose

# FastAPI server
uvicorn src.api.app:app --reload --port 8000
# Then show Swagger docs at http://localhost:8000/docs
```

---

**Video Length Target:** 4:30 - 5:00  
**Upload:** YouTube (Public or Unlisted per competition rules)
