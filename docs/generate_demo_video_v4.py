"""
Video Demo Generator v4 - Perfect Voice-Subtitle Sync + Beautiful Diagrams
============================================================================
Key improvements:
1. CONTINUOUS SUBTITLES - Long flowing text, split only at natural pauses
2. WPM-BASED TIMING - Calculate duration from word count (150 WPM for clear speech)
3. BEAUTIFUL DIAGRAMS - Gradient backgrounds, shadows, icons, modern design
4. SMOOTH ANIMATIONS - Easing functions, professional transitions
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import asyncio
import edge_tts
import subprocess
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

# ============================================================================
# CONFIGURATION
# ============================================================================

WIDTH, HEIGHT = 1920, 1080
FPS = 30
OUTPUT_DIR = "d:/Projects/ai-agents-business-support/docs"
AUDIO_DIR = f"{OUTPUT_DIR}/audio_segments_v4"

# Colors - Modern Dark Theme
COLORS = {
    'bg_dark': (15, 23, 42),           # Slate 900
    'bg_medium': (30, 41, 59),          # Slate 800
    'bg_light': (51, 65, 85),           # Slate 700
    'primary': (59, 130, 246),          # Blue 500
    'primary_dark': (37, 99, 235),      # Blue 600
    'secondary': (139, 92, 246),        # Violet 500
    'success': (34, 197, 94),           # Green 500
    'warning': (251, 191, 36),          # Amber 400
    'error': (239, 68, 68),             # Red 500
    'text_white': (248, 250, 252),      # Slate 50
    'text_gray': (148, 163, 184),       # Slate 400
    'text_muted': (100, 116, 139),      # Slate 500
    'accent_cyan': (34, 211, 238),      # Cyan 400
    'accent_pink': (244, 114, 182),     # Pink 400
    'accent_orange': (251, 146, 60),    # Orange 400
    'border': (71, 85, 105),            # Slate 600
}

# Words per minute for timing calculation
WPM = 150  # Clear, professional narration speed

# ============================================================================
# NARRATION DATA - Continuous Subtitles
# ============================================================================

@dataclass
class NarrationBlock:
    """A block of narration with continuous subtitle display"""
    text: str  # Full narration text (also displayed as subtitle)
    scene: str  # Which scene this belongs to
    
    @property
    def word_count(self) -> int:
        return len(self.text.split())
    
    @property
    def duration_sec(self) -> float:
        # Calculate based on WPM, minimum 2 seconds
        return max(2.0, (self.word_count / WPM) * 60)

# Define all narration as continuous blocks
NARRATION_BLOCKS = [
    # === INTRO SCENE (13s total) ===
    NarrationBlock(
        text="Welcome to the Multi-Agent Customer Support Assistant, a Kaggle Capstone project for the Agents for Business track.",
        scene="intro"
    ),
    NarrationBlock(
        text="This system demonstrates how AI agents can transform small business customer support.",
        scene="intro"
    ),
    
    # === PROBLEM SCENE (16s total) ===
    NarrationBlock(
        text="Small businesses face a critical challenge. 80% of support tickets are repetitive questions like order tracking, refund requests, and password resets.",
        scene="problem"
    ),
    NarrationBlock(
        text="Yet customers wait hours for answers. Our multi-agent solution handles these requests instantly, securely, and accurately.",
        scene="problem"
    ),
    
    # === ARCHITECTURE SCENE (28s total) ===
    NarrationBlock(
        text="The system implements all seven course concepts from the 5-Day AI Agents course using a modular multi-agent architecture.",
        scene="architecture"
    ),
    NarrationBlock(
        text="Four specialized agents work together: Intent Classifier analyzes queries, Data Retrieval fetches information via MCP tools, Response Generator creates helpful replies, and Quality Safety ensures security.",
        scene="architecture"
    ),
    NarrationBlock(
        text="Six MCP tools handle business operations including order lookup, refund processing, ticket creation, and customer authentication.",
        scene="architecture"
    ),
    
    # === DEMO SCENE (50s total) ===
    NarrationBlock(
        text="Let me demonstrate the system in action. First, I'll set the customer email to alice.johnson@email.com and ask about order ORD-2024-002.",
        scene="demo"
    ),
    NarrationBlock(
        text="The system classifies the intent as ORDER_STATUS, retrieves the order through MCP tools, validates ownership, and generates a response in under one second.",
        scene="demo"
    ),
    NarrationBlock(
        text="Now watch session memory in action. When I ask 'Can I refund it?', the system remembers the order from context and resolves the reference automatically.",
        scene="demo"
    ),
    NarrationBlock(
        text="For security demonstration, I'll try accessing order ORD-2024-001 which belongs to a different customer. The system blocks access and increments the violation counter.",
        scene="demo"
    ),
    NarrationBlock(
        text="Three security violations would trigger automatic session lockout, preventing cross-customer data leakage.",
        scene="demo"
    ),
    
    # === SECURITY SCENE (20s total) ===
    NarrationBlock(
        text="Every security claim is verified by automated tests. The test suite includes 66 tests covering intent classification, PII masking, access control, and session management.",
        scene="security"
    ),
    NarrationBlock(
        text="PII masking protects sensitive data: credit cards show only the last 4 digits, emails are partially redacted, and internal IDs are completely hidden.",
        scene="security"
    ),
    
    # === CONCLUSION SCENE (18s total) ===
    NarrationBlock(
        text="This Multi-Agent Customer Support Assistant demonstrates how AI agents can provide real business value, reducing customer wait times from hours to seconds.",
        scene="conclusion"
    ),
    NarrationBlock(
        text="The code is fully open source on GitHub. Thank you for watching, and I welcome your feedback!",
        scene="conclusion"
    ),
]

# ============================================================================
# VIDEO GENERATOR CLASS
# ============================================================================

class VideoGenerator:
    def __init__(self):
        self.frames: List[np.ndarray] = []
        self.current_frame = 0
        
        # Load fonts
        self.font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 64)
        self.font_heading = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 48)
        self.font_subheading = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 36)
        self.font_body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 28)
        self.font_small = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 24)
        self.font_code = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)
        self.font_subtitle = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 32)
        self.font_icon = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 40)
        
    def create_base_frame(self) -> Image.Image:
        """Create base frame with gradient background"""
        img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['bg_dark'])
        draw = ImageDraw.Draw(img)
        
        # Subtle gradient effect using rectangles
        for y in range(0, HEIGHT, 4):
            progress = y / HEIGHT
            r = int(COLORS['bg_dark'][0] + (COLORS['bg_medium'][0] - COLORS['bg_dark'][0]) * progress * 0.3)
            g = int(COLORS['bg_dark'][1] + (COLORS['bg_medium'][1] - COLORS['bg_dark'][1]) * progress * 0.3)
            b = int(COLORS['bg_dark'][2] + (COLORS['bg_medium'][2] - COLORS['bg_dark'][2]) * progress * 0.3)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
        
        return img
    
    def draw_rounded_rect(self, draw: ImageDraw.Draw, xy: Tuple[int, int, int, int], 
                          radius: int, fill: Tuple[int, int, int], 
                          outline: Optional[Tuple[int, int, int]] = None,
                          outline_width: int = 2):
        """Draw a rounded rectangle"""
        x1, y1, x2, y2 = xy
        
        # Draw main rectangle
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=outline_width)
    
    def draw_gradient_rect(self, img: Image.Image, xy: Tuple[int, int, int, int],
                           color1: Tuple[int, int, int], color2: Tuple[int, int, int],
                           radius: int = 0, vertical: bool = True):
        """Draw rectangle with gradient fill"""
        x1, y1, x2, y2 = xy
        gradient = Image.new('RGB', (x2 - x1, y2 - y1))
        draw_grad = ImageDraw.Draw(gradient)
        
        if vertical:
            for y in range(y2 - y1):
                progress = y / (y2 - y1)
                r = int(color1[0] + (color2[0] - color1[0]) * progress)
                g = int(color1[1] + (color2[1] - color1[1]) * progress)
                b = int(color1[2] + (color2[2] - color1[2]) * progress)
                draw_grad.line([(0, y), (x2 - x1, y)], fill=(r, g, b))
        else:
            for x in range(x2 - x1):
                progress = x / (x2 - x1)
                r = int(color1[0] + (color2[0] - color1[0]) * progress)
                g = int(color1[1] + (color2[1] - color1[1]) * progress)
                b = int(color1[2] + (color2[2] - color1[2]) * progress)
                draw_grad.line([(x, 0), (x, y2 - y1)], fill=(r, g, b))
        
        # Create mask for rounded corners if needed
        if radius > 0:
            mask = Image.new('L', (x2 - x1, y2 - y1), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, x2 - x1, y2 - y1), radius=radius, fill=255)
            img.paste(gradient, (x1, y1), mask)
        else:
            img.paste(gradient, (x1, y1))
    
    def draw_text_centered(self, draw: ImageDraw.Draw, text: str, y: int, 
                           font: ImageFont.FreeTypeFont, color: Tuple[int, int, int]):
        """Draw text centered horizontally"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) // 2
        draw.text((x, y), text, font=font, fill=color)
    
    def draw_text_wrapped(self, draw: ImageDraw.Draw, text: str, xy: Tuple[int, int],
                          max_width: int, font: ImageFont.FreeTypeFont, 
                          color: Tuple[int, int, int], line_spacing: int = 8) -> int:
        """Draw wrapped text and return total height"""
        x, y = xy
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        total_height = 0
        for line in lines:
            draw.text((x, y + total_height), line, font=font, fill=color)
            bbox = draw.textbbox((0, 0), line, font=font)
            total_height += (bbox[3] - bbox[1]) + line_spacing
        
        return total_height
    
    def draw_subtitle_bar(self, img: Image.Image, text: str, progress: float):
        """Draw beautiful subtitle bar at bottom"""
        draw = ImageDraw.Draw(img)
        
        # Subtitle background - dark semi-transparent bar
        bar_height = 120
        bar_y = HEIGHT - bar_height - 40
        
        # Create gradient background for subtitle
        self.draw_gradient_rect(img, (100, bar_y, WIDTH - 100, bar_y + bar_height),
                                (20, 30, 50), (30, 45, 70), radius=20)
        
        # Add subtle border
        draw.rounded_rectangle((100, bar_y, WIDTH - 100, bar_y + bar_height),
                               radius=20, outline=COLORS['border'], width=2)
        
        # Draw subtitle text - wrapped and centered
        max_text_width = WIDTH - 280
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=self.font_subtitle)
            if bbox[2] - bbox[0] <= max_text_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total text height
        line_height = 40
        total_text_height = len(lines) * line_height
        start_y = bar_y + (bar_height - total_text_height) // 2
        
        # Draw each line centered
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=self.font_subtitle)
            line_width = bbox[2] - bbox[0]
            x = (WIDTH - line_width) // 2
            draw.text((x, start_y + i * line_height), line, 
                      font=self.font_subtitle, fill=COLORS['text_white'])
        
        # Progress indicator dots
        dot_y = bar_y + bar_height + 15
        for i in range(5):
            dot_x = WIDTH // 2 - 60 + i * 30
            if i / 5 <= progress:
                draw.ellipse((dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5), 
                            fill=COLORS['primary'])
            else:
                draw.ellipse((dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5), 
                            fill=COLORS['bg_light'])
    
    def draw_progress_bar(self, img: Image.Image, progress: float, scene_name: str):
        """Draw top progress bar"""
        draw = ImageDraw.Draw(img)
        
        # Background bar
        bar_y = 20
        bar_height = 6
        draw.rounded_rectangle((60, bar_y, WIDTH - 60, bar_y + bar_height),
                               radius=3, fill=COLORS['bg_light'])
        
        # Progress fill
        fill_width = int((WIDTH - 120) * progress)
        if fill_width > 0:
            draw.rounded_rectangle((60, bar_y, 60 + fill_width, bar_y + bar_height),
                                   radius=3, fill=COLORS['primary'])
        
        # Scene indicator
        draw.text((60, bar_y + 15), scene_name.upper(), 
                  font=self.font_small, fill=COLORS['text_muted'])
    
    # ========================================================================
    # SCENE RENDERERS
    # ========================================================================
    
    def render_intro_scene(self, block: NarrationBlock, frame_in_block: int, 
                           total_frames: int) -> Image.Image:
        """Render intro scene with animated logo and title"""
        img = self.create_base_frame()
        draw = ImageDraw.Draw(img)
        
        progress = frame_in_block / total_frames
        ease_progress = self.ease_out_cubic(min(1.0, progress * 2))
        
        # Animated background circles
        for i in range(3):
            circle_progress = (progress + i * 0.3) % 1.0
            alpha = int(30 * (1 - circle_progress))
            radius = int(100 + circle_progress * 400)
            cx, cy = WIDTH // 2, HEIGHT // 2 - 100
            # Draw expanding circles
            if alpha > 5:
                draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                            outline=(*COLORS['primary'][:3],), width=2)
        
        # Main title card
        card_width = 1000
        card_height = 400
        card_x = (WIDTH - card_width) // 2
        card_y = int(150 + (1 - ease_progress) * 50)
        
        # Card with gradient
        self.draw_gradient_rect(img, (card_x, card_y, card_x + card_width, card_y + card_height),
                                COLORS['bg_medium'], COLORS['bg_light'], radius=30)
        draw.rounded_rectangle((card_x, card_y, card_x + card_width, card_y + card_height),
                               radius=30, outline=COLORS['primary'], width=3)
        
        # Icon
        icon_text = "🤖"
        draw.text((WIDTH // 2 - 30, card_y + 40), icon_text, 
                  font=self.font_title, fill=COLORS['primary'])
        
        # Title
        self.draw_text_centered(draw, "Multi-Agent Customer Support", 
                               card_y + 130, self.font_title, COLORS['text_white'])
        self.draw_text_centered(draw, "Assistant for SMBs", 
                               card_y + 210, self.font_heading, COLORS['text_gray'])
        
        # Badge
        badge_text = "Kaggle Capstone • Agents for Business Track"
        badge_bbox = draw.textbbox((0, 0), badge_text, font=self.font_subheading)
        badge_width = badge_bbox[2] - badge_bbox[0] + 40
        badge_x = (WIDTH - badge_width) // 2
        badge_y = card_y + 300
        
        draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_width, badge_y + 50),
                               radius=25, fill=COLORS['primary_dark'])
        self.draw_text_centered(draw, badge_text, badge_y + 8, 
                               self.font_subheading, COLORS['text_white'])
        
        return img
    
    def render_problem_scene(self, block: NarrationBlock, frame_in_block: int,
                             total_frames: int) -> Image.Image:
        """Render problem scene with statistics"""
        img = self.create_base_frame()
        draw = ImageDraw.Draw(img)
        
        progress = frame_in_block / total_frames
        
        # Title
        self.draw_text_centered(draw, "The Challenge", 120, self.font_title, COLORS['text_white'])
        
        # Animated stat cards
        cards = [
            ("80%", "Repetitive Tickets", "Order tracking, refunds, passwords", COLORS['error']),
            ("Hours", "Wait Times", "Customers wait for simple answers", COLORS['warning']),
            ("<1s", "Our Solution", "Instant, accurate responses", COLORS['success']),
        ]
        
        card_width = 350
        card_height = 280
        gap = 80
        total_width = len(cards) * card_width + (len(cards) - 1) * gap
        start_x = (WIDTH - total_width) // 2
        
        for i, (stat, title, desc, accent) in enumerate(cards):
            # Staggered animation
            card_progress = self.ease_out_cubic(max(0, min(1, (progress - i * 0.15) * 2)))
            
            x = start_x + i * (card_width + gap)
            y = int(250 + (1 - card_progress) * 100)
            
            # Card background
            self.draw_gradient_rect(img, (x, y, x + card_width, y + card_height),
                                    COLORS['bg_medium'], COLORS['bg_light'], radius=20)
            
            # Accent top bar
            draw.rounded_rectangle((x, y, x + card_width, y + 8), radius=4, fill=accent)
            
            # Big stat number
            stat_bbox = draw.textbbox((0, 0), stat, font=self.font_title)
            stat_x = x + (card_width - (stat_bbox[2] - stat_bbox[0])) // 2
            draw.text((stat_x, y + 40), stat, font=self.font_title, fill=accent)
            
            # Title
            title_bbox = draw.textbbox((0, 0), title, font=self.font_heading)
            title_x = x + (card_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, y + 130), title, font=self.font_heading, fill=COLORS['text_white'])
            
            # Description
            self.draw_text_wrapped(draw, desc, (x + 20, y + 200), card_width - 40,
                                   self.font_body, COLORS['text_gray'])
        
        return img
    
    def render_architecture_scene(self, block: NarrationBlock, frame_in_block: int,
                                   total_frames: int) -> Image.Image:
        """Render beautiful architecture diagram"""
        img = self.create_base_frame()
        draw = ImageDraw.Draw(img)
        
        progress = frame_in_block / total_frames
        
        # Title
        self.draw_text_centered(draw, "Multi-Agent Architecture", 80, 
                               self.font_title, COLORS['text_white'])
        
        # Course concepts badge
        badge_text = "Implementing 7 Course Concepts"
        badge_bbox = draw.textbbox((0, 0), badge_text, font=self.font_body)
        badge_w = badge_bbox[2] - badge_bbox[0] + 30
        badge_x = (WIDTH - badge_w) // 2
        draw.rounded_rectangle((badge_x, 145, badge_x + badge_w, 185), 
                               radius=20, fill=COLORS['secondary'])
        self.draw_text_centered(draw, badge_text, 152, self.font_body, COLORS['text_white'])
        
        # Agent pipeline - horizontal flow
        agents = [
            ("Intent\nClassifier", "🎯", COLORS['primary'], "Analyzes\nquery type"),
            ("Data\nRetrieval", "📊", COLORS['accent_cyan'], "Fetches info\nvia MCP"),
            ("Response\nGenerator", "💬", COLORS['success'], "Creates\nhelpful reply"),
            ("Quality\nSafety", "🛡️", COLORS['error'], "Ensures\nsecurity"),
        ]
        
        box_width = 200
        box_height = 160
        gap = 100
        total_w = len(agents) * box_width + (len(agents) - 1) * gap
        start_x = (WIDTH - total_w) // 2
        agents_y = 230
        
        for i, (name, icon, color, desc) in enumerate(agents):
            anim_progress = self.ease_out_cubic(max(0, min(1, (progress - i * 0.1) * 2.5)))
            
            x = start_x + i * (box_width + gap)
            y = agents_y + int((1 - anim_progress) * 30)
            
            # Box with gradient
            self.draw_gradient_rect(img, (x, y, x + box_width, y + box_height),
                                    COLORS['bg_medium'], COLORS['bg_light'], radius=15)
            draw.rounded_rectangle((x, y, x + box_width, y + box_height),
                                   radius=15, outline=color, width=3)
            
            # Icon circle
            icon_cx = x + box_width // 2
            icon_cy = y + 45
            draw.ellipse((icon_cx - 25, icon_cy - 25, icon_cx + 25, icon_cy + 25), fill=color)
            
            # Name
            for j, line in enumerate(name.split('\n')):
                line_bbox = draw.textbbox((0, 0), line, font=self.font_body)
                line_x = x + (box_width - (line_bbox[2] - line_bbox[0])) // 2
                draw.text((line_x, y + 80 + j * 30), line, 
                         font=self.font_body, fill=COLORS['text_white'])
            
            # Arrow to next
            if i < len(agents) - 1:
                arrow_x = x + box_width + 20
                arrow_y = y + box_height // 2
                # Arrow line
                draw.line((arrow_x, arrow_y, arrow_x + 60, arrow_y), 
                         fill=COLORS['text_muted'], width=3)
                # Arrow head
                draw.polygon([(arrow_x + 60, arrow_y), (arrow_x + 50, arrow_y - 8),
                             (arrow_x + 50, arrow_y + 8)], fill=COLORS['text_muted'])
        
        # MCP Tools section
        tools_y = 450
        draw.text((100, tools_y), "MCP Tools", font=self.font_heading, fill=COLORS['accent_cyan'])
        
        tools = [
            ("get_order_details", "📦"),
            ("get_refund_policy", "💰"),
            ("create_support_ticket", "🎫"),
            ("verify_customer", "✓"),
            ("get_customer_history", "📋"),
            ("update_order_status", "🔄"),
        ]
        
        tool_box_w = 250
        tool_box_h = 50
        tools_per_row = 3
        tool_gap = 30
        
        for i, (tool_name, tool_icon) in enumerate(tools):
            row = i // tools_per_row
            col = i % tools_per_row
            
            tool_anim = self.ease_out_cubic(max(0, min(1, (progress - 0.3 - i * 0.05) * 3)))
            
            x = 100 + col * (tool_box_w + tool_gap)
            y = tools_y + 60 + row * (tool_box_h + 15) + int((1 - tool_anim) * 20)
            
            draw.rounded_rectangle((x, y, x + tool_box_w, y + tool_box_h),
                                   radius=10, fill=COLORS['bg_medium'], 
                                   outline=COLORS['accent_cyan'], width=1)
            draw.text((x + 15, y + 12), f"{tool_icon} {tool_name}", 
                     font=self.font_code, fill=COLORS['text_white'])
        
        # Session & Memory section
        session_y = 450
        session_x = 950
        draw.text((session_x, session_y), "Session & Memory", 
                 font=self.font_heading, fill=COLORS['secondary'])
        
        # Memory features
        memory_features = [
            "SQLite-backed persistent sessions",
            "Multi-turn conversation context",
            "Automatic reference resolution",
            "Session security tracking",
        ]
        
        for i, feature in enumerate(memory_features):
            feat_anim = self.ease_out_cubic(max(0, min(1, (progress - 0.4 - i * 0.05) * 3)))
            y = session_y + 60 + i * 45 + int((1 - feat_anim) * 20)
            
            # Bullet
            draw.ellipse((session_x, y + 8, session_x + 12, y + 20), fill=COLORS['secondary'])
            draw.text((session_x + 25, y), feature, font=self.font_body, fill=COLORS['text_white'])
        
        # Security section at bottom
        security_y = 700
        draw.text((100, security_y), "Security Guardrails", 
                 font=self.font_heading, fill=COLORS['error'])
        
        security_items = ["PII Masking", "Access Control", "Session Lockout", "Audit Logging"]
        
        for i, item in enumerate(security_items):
            sec_anim = self.ease_out_cubic(max(0, min(1, (progress - 0.5 - i * 0.05) * 3)))
            
            x = 100 + i * 220
            y = security_y + 50 + int((1 - sec_anim) * 20)
            
            draw.rounded_rectangle((x, y, x + 200, y + 45), radius=8,
                                   fill=COLORS['bg_medium'], outline=COLORS['error'], width=2)
            
            item_bbox = draw.textbbox((0, 0), item, font=self.font_body)
            item_x = x + (200 - (item_bbox[2] - item_bbox[0])) // 2
            draw.text((item_x, y + 10), item, font=self.font_body, fill=COLORS['text_white'])
        
        return img
    
    def render_demo_scene(self, block: NarrationBlock, frame_in_block: int,
                          total_frames: int) -> Image.Image:
        """Render demo scene with terminal simulation"""
        img = self.create_base_frame()
        draw = ImageDraw.Draw(img)
        
        progress = frame_in_block / total_frames
        
        # Terminal window
        term_x, term_y = 100, 100
        term_w, term_h = WIDTH - 200, HEIGHT - 300
        
        # Terminal chrome (title bar)
        draw.rounded_rectangle((term_x, term_y, term_x + term_w, term_y + 40),
                               radius=10, fill=COLORS['bg_light'])
        
        # Window buttons
        for i, color in enumerate([COLORS['error'], COLORS['warning'], COLORS['success']]):
            draw.ellipse((term_x + 20 + i * 25, term_y + 12, 
                         term_x + 36 + i * 25, term_y + 28), fill=color)
        
        # Terminal title
        draw.text((term_x + term_w // 2 - 100, term_y + 8), 
                 "Multi-Agent Support CLI", font=self.font_small, fill=COLORS['text_gray'])
        
        # Terminal body
        draw.rectangle((term_x, term_y + 40, term_x + term_w, term_y + term_h),
                       fill=COLORS['bg_dark'])
        draw.rectangle((term_x, term_y + 40, term_x + term_w, term_y + term_h),
                       outline=COLORS['border'], width=1)
        
        # Terminal content - based on narration block
        content_y = term_y + 60
        line_height = 32
        
        # Determine which demo phase we're in based on block text
        if "set the customer email" in block.text.lower():
            lines = [
                ("$ python -m src.cli chat", COLORS['text_gray']),
                ("", None),
                ("Welcome to Multi-Agent Support CLI", COLORS['accent_cyan']),
                ("Type /help for commands, /quit to exit", COLORS['text_muted']),
                ("", None),
                ("> /email alice.johnson@email.com", COLORS['text_white']),
                ("✓ Email set to: alice.johnson@email.com", COLORS['success']),
                ("", None),
                ("> Where is my order ORD-2024-002?", COLORS['text_white']),
            ]
            # Animated typing effect
            visible_lines = int(len(lines) * min(1, progress * 1.5))
            lines = lines[:visible_lines]
            
        elif "classifies the intent" in block.text.lower():
            lines = [
                ("> Where is my order ORD-2024-002?", COLORS['text_white']),
                ("", None),
                ("┌─ Agent Pipeline ─────────────────────────────────────┐", COLORS['border']),
                ("│ ▶ Intent Classifier: ORDER_STATUS                    │", COLORS['primary']),
                ("│ ▶ Data Retrieval: Fetching order details...          │", COLORS['accent_cyan']),
                ("│ ▶ MCP Tool: get_order_details(ORD-2024-002)          │", COLORS['secondary']),
                ("│ ▶ Access Control: ✓ Verified owner                   │", COLORS['success']),
                ("│ ▶ Response Generator: Creating reply...              │", COLORS['accent_pink']),
                ("└───────────────────────────────────────────────────────┘", COLORS['border']),
                ("", None),
                ("📦 Order ORD-2024-002 Status:", COLORS['accent_cyan']),
                ("   Status: Shipped", COLORS['text_white']),
                ("   Carrier: FedEx • Tracking: FX123456789", COLORS['text_white']),
                ("   Estimated Delivery: June 26, 2026", COLORS['success']),
            ]
            visible_lines = int(len(lines) * min(1, progress * 1.2))
            lines = lines[:visible_lines]
            
        elif "session memory" in block.text.lower():
            lines = [
                ("> Can I refund it?", COLORS['text_white']),
                ("", None),
                ("┌─ Context Resolution ─────────────────────────────────┐", COLORS['border']),
                ("│ 🧠 Session Memory: Resolving 'it'...                 │", COLORS['secondary']),
                ("│ ▶ Found reference: 'it' → ORD-2024-002               │", COLORS['success']),
                ("│ ▶ Intent: REFUND_REQUEST                             │", COLORS['primary']),
                ("│ ▶ MCP Tool: get_refund_policy()                      │", COLORS['accent_cyan']),
                ("└───────────────────────────────────────────────────────┘", COLORS['border']),
                ("", None),
                ("💰 Refund Policy for ORD-2024-002:", COLORS['accent_cyan']),
                ("   Order delivered 3 days ago", COLORS['text_white']),
                ("   ✓ Within 30-day return window", COLORS['success']),
                ("   Refund can be processed upon item return", COLORS['text_white']),
            ]
            visible_lines = int(len(lines) * min(1, progress * 1.2))
            lines = lines[:visible_lines]
            
        elif "security demonstration" in block.text.lower() or "different customer" in block.text.lower():
            lines = [
                ("> Show me order ORD-2024-001", COLORS['text_white']),
                ("", None),
                ("┌─ Security Check ─────────────────────────────────────┐", COLORS['border']),
                ("│ ▶ Intent: ORDER_STATUS                               │", COLORS['primary']),
                ("│ ▶ MCP Tool: get_order_details(ORD-2024-001)          │", COLORS['accent_cyan']),
                ("│ ⚠ Access Control: Checking ownership...              │", COLORS['warning']),
                ("│ ✗ DENIED: Order belongs to different customer        │", COLORS['error']),
                ("│ ⚠ Security: Violation count incremented (1/3)        │", COLORS['warning']),
                ("└───────────────────────────────────────────────────────┘", COLORS['border']),
                ("", None),
                ("🚫 Access Denied", COLORS['error']),
                ("   You don't have permission to view this order.", COLORS['text_white']),
                ("   This incident has been logged.", COLORS['text_muted']),
            ]
            visible_lines = int(len(lines) * min(1, progress * 1.2))
            lines = lines[:visible_lines]
            
        elif "lockout" in block.text.lower():
            lines = [
                ("┌─ Security Guardrails ─────────────────────────────────┐", COLORS['border']),
                ("│                                                       │", COLORS['border']),
                ("│   🛡️  Session Protection Active                       │", COLORS['error']),
                ("│                                                       │", COLORS['border']),
                ("│   • Cross-customer access blocked                     │", COLORS['text_white']),
                ("│   • Violation tracking: 1/3 attempts                  │", COLORS['warning']),
                ("│   • 3 violations → Automatic session lockout          │", COLORS['error']),
                ("│   • All access attempts logged for audit              │", COLORS['text_muted']),
                ("│                                                       │", COLORS['border']),
                ("└───────────────────────────────────────────────────────┘", COLORS['border']),
                ("", None),
                ("Security features prevent data leakage", COLORS['text_gray']),
                ("between customer accounts.", COLORS['text_gray']),
            ]
            visible_lines = int(len(lines) * min(1, progress * 1.5))
            lines = lines[:visible_lines]
        else:
            # Default demo content
            lines = [
                ("$ python -m src.cli chat", COLORS['text_gray']),
                ("", None),
                ("Welcome to Multi-Agent Support CLI", COLORS['accent_cyan']),
                ("Type /help for commands, /quit to exit", COLORS['text_muted']),
            ]
        
        # Draw terminal lines
        for i, (line, color) in enumerate(lines):
            if color:
                draw.text((term_x + 20, content_y + i * line_height), 
                         line, font=self.font_code, fill=color)
        
        return img
    
    def render_security_scene(self, block: NarrationBlock, frame_in_block: int,
                               total_frames: int) -> Image.Image:
        """Render security and testing scene"""
        img = self.create_base_frame()
        draw = ImageDraw.Draw(img)
        
        progress = frame_in_block / total_frames
        
        # Title
        self.draw_text_centered(draw, "Security & Testing", 80, 
                               self.font_title, COLORS['text_white'])
        
        if "66 tests" in block.text.lower() or "automated tests" in block.text.lower():
            # Test results panel
            panel_x, panel_y = 100, 180
            panel_w = 800
            
            draw.text((panel_x, panel_y), "Test Suite Results", 
                     font=self.font_heading, fill=COLORS['success'])
            
            # Test categories with progress bars
            tests = [
                ("Intent Classification", 24, 24, COLORS['primary']),
                ("PII Masking", 12, 12, COLORS['error']),
                ("Access Control", 15, 15, COLORS['warning']),
                ("Session Management", 8, 8, COLORS['secondary']),
                ("Full Orchestrator", 7, 7, COLORS['success']),
            ]
            
            for i, (name, passed, total, color) in enumerate(tests):
                test_anim = self.ease_out_cubic(max(0, min(1, (progress - i * 0.1) * 2)))
                
                y = panel_y + 70 + i * 70
                
                # Test name
                draw.text((panel_x, y), name, font=self.font_body, fill=COLORS['text_white'])
                
                # Progress bar background
                bar_x = panel_x + 300
                bar_w = 400
                bar_h = 24
                draw.rounded_rectangle((bar_x, y + 5, bar_x + bar_w, y + 5 + bar_h),
                                       radius=12, fill=COLORS['bg_light'])
                
                # Progress bar fill
                fill_w = int(bar_w * (passed / total) * test_anim)
                if fill_w > 0:
                    draw.rounded_rectangle((bar_x, y + 5, bar_x + fill_w, y + 5 + bar_h),
                                           radius=12, fill=color)
                
                # Count
                draw.text((bar_x + bar_w + 20, y), f"{passed}/{total}", 
                         font=self.font_body, fill=COLORS['success'])
            
            # Total badge
            total_y = panel_y + 450
            draw.rounded_rectangle((panel_x, total_y, panel_x + 250, total_y + 60),
                                   radius=30, fill=COLORS['success'])
            draw.text((panel_x + 30, total_y + 12), "66/66 PASSED", 
                     font=self.font_heading, fill=COLORS['text_white'])
            
            # Code snippet panel
            code_x = 950
            code_y = 180
            code_w = 850
            code_h = 400
            
            draw.rounded_rectangle((code_x, code_y, code_x + code_w, code_y + code_h),
                                   radius=15, fill=COLORS['bg_medium'])
            draw.text((code_x + 20, code_y + 15), "tests/test_security.py", 
                     font=self.font_code, fill=COLORS['text_muted'])
            
            code_lines = [
                "def test_pii_masking():",
                "    masker = PIIMasker()",
                "    ",
                "    # Credit card masking",
                "    text = 'Card: 4532-1234-5678-9012'",
                "    result = masker.mask(text)",
                "    assert result == 'Card: ****-****-****-9012'",
                "    ",
                "    # Email partial redaction",
                "    text = 'Email: alice@email.com'",
                "    result = masker.mask(text)",
                "    assert 'ali***' in result",
            ]
            
            for i, line in enumerate(code_lines):
                code_anim = self.ease_out_cubic(max(0, min(1, (progress - 0.2 - i * 0.03) * 3)))
                if code_anim > 0:
                    y = code_y + 50 + i * 28
                    # Syntax highlighting
                    if line.startswith("def "):
                        color = COLORS['primary']
                    elif line.strip().startswith("#"):
                        color = COLORS['text_muted']
                    elif "assert" in line:
                        color = COLORS['accent_pink']
                    elif "'" in line or '"' in line:
                        color = COLORS['success']
                    else:
                        color = COLORS['text_white']
                    draw.text((code_x + 20, y), line, font=self.font_code, fill=color)
        
        else:  # PII masking details
            # PII Masking visualization
            draw.text((100, 180), "PII Protection in Action", 
                     font=self.font_heading, fill=COLORS['error'])
            
            examples = [
                ("Credit Card", "4532-1234-5678-9012", "****-****-****-9012", COLORS['error']),
                ("Email Address", "alice.johnson@email.com", "ali***@***.com", COLORS['warning']),
                ("Internal ID", "CUST-2024-001", "[REDACTED]", COLORS['secondary']),
                ("Phone Number", "(555) 123-4567", "(***) ***-4567", COLORS['primary']),
            ]
            
            for i, (label, before, after, color) in enumerate(examples):
                ex_anim = self.ease_out_cubic(max(0, min(1, (progress - i * 0.15) * 2)))
                
                y = 260 + i * 120
                
                # Label
                draw.text((100, y), label, font=self.font_body, fill=COLORS['text_gray'])
                
                # Before box
                draw.rounded_rectangle((100, y + 35, 500, y + 85), radius=10,
                                       fill=COLORS['bg_medium'], outline=COLORS['border'])
                draw.text((120, y + 45), f"Input: {before}", 
                         font=self.font_code, fill=COLORS['text_white'])
                
                # Arrow
                arrow_x = 520
                draw.text((arrow_x, y + 45), "→", font=self.font_heading, fill=color)
                
                # After box
                draw.rounded_rectangle((580, y + 35, 980, y + 85), radius=10,
                                       fill=COLORS['bg_medium'], outline=color, width=2)
                draw.text((600, y + 45), f"Output: {after}", 
                         font=self.font_code, fill=color)
        
        return img
    
    def render_conclusion_scene(self, block: NarrationBlock, frame_in_block: int,
                                 total_frames: int) -> Image.Image:
        """Render conclusion scene"""
        img = self.create_base_frame()
        draw = ImageDraw.Draw(img)
        
        progress = frame_in_block / total_frames
        
        # Title
        self.draw_text_centered(draw, "Summary & Next Steps", 100, 
                               self.font_title, COLORS['text_white'])
        
        if "business value" in block.text.lower():
            # Key achievements
            achievements = [
                ("🤖", "Multi-Agent Architecture", "4 specialized agents working together"),
                ("🔧", "MCP Tool Integration", "6 business tools via protocol"),
                ("🧠", "Session Memory", "Context-aware conversations"),
                ("🛡️", "Security First", "PII masking, access control, audit"),
                ("✓", "Fully Tested", "66 automated tests"),
                ("⚡", "Instant Response", "< 1 second processing"),
            ]
            
            cols = 2
            col_width = 700
            start_x = (WIDTH - cols * col_width) // 2
            
            for i, (icon, title, desc) in enumerate(achievements):
                ach_anim = self.ease_out_cubic(max(0, min(1, (progress - i * 0.08) * 2.5)))
                
                col = i % cols
                row = i // cols
                
                x = start_x + col * col_width
                y = 220 + row * 130 + int((1 - ach_anim) * 30)
                
                # Card
                card_w = 650
                card_h = 100
                self.draw_gradient_rect(img, (x, y, x + card_w, y + card_h),
                                        COLORS['bg_medium'], COLORS['bg_light'], radius=15)
                
                # Icon circle
                draw.ellipse((x + 20, y + 25, x + 70, y + 75), fill=COLORS['primary'])
                
                # Text
                draw.text((x + 90, y + 20), title, font=self.font_heading, fill=COLORS['text_white'])
                draw.text((x + 90, y + 60), desc, font=self.font_body, fill=COLORS['text_gray'])
        
        else:  # Thank you / GitHub
            # Big thank you
            self.draw_text_centered(draw, "Thank You!", 250, self.font_title, COLORS['primary'])
            
            # GitHub link
            github_y = 380
            github_text = "github.com/Trungnef/ai-agents-business-support"
            
            # GitHub card
            card_w = 800
            card_h = 100
            card_x = (WIDTH - card_w) // 2
            
            self.draw_gradient_rect(img, (card_x, github_y, card_x + card_w, github_y + card_h),
                                    COLORS['bg_medium'], COLORS['bg_light'], radius=20)
            draw.rounded_rectangle((card_x, github_y, card_x + card_w, github_y + card_h),
                                   radius=20, outline=COLORS['text_white'], width=2)
            
            self.draw_text_centered(draw, "Open Source on GitHub", github_y + 15, 
                                   self.font_body, COLORS['text_gray'])
            self.draw_text_centered(draw, github_text, github_y + 50, 
                                   self.font_heading, COLORS['text_white'])
            
            # Feedback request
            feedback_y = 520
            self.draw_text_centered(draw, "I welcome your feedback!", feedback_y, 
                                   self.font_subheading, COLORS['text_gray'])
            
            # Course concepts summary
            concepts_y = 600
            concepts = ["Multi-Agent", "MCP Tools", "Sessions", "Memory", 
                       "Security", "Testing", "Orchestration"]
            
            concept_width = 180
            gap = 20
            total_w = len(concepts) * concept_width + (len(concepts) - 1) * gap
            start_x = (WIDTH - total_w) // 2
            
            for i, concept in enumerate(concepts):
                con_anim = self.ease_out_cubic(max(0, min(1, (progress - 0.3 - i * 0.05) * 3)))
                
                x = start_x + i * (concept_width + gap)
                y = concepts_y + int((1 - con_anim) * 20)
                
                draw.rounded_rectangle((x, y, x + concept_width, y + 50), radius=25,
                                       fill=COLORS['primary_dark'])
                
                con_bbox = draw.textbbox((0, 0), concept, font=self.font_small)
                con_x = x + (concept_width - (con_bbox[2] - con_bbox[0])) // 2
                draw.text((con_x, y + 13), concept, font=self.font_small, fill=COLORS['text_white'])
        
        return img
    
    def ease_out_cubic(self, t: float) -> float:
        """Easing function for smooth animations"""
        return 1 - pow(1 - t, 3)
    
    def render_frame(self, block: NarrationBlock, frame_in_block: int, 
                     total_frames: int, total_progress: float) -> np.ndarray:
        """Render a single frame based on current block"""
        
        # Select scene renderer
        scene = block.scene
        if scene == "intro":
            img = self.render_intro_scene(block, frame_in_block, total_frames)
        elif scene == "problem":
            img = self.render_problem_scene(block, frame_in_block, total_frames)
        elif scene == "architecture":
            img = self.render_architecture_scene(block, frame_in_block, total_frames)
        elif scene == "demo":
            img = self.render_demo_scene(block, frame_in_block, total_frames)
        elif scene == "security":
            img = self.render_security_scene(block, frame_in_block, total_frames)
        elif scene == "conclusion":
            img = self.render_conclusion_scene(block, frame_in_block, total_frames)
        else:
            img = self.create_base_frame()
        
        # Add common elements
        draw = ImageDraw.Draw(img)
        
        # Progress bar
        self.draw_progress_bar(img, total_progress, block.scene)
        
        # Subtitle
        self.draw_subtitle_bar(img, block.text, total_progress)
        
        # Convert to OpenCV format
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    async def generate_audio(self):
        """Generate audio for all narration blocks"""
        os.makedirs(AUDIO_DIR, exist_ok=True)
        
        print("Generating audio segments...")
        
        for i, block in enumerate(NARRATION_BLOCKS):
            output_file = f"{AUDIO_DIR}/segment_{i:02d}.mp3"
            
            communicate = edge_tts.Communicate(block.text, "en-US-AriaNeural")
            await communicate.save(output_file)
            
            print(f"  Generated: segment_{i:02d}.mp3 ({block.word_count} words, ~{block.duration_sec:.1f}s)")
        
        # Concatenate all audio
        concat_file = f"{AUDIO_DIR}/concat.txt"
        with open(concat_file, 'w') as f:
            for i in range(len(NARRATION_BLOCKS)):
                f.write(f"file 'segment_{i:02d}.mp3'\n")
        
        full_audio = f"{AUDIO_DIR}/full_narration.mp3"
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file, '-c', 'copy', full_audio
        ], capture_output=True)
        
        print(f"Combined audio saved to: {full_audio}")
        
        # Get actual audio durations using ffprobe
        actual_durations = []
        for i in range(len(NARRATION_BLOCKS)):
            segment_file = f"{AUDIO_DIR}/segment_{i:02d}.mp3"
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', segment_file
            ], capture_output=True, text=True)
            duration = float(result.stdout.strip())
            actual_durations.append(duration)
            print(f"  Actual duration segment_{i:02d}: {duration:.2f}s")
        
        return actual_durations
    
    def generate_video(self, actual_durations: List[float]):
        """Generate video frames synchronized with audio"""
        
        video_file = f"{OUTPUT_DIR}/multi_agent_support_demo.mp4"
        
        # Calculate total duration and frames per block
        total_duration = sum(actual_durations)
        total_frames = int(total_duration * FPS)
        
        print(f"\nGenerating video: {total_frames} frames ({total_duration:.1f}s)")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_file, fourcc, FPS, (WIDTH, HEIGHT))
        
        frame_count = 0
        cumulative_time = 0
        
        for block_idx, block in enumerate(NARRATION_BLOCKS):
            block_duration = actual_durations[block_idx]
            block_frames = int(block_duration * FPS)
            
            print(f"  Rendering: {block.scene} - '{block.text[:50]}...' ({block_frames} frames)")
            
            for frame_in_block in range(block_frames):
                # Calculate progress
                total_progress = (cumulative_time + frame_in_block / FPS) / total_duration
                
                # Render frame
                frame = self.render_frame(block, frame_in_block, block_frames, total_progress)
                out.write(frame)
                frame_count += 1
            
            cumulative_time += block_duration
        
        out.release()
        print(f"\nVideo saved: {video_file} ({frame_count} frames)")
        
        return video_file
    
    def combine_audio_video(self, video_file: str):
        """Combine video with audio using ffmpeg"""
        
        audio_file = f"{AUDIO_DIR}/full_narration.mp3"
        output_file = f"{OUTPUT_DIR}/multi_agent_support_demo_final.mp4"
        
        print(f"\nCombining video + audio...")
        
        subprocess.run([
            'ffmpeg', '-y',
            '-i', video_file,
            '-i', audio_file,
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest',
            output_file
        ], capture_output=True)
        
        # Replace original with final
        os.replace(output_file, video_file)
        
        print(f"Final video saved: {video_file}")
        
        # Get final video info
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,nb_frames',
            '-show_entries', 'format=duration,size',
            '-of', 'json', video_file
        ], capture_output=True, text=True)
        
        print(f"\nVideo info:\n{result.stdout}")

async def main():
    print("=" * 60)
    print("Video Demo Generator v4")
    print("Perfect Voice-Subtitle Sync + Beautiful Diagrams")
    print("=" * 60)
    
    generator = VideoGenerator()
    
    # Step 1: Generate audio and get actual durations
    actual_durations = await generator.generate_audio()
    
    # Step 2: Generate video synchronized with audio durations
    video_file = generator.generate_video(actual_durations)
    
    # Step 3: Combine audio and video
    generator.combine_audio_video(video_file)
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
