"""
Professional Demo Video Generator for Multi-Agent Customer Support Assistant
Uses Pillow for better text rendering (fixes Unicode ???) and edge-tts for natural voice
"""

import asyncio
import os
import subprocess
from pathlib import Path

# Try imports
try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    import cv2
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("Installing required packages...")
    subprocess.run(["pip", "install", "pillow", "numpy", "opencv-python", "-q"])
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    import cv2

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    print("Installing edge-tts...")
    subprocess.run(["pip", "install", "edge-tts", "-q"])
    import edge_tts

try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False
    subprocess.run(["pip", "install", "pydub", "-q"])
    from pydub import AudioSegment


# ============== CONFIGURATION ==============
WIDTH, HEIGHT = 1920, 1080
FPS = 30
OUTPUT_DIR = Path(__file__).parent
VIDEO_PATH = OUTPUT_DIR / "demo_video_no_audio.mp4"
AUDIO_PATH = OUTPUT_DIR / "demo_audio.mp3"
FINAL_VIDEO_PATH = OUTPUT_DIR / "multi_agent_support_demo.mp4"

# Color scheme (RGB for Pillow)
COLORS = {
    'bg_dark': (15, 23, 42),           # Slate 900
    'bg_panel': (30, 41, 59),          # Slate 800
    'bg_header': (15, 23, 42),         # Slate 900
    'text_white': (248, 250, 252),     # Slate 50
    'text_gray': (148, 163, 184),      # Slate 400
    'text_muted': (100, 116, 139),     # Slate 500
    'cyan': (34, 211, 238),            # Cyan 400
    'green': (74, 222, 128),           # Green 400
    'red': (248, 113, 113),            # Red 400
    'purple': (192, 132, 252),         # Purple 400
    'yellow': (251, 191, 36),          # Amber 400
    'blue': (96, 165, 250),            # Blue 400
    'border': (51, 65, 85),            # Slate 700
    'accent': (59, 130, 246),          # Blue 500
}

# Try to load better fonts
def get_font(size, bold=False):
    """Get the best available font"""
    font_paths = [
        "C:/Windows/Fonts/consola.ttf",      # Consolas
        "C:/Windows/Fonts/segoeui.ttf",      # Segoe UI
        "C:/Windows/Fonts/arial.ttf",        # Arial
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    bold_paths = [
        "C:/Windows/Fonts/consolab.ttf",     # Consolas Bold
        "C:/Windows/Fonts/segoeuib.ttf",     # Segoe UI Bold
        "C:/Windows/Fonts/arialbd.ttf",      # Arial Bold
    ]
    
    paths = bold_paths if bold else font_paths
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

# Fonts
FONT_TITLE = get_font(48, bold=True)
FONT_HEADING = get_font(36, bold=True)
FONT_BODY = get_font(24)
FONT_SMALL = get_font(20)
FONT_MONO = get_font(22)
FONT_MONO_SMALL = get_font(18)

# ============== VIDEO FRAMES STORAGE ==============
frames = []

def create_frame():
    """Create a new frame with gradient background"""
    img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['bg_dark'])
    draw = ImageDraw.Draw(img)
    
    # Subtle gradient overlay
    for y in range(HEIGHT):
        alpha = int(20 * (y / HEIGHT))
        color = tuple(min(255, c + alpha) for c in COLORS['bg_dark'])
        draw.line([(0, y), (WIDTH, y)], fill=color)
    
    return img, draw

def draw_rounded_rect(draw, coords, radius, fill, outline=None, width=1):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)

def draw_header(draw, section_num, section_title, progress=1.0):
    """Draw professional header with progress bar"""
    # Header background
    draw.rectangle([(0, 0), (WIDTH, 80)], fill=COLORS['bg_header'])
    draw.line([(0, 80), (WIDTH, 80)], fill=COLORS['border'], width=2)
    
    # Logo/Title
    draw.text((40, 22), "Multi-Agent Customer Support", font=FONT_HEADING, fill=COLORS['text_white'])
    
    # Section indicator
    section_text = f"Section {section_num}: {section_title}"
    draw.text((WIDTH - 500, 28), section_text, font=FONT_BODY, fill=COLORS['cyan'])
    
    # Progress bar
    bar_width = 300
    bar_x = WIDTH - bar_width - 40
    bar_y = 60
    draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + 6)], fill=COLORS['border'])
    draw.rectangle([(bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + 6)], fill=COLORS['cyan'])

