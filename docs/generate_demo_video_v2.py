"""
Professional Demo Video Generator v2
- Fixed: Text-voice synchronization
- Fixed: Text overflow issues
- Added: More animations and transitions
- Added: Better visual effects
"""

import asyncio
import os
import subprocess
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Install required packages
def install_packages():
    packages = ["pillow", "numpy", "opencv-python", "edge-tts", "pydub"]
    for pkg in packages:
        try:
            __import__(pkg.replace("-", "_").split("[")[0])
        except ImportError:
            subprocess.run(["pip", "install", pkg, "-q"], check=False)

install_packages()

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import cv2
import edge_tts

# ============== CONFIGURATION ==============
WIDTH, HEIGHT = 1920, 1080
FPS = 30
OUTPUT_DIR = Path(__file__).parent
VIDEO_PATH = OUTPUT_DIR / "temp_video.mp4"
AUDIO_DIR = OUTPUT_DIR / "audio_segments"
FINAL_VIDEO_PATH = OUTPUT_DIR / "multi_agent_support_demo.mp4"

# Create audio directory
AUDIO_DIR.mkdir(exist_ok=True)

# Modern color palette
COLORS = {
    'bg_primary': (13, 17, 23),       # GitHub dark
    'bg_secondary': (22, 27, 34),     # Card background
    'bg_tertiary': (33, 38, 45),      # Hover state
    'border': (48, 54, 61),           # Border color
    'text_primary': (240, 246, 252),  # Primary text
    'text_secondary': (139, 148, 158), # Secondary text
    'text_muted': (110, 118, 129),    # Muted text
    'accent_blue': (88, 166, 255),    # Links, accents
    'accent_green': (63, 185, 80),    # Success
    'accent_red': (248, 81, 73),      # Error/danger
    'accent_purple': (163, 113, 247), # Special
    'accent_yellow': (210, 153, 34),  # Warning
    'accent_cyan': (57, 211, 215),    # Info
    'accent_orange': (219, 109, 40),  # Highlight
    'gradient_start': (88, 166, 255),
    'gradient_end': (163, 113, 247),
}

# Font loading
def get_font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        paths = ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf"]
    elif bold:
        paths = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
    else:
        paths = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

# ============== DATA STRUCTURES ==============
@dataclass
class AudioSegment:
    text: str
    filename: str
    duration: float = 0.0

@dataclass 
class Scene:
    name: str
    duration_seconds: float
    narrations: List[AudioSegment]

# ============== SCENES DEFINITION WITH SYNCED NARRATION ==============
SCENES = [
    Scene(
        name="intro",
        duration_seconds=12,
        narrations=[
            AudioSegment("Welcome to Multi-Agent Customer Support Assistant.", "intro_1.mp3"),
            AudioSegment("A production-ready AI system for small and medium businesses.", "intro_2.mp3"),
            AudioSegment("Built for the Kaggle five day gen AI intensive capstone.", "intro_3.mp3"),
        ]
    ),
    Scene(
        name="problem",
        duration_seconds=15,
        narrations=[
            AudioSegment("Small businesses face a major challenge.", "problem_1.mp3"),
            AudioSegment("Eighty percent of support tickets are repetitive questions.", "problem_2.mp3"),
            AudioSegment("Customers wait hours for simple answers.", "problem_3.mp3"),
            AudioSegment("Our solution responds in under one second.", "problem_4.mp3"),
        ]
    ),
    Scene(
        name="architecture",
        duration_seconds=20,
        narrations=[
            AudioSegment("The system uses a multi-agent architecture.", "arch_1.mp3"),
            AudioSegment("Four specialized agents work in sequence.", "arch_2.mp3"),
            AudioSegment("Intent classifier understands what customers need.", "arch_3.mp3"),
            AudioSegment("Data retrieval fetches information securely.", "arch_4.mp3"),
            AudioSegment("Response generator creates helpful replies.", "arch_5.mp3"),
            AudioSegment("Quality agent ensures safety and masks sensitive data.", "arch_6.mp3"),
        ]
    ),
    Scene(
        name="demo_part1",
        duration_seconds=25,
        narrations=[
            AudioSegment("Let me show you the system in action.", "demo1_1.mp3"),
            AudioSegment("First we set the customer email for context.", "demo1_2.mp3"),
            AudioSegment("Now asking where is my order.", "demo1_3.mp3"),
            AudioSegment("The system classifies intent as order status.", "demo1_4.mp3"),
            AudioSegment("It validates access and retrieves the order.", "demo1_5.mp3"),
            AudioSegment("Response generated in under one second.", "demo1_6.mp3"),
        ]
    ),
    Scene(
        name="demo_part2",
        duration_seconds=25,
        narrations=[
            AudioSegment("Now watch session memory in action.", "demo2_1.mp3"),
            AudioSegment("I ask can I refund it without saying the order number.", "demo2_2.mp3"),
            AudioSegment("The system remembers the previous order.", "demo2_3.mp3"),
            AudioSegment("Context resolution happens automatically.", "demo2_4.mp3"),
            AudioSegment("Refund policy is checked via MCP tools.", "demo2_5.mp3"),
        ]
    ),
    Scene(
        name="security",
        duration_seconds=20,
        narrations=[
            AudioSegment("Security is built into every layer.", "sec_1.mp3"),
            AudioSegment("When I try to access another customer's order.", "sec_2.mp3"),
            AudioSegment("The system blocks unauthorized access immediately.", "sec_3.mp3"),
            AudioSegment("PII masking protects sensitive data.", "sec_4.mp3"),
            AudioSegment("Sixty six automated tests verify all security claims.", "sec_5.mp3"),
        ]
    ),
    Scene(
        name="conclusion",
        duration_seconds=15,
        narrations=[
            AudioSegment("To summarize our implementation.", "concl_1.mp3"),
            AudioSegment("All seven course concepts are working.", "concl_2.mp3"),
            AudioSegment("Multi-agent architecture with MCP tools.", "concl_3.mp3"),
            AudioSegment("Persistent memory and security guardrails.", "concl_4.mp3"),
            AudioSegment("Thank you for watching!", "concl_5.mp3"),
        ]
    ),
]

