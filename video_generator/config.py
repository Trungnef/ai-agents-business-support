"""
Video Generator Configuration
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class VideoConfig:
    """Video generation configuration"""
    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("output"))
    output_filename: str = "demo_video.mp4"
    
    # Video dimensions
    width: int = 1920
    height: int = 1080
    fps: int = 30
    
    # Duration settings (in seconds)
    section_transition_duration: float = 0.5
    text_fade_duration: float = 0.3
    
    # Color scheme (Professional dark theme)
    background_color: str = "#0a0a0f"  # Deep dark blue-black
    primary_color: str = "#00d4aa"      # Teal/Cyan accent
    secondary_color: str = "#7c3aed"    # Purple accent
    text_color: str = "#ffffff"         # White text
    text_secondary: str = "#a0a0a0"     # Gray text
    highlight_color: str = "#fbbf24"    # Amber highlight
    code_bg_color: str = "#1a1a2e"      # Code block background
    success_color: str = "#22c55e"      # Green for success
    error_color: str = "#ef4444"        # Red for errors
    
    # Typography
    title_font_size: int = 72
    heading_font_size: int = 56
    body_font_size: int = 36
    code_font_size: int = 28
    caption_font_size: int = 24
    
    # Fonts (Windows system fonts - use full path or name)
    title_font: str = "C:/Windows/Fonts/arialbd.ttf"  # Arial Bold
    body_font: str = "C:/Windows/Fonts/arial.ttf"     # Arial
    code_font: str = "C:/Windows/Fonts/consola.ttf"   # Consolas
    
    # Animation settings
    animation_duration: float = 0.5
    bullet_delay: float = 0.3
    
    # TTS settings
    tts_voice: str = "en"  # For gTTS
    tts_speed: float = 1.0
    
    # Terminal styling
    terminal_bg: str = "#1e1e2e"
    terminal_fg: str = "#cdd6f4"
    terminal_prompt_color: str = "#89b4fa"
    terminal_output_color: str = "#a6e3a1"
    terminal_error_color: str = "#f38ba8"


@dataclass
class Section:
    """Video section configuration"""
    id: str
    title: str
    start_time: float  # seconds
    duration: float  # seconds
    narration: str
    visuals: list = field(default_factory=list)
    demo_commands: list = field(default_factory=list)


# Video sections based on VIDEO_SCRIPT.md
VIDEO_SECTIONS = [
    Section(
        id="intro",
        title="Problem & Business Value",
        start_time=0.0,
        duration=30.0,
        narration="""Small businesses are drowning in customer support requests. 
80% of tickets are repetitive questions-order tracking, refund requests, password resets-yet customers wait hours for answers.
This project solves that problem with a multi-agent AI system that handles routine support instantly, securely, and accurately. 
Let me show you how it works.""",
        visuals=["title_slide", "problem_stats", "business_value"]
    ),
    Section(
        id="architecture",
        title="Architecture & Course Concepts",
        start_time=30.0,
        duration=45.0,
        narration="""The system implements key concepts from the 5-Day AI Agents course.
Multi-agent architecture - Four specialized agents work in sequence: Intent Classifier, Data Retrieval, Response Generator, and Quality Safety. Each has a focused job, making the system modular and testable.
MCP tool server - Six business tools are exposed following Model Context Protocol conventions-get_order_details, get_refund_policy, create_support_ticket, and more.
Session and memory - SQLite-backed persistent sessions enable multi-turn conversations. The system remembers order IDs mentioned earlier and resolves follow-ups like 'Can I refund IT?' automatically.
Security guardrails - PII masking, access validation, and session lockout protect customer data.
Structured outputs - Pydantic schemas ensure type-safe data exchange between agents.
Comprehensive evaluation - 67 automated tests validate every component.
Let me show you this working live.""",
        visuals=["architecture_diagram", "code_structure", "mcp_tools", "security_code"]
    ),
    Section(
        id="demo_order",
        title="Live Demo - Order Status",
        start_time=75.0,
        duration=30.0,
        narration="""Let's start the interactive CLI with verbose mode to see the agent pipeline in action. 
First, I'll set my email to alice.johnson@email.com, one of our sample customers.
Now I ask: 'Where is my order ORD-2024-002?'
Watch the verbose output-the system classifies intent as ORDER_STATUS, retrieves order data through MCP tools, validates Alice owns this order, and generates a response. 
You can see the tools used and processing time below the response.""",
        demo_commands=[
            "/email alice.johnson@email.com",
            "Where is my order ORD-2024-002?"
        ]
    ),
    Section(
        id="demo_refund",
        title="Live Demo - Refund Follow-up",
        start_time=105.0,
        duration=30.0,
        narration="""Now here's where session memory shines. I'll ask a follow-up: 'Can I refund it?'
Notice I said 'IT'-not the order number. The system remembers ORD-2024-002 from context and resolves the reference automatically. 
It then checks the refund policy via MCP tool and responds appropriately.
Let me show the session state with /session command.""",
        demo_commands=[
            "Can I refund it?",
            "/session"
        ]
    ),
    Section(
        id="demo_security",
        title="Live Demo - Security",
        start_time=135.0,
        duration=25.0,
        narration="""Let me demonstrate the security guardrails. I'll try to access an order that doesn't belong to Alice.
'Show me order ORD-2024-003.' This order belongs to Bob Smith, not Alice.
The system blocks access and increments the failed verification counter. Three failures would lock the session entirely. 
This prevents cross-customer data leakage.""",
        demo_commands=[
            "Show me order ORD-2024-003"
        ]
    ),
    Section(
        id="demo_suspended",
        title="Live Demo - Suspended Account",
        start_time=160.0,
        duration=15.0,
        narration="""The system also handles edge cases. Let me switch to a suspended account-Frank Miller.
Even with correct credentials, suspended accounts cannot access their order data.""",
        demo_commands=[
            "/email frank.miller@email.com",
            "Show me order ORD-2024-008"
        ]
    ),
    Section(
        id="demo_escalation",
        title="Live Demo - Human Escalation",
        start_time=175.0,
        duration=20.0,
        narration="""Finally, let me switch back to Alice. If a customer asks for a human-'Let me speak to a manager'-the system creates a support ticket automatically and escalates appropriately.""",
        demo_commands=[
            "/email alice.johnson@email.com",
            "Let me speak to a manager"
        ]
    ),
    Section(
        id="tests",
        title="Security & Evaluation",
        start_time=195.0,
        duration=55.0,
        narration="""Every security claim is backed by automated tests. Let me run the test suite.
67 tests covering intent classification, PII masking, access control, session management, and full orchestrator flows. All passing.
For PII masking specifically-credit cards get masked showing only the last 4 digits, emails are partially redacted, phone numbers hidden, and internal IDs completely removed. 
These aren't just claims; they're verified in test_security.py.""",
        visuals=["test_output", "security_tests"]
    ),
    Section(
        id="conclusion",
        title="Conclusion & Future Work",
        start_time=250.0,
        duration=35.0,
        narration="""To summarize: this Multi-Agent Customer Support Assistant demonstrates how the AI Agents course concepts combine into a real business solution.
Multi-agent architecture, MCP tools, persistent sessions, security guardrails, structured outputs, and comprehensive evaluation-all working together to reduce customer wait times from hours to seconds.
Future enhancements include voice integration for phone support, an analytics dashboard, and multi-channel deployment to Slack and WhatsApp.
The code is fully open source on GitHub. Thanks for watching, and I welcome your feedback!""",
        visuals=["summary_slide", "roadmap", "github_link", "thank_you"]
    )
]