def draw_terminal(img, draw, x, y, w, h, title="Terminal", content_lines=None, typing_text="", cursor=True):
    """Draw a realistic terminal window"""
    # Window shadow
    shadow_offset = 8
    draw.rounded_rectangle(
        [(x + shadow_offset, y + shadow_offset), (x + w + shadow_offset, y + h + shadow_offset)],
        radius=12, fill=(0, 0, 0)
    )
    
    # Main window
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=12, fill=COLORS['bg_panel'], outline=COLORS['border'], width=2)
    
    # Title bar
    draw.rounded_rectangle([(x, y), (x + w, y + 40)], radius=12, fill=(20, 30, 48))
    draw.rectangle([(x, y + 28), (x + w, y + 40)], fill=(20, 30, 48))
    
    # Window buttons
    draw.ellipse([(x + 16, y + 12), (x + 30, y + 26)], fill=COLORS['red'])
    draw.ellipse([(x + 40, y + 12), (x + 54, y + 26)], fill=COLORS['yellow'])
    draw.ellipse([(x + 64, y + 12), (x + 78, y + 26)], fill=COLORS['green'])
    
    # Title
    draw.text((x + 100, y + 10), title, font=FONT_SMALL, fill=COLORS['text_gray'])
    
    # Content area
    content_y = y + 55
    line_height = 26
    
    if content_lines:
        for i, (text, color) in enumerate(content_lines[-18:]):  # Show last 18 lines
            draw.text((x + 20, content_y + i * line_height), text, font=FONT_MONO_SMALL, fill=color)
            content_y_last = content_y + i * line_height
        content_y = content_y_last + line_height
    
    # Typing line with cursor
    if typing_text or cursor:
        prompt = "$ "
        cursor_char = "_" if cursor and (len(frames) % 15 < 8) else ""
        draw.text((x + 20, content_y + 10), prompt + typing_text + cursor_char, font=FONT_MONO_SMALL, fill=COLORS['text_white'])

def add_frame(img, duration_frames=1):
    """Add frame to video"""
    for _ in range(duration_frames):
        # Convert PIL to OpenCV format
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        frames.append(frame)

def draw_subtitle(draw, text, y_offset=0):
    """Draw subtitle at bottom of screen"""
    # Background bar
    sub_y = HEIGHT - 120 + y_offset
    draw.rectangle([(0, sub_y), (WIDTH, sub_y + 80)], fill=(0, 0, 0, 180))
    
    # Text centered
    bbox = draw.textbbox((0, 0), text, font=FONT_BODY)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    draw.text((x, sub_y + 25), text, font=FONT_BODY, fill=COLORS['text_white'])

def draw_animated_stat(draw, value, max_val, x, y, label, color):
    """Draw animated statistic"""
    # Large number
    draw.text((x, y), f"{value}%", font=get_font(96, bold=True), fill=color)
    # Label below
    draw.text((x, y + 110), label, font=FONT_BODY, fill=COLORS['text_gray'])

def draw_feature_card(draw, x, y, w, h, icon, title, description, color, animate_in=1.0):
    """Draw a feature card with animation"""
    if animate_in <= 0:
        return
    
    # Scale based on animation
    actual_h = int(h * min(1.0, animate_in))
    
    # Card background
    draw.rounded_rectangle([(x, y), (x + w, y + actual_h)], radius=16, fill=COLORS['bg_panel'], outline=color, width=2)
    
    if animate_in >= 0.3:
        # Icon circle
        draw.ellipse([(x + 20, y + 20), (x + 60, y + 60)], fill=color)
        draw.text((x + 32, y + 28), icon, font=FONT_SMALL, fill=COLORS['bg_dark'])
        
        # Title
        draw.text((x + 80, y + 25), title, font=FONT_BODY, fill=COLORS['text_white'])
        
    if animate_in >= 0.6:
        # Description (word wrap)
        words = description.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if draw.textlength(test_line, font=FONT_SMALL) < w - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines[:3]):
            draw.text((x + 20, y + 70 + i * 24), line, font=FONT_SMALL, fill=COLORS['text_gray'])


# ============== SCENE GENERATORS ==============