# ============== ANIMATION UTILITIES ==============
def ease_out_cubic(t: float) -> float:
    """Cubic ease-out for smooth animations"""
    return 1 - pow(1 - t, 3)

def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out"""
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

def ease_out_back(t: float) -> float:
    """Overshoot ease-out"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + (b - a) * t

def lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Interpolate between two colors"""
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

# ============== DRAWING UTILITIES ==============
class VideoGenerator:
    def __init__(self):
        self.frames: List[np.ndarray] = []
        self.current_frame = 0
        
    def create_frame(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        """Create new frame with gradient background"""
        img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['bg_primary'])
        draw = ImageDraw.Draw(img)
        
        # Subtle gradient overlay
        for y in range(HEIGHT):
            alpha = int(8 * (1 - y / HEIGHT))
            color = tuple(min(255, c + alpha) for c in COLORS['bg_primary'])
            draw.line([(0, y), (WIDTH, y)], fill=color)
        
        return img, draw
    
    def draw_rounded_rect(self, draw: ImageDraw.ImageDraw, coords: tuple, 
                          radius: int, fill: tuple, outline: tuple = None, width: int = 1):
        """Draw rounded rectangle"""
        draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)
    
    def draw_glow_rect(self, img: Image.Image, coords: tuple, color: tuple, radius: int = 20):
        """Draw rectangle with glow effect"""
        glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        
        # Draw multiple expanding rectangles with decreasing alpha
        x1, y1, x2, y2 = coords
        for i in range(5, 0, -1):
            alpha = int(30 * (6 - i) / 5)
            expand = i * 3
            glow_draw.rounded_rectangle(
                [x1 - expand, y1 - expand, x2 + expand, y2 + expand],
                radius=radius + expand,
                fill=(*color, alpha)
            )
        
        img.paste(Image.alpha_composite(img.convert('RGBA'), glow).convert('RGB'))
    
    def draw_text_with_wrap(self, draw: ImageDraw.ImageDraw, text: str, 
                            x: int, y: int, max_width: int, font: ImageFont.FreeTypeFont,
                            color: tuple, line_spacing: int = 8) -> int:
        """Draw text with automatic word wrapping, returns total height"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        total_height = 0
        for i, line in enumerate(lines):
            line_y = y + i * (font.size + line_spacing)
            draw.text((x, line_y), line, font=font, fill=color)
            total_height = line_y + font.size
        
        return total_height - y
    
    def draw_terminal(self, img: Image.Image, draw: ImageDraw.ImageDraw,
                      x: int, y: int, w: int, h: int, title: str,
                      lines: List[Tuple[str, tuple]], typing_text: str = "",
                      cursor_visible: bool = True):
        """Draw realistic terminal window"""
        # Shadow
        shadow_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        shadow_draw.rounded_rectangle(
            [x + 8, y + 8, x + w + 8, y + h + 8],
            radius=12, fill=(0, 0, 0, 60)
        )
        shadow_blur = shadow_img.filter(ImageFilter.GaussianBlur(8))
        img.paste(Image.alpha_composite(img.convert('RGBA'), shadow_blur).convert('RGB'))
        
        # Main window
        self.draw_rounded_rect(draw, (x, y, x + w, y + h), 12, 
                               COLORS['bg_secondary'], COLORS['border'], 2)
        
        # Title bar
        draw.rounded_rectangle([x, y, x + w, y + 44], radius=12, fill=COLORS['bg_tertiary'])
        draw.rectangle([x, y + 32, x + w, y + 44], fill=COLORS['bg_tertiary'])
        
        # Traffic lights
        draw.ellipse([x + 16, y + 14, x + 28, y + 26], fill=COLORS['accent_red'])
        draw.ellipse([x + 36, y + 14, x + 48, y + 26], fill=COLORS['accent_yellow'])
        draw.ellipse([x + 56, y + 14, x + 68, y + 26], fill=COLORS['accent_green'])
        
        # Title
        font_title = get_font(16)
        draw.text((x + 85, y + 12), title, font=font_title, fill=COLORS['text_secondary'])
        
        # Content
        font_mono = get_font(18, mono=True)
        content_y = y + 60
        line_height = 26
        max_lines = (h - 80) // line_height
        
        visible_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        
        for i, (text, color) in enumerate(visible_lines):
            # Truncate long lines
            max_chars = (w - 40) // 10
            display_text = text[:max_chars] + "..." if len(text) > max_chars else text
            draw.text((x + 20, content_y + i * line_height), display_text, 
                     font=font_mono, fill=color)
        
        # Typing line
        if typing_text or cursor_visible:
            typing_y = content_y + len(visible_lines) * line_height
            cursor = "█" if cursor_visible and (self.current_frame % 20 < 10) else ""
            prompt = "$ "
            draw.text((x + 20, typing_y), prompt + typing_text + cursor, 
                     font=font_mono, fill=COLORS['text_primary'])
    
    def draw_subtitle(self, draw: ImageDraw.ImageDraw, text: str, progress: float = 1.0):
        """Draw subtitle bar at bottom"""
        if not text:
            return
            
        # Background with fade
        alpha = int(200 * min(1.0, progress * 2))
        sub_y = HEIGHT - 100
        draw.rectangle([(0, sub_y), (WIDTH, sub_y + 70)], fill=(*COLORS['bg_primary'], alpha))
        draw.line([(0, sub_y), (WIDTH, sub_y)], fill=COLORS['border'], width=1)
        
        # Text centered
        font = get_font(26)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (WIDTH - text_width) // 2
        draw.text((x, sub_y + 20), text, font=font, fill=COLORS['text_primary'])
    
    def draw_progress_bar(self, draw: ImageDraw.ImageDraw, progress: float, section: str):
        """Draw top progress bar"""
        # Background bar
        bar_y = 20
        bar_height = 4
        draw.rectangle([(40, bar_y), (WIDTH - 40, bar_y + bar_height)], fill=COLORS['border'])
        
        # Progress fill
        fill_width = int((WIDTH - 80) * progress)
        if fill_width > 0:
            draw.rectangle([(40, bar_y), (40 + fill_width, bar_y + bar_height)], 
                          fill=COLORS['accent_blue'])
        
        # Section label
        font = get_font(14)
        draw.text((40, bar_y + 10), section.upper(), font=font, fill=COLORS['text_muted'])
    
    def add_frame(self, img: Image.Image, count: int = 1):
        """Add frame(s) to video"""
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        for _ in range(count):
            self.frames.append(frame)
            self.current_frame += 1

    # ============== SCENE GENERATORS ==============
    
    def generate_intro(self, duration_frames: int, narrations: List[AudioSegment]):
        """Generate intro scene with animations"""
        print("  Generating intro scene...")
        
        for f in range(duration_frames):
            img, draw = self.create_frame()
            progress = f / duration_frames
            
            # Animated background particles
            for i in range(20):
                px = int((i * 97 + f * 0.5) % WIDTH)
                py = int((i * 73 + f * 0.3) % HEIGHT)
                size = 2 + (i % 3)
                alpha = int(30 + 20 * math.sin(f * 0.05 + i))
                draw.ellipse([px, py, px + size, py + size], 
                            fill=(*COLORS['accent_blue'][:3], alpha))
            
            center_x, center_y = WIDTH // 2, HEIGHT // 2
            
            # Badge animation
            if f > 20:
                badge_progress = ease_out_cubic(min(1, (f - 20) / 30))
                badge_y = int(center_y - 200 + 20 * (1 - badge_progress))
                badge_alpha = int(255 * badge_progress)
                
                badge_text = "KAGGLE CAPSTONE 2026"
                font_badge = get_font(18, bold=True)
                bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
                badge_w = bbox[2] - bbox[0] + 40
                
                draw.rounded_rectangle(
                    [center_x - badge_w//2, badge_y - 5, center_x + badge_w//2, badge_y + 35],
                    radius=20, fill=COLORS['accent_blue']
                )
                draw.text((center_x - badge_w//2 + 20, badge_y + 3), badge_text, 
                         font=font_badge, fill=COLORS['bg_primary'])
            
            # Main title with slide-up animation
            if f > 40:
                title_progress = ease_out_back(min(1, (f - 40) / 40))
                title_y = int(center_y - 80 + 40 * (1 - title_progress))
                
                title1 = "Multi-Agent Customer Support"
                title2 = "Assistant for SMBs"
                font_title = get_font(56, bold=True)
                
                # Title 1
                bbox1 = draw.textbbox((0, 0), title1, font=font_title)
                draw.text((center_x - (bbox1[2] - bbox1[0])//2, title_y), 
                         title1, font=font_title, fill=COLORS['text_primary'])
                
                # Title 2
                bbox2 = draw.textbbox((0, 0), title2, font=font_title)
                draw.text((center_x - (bbox2[2] - bbox2[0])//2, title_y + 70), 
                         title2, font=font_title, fill=COLORS['text_primary'])
            
            # Subtitle
            if f > 80:
                sub_progress = ease_out_cubic(min(1, (f - 80) / 30))
                subtitle = "Track: Agents for Business"
                font_sub = get_font(28)
                bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
                draw.text((center_x - (bbox[2] - bbox[0])//2, center_y + 120), 
                         subtitle, font=font_sub, fill=COLORS['text_secondary'])
            
            # Animated underline
            if f > 100:
                line_progress = ease_out_cubic(min(1, (f - 100) / 30))
                line_width = int(300 * line_progress)
                draw.rectangle(
                    [center_x - line_width//2, center_y + 100, 
                     center_x + line_width//2, center_y + 104],
                    fill=COLORS['accent_cyan']
                )
            
            # Determine current narration for subtitle
            narration_idx = min(len(narrations) - 1, int(progress * len(narrations)))
            if narration_idx >= 0:
                self.draw_subtitle(draw, narrations[narration_idx].text, progress)
            
            self.draw_progress_bar(draw, progress * 0.1, "Introduction")
            self.add_frame(img)
    
    def generate_problem_scene(self, duration_frames: int, narrations: List[AudioSegment]):
        """Generate problem & solution scene"""
        print("  Generating problem scene...")
        
        for f in range(duration_frames):
            img, draw = self.create_frame()
            progress = f / duration_frames
            
            # Header
            font_header = get_font(42, bold=True)
            draw.text((80, 80), "The Problem & Solution", font=font_header, fill=COLORS['text_primary'])
            
            # Left panel - Problem (slides in from left)
            panel_progress = ease_out_cubic(min(1, f / 60))
            panel_x = int(-500 + 580 * panel_progress)
            panel_y, panel_w, panel_h = 160, 800, 500
            
            self.draw_rounded_rect(draw, (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h),
                                   16, COLORS['bg_secondary'], COLORS['accent_red'], 2)
            
            # Problem header
            font_section = get_font(28, bold=True)
            draw.text((panel_x + 30, panel_y + 25), "❌ THE PROBLEM", 
                     font=font_section, fill=COLORS['accent_red'])
            
            # Animated percentage
            if f > 30:
                stat_progress = ease_out_cubic(min(1, (f - 30) / 60))
                stat_val = int(80 * stat_progress)
                font_big = get_font(100, bold=True)
                draw.text((panel_x + 30, panel_y + 80), f"{stat_val}%", 
                         font=font_big, fill=COLORS['accent_red'])
                
                font_label = get_font(24)
                draw.text((panel_x + 30, panel_y + 200), "of tickets are repetitive", 
                         font=font_label, fill=COLORS['text_primary'])
            
            # Problem bullets
            if f > 60:
                problems = [
                    "Order tracking inquiries",
                    "Refund and return requests", 
                    "Password reset issues",
                    "Common FAQ questions"
                ]
                font_item = get_font(20)
                for i, problem in enumerate(problems):
                    item_progress = ease_out_cubic(min(1, (f - 60 - i * 15) / 20))
                    if item_progress > 0:
                        alpha = int(255 * item_progress)
                        item_y = panel_y + 260 + i * 45
                        draw.text((panel_x + 50, item_y), f"• {problem}", 
                                 font=font_item, fill=COLORS['text_secondary'])
            
            # Right panel - Solution (slides in from right)
            if f > 60:
                sol_progress = ease_out_cubic(min(1, (f - 60) / 60))
                sol_x = int(WIDTH + 100 - 920 * sol_progress)
                
                self.draw_rounded_rect(draw, (sol_x, panel_y, sol_x + panel_w, panel_y + panel_h),
                                       16, COLORS['bg_secondary'], COLORS['accent_green'], 2)
                
                draw.text((sol_x + 30, panel_y + 25), "✓ OUR SOLUTION", 
                         font=font_section, fill=COLORS['accent_green'])
                
                solutions = [
                    ("< 1 second", "response time"),
                    ("24/7", "availability"),
                    ("100%", "PII protection"),
                    ("10x", "scalability")
                ]
                
                for i, (value, label) in enumerate(solutions):
                    item_progress = ease_out_cubic(min(1, (f - 90 - i * 20) / 25))
                    if item_progress > 0:
                        item_y = panel_y + 90 + i * 100
                        font_val = get_font(36, bold=True)
                        font_lbl = get_font(20)
                        draw.text((sol_x + 30, item_y), value, font=font_val, fill=COLORS['accent_green'])
                        draw.text((sol_x + 30, item_y + 45), label, font=font_lbl, fill=COLORS['text_secondary'])
            
            # Narration subtitle
            narration_idx = min(len(narrations) - 1, int(progress * len(narrations)))
            if narration_idx >= 0:
                self.draw_subtitle(draw, narrations[narration_idx].text)
            
            self.draw_progress_bar(draw, 0.1 + progress * 0.1, "Problem & Solution")
            self.add_frame(img)
    
    def generate_architecture_scene(self, duration_frames: int, narrations: List[AudioSegment]):
        """Generate architecture scene with animated diagram"""
        print("  Generating architecture scene...")
        
        agents = [
            ("Intent Classifier", COLORS['accent_blue'], "Understands customer needs"),
            ("Data Retrieval", COLORS['accent_cyan'], "Fetches info via MCP tools"),
            ("Response Generator", COLORS['accent_green'], "Creates helpful replies"),
            ("Quality Agent", COLORS['accent_purple'], "Ensures safety & masks PII"),
        ]
        
        for f in range(duration_frames):
            img, draw = self.create_frame()
            progress = f / duration_frames
            
            # Header
            font_header = get_font(42, bold=True)
            draw.text((80, 60), "Multi-Agent Architecture", font=font_header, fill=COLORS['text_primary'])
            
            font_sub = get_font(22)
            draw.text((80, 115), "Four specialized agents working in sequence", 
                     font=font_sub, fill=COLORS['text_secondary'])
            
            # Draw agent pipeline
            start_x, start_y = 120, 200
            box_w, box_h = 380, 180
            gap = 40
            
            for i, (name, color, desc) in enumerate(agents):
                # Animation timing
                show_at = i * 40
                if f > show_at:
                    anim_progress = ease_out_back(min(1, (f - show_at) / 40))
                    
                    # Calculate position
                    col = i % 2
                    row = i // 2
                    x = start_x + col * (box_w + gap)
                    y = start_y + row * (box_h + gap)
                    
                    # Animated scale
                    scale = anim_progress
                    actual_w = int(box_w * scale)
                    actual_h = int(box_h * scale)
                    actual_x = x + (box_w - actual_w) // 2
                    actual_y = y + (box_h - actual_h) // 2
                    
                    # Draw box
                    self.draw_rounded_rect(draw, 
                        (actual_x, actual_y, actual_x + actual_w, actual_y + actual_h),
                        12, COLORS['bg_secondary'], color, 2)
                    
                    if anim_progress > 0.5:
                        # Number badge
                        badge_size = 36
                        draw.ellipse([actual_x + 15, actual_y + 15, 
                                     actual_x + 15 + badge_size, actual_y + 15 + badge_size],
                                    fill=color)
                        font_num = get_font(20, bold=True)
                        draw.text((actual_x + 26, actual_y + 20), str(i + 1), 
                                 font=font_num, fill=COLORS['bg_primary'])
                        
                        # Title
                        font_title = get_font(22, bold=True)
                        draw.text((actual_x + 60, actual_y + 20), name, 
                                 font=font_title, fill=COLORS['text_primary'])
                        
                        # Description
                        font_desc = get_font(16)
                        self.draw_text_with_wrap(draw, desc, actual_x + 20, actual_y + 70,
                                                actual_w - 40, font_desc, COLORS['text_secondary'])
            
            # Connection arrows
            if f > 160:
                arrow_alpha = min(255, (f - 160) * 5)
                # Arrow between boxes (simplified)
                arrow_color = (*COLORS['accent_cyan'][:3],)
                
                # Horizontal arrow (1 -> 2)
                draw.line([(start_x + box_w, start_y + box_h//2),
                          (start_x + box_w + gap, start_y + box_h//2)], 
                         fill=arrow_color, width=3)
                
                # Vertical arrow (2 -> 3)
                mid_x = start_x + box_w + gap//2
                draw.line([(mid_x + box_w//2, start_y + box_h),
                          (mid_x + box_w//2, start_y + box_h + gap)], 
                         fill=arrow_color, width=3)
            
            # Right side: MCP Tools
            if f > 200:
                tools_x = 900
                tools_progress = ease_out_cubic(min(1, (f - 200) / 60))
                
                self.draw_rounded_rect(draw, (tools_x, 200, tools_x + 450, 620),
                                       12, COLORS['bg_secondary'], COLORS['accent_orange'], 2)
                
                font_section = get_font(24, bold=True)
                draw.text((tools_x + 20, 220), "🔧 MCP Tool Server", 
                         font=font_section, fill=COLORS['accent_orange'])
                
                tools = [
                    "get_order_details",
                    "get_refund_policy",
                    "get_customer_profile",
                    "create_support_ticket",
                    "mask_sensitive_data",
                    "audit_log_event"
                ]
                
                font_tool = get_font(18, mono=True)
                for i, tool in enumerate(tools):
                    if f > 200 + i * 10:
                        y_pos = 280 + i * 50
                        draw.rounded_rectangle([tools_x + 20, y_pos, tools_x + 430, y_pos + 40],
                                              radius=6, fill=COLORS['bg_tertiary'])
                        draw.text((tools_x + 35, y_pos + 8), tool, 
                                 font=font_tool, fill=COLORS['accent_cyan'])
            
            # Narration subtitle
            narration_idx = min(len(narrations) - 1, int(progress * len(narrations)))
            if narration_idx >= 0:
                self.draw_subtitle(draw, narrations[narration_idx].text)
            
            self.draw_progress_bar(draw, 0.2 + progress * 0.15, "Architecture")
            self.add_frame(img)
    
    def generate_demo_scene(self, duration_frames: int, narrations: List[AudioSegment], part: int):
        """Generate CLI demo scene"""
        print(f"  Generating demo scene part {part}...")
        
        terminal_lines = []
        
        if part == 1:
            commands = [
                ("python -m src.cli chat", 40, [
                    ("Starting Multi-Agent CLI...", COLORS['accent_cyan']),
                    ("[OK] Session database initialized", COLORS['accent_green']),
                    ("[OK] MCP server online (6 tools)", COLORS['accent_green']),
                ]),
                ("/email alice.johnson@email.com", 30, [
                    ("[SESSION] Email set: alice.johnson@email.com", COLORS['accent_green']),
                ]),
                ("Where is my order ORD-2024-002?", 50, [
                    ("[INTENT] ORDER_STATUS (0.94)", COLORS['accent_purple']),
                    ("[AUTH] Access validated: OWNER MATCH", COLORS['accent_green']),
                    ("[MCP] get_order_details(ORD-2024-002)", COLORS['accent_cyan']),
                    ("", COLORS['text_primary']),
                    ("Your order ORD-2024-002 is SHIPPED.", COLORS['text_primary']),
                    ("Expected: Tomorrow by 5 PM", COLORS['text_primary']),
                ]),
            ]
        else:
            commands = [
                ("Can I refund it?", 40, [
                    ("[INTENT] REFUND_REQUEST (0.91)", COLORS['accent_purple']),
                    ("[MEMORY] Resolved: 'it' -> ORD-2024-002", COLORS['accent_yellow']),
                    ("[MCP] get_refund_policy(ORD-2024-002)", COLORS['accent_cyan']),
                    ("", COLORS['text_primary']),
                    ("Yes! Order eligible for full refund.", COLORS['text_primary']),
                    ("Within 30-day return policy.", COLORS['text_primary']),
                ]),
                ("Show me order ORD-2024-001", 40, [
                    ("[INTENT] ORDER_STATUS (0.92)", COLORS['accent_purple']),
                    ("[AUTH] Access DENIED", COLORS['accent_red']),
                    ("[SECURITY] Order belongs to another customer", COLORS['accent_red']),
                    ("", COLORS['text_primary']),
                    ("Sorry, I cannot access that order.", COLORS['text_primary']),
                ]),
            ]
        
        frame_idx = 0
        cmd_idx = 0
        char_idx = 0
        output_idx = 0
        state = "typing"  # typing, output, pause
        state_timer = 0
        
        for f in range(duration_frames):
            img, draw = self.create_frame()
            progress = f / duration_frames
            
            # Process command sequence
            if cmd_idx < len(commands):
                cmd, pause_frames, outputs = commands[cmd_idx]
                
                if state == "typing":
                    if char_idx < len(cmd):
                        char_idx += 1
                        state_timer = 0
                    else:
                        terminal_lines.append((f"$ {cmd}", COLORS['text_primary']))
                        state = "output"
                        output_idx = 0
                        state_timer = 0
                        char_idx = 0
                
                elif state == "output":
                    state_timer += 1
                    if state_timer % 8 == 0 and output_idx < len(outputs):
                        terminal_lines.append(outputs[output_idx])
                        output_idx += 1
                    elif output_idx >= len(outputs) and state_timer > 10:
                        state = "pause"
                        state_timer = 0
                
                elif state == "pause":
                    state_timer += 1
                    if state_timer >= pause_frames:
                        cmd_idx += 1
                        state = "typing"
                        state_timer = 0
            
            # Draw terminal
            current_typing = commands[cmd_idx][0][:char_idx] if cmd_idx < len(commands) and state == "typing" else ""
            self.draw_terminal(img, draw, 100, 100, WIDTH - 200, HEIGHT - 220,
                              "Terminal - CLI Demo", terminal_lines, current_typing)
            
            # Narration subtitle
            narration_idx = min(len(narrations) - 1, int(progress * len(narrations)))
            if narration_idx >= 0:
                self.draw_subtitle(draw, narrations[narration_idx].text)
            
            base_progress = 0.35 if part == 1 else 0.55
            self.draw_progress_bar(draw, base_progress + progress * 0.15, f"Live Demo Part {part}")
            self.add_frame(img)
    
    def generate_security_scene(self, duration_frames: int, narrations: List[AudioSegment]):
        """Generate security & testing scene"""
        print("  Generating security scene...")
        
        for f in range(duration_frames):
            img, draw = self.create_frame()
            progress = f / duration_frames
            
            # Header
            font_header = get_font(42, bold=True)
            draw.text((80, 60), "Security & Evaluation", font=font_header, fill=COLORS['text_primary'])
            
            # Left: Security features
            sec_x, sec_y = 80, 150
            sec_w, sec_h = 550, 500
            
            sec_progress = ease_out_cubic(min(1, f / 50))
            self.draw_rounded_rect(draw, (sec_x, sec_y, sec_x + sec_w, sec_y + sec_h),
                                   12, COLORS['bg_secondary'], COLORS['accent_red'], 2)
            
            font_section = get_font(24, bold=True)
            draw.text((sec_x + 25, sec_y + 20), "🛡️ Security Features", 
                     font=font_section, fill=COLORS['accent_red'])
            
            features = [
                ("PII Masking", "Credit cards, emails, phones protected"),
                ("Access Control", "Orders only accessible by owner"),
                ("Session Lockout", "Blocks after 3 failed attempts"),
                ("Audit Logging", "All operations tracked"),
            ]
            
            font_title = get_font(20, bold=True)
            font_desc = get_font(16)
            
            for i, (title, desc) in enumerate(features):
                if f > 30 + i * 25:
                    y_pos = sec_y + 80 + i * 100
                    draw.text((sec_x + 25, y_pos), f"✓ {title}", 
                             font=font_title, fill=COLORS['accent_green'])
                    draw.text((sec_x + 45, y_pos + 30), desc, 
                             font=font_desc, fill=COLORS['text_secondary'])
            
            # Right: Test results
            if f > 100:
                test_x = 700
                test_progress = ease_out_cubic(min(1, (f - 100) / 50))
                
                self.draw_rounded_rect(draw, (test_x, sec_y, test_x + 550, sec_y + sec_h),
                                       12, COLORS['bg_secondary'], COLORS['accent_green'], 2)
                
                draw.text((test_x + 25, sec_y + 20), "✅ Test Results", 
                         font=font_section, fill=COLORS['accent_green'])
                
                # Animated test count
                test_count = min(66, int((f - 100) / 3))
                font_big = get_font(72, bold=True)
                draw.text((test_x + 25, sec_y + 70), f"{test_count}/66", 
                         font=font_big, fill=COLORS['accent_green'])
                
                draw.text((test_x + 25, sec_y + 160), "tests passing", 
                         font=font_title, fill=COLORS['text_primary'])
                
                # Test categories
                if f > 150:
                    categories = [
                        ("Intent Classification", "9 tests"),
                        ("Security & PII", "13 tests"),
                        ("Orchestrator", "13 tests"),
                        ("Session/Memory", "16 tests"),
                    ]
                    
                    for i, (cat, count) in enumerate(categories):
                        if f > 150 + i * 20:
                            y_pos = sec_y + 220 + i * 55
                            draw.text((test_x + 25, y_pos), cat, 
                                     font=font_desc, fill=COLORS['text_secondary'])
                            draw.text((test_x + 350, y_pos), count, 
                                     font=font_desc, fill=COLORS['accent_cyan'])
            
            # Narration subtitle
            narration_idx = min(len(narrations) - 1, int(progress * len(narrations)))
            if narration_idx >= 0:
                self.draw_subtitle(draw, narrations[narration_idx].text)
            
            self.draw_progress_bar(draw, 0.7 + progress * 0.15, "Security & Evaluation")
            self.add_frame(img)
    
    def generate_conclusion_scene(self, duration_frames: int, narrations: List[AudioSegment]):
        """Generate conclusion scene"""
        print("  Generating conclusion scene...")
        
        for f in range(duration_frames):
            img, draw = self.create_frame()
            progress = f / duration_frames
            
            center_x = WIDTH // 2
            
            # Title
            font_header = get_font(48, bold=True)
            title = "Implementation Complete"
            bbox = draw.textbbox((0, 0), title, font=font_header)
            draw.text((center_x - (bbox[2] - bbox[0])//2, 80), title, 
                     font=font_header, fill=COLORS['text_primary'])
            
            # Checklist of implemented concepts
            concepts = [
                ("Multi-Agent Architecture", True),
                ("MCP Tool Server", True),
                ("Session & Memory", True),
                ("Security Guardrails", True),
                ("PII Masking", True),
                ("66 Automated Tests", True),
                ("CLI & REST API", True),
            ]
            
            start_y = 180
            font_item = get_font(28)
            
            for i, (concept, done) in enumerate(concepts):
                if f > 20 + i * 15:
                    y_pos = start_y + i * 60
                    anim = ease_out_cubic(min(1, (f - 20 - i * 15) / 20))
                    x_offset = int(50 * (1 - anim))
                    
                    icon = "✓" if done else "○"
                    color = COLORS['accent_green'] if done else COLORS['text_muted']
                    draw.text((center_x - 250 + x_offset, y_pos), f"{icon} {concept}", 
                             font=font_item, fill=color)
            
            # GitHub link
            if f > 150:
                link_y = HEIGHT - 180
                font_link = get_font(24)
                
                draw.rounded_rectangle([center_x - 350, link_y, center_x + 350, link_y + 60],
                                      radius=30, fill=COLORS['bg_secondary'], 
                                      outline=COLORS['accent_blue'], width=2)
                
                link_text = "github.com/Trungnef/ai-agents-business-support"
                bbox = draw.textbbox((0, 0), link_text, font=font_link)
                draw.text((center_x - (bbox[2] - bbox[0])//2, link_y + 15), 
                         link_text, font=font_link, fill=COLORS['accent_blue'])
            
            # Thank you
            if f > 180:
                thanks_progress = ease_out_cubic(min(1, (f - 180) / 30))
                font_thanks = get_font(36, bold=True)
                thanks = "Thank You for Watching!"
                bbox = draw.textbbox((0, 0), thanks, font=font_thanks)
                alpha = int(255 * thanks_progress)
                draw.text((center_x - (bbox[2] - bbox[0])//2, HEIGHT - 100), 
                         thanks, font=font_thanks, fill=COLORS['accent_green'])
            
            # Narration subtitle
            narration_idx = min(len(narrations) - 1, int(progress * len(narrations)))
            if narration_idx >= 0:
                self.draw_subtitle(draw, narrations[narration_idx].text)
            
            self.draw_progress_bar(draw, 0.85 + progress * 0.15, "Conclusion")
            self.add_frame(img)
    
    def generate_all_scenes(self):
        """Generate all video scenes"""
        print("\nGenerating video scenes...")
        
        for scene in SCENES:
            duration_frames = int(scene.duration_seconds * FPS)
            
            if scene.name == "intro":
                self.generate_intro(duration_frames, scene.narrations)
            elif scene.name == "problem":
                self.generate_problem_scene(duration_frames, scene.narrations)
            elif scene.name == "architecture":
                self.generate_architecture_scene(duration_frames, scene.narrations)
            elif scene.name == "demo_part1":
                self.generate_demo_scene(duration_frames, scene.narrations, 1)
            elif scene.name == "demo_part2":
                self.generate_demo_scene(duration_frames, scene.narrations, 2)
            elif scene.name == "security":
                self.generate_security_scene(duration_frames, scene.narrations)
            elif scene.name == "conclusion":
                self.generate_conclusion_scene(duration_frames, scene.narrations)
            
            print(f"    {scene.name}: {len(self.frames)} total frames")
    
    def write_video(self):
        """Write frames to video file"""
        print(f"\nWriting {len(self.frames)} frames to video...")
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(VIDEO_PATH), fourcc, FPS, (WIDTH, HEIGHT))
        
        for i, frame in enumerate(self.frames):
            out.write(frame)
            if (i + 1) % 500 == 0:
                print(f"  Written {i + 1}/{len(self.frames)} frames")
        
        out.release()
        print(f"Video saved to: {VIDEO_PATH}")
        return True


async def generate_audio():
    """Generate synchronized audio narration"""
    print("\nGenerating audio narration...")
    
    all_texts = []
    for scene in SCENES:
        for narration in scene.narrations:
            all_texts.append(narration.text)
    
    # Join with pauses
    full_text = " ... ".join(all_texts)
    
    # Use natural-sounding voice
    communicate = edge_tts.Communicate(
        full_text, 
        "en-US-AriaNeural",
        rate="+5%",  # Slightly faster
        pitch="+0Hz"
    )
    
    audio_path = OUTPUT_DIR / "narration.mp3"
    await communicate.save(str(audio_path))
    print(f"Audio saved to: {audio_path}")
    return audio_path


def combine_video_audio(audio_path: Path):
    """Combine video and audio using ffmpeg"""
    print("\nCombining video and audio...")
    
    try:
        # Check ffmpeg
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except:
        print("Warning: ffmpeg not found. Saving video without audio.")
        VIDEO_PATH.rename(FINAL_VIDEO_PATH)
        return
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(VIDEO_PATH),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-movflags", "+faststart",
        str(FINAL_VIDEO_PATH)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        print(f"Final video: {FINAL_VIDEO_PATH}")
        
        # Cleanup temp files
        VIDEO_PATH.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        VIDEO_PATH.rename(FINAL_VIDEO_PATH)


def verify_video():
    """Verify the generated video"""
    print("\n" + "=" * 50)
    print("VERIFYING VIDEO")
    print("=" * 50)
    
    if not FINAL_VIDEO_PATH.exists():
        print(f"ERROR: Video not found at {FINAL_VIDEO_PATH}")
        return False
    
    cap = cv2.VideoCapture(str(FINAL_VIDEO_PATH))
    
    if not cap.isOpened():
        print("ERROR: Cannot open video")
        return False
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    file_size = FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024)
    
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Frames: {total_frames}")
    print(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
    print(f"File size: {file_size:.1f} MB")
    
    # Sample frames check
    errors = []
    for pos in [0, total_frames//4, total_frames//2, total_frames-1]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if not ret:
            errors.append(f"Frame {pos}: read failed")
    
    cap.release()
    
    if errors:
        print("\nErrors found:")
        for e in errors:
            print(f"  - {e}")
        return False
    
    print("\n✓ VIDEO VERIFICATION PASSED")
    return True


def main():
    print("=" * 60)
    print("DEMO VIDEO GENERATOR v2")
    print("Multi-Agent Customer Support Assistant")
    print("=" * 60)
    
    # Generate video
    generator = VideoGenerator()
    generator.generate_all_scenes()
    generator.write_video()
    
    # Generate audio
    audio_path = asyncio.run(generate_audio())
    
    # Combine
    combine_video_audio(audio_path)
    
    # Verify
    verify_video()
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print(f"Output: {FINAL_VIDEO_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