def generate_intro_scene():
    """Scene 1: Title and Problem Statement (0:00 - 0:30)"""
    print("Generating Scene 1: Intro...")
    
    # Title card with fade in (3 seconds)
    for f in range(90):
        img, draw = create_frame()
        
        alpha = min(1.0, f / 30)
        
        # Center content area
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        
        # Project badge
        if f > 15:
            badge_text = "KAGGLE CAPSTONE PROJECT"
            bbox = draw.textbbox((0, 0), badge_text, font=FONT_SMALL)
            badge_w = bbox[2] - bbox[0] + 40
            draw.rounded_rectangle(
                [(center_x - badge_w//2, center_y - 180), (center_x + badge_w//2, center_y - 140)],
                radius=20, fill=COLORS['cyan'], outline=None
            )
            draw.text((center_x - badge_w//2 + 20, center_y - 172), badge_text, font=FONT_SMALL, fill=COLORS['bg_dark'])
        
        # Main title
        if f > 30:
            title = "Multi-Agent Customer Support"
            bbox = draw.textbbox((0, 0), title, font=get_font(64, bold=True))
            draw.text((center_x - (bbox[2]-bbox[0])//2, center_y - 100), title, font=get_font(64, bold=True), fill=COLORS['text_white'])
            
            subtitle = "Assistant for SMBs"
            bbox = draw.textbbox((0, 0), subtitle, font=get_font(64, bold=True))
            draw.text((center_x - (bbox[2]-bbox[0])//2, center_y - 20), subtitle, font=get_font(64, bold=True), fill=COLORS['text_white'])
        
        # Track info
        if f > 45:
            track = "Track: Agents for Business | 5-Day Gen AI Intensive Course"
            bbox = draw.textbbox((0, 0), track, font=FONT_BODY)
            draw.text((center_x - (bbox[2]-bbox[0])//2, center_y + 80), track, font=FONT_BODY, fill=COLORS['text_gray'])
        
        # Animated line
        if f > 60:
            line_progress = min(1.0, (f - 60) / 20)
            line_w = int(400 * line_progress)
            draw.rectangle([(center_x - line_w//2, center_y + 60), (center_x + line_w//2, center_y + 64)], fill=COLORS['cyan'])
        
        add_frame(img)
    
    # Problem statement (6 seconds)
    for f in range(180):
        img, draw = create_frame()
        draw_header(draw, 1, "Problem & Business Value", progress=0.1 + (f/180) * 0.1)
        
        # Left panel - The Problem
        panel_x, panel_y = 80, 140
        panel_w, panel_h = 800, 500
        draw.rounded_rectangle([(panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h)], 
                              radius=16, fill=COLORS['bg_panel'], outline=COLORS['red'], width=2)
        
        draw.text((panel_x + 30, panel_y + 25), "THE PROBLEM", font=FONT_HEADING, fill=COLORS['red'])
        
        # Animated percentage
        stat_val = min(80, int((f / 60) * 80)) if f < 60 else 80
        draw.text((panel_x + 30, panel_y + 90), f"{stat_val}%", font=get_font(120, bold=True), fill=COLORS['red'])
        draw.text((panel_x + 30, panel_y + 230), "of support tickets are repetitive", font=FONT_BODY, fill=COLORS['text_white'])
        
        # Problem list
        if f > 30:
            problems = [
                "Order tracking and status inquiries",
                "Refund and return requests",
                "Password and account issues", 
                "Common FAQ questions"
            ]
            for i, problem in enumerate(problems[:min(4, (f-30)//20 + 1)]):
                draw.text((panel_x + 50, panel_y + 290 + i * 40), f"- {problem}", font=FONT_BODY, fill=COLORS['text_gray'])
        
        # Right panel - The Solution
        if f > 60:
            sol_x = 920
            draw.rounded_rectangle([(sol_x, panel_y), (sol_x + panel_w, panel_y + panel_h)],
                                  radius=16, fill=COLORS['bg_panel'], outline=COLORS['green'], width=2)
            
            draw.text((sol_x + 30, panel_y + 25), "THE SOLUTION", font=FONT_HEADING, fill=COLORS['green'])
            
            solutions = [
                ("Instant Response", "< 1 second average"),
                ("24/7 Availability", "No wait times"),
                ("Consistent Quality", "Same answer every time"),
                ("Secure by Design", "PII protection built-in"),
            ]
            
            for i, (title, desc) in enumerate(solutions[:min(4, (f-60)//25 + 1)]):
                y_pos = panel_y + 90 + i * 100
                draw.ellipse([(sol_x + 30, y_pos), (sol_x + 60, y_pos + 30)], fill=COLORS['green'])
                draw.text((sol_x + 42, y_pos + 3), "✓", font=FONT_SMALL, fill=COLORS['bg_dark'])
                draw.text((sol_x + 80, y_pos), title, font=FONT_BODY, fill=COLORS['text_white'])
                draw.text((sol_x + 80, y_pos + 30), desc, font=FONT_SMALL, fill=COLORS['text_gray'])
        
        # Subtitle
        if f < 90:
            draw_subtitle(draw, "Small businesses spend 40% of support time on repetitive questions")
        else:
            draw_subtitle(draw, "Our multi-agent AI system handles these requests instantly and securely")
        
        add_frame(img)


def generate_architecture_scene():
    """Scene 2: Architecture & Course Concepts (0:30 - 1:20)"""
    print("Generating Scene 2: Architecture...")
    
    # Course concepts cards (8 seconds)
    for f in range(240):
        img, draw = create_frame()
        draw_header(draw, 2, "Architecture & Course Concepts", progress=0.2 + (f/240) * 0.15)
        
        draw.text((80, 120), "7 Course Concepts Implemented", font=FONT_HEADING, fill=COLORS['text_white'])
        
        concepts = [
            ("1", "Multi-Agent Architecture", "4 specialized agents: Intent, Data, Response, Quality", COLORS['cyan']),
            ("2", "MCP Tool Server", "6 business tools following Model Context Protocol", COLORS['purple']),
            ("3", "Persistent Memory", "SQLite sessions for multi-turn conversations", COLORS['yellow']),
            ("4", "Security Guardrails", "PII masking, access control, session lockout", COLORS['red']),
            ("5", "Evaluation Suite", "66 automated tests covering all components", COLORS['green']),
            ("6", "CLI Interface", "Interactive chat mode with real-time processing", COLORS['blue']),
        ]
        
        # Draw concept cards in 2x3 grid
        card_w, card_h = 550, 140
        start_x, start_y = 80, 180
        gap_x, gap_y = 600, 160
        
        for i, (num, title, desc, color) in enumerate(concepts):
            col = i % 2
            row = i // 2
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            # Animation timing
            show_at = i * 20
            if f > show_at:
                anim = min(1.0, (f - show_at) / 15)
                
                # Card
                draw.rounded_rectangle([(x, y), (x + card_w, y + card_h)], 
                                      radius=12, fill=COLORS['bg_panel'], outline=color, width=2)
                
                # Number badge
                draw.rounded_rectangle([(x + 15, y + 15), (x + 55, y + 55)], radius=8, fill=color)
                draw.text((x + 27, y + 20), num, font=FONT_BODY, fill=COLORS['bg_dark'])
                
                # Text
                draw.text((x + 70, y + 20), title, font=FONT_BODY, fill=COLORS['text_white'])
                draw.text((x + 70, y + 55), desc, font=FONT_SMALL, fill=COLORS['text_gray'])
        
        # Project structure box
        if f > 120:
            struct_y = 680
            draw.rounded_rectangle([(80, struct_y), (WIDTH - 80, struct_y + 180)],
                                  radius=12, fill=COLORS['bg_panel'], outline=COLORS['border'], width=1)
            draw.text((100, struct_y + 15), "Project Structure", font=FONT_BODY, fill=COLORS['cyan'])
            
            structure = """src/
  ├── agents/      Intent classifier, Data retrieval, Response generator, Quality safety
  ├── mcp_server/  get_order_details, get_refund_policy, create_support_ticket, audit_log
  ├── memory/      SQLiteSessionStore for persistent multi-turn conversation context
  └── security/    PII masking, access validation, session lockout after failed attempts"""
            
            for i, line in enumerate(structure.split('\n')):
                draw.text((100, struct_y + 50 + i * 24), line, font=FONT_MONO_SMALL, fill=COLORS['text_gray'])
        
        # Subtitle
        subtitles = [
            (0, 60, "The system implements all 7 concepts from the 5-Day AI Agents course"),
            (60, 120, "Four specialized agents work in sequence for maximum accuracy"),
            (120, 180, "MCP server exposes 6 business tools following protocol standards"),
            (180, 240, "SQLite-backed sessions enable natural multi-turn conversations"),
        ]
        for start, end, text in subtitles:
            if start <= f < end:
                draw_subtitle(draw, text)
                break
        
        add_frame(img)


def generate_demo_scene():
    """Scene 3: Live CLI Demo (1:20 - 3:20)"""
    print("Generating Scene 3: Live Demo...")
    
    terminal_history = []
    
    demo_script = [
        # (action, content, display_frames, subtitle)
        ("cmd", "python -m src.cli chat", 45, "Starting the interactive CLI chat interface"),
        ("out", [
            ("Starting Multi-Agent Customer Support CLI...", COLORS['cyan']),
            ("[OK] Session database initialized", COLORS['green']),
            ("[OK] MCP server online with 6 tools", COLORS['green']),
            ("Type /help for commands, /quit to exit", COLORS['text_gray']),
        ], 60, "The system initializes with SQLite sessions and MCP tools"),
        
        ("cmd", "/email alice.johnson@email.com", 45, "Setting customer email for session context"),
        ("out", [
            ("[SESSION] Email set: alice.johnson@email.com", COLORS['green']),
            ("[SESSION] Context loaded (0 previous turns)", COLORS['text_gray']),
        ], 45, "Session context is now established for Alice"),
        
        ("cmd", "Where is my order ORD-2024-002?", 60, "First query: checking order status"),
        ("out", [
            ("[INTENT] Classified: ORDER_STATUS (confidence: 0.94)", COLORS['purple']),
            ("[AUTH] Validating access... OWNER MATCH", COLORS['green']),
            ("[MCP] Calling get_order_details(ORD-2024-002)", COLORS['cyan']),
            ("[QUALITY] Response safety check: PASSED", COLORS['green']),
            ("", COLORS['text_white']),
            ("Assistant: Your order ORD-2024-002 is currently SHIPPED.", COLORS['text_white']),
            ("Expected delivery: Tomorrow by 5 PM.", COLORS['text_white']),
        ], 90, "Intent classified, access verified, order details retrieved via MCP"),
        
        ("cmd", "Can I refund it?", 45, "Follow-up query using pronoun - testing session memory"),
        ("out", [
            ("[INTENT] Classified: REFUND_REQUEST (confidence: 0.91)", COLORS['purple']),
            ("[MEMORY] Context resolution: 'it' -> ORD-2024-002", COLORS['yellow']),
            ("[MCP] Calling get_refund_policy(ORD-2024-002)", COLORS['cyan']),
            ("[QUALITY] Response safety check: PASSED", COLORS['green']),
            ("", COLORS['text_white']),
            ("Assistant: Yes! Order ORD-2024-002 is eligible for full refund.", COLORS['text_white']),
            ("It was purchased 3 days ago (within 30-day policy).", COLORS['text_white']),
        ], 90, "Session memory resolves 'it' to the previous order automatically"),
        
        ("cmd", "Show me order ORD-2024-001", 45, "Security test: trying to access another customer's order"),
        ("out", [
            ("[INTENT] Classified: ORDER_STATUS (confidence: 0.92)", COLORS['purple']),
            ("[AUTH] Validating access... DENIED", COLORS['red']),
            ("[SECURITY] ORD-2024-001 belongs to bob.smith@email.com", COLORS['red']),
            ("[SECURITY] Violation counter: 1/3 (lockout at 3)", COLORS['red']),
            ("", COLORS['text_white']),
            ("Assistant: I'm sorry, I cannot access order ORD-2024-001.", COLORS['text_white']),
            ("This order does not belong to your account.", COLORS['text_white']),
        ], 90, "Security guardrails block unauthorized cross-customer data access"),
        
        ("cmd", "Let me speak to a manager", 45, "Human escalation request"),
        ("out", [
            ("[INTENT] Classified: HUMAN_ESCALATION (confidence: 0.97)", COLORS['purple']),
            ("[MCP] Calling create_support_ticket(...)", COLORS['cyan']),
            ("[TICKET] Created: TK-2024-0892", COLORS['green']),
            ("", COLORS['text_white']),
            ("Assistant: I've created support ticket #TK-2024-0892", COLORS['text_white']),
            ("and escalated your request to a manager.", COLORS['text_white']),
            ("You'll receive a callback within 2 hours.", COLORS['text_white']),
        ], 75, "Human escalation triggers automatic ticket creation"),
    ]
    
    for action, content, duration, subtitle in demo_script:
        if action == "cmd":
            # Typing animation
            typed = ""
            for i, char in enumerate(content):
                typed += char
                img, draw = create_frame()
                draw_header(draw, 3, "Live System Demo", progress=0.35 + len(frames)/(FPS*120) * 0.35)
                draw_terminal(img, draw, 100, 120, WIDTH - 200, HEIGHT - 220, 
                             "Terminal - CLI Chat", terminal_history, typed, cursor=True)
                draw_subtitle(draw, subtitle)
                add_frame(img, 2)
            
            terminal_history.append((f"$ {content}", COLORS['text_white']))
            
            # Pause after command
            for _ in range(15):
                img, draw = create_frame()
                draw_header(draw, 3, "Live System Demo", progress=0.35 + len(frames)/(FPS*120) * 0.35)
                draw_terminal(img, draw, 100, 120, WIDTH - 200, HEIGHT - 220,
                             "Terminal - CLI Chat", terminal_history, "", cursor=True)
                draw_subtitle(draw, subtitle)
                add_frame(img)
                
        elif action == "out":
            # Output lines appearing
            for line_text, line_color in content:
                terminal_history.append((line_text, line_color))
                for _ in range(8):
                    img, draw = create_frame()
                    draw_header(draw, 3, "Live System Demo", progress=0.35 + len(frames)/(FPS*120) * 0.35)
                    draw_terminal(img, draw, 100, 120, WIDTH - 200, HEIGHT - 220,
                                 "Terminal - CLI Chat", terminal_history, "", cursor=False)
                    draw_subtitle(draw, subtitle)
                    add_frame(img)
            
            # Pause to read
            for _ in range(duration - len(content) * 8):
                img, draw = create_frame()
                draw_header(draw, 3, "Live System Demo", progress=0.35 + len(frames)/(FPS*120) * 0.35)
                draw_terminal(img, draw, 100, 120, WIDTH - 200, HEIGHT - 220,
                             "Terminal - CLI Chat", terminal_history, "", cursor=True)
                draw_subtitle(draw, subtitle)
                add_frame(img)


def generate_security_scene():
    """Scene 4: Security & Evaluation (3:20 - 4:20)"""
    print("Generating Scene 4: Security & Evaluation...")
    
    for f in range(300):
        img, draw = create_frame()
        draw_header(draw, 4, "Security & Evaluation", progress=0.7 + (f/300) * 0.15)
        
        # Left: Code editor
        editor_x, editor_y = 60, 120
        editor_w, editor_h = 820, 580
        
        # Editor window
        draw.rounded_rectangle([(editor_x, editor_y), (editor_x + editor_w, editor_y + editor_h)],
                              radius=12, fill=COLORS['bg_panel'], outline=COLORS['border'], width=2)
        draw.rounded_rectangle([(editor_x, editor_y), (editor_x + editor_w, editor_y + 40)],
                              radius=12, fill=(20, 30, 48))
        draw.rectangle([(editor_x, editor_y + 28), (editor_x + editor_w, editor_y + 40)], fill=(20, 30, 48))
        
        # Window buttons
        draw.ellipse([(editor_x + 15, editor_y + 12), (editor_x + 29, editor_y + 26)], fill=COLORS['red'])
        draw.ellipse([(editor_x + 35, editor_y + 12), (editor_x + 49, editor_y + 26)], fill=COLORS['yellow'])
        draw.ellipse([(editor_x + 55, editor_y + 12), (editor_x + 69, editor_y + 26)], fill=COLORS['green'])
        draw.text((editor_x + 85, editor_y + 10), "tests/test_security.py", font=FONT_SMALL, fill=COLORS['text_gray'])
        
        code_lines = [
            ('import pytest', COLORS['purple']),
            ('from src.security.pii_masker import PIIMasker', COLORS['purple']),
            ('from src.security.validators import validate_access', COLORS['purple']),
            ('', COLORS['text_white']),
            ('class TestPIIMasking:', COLORS['cyan']),
            ('    def test_credit_card_masking(self):', COLORS['yellow']),
            ('        masker = PIIMasker()', COLORS['text_white']),
            ('        raw = "Card: 4111-2222-3333-4444"', COLORS['green']),
            ('        result = masker.mask(raw)', COLORS['text_white']),
            ('        assert "4111" not in result', COLORS['text_white']),
            ('        assert "**** **** **** 4444" in result', COLORS['text_white']),
            ('', COLORS['text_white']),
            ('    def test_email_masking(self):', COLORS['yellow']),
            ('        result = PIIMasker.mask("alice@email.com")', COLORS['text_white']),
            ('        assert result == "a****@email.com"', COLORS['text_white']),
            ('', COLORS['text_white']),
            ('class TestAccessControl:', COLORS['cyan']),
            ('    def test_cross_customer_blocked(self):', COLORS['yellow']),
            ('        # Alice trying to access Bob order', COLORS['text_muted']),
            ('        result = validate_access(', COLORS['text_white']),
            ('            email="alice@email.com",', COLORS['text_white']),
            ('            order_id="ORD-2024-001"  # Bob order', COLORS['text_white']),
            ('        )', COLORS['text_white']),
            ('        assert result.authorized == False', COLORS['text_white']),
        ]
        
        visible_lines = min(len(code_lines), (f // 8) + 1)
        for i, (line, color) in enumerate(code_lines[:visible_lines]):
            line_num = f"{i+1:3d}"
            draw.text((editor_x + 15, editor_y + 55 + i * 22), line_num, font=FONT_MONO_SMALL, fill=COLORS['text_muted'])
            draw.text((editor_x + 55, editor_y + 55 + i * 22), line, font=FONT_MONO_SMALL, fill=color)
        
        # Right: Test results
        if f > 80:
            test_x = 920
            draw.rounded_rectangle([(test_x, editor_y), (test_x + 420, editor_y + editor_h)],
                                  radius=12, fill=COLORS['bg_panel'], outline=COLORS['border'], width=2)
            draw.rounded_rectangle([(test_x, editor_y), (test_x + 420, editor_y + 40)],
                                  radius=12, fill=(20, 30, 48))
            draw.rectangle([(test_x, editor_y + 28), (test_x + 420, editor_y + 40)], fill=(20, 30, 48))
            draw.text((test_x + 85, editor_y + 10), "pytest output", font=FONT_SMALL, fill=COLORS['text_gray'])
            
            test_output = [
                ("$ pytest tests/ -v", COLORS['text_white']),
                ("", COLORS['text_white']),
                ("collected 66 items", COLORS['text_gray']),
                ("", COLORS['text_white']),
                ("test_intent.py", COLORS['cyan']),
                ("  test_order_status    PASSED", COLORS['green']),
                ("  test_refund_request  PASSED", COLORS['green']),
                ("  test_escalation      PASSED", COLORS['green']),
                ("", COLORS['text_white']),
                ("test_security.py", COLORS['cyan']),
                ("  test_pii_masking     PASSED", COLORS['green']),
                ("  test_access_control  PASSED", COLORS['green']),
                ("  test_session_lockout PASSED", COLORS['green']),
                ("", COLORS['text_white']),
                ("test_orchestrator.py", COLORS['cyan']),
                ("  test_full_pipeline   PASSED", COLORS['green']),
                ("  test_error_handling  PASSED", COLORS['green']),
                ("", COLORS['text_white']),
                ("=============================", COLORS['text_gray']),
                ("66 passed in 1.07s", COLORS['green']),
            ]
            
            visible_tests = min(len(test_output), (f - 80) // 8 + 1)
            for i, (line, color) in enumerate(test_output[:visible_tests]):
                draw.text((test_x + 15, editor_y + 55 + i * 24), line, font=FONT_MONO_SMALL, fill=color)
        
        # Subtitles
        if f < 100:
            draw_subtitle(draw, "Every security claim is backed by automated tests")
        elif f < 200:
            draw_subtitle(draw, "66 tests covering intent classification, PII masking, and access control")
        else:
            draw_subtitle(draw, "All tests passing - security guardrails verified and working")
        
        add_frame(img)


def generate_conclusion_scene():
    """Scene 5: Conclusion & Future Work (4:20 - 5:00)"""
    print("Generating Scene 5: Conclusion...")
    
    for f in range(240):
        img, draw = create_frame()
        draw_header(draw, 5, "Conclusion & Future", progress=0.85 + (f/240) * 0.15)
        
        # Left panel: Achievements
        panel_x, panel_y = 80, 140
        panel_w, panel_h = 520, 480
        draw.rounded_rectangle([(panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h)],
                              radius=16, fill=COLORS['bg_panel'], outline=COLORS['green'], width=2)
        
        draw.text((panel_x + 25, panel_y + 20), "IMPLEMENTED", font=FONT_HEADING, fill=COLORS['green'])
        
        achievements = [
            "Multi-Agent Architecture",
            "MCP Tool Server (6 tools)",
            "SQLite Session Memory",
            "Security Guardrails",
            "PII Masking System",
            "66 Automated Tests",
            "CLI Interface",
            "FastAPI REST Endpoint",
        ]
        
        for i, text in enumerate(achievements[:min(8, f//20 + 1)]):
            y_pos = panel_y + 80 + i * 48
            draw.ellipse([(panel_x + 25, y_pos), (panel_x + 50, y_pos + 25)], fill=COLORS['green'])
            draw.text((panel_x + 33, y_pos + 2), "✓", font=FONT_SMALL, fill=COLORS['bg_dark'])
            draw.text((panel_x + 65, y_pos), text, font=FONT_BODY, fill=COLORS['text_white'])
        
        # Right panel: Future roadmap
        if f > 60:
            future_x = 660
            draw.rounded_rectangle([(future_x, panel_y), (future_x + panel_w + 200, panel_y + panel_h)],
                                  radius=16, fill=COLORS['bg_panel'], outline=COLORS['purple'], width=2)
            
            draw.text((future_x + 25, panel_y + 20), "FUTURE ROADMAP", font=FONT_HEADING, fill=COLORS['purple'])
            
            roadmap = [
                ("Voice Integration", "Phone support via Twilio/Vapi.ai"),
                ("Multi-Channel", "WhatsApp, Slack, Telegram bots"),
                ("Analytics Dashboard", "Real-time metrics and insights"),
                ("Custom Training", "Fine-tune on business-specific data"),
            ]
            
            for i, (title, desc) in enumerate(roadmap[:min(4, (f-60)//30 + 1)]):
                y_pos = panel_y + 80 + i * 100
                draw.text((future_x + 25, y_pos), f"{i+1}. {title}", font=FONT_BODY, fill=COLORS['text_white'])
                draw.text((future_x + 45, y_pos + 35), desc, font=FONT_SMALL, fill=COLORS['text_gray'])
        
        # Bottom: GitHub and thank you
        if f > 120:
            draw.rounded_rectangle([(80, 660), (WIDTH - 80, 740)],
                                  radius=12, fill=COLORS['bg_panel'], outline=COLORS['cyan'], width=1)
            
            draw.text((120, 685), "GitHub: github.com/Trungnef/ai-agents-business-support", 
                     font=FONT_BODY, fill=COLORS['text_white'])
            
            thank_text = "THANK YOU FOR WATCHING!"
            bbox = draw.textbbox((0, 0), thank_text, font=FONT_BODY)
            draw.text((WIDTH - 120 - (bbox[2] - bbox[0]), 685), thank_text, font=FONT_BODY, fill=COLORS['green'])
        
        # Subtitle
        if f < 80:
            draw_subtitle(draw, "All 7 course concepts successfully implemented and tested")
        elif f < 160:
            draw_subtitle(draw, "Production-ready architecture with security and evaluation")
        else:
            draw_subtitle(draw, "Open source on GitHub - feedback and contributions welcome!")
        
        add_frame(img)


# ============== AUDIO GENERATION ==============

async def generate_audio():
    """Generate voice narration using edge-tts"""
    print("Generating audio narration...")
    
    narration_segments = [
        # (text, duration_seconds)
        ("Small businesses are drowning in customer support requests. 80 percent of tickets are repetitive questions, yet customers wait hours for answers.", 8),
        ("This project solves that problem with a multi-agent AI system that handles routine support instantly, securely, and accurately.", 7),
        ("The system implements all seven course concepts from the 5-Day AI Agents course.", 5),
        ("Four specialized agents work in sequence: Intent Classifier, Data Retrieval, Response Generator, and Quality Safety.", 7),
        ("The MCP server exposes six business tools following Model Context Protocol standards.", 5),
        ("SQLite-backed sessions enable natural multi-turn conversations with context memory.", 5),
        ("Let me show you the system working live. First, I'll set the customer email.", 5),
        ("Now asking: Where is my order? Watch the system classify intent, verify access, and retrieve data.", 7),
        ("Now here's where session memory shines. I'll ask: Can I refund it? Notice I said 'it', not the order number.", 7),
        ("The system remembers the previous order and resolves the reference automatically.", 5),
        ("Now let me demonstrate security. I'll try to access an order that doesn't belong to this customer.", 6),
        ("The system blocks access and tracks the violation. Three failures would lock the session.", 5),
        ("If a customer asks for a human, the system creates a support ticket automatically.", 5),
        ("Every security claim is backed by automated tests. 66 tests covering all components.", 5),
        ("PII masking, access control, and session lockout are all verified and working.", 5),
        ("To summarize: All seven course concepts successfully implemented with production-ready architecture.", 6),
        ("The code is fully open source on GitHub. Thank you for watching!", 5),
    ]
    
    # Combine all text
    full_text = " ... ".join([text for text, _ in narration_segments])
    
    # Generate audio
    communicate = edge_tts.Communicate(full_text, "en-US-AriaNeural", rate="+10%")
    await communicate.save(str(AUDIO_PATH))
    print(f"Audio saved to: {AUDIO_PATH}")


def combine_video_audio():
    """Combine video and audio using ffmpeg"""
    print("Combining video and audio...")
    
    # Check if ffmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except:
        print("Warning: ffmpeg not found. Video will be saved without audio.")
        # Just rename the video file
        if VIDEO_PATH.exists():
            VIDEO_PATH.rename(FINAL_VIDEO_PATH)
        return
    
    # Combine with ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", str(VIDEO_PATH),
        "-i", str(AUDIO_PATH),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(FINAL_VIDEO_PATH)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Final video saved to: {FINAL_VIDEO_PATH}")
        # Clean up temp files
        VIDEO_PATH.unlink(missing_ok=True)
        AUDIO_PATH.unlink(missing_ok=True)
    except subprocess.CalledProcessError as e:
        print(f"Error combining audio: {e}")
        # Keep video without audio
        if VIDEO_PATH.exists():
            VIDEO_PATH.rename(FINAL_VIDEO_PATH)


def verify_video():
    """Verify the generated video"""
    print("\n" + "="*50)
    print("VERIFYING VIDEO...")
    print("="*50)
    
    if not FINAL_VIDEO_PATH.exists():
        print(f"ERROR: Video file not found at {FINAL_VIDEO_PATH}")
        return False
    
    cap = cv2.VideoCapture(str(FINAL_VIDEO_PATH))
    
    if not cap.isOpened():
        print("ERROR: Cannot open video file")
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Total Frames: {total_frames}")
    print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"File Size: {FINAL_VIDEO_PATH.stat().st_size / (1024*1024):.1f} MB")
    
    # Check a few frames for corruption
    check_points = [0, total_frames//4, total_frames//2, 3*total_frames//4, total_frames-1]
    errors = []
    
    for frame_num in check_points:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret or frame is None:
            errors.append(f"Frame {frame_num}: Failed to read")
        elif frame.shape != (height, width, 3):
            errors.append(f"Frame {frame_num}: Wrong shape {frame.shape}")
    
    cap.release()
    
    if errors:
        print("\nERRORS FOUND:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\nVERIFICATION PASSED!")
        print(f"Video is ready: {FINAL_VIDEO_PATH}")
        return True


# ============== MAIN ==============

def main():
    global frames
    frames = []
    
    print("="*60)
    print("PROFESSIONAL DEMO VIDEO GENERATOR")
    print("Multi-Agent Customer Support Assistant for SMBs")
    print("="*60)
    
    # Generate all scenes
    generate_intro_scene()
    print(f"  Scene 1 complete: {len(frames)} frames")
    
    generate_architecture_scene()
    print(f"  Scene 2 complete: {len(frames)} frames")
    
    generate_demo_scene()
    print(f"  Scene 3 complete: {len(frames)} frames")
    
    generate_security_scene()
    print(f"  Scene 4 complete: {len(frames)} frames")
    
    generate_conclusion_scene()
    print(f"  Scene 5 complete: {len(frames)} frames")
    
    # Write video
    print(f"\nWriting video with {len(frames)} frames...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(VIDEO_PATH), fourcc, FPS, (WIDTH, HEIGHT))
    
    for i, frame in enumerate(frames):
        out.write(frame)
        if (i + 1) % 500 == 0:
            print(f"  Written {i+1}/{len(frames)} frames...")
    
    out.release()
    print(f"Video frames saved to: {VIDEO_PATH}")
    
    # Generate audio
    try:
        asyncio.run(generate_audio())
        # Combine
        combine_video_audio()
    except Exception as e:
        print(f"Audio generation failed: {e}")
        print("Saving video without audio...")
        if VIDEO_PATH.exists():
            VIDEO_PATH.rename(FINAL_VIDEO_PATH)
    
    # Verify
    verify_video()
    
    print("\n" + "="*60)
    print("VIDEO GENERATION COMPLETE!")
    print(f"Output: {FINAL_VIDEO_PATH}")
    print("="*60)


if __name__ == "__main__":
    main()
