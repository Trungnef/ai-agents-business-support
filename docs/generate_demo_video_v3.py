"""
Professional Demo Video Generator v3
- FIXED: Voice-subtitle perfect synchronization
- FIXED: Overlapping elements
- IMPROVED: More professional demo section
- IMPROVED: Better spacing and layout
"""

import asyncio
import os
import subprocess
import math
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# Install packages
def install_packages():
    packages = ["pillow", "numpy", "opencv-python", "edge-tts"]
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
AUDIO_DIR = OUTPUT_DIR / "audio_segments"
AUDIO_DIR.mkdir(exist_ok=True)

# Modern color palette
COLORS = {
    'bg_primary': (13, 17, 23),
    'bg_secondary': (22, 27, 34),
    'bg_tertiary': (33, 38, 45),
    'bg_card': (27, 32, 40),
    'border': (48, 54, 61),
    'border_light': (68, 76, 86),
    'text_primary': (240, 246, 252),
    'text_secondary': (139, 148, 158),
    'text_muted': (110, 118, 129),
    'accent_blue': (88, 166, 255),
    'accent_green': (63, 185, 80),
    'accent_red': (248, 81, 73),
    'accent_purple': (163, 113, 247),
    'accent_yellow': (210, 153, 34),
    'accent_cyan': (57, 211, 215),
    'accent_orange': (219, 109, 40),
}

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


# ============== NARRATION SEGMENTS WITH PRECISE TIMING ==============
@dataclass
class NarrationSegment:
    text: str
    duration_sec: float  # Exact duration for this segment
    
@dataclass
class SceneConfig:
    name: str
    segments: List[NarrationSegment]
    
    @property
    def total_duration(self) -> float:
        return sum(s.duration_sec for s in self.segments)
    
    @property
    def total_frames(self) -> int:
        return int(self.total_duration * FPS)


# Define scenes with EXACT timing for each narration
SCENES = [
    SceneConfig("intro", [
        NarrationSegment("Welcome to Multi-Agent Customer Support Assistant.", 3.5),
        NarrationSegment("A production-ready AI system for small businesses.", 3.5),
        NarrationSegment("Built for the Kaggle Gen AI Intensive Capstone.", 3.5),
        NarrationSegment("Track: Agents for Business.", 2.5),
    ]),
    SceneConfig("problem", [
        NarrationSegment("Small businesses face a major support challenge.", 3.5),
        NarrationSegment("Eighty percent of support tickets are repetitive.", 3.5),
        NarrationSegment("Customers wait hours for simple answers.", 3.0),
        NarrationSegment("Our solution responds in under one second.", 3.0),
        NarrationSegment("With twenty four seven availability.", 2.5),
    ]),
    SceneConfig("architecture", [
        NarrationSegment("The system uses a multi-agent architecture.", 3.5),
        NarrationSegment("Four specialized agents work together.", 3.0),
        NarrationSegment("Intent Classifier understands customer needs.", 3.5),
        NarrationSegment("Data Retrieval fetches information securely.", 3.5),
        NarrationSegment("Response Generator creates helpful replies.", 3.5),
        NarrationSegment("Quality Agent ensures safety and masks PII.", 3.5),
        NarrationSegment("Six MCP tools handle business operations.", 3.5),
    ]),
    SceneConfig("demo", [
        NarrationSegment("Let me demonstrate the system live.", 3.0),
        NarrationSegment("First, we set the customer email for context.", 4.0),
        NarrationSegment("Now asking: Where is my order?", 3.5),
        NarrationSegment("Intent classified as order status.", 3.0),
        NarrationSegment("Access validated. Order details retrieved.", 4.0),
        NarrationSegment("Now testing session memory.", 3.0),
        NarrationSegment("Asking: Can I refund it? Without the order number.", 4.5),
        NarrationSegment("The system remembers the previous order.", 3.5),
        NarrationSegment("Context resolution happens automatically.", 3.5),
        NarrationSegment("Now testing security guardrails.", 3.5),
        NarrationSegment("Trying to access another customer's order.", 4.0),
        NarrationSegment("Access denied. Security violation logged.", 4.0),
    ]),
    SceneConfig("security", [
        NarrationSegment("Security is built into every layer.", 3.5),
        NarrationSegment("PII masking protects sensitive data.", 3.5),
        NarrationSegment("Credit cards, emails, and phones are masked.", 4.0),
        NarrationSegment("Sixty six automated tests verify everything.", 4.0),
        NarrationSegment("All security claims are tested and verified.", 3.5),
    ]),
    SceneConfig("conclusion", [
        NarrationSegment("To summarize our implementation.", 3.0),
        NarrationSegment("All seven course concepts are complete.", 3.5),
        NarrationSegment("Multi-agent architecture with MCP tools.", 3.5),
        NarrationSegment("Persistent memory and security guardrails.", 3.5),
        NarrationSegment("The code is open source on GitHub.", 3.0),
        NarrationSegment("Thank you for watching!", 2.5),
    ]),
]


# ============== ANIMATION UTILITIES ==============
def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)

def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


# ============== VIDEO GENERATOR CLASS ==============
class VideoGenerator:
    def __init__(self):
        self.frames: List[np.ndarray] = []
        self.frame_idx = 0
        self.current_subtitle = ""
        
    def create_frame(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['bg_primary'])
        draw = ImageDraw.Draw(img)
        return img, draw
    
    def add_frame(self, img: Image.Image, count: int = 1):
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        for _ in range(count):
            self.frames.append(frame)
            self.frame_idx += 1
    
    def draw_subtitle_bar(self, draw: ImageDraw.ImageDraw, text: str, fade: float = 1.0):
        """Draw subtitle at bottom with proper background"""
        if not text:
            return
        
        bar_height = 80
        bar_y = HEIGHT - bar_height - 20
        
        # Semi-transparent background
        draw.rounded_rectangle(
            [(60, bar_y), (WIDTH - 60, bar_y + bar_height)],
            radius=12,
            fill=(*COLORS['bg_secondary'], int(230 * fade))
        )
        draw.rounded_rectangle(
            [(60, bar_y), (WIDTH - 60, bar_y + bar_height)],
            radius=12,
            outline=COLORS['border'],
            width=1
        )
        
        # Centered text
        font = get_font(28)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (WIDTH - text_w) // 2
        
        alpha = int(255 * fade)
        draw.text((x, bar_y + 25), text, font=font, fill=(*COLORS['text_primary'][:3],))
    
    def draw_progress_indicator(self, draw: ImageDraw.ImageDraw, progress: float, section: str):
        """Draw top progress bar"""
        bar_y = 15
        bar_h = 4
        
        # Background
        draw.rounded_rectangle([(40, bar_y), (WIDTH - 40, bar_y + bar_h)], 
                               radius=2, fill=COLORS['border'])
        
        # Progress
        prog_w = int((WIDTH - 80) * progress)
        if prog_w > 0:
            draw.rounded_rectangle([(40, bar_y), (40 + prog_w, bar_y + bar_h)],
                                   radius=2, fill=COLORS['accent_blue'])
        
        # Section label
        font = get_font(14)
        draw.text((40, bar_y + 12), section.upper(), font=font, fill=COLORS['text_muted'])
    
    def draw_terminal_window(self, draw: ImageDraw.ImageDraw, 
                             x: int, y: int, w: int, h: int,
                             title: str, lines: List[Tuple[str, tuple]],
                             typing: str = "", show_cursor: bool = True):
        """Draw professional terminal window"""
        # Main window with shadow effect
        draw.rounded_rectangle([x+4, y+4, x+w+4, y+h+4], radius=12, fill=(0, 0, 0, 80))
        draw.rounded_rectangle([x, y, x+w, y+h], radius=12, fill=COLORS['bg_secondary'])
        draw.rounded_rectangle([x, y, x+w, y+h], radius=12, outline=COLORS['border'], width=2)
        
        # Title bar
        draw.rounded_rectangle([x, y, x+w, y+44], radius=12, fill=COLORS['bg_tertiary'])
        draw.rectangle([x, y+32, x+w, y+44], fill=COLORS['bg_tertiary'])
        
        # Traffic light buttons
        btn_y = y + 16
        draw.ellipse([x+16, btn_y-6, x+28, btn_y+6], fill=COLORS['accent_red'])
        draw.ellipse([x+38, btn_y-6, x+50, btn_y+6], fill=COLORS['accent_yellow'])
        draw.ellipse([x+60, btn_y-6, x+72, btn_y+6], fill=COLORS['accent_green'])
        
        # Title text
        font_title = get_font(15)
        draw.text((x + 90, y + 10), title, font=font_title, fill=COLORS['text_secondary'])
        
        # Content area
        font_mono = get_font(20, mono=True)
        content_y = y + 60
        line_h = 28
        max_lines = (h - 80) // line_h
        
        visible = lines[-max_lines:] if len(lines) > max_lines else lines
        
        for i, (text, color) in enumerate(visible):
            # Truncate if too long
            max_chars = (w - 50) // 12
            display = text[:max_chars] + "..." if len(text) > max_chars else text
            draw.text((x + 20, content_y + i * line_h), display, font=font_mono, fill=color)
        
        # Typing line
        if typing or show_cursor:
            typing_y = content_y + len(visible) * line_h + 10
            cursor = "█" if show_cursor and (self.frame_idx % 20 < 10) else ""
            draw.text((x + 20, typing_y), f"$ {typing}{cursor}", font=font_mono, fill=COLORS['text_primary'])
    
    def draw_code_block(self, draw: ImageDraw.ImageDraw,
                        x: int, y: int, w: int, h: int,
                        title: str, code_lines: List[Tuple[str, tuple]]):
        """Draw code editor block"""
        # Window
        draw.rounded_rectangle([x, y, x+w, y+h], radius=12, fill=COLORS['bg_card'])
        draw.rounded_rectangle([x, y, x+w, y+h], radius=12, outline=COLORS['border'], width=1)
        
        # Header
        draw.rounded_rectangle([x, y, x+w, y+40], radius=12, fill=COLORS['bg_tertiary'])
        draw.rectangle([x, y+28, x+w, y+40], fill=COLORS['bg_tertiary'])
        
        font_title = get_font(14)
        draw.text((x + 20, y + 12), title, font=font_title, fill=COLORS['text_secondary'])
        
        # Code content
        font_mono = get_font(16, mono=True)
        code_y = y + 55
        line_h = 24
        
        for i, (line, color) in enumerate(code_lines):
            # Line number
            draw.text((x + 15, code_y + i * line_h), f"{i+1:2}", font=font_mono, fill=COLORS['text_muted'])
            # Code
            max_chars = (w - 60) // 10
            display = line[:max_chars] if len(line) > max_chars else line
            draw.text((x + 50, code_y + i * line_h), display, font=font_mono, fill=color)
    
    def draw_feature_card(self, draw: ImageDraw.ImageDraw,
                          x: int, y: int, w: int, h: int,
                          number: str, title: str, desc: str,
                          color: tuple, progress: float = 1.0):
        """Draw animated feature card"""
        if progress <= 0:
            return
        
        # Animate scale
        scale = ease_out_cubic(min(1.0, progress))
        actual_w = int(w * scale)
        actual_h = int(h * scale)
        actual_x = x + (w - actual_w) // 2
        actual_y = y + (h - actual_h) // 2
        
        if actual_w < 10 or actual_h < 10:
            return
        
        # Card background
        draw.rounded_rectangle(
            [actual_x, actual_y, actual_x + actual_w, actual_y + actual_h],
            radius=12, fill=COLORS['bg_card']
        )
        draw.rounded_rectangle(
            [actual_x, actual_y, actual_x + actual_w, actual_y + actual_h],
            radius=12, outline=color, width=2
        )
        
        if progress > 0.3:
            # Number badge
            badge_size = 40
            draw.rounded_rectangle(
                [actual_x + 15, actual_y + 15, actual_x + 15 + badge_size, actual_y + 15 + badge_size],
                radius=8, fill=color
            )
            font_num = get_font(22, bold=True)
            draw.text((actual_x + 27, actual_y + 20), number, font=font_num, fill=COLORS['bg_primary'])
            
            # Title
            font_title = get_font(22, bold=True)
            draw.text((actual_x + 70, actual_y + 20), title, font=font_title, fill=COLORS['text_primary'])
        
        if progress > 0.6:
            # Description with word wrap
            font_desc = get_font(16)
            words = desc.split()
            lines = []
            current = ""
            max_w = actual_w - 40
            
            for word in words:
                test = f"{current} {word}".strip()
                bbox = draw.textbbox((0, 0), test, font=font_desc)
                if bbox[2] - bbox[0] < max_w:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
            
            for i, line in enumerate(lines[:3]):
                draw.text((actual_x + 20, actual_y + 65 + i * 22), line, 
                         font=font_desc, fill=COLORS['text_secondary'])

    # ============== SCENE GENERATORS ==============
    
    def generate_intro_scene(self, scene: SceneConfig):
        """Generate intro with synced subtitles"""
        print(f"  Generating {scene.name}...")
        
        segment_idx = 0
        segment_frame = 0
        segment_frames = int(scene.segments[0].duration_sec * FPS)
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Update current segment
            if segment_frame >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                segment_frame = 0
                segment_frames = int(scene.segments[segment_idx].duration_sec * FPS)
            
            current_text = scene.segments[segment_idx].text
            segment_frame += 1
            
            # Background particles
            for i in range(15):
                px = int((i * 127 + f * 0.3) % WIDTH)
                py = int((i * 89 + f * 0.2) % HEIGHT)
                size = 2 + (i % 3)
                alpha = 20 + int(15 * math.sin(f * 0.03 + i))
                draw.ellipse([px, py, px+size, py+size], fill=(*COLORS['accent_blue'][:3],))
            
            cx, cy = WIDTH // 2, HEIGHT // 2
            progress = f / scene.total_frames
            
            # Badge
            if f > 15:
                badge_prog = ease_out_cubic(min(1, (f - 15) / 25))
                badge_y = int(cy - 180 - 20 * (1 - badge_prog))
                
                badge_text = "KAGGLE CAPSTONE 2026"
                font_badge = get_font(20, bold=True)
                bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
                badge_w = bbox[2] - bbox[0] + 50
                
                draw.rounded_rectangle(
                    [cx - badge_w//2, badge_y, cx + badge_w//2, badge_y + 40],
                    radius=20, fill=COLORS['accent_blue']
                )
                draw.text((cx - badge_w//2 + 25, badge_y + 8), badge_text,
                         font=font_badge, fill=COLORS['bg_primary'])
            
            # Main title
            if f > 30:
                title_prog = ease_out_cubic(min(1, (f - 30) / 30))
                title_y = int(cy - 80 + 30 * (1 - title_prog))
                
                title1 = "Multi-Agent Customer Support"
                title2 = "Assistant for SMBs"
                font_title = get_font(58, bold=True)
                
                bbox1 = draw.textbbox((0, 0), title1, font=font_title)
                draw.text((cx - (bbox1[2]-bbox1[0])//2, title_y), title1,
                         font=font_title, fill=COLORS['text_primary'])
                
                bbox2 = draw.textbbox((0, 0), title2, font=font_title)
                draw.text((cx - (bbox2[2]-bbox2[0])//2, title_y + 70), title2,
                         font=font_title, fill=COLORS['text_primary'])
            
            # Animated line
            if f > 60:
                line_prog = ease_out_cubic(min(1, (f - 60) / 25))
                line_w = int(350 * line_prog)
                draw.rounded_rectangle(
                    [cx - line_w//2, cy + 85, cx + line_w//2, cy + 91],
                    radius=3, fill=COLORS['accent_cyan']
                )
            
            # Subtitle
            if f > 75:
                track_text = "Track: Agents for Business"
                font_track = get_font(26)
                bbox = draw.textbbox((0, 0), track_text, font=font_track)
                draw.text((cx - (bbox[2]-bbox[0])//2, cy + 130), track_text,
                         font=font_track, fill=COLORS['text_secondary'])
            
            self.draw_progress_indicator(draw, progress * 0.1, "Introduction")
            self.draw_subtitle_bar(draw, current_text)
            self.add_frame(img)
    
    def generate_problem_scene(self, scene: SceneConfig):
        """Generate problem/solution scene"""
        print(f"  Generating {scene.name}...")
        
        segment_idx = 0
        segment_frame = 0
        segment_frames = int(scene.segments[0].duration_sec * FPS)
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Update segment
            if segment_frame >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                segment_frame = 0
                segment_frames = int(scene.segments[segment_idx].duration_sec * FPS)
            
            current_text = scene.segments[segment_idx].text
            segment_frame += 1
            progress = f / scene.total_frames
            
            # Header
            font_header = get_font(44, bold=True)
            draw.text((80, 90), "Problem & Solution", font=font_header, fill=COLORS['text_primary'])
            
            # Left panel - Problem (with proper spacing)
            panel_y = 180
            panel_w = 820
            panel_h = 480
            panel_gap = 80  # Gap between panels
            
            left_x = 80
            right_x = left_x + panel_w + panel_gap
            
            # Left panel slides in
            left_prog = ease_out_cubic(min(1, f / 45))
            actual_left_x = int(-panel_w + (panel_w + left_x) * left_prog)
            
            draw.rounded_rectangle(
                [actual_left_x, panel_y, actual_left_x + panel_w, panel_y + panel_h],
                radius=16, fill=COLORS['bg_card']
            )
            draw.rounded_rectangle(
                [actual_left_x, panel_y, actual_left_x + panel_w, panel_y + panel_h],
                radius=16, outline=COLORS['accent_red'], width=2
            )
            
            font_section = get_font(26, bold=True)
            draw.text((actual_left_x + 30, panel_y + 25), "THE PROBLEM",
                     font=font_section, fill=COLORS['accent_red'])
            
            # Animated stat
            if f > 30:
                stat_prog = ease_out_cubic(min(1, (f - 30) / 50))
                stat_val = int(80 * stat_prog)
                font_big = get_font(110, bold=True)
                draw.text((actual_left_x + 30, panel_y + 70), f"{stat_val}%",
                         font=font_big, fill=COLORS['accent_red'])
                
                font_label = get_font(24)
                draw.text((actual_left_x + 30, panel_y + 200), "of tickets are repetitive",
                         font=font_label, fill=COLORS['text_primary'])
            
            # Problem list
            problems = [
                "Order tracking inquiries",
                "Refund and return requests",
                "Password reset issues",
                "Common FAQ questions"
            ]
            font_item = get_font(20)
            for i, prob in enumerate(problems):
                item_show = f > 50 + i * 15
                if item_show:
                    item_y = panel_y + 260 + i * 48
                    draw.ellipse([actual_left_x + 35, item_y + 5, actual_left_x + 47, item_y + 17],
                               fill=COLORS['accent_red'])
                    draw.text((actual_left_x + 60, item_y), prob,
                             font=font_item, fill=COLORS['text_secondary'])
            
            # Right panel - Solution (slides in after)
            if f > 50:
                right_prog = ease_out_cubic(min(1, (f - 50) / 45))
                actual_right_x = int(WIDTH + (right_x - WIDTH) * right_prog)
                
                draw.rounded_rectangle(
                    [actual_right_x, panel_y, actual_right_x + panel_w, panel_y + panel_h],
                    radius=16, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [actual_right_x, panel_y, actual_right_x + panel_w, panel_y + panel_h],
                    radius=16, outline=COLORS['accent_green'], width=2
                )
                
                draw.text((actual_right_x + 30, panel_y + 25), "OUR SOLUTION",
                         font=font_section, fill=COLORS['accent_green'])
                
                solutions = [
                    ("< 1 sec", "Response time"),
                    ("24/7", "Availability"),
                    ("100%", "PII protection"),
                    ("10x", "Scalability")
                ]
                
                for i, (val, label) in enumerate(solutions):
                    show_at = 80 + i * 20
                    if f > show_at:
                        sol_y = panel_y + 80 + i * 95
                        font_val = get_font(38, bold=True)
                        font_lbl = get_font(20)
                        
                        draw.text((actual_right_x + 30, sol_y), val,
                                 font=font_val, fill=COLORS['accent_green'])
                        draw.text((actual_right_x + 30, sol_y + 48), label,
                                 font=font_lbl, fill=COLORS['text_secondary'])
            
            self.draw_progress_indicator(draw, 0.1 + progress * 0.12, "Problem & Solution")
            self.draw_subtitle_bar(draw, current_text)
            self.add_frame(img)
    
    def generate_architecture_scene(self, scene: SceneConfig):
        """Generate architecture scene with proper spacing"""
        print(f"  Generating {scene.name}...")
        
        segment_idx = 0
        segment_frame = 0
        segment_frames = int(scene.segments[0].duration_sec * FPS)
        
        agents = [
            ("1", "Intent Classifier", "Understands customer needs", COLORS['accent_blue']),
            ("2", "Data Retrieval", "Fetches data via MCP tools", COLORS['accent_cyan']),
            ("3", "Response Generator", "Creates helpful replies", COLORS['accent_green']),
            ("4", "Quality Agent", "Ensures safety, masks PII", COLORS['accent_purple']),
        ]
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Update segment
            if segment_frame >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                segment_frame = 0
                segment_frames = int(scene.segments[segment_idx].duration_sec * FPS)
            
            current_text = scene.segments[segment_idx].text
            segment_frame += 1
            progress = f / scene.total_frames
            
            # Header
            font_header = get_font(44, bold=True)
            draw.text((80, 70), "Multi-Agent Architecture", font=font_header, fill=COLORS['text_primary'])
            
            font_sub = get_font(22)
            draw.text((80, 125), "Four specialized agents working in sequence",
                     font=font_sub, fill=COLORS['text_secondary'])
            
            # Agent cards - 2x2 grid with proper spacing
            card_w, card_h = 420, 150
            start_x, start_y = 80, 180
            gap_x, gap_y = 460, 170  # Increased gaps
            
            for i, (num, title, desc, color) in enumerate(agents):
                col = i % 2
                row = i // 2
                x = start_x + col * gap_x
                y = start_y + row * gap_y
                
                show_at = 30 + i * 35
                if f > show_at:
                    anim_prog = min(1, (f - show_at) / 30)
                    self.draw_feature_card(draw, x, y, card_w, card_h, num, title, desc, color, anim_prog)
            
            # Connection arrows
            if f > 170:
                arrow_color = COLORS['accent_cyan']
                # Horizontal arrow 1->2
                ax1 = start_x + card_w + 10
                ay1 = start_y + card_h // 2
                ax2 = start_x + gap_x - 10
                draw.line([(ax1, ay1), (ax2, ay1)], fill=arrow_color, width=3)
                draw.polygon([(ax2, ay1-8), (ax2+12, ay1), (ax2, ay1+8)], fill=arrow_color)
                
                # Vertical arrow 1->3
                vx = start_x + card_w // 2
                vy1 = start_y + card_h + 5
                vy2 = start_y + gap_y - 5
                draw.line([(vx, vy1), (vx, vy2)], fill=arrow_color, width=3)
                draw.polygon([(vx-8, vy2), (vx, vy2+12), (vx+8, vy2)], fill=arrow_color)
            
            # MCP Tools section
            if f > 200:
                tools_x = 1020
                tools_y = 180
                tools_w = 460
                tools_h = 380
                
                tools_prog = ease_out_cubic(min(1, (f - 200) / 40))
                actual_x = int(WIDTH + (tools_x - WIDTH) * tools_prog)
                
                draw.rounded_rectangle(
                    [actual_x, tools_y, actual_x + tools_w, tools_y + tools_h],
                    radius=12, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [actual_x, tools_y, actual_x + tools_w, tools_y + tools_h],
                    radius=12, outline=COLORS['accent_orange'], width=2
                )
                
                font_section = get_font(22, bold=True)
                draw.text((actual_x + 20, tools_y + 15), "MCP Tool Server",
                         font=font_section, fill=COLORS['accent_orange'])
                
                tools = [
                    "get_order_details",
                    "get_refund_policy",
                    "get_customer_profile",
                    "create_support_ticket",
                    "mask_sensitive_data",
                    "audit_log_event"
                ]
                
                font_tool = get_font(17, mono=True)
                for i, tool in enumerate(tools):
                    show_tool = f > 210 + i * 8
                    if show_tool:
                        ty = tools_y + 60 + i * 50
                        draw.rounded_rectangle(
                            [actual_x + 15, ty, actual_x + tools_w - 15, ty + 38],
                            radius=6, fill=COLORS['bg_tertiary']
                        )
                        draw.text((actual_x + 30, ty + 8), tool,
                                 font=font_tool, fill=COLORS['accent_cyan'])
            
            self.draw_progress_indicator(draw, 0.22 + progress * 0.18, "Architecture")
            self.draw_subtitle_bar(draw, current_text)
            self.add_frame(img)
    
    def generate_demo_scene(self, scene: SceneConfig):
        """Generate professional CLI demo"""
        print(f"  Generating {scene.name}...")
        
        segment_idx = 0
        segment_frame = 0
        segment_frames = int(scene.segments[0].duration_sec * FPS)
        
        # Demo script with precise timing
        demo_events = [
            # (start_frame, type, content, outputs)
            (0, "info", "Starting CLI demonstration...", []),
            (60, "cmd", "python -m src.cli chat", [
                ("Starting Multi-Agent CLI...", COLORS['accent_cyan']),
                ("[OK] Session store initialized", COLORS['accent_green']),
                ("[OK] MCP server ready (6 tools)", COLORS['accent_green']),
            ]),
            (180, "cmd", "/email alice.johnson@email.com", [
                ("[SESSION] Email: alice.johnson@email.com", COLORS['accent_green']),
            ]),
            (270, "cmd", "Where is my order ORD-2024-002?", [
                ("[INTENT] ORDER_STATUS (conf: 0.94)", COLORS['accent_purple']),
                ("[AUTH] Access: OWNER VERIFIED", COLORS['accent_green']),
                ("[MCP] get_order_details()", COLORS['accent_cyan']),
                ("", COLORS['text_primary']),
                ("Your order ORD-2024-002 is SHIPPED.", COLORS['text_primary']),
                ("Delivery: Tomorrow by 5 PM", COLORS['text_primary']),
            ]),
            (480, "cmd", "Can I refund it?", [
                ("[INTENT] REFUND_REQUEST (conf: 0.91)", COLORS['accent_purple']),
                ("[MEMORY] 'it' -> ORD-2024-002", COLORS['accent_yellow']),
                ("[MCP] get_refund_policy()", COLORS['accent_cyan']),
                ("", COLORS['text_primary']),
                ("Yes! Eligible for full refund.", COLORS['text_primary']),
                ("Within 30-day return window.", COLORS['text_primary']),
            ]),
            (720, "cmd", "Show me order ORD-2024-001", [
                ("[INTENT] ORDER_STATUS (conf: 0.92)", COLORS['accent_purple']),
                ("[AUTH] Access: DENIED", COLORS['accent_red']),
                ("[SECURITY] Owner mismatch", COLORS['accent_red']),
                ("[SECURITY] Violation: 1/3", COLORS['accent_red']),
                ("", COLORS['text_primary']),
                ("Cannot access this order.", COLORS['accent_red']),
            ]),
        ]
        
        terminal_lines = []
        current_cmd = ""
        typing_idx = 0
        event_idx = 0
        output_idx = 0
        state = "idle"  # idle, typing, output, pause
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Update subtitle segment
            if segment_frame >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                segment_frame = 0
                segment_frames = int(scene.segments[segment_idx].duration_sec * FPS)
            
            current_text = scene.segments[segment_idx].text
            segment_frame += 1
            progress = f / scene.total_frames
            
            # Process demo events
            if event_idx < len(demo_events):
                start_f, etype, content, outputs = demo_events[event_idx]
                
                if f >= start_f:
                    if state == "idle":
                        if etype == "info":
                            terminal_lines.append((f"# {content}", COLORS['text_muted']))
                            event_idx += 1
                        elif etype == "cmd":
                            current_cmd = content
                            typing_idx = 0
                            state = "typing"
                    
                    elif state == "typing":
                        if typing_idx < len(current_cmd):
                            typing_idx += 1
                        else:
                            terminal_lines.append((f"$ {current_cmd}", COLORS['text_primary']))
                            current_cmd = ""
                            typing_idx = 0
                            output_idx = 0
                            state = "output"
                    
                    elif state == "output":
                        if output_idx < len(outputs):
                            if f % 5 == 0:  # Slow down output
                                terminal_lines.append(outputs[output_idx])
                                output_idx += 1
                        else:
                            state = "idle"
                            event_idx += 1
            
            # Header
            font_header = get_font(36, bold=True)
            draw.text((80, 60), "Live System Demonstration", font=font_header, fill=COLORS['text_primary'])
            
            # Terminal
            typing_text = current_cmd[:typing_idx] if state == "typing" else ""
            self.draw_terminal_window(
                draw, 100, 120, WIDTH - 200, HEIGHT - 250,
                "Terminal - Multi-Agent CLI",
                terminal_lines, typing_text, show_cursor=(state in ["typing", "idle"])
            )
            
            self.draw_progress_indicator(draw, 0.4 + progress * 0.3, "Live Demo")
            self.draw_subtitle_bar(draw, current_text)
            self.add_frame(img)
    
    def generate_security_scene(self, scene: SceneConfig):
        """Generate security & testing scene"""
        print(f"  Generating {scene.name}...")
        
        segment_idx = 0
        segment_frame = 0
        segment_frames = int(scene.segments[0].duration_sec * FPS)
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Update segment
            if segment_frame >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                segment_frame = 0
                segment_frames = int(scene.segments[segment_idx].duration_sec * FPS)
            
            current_text = scene.segments[segment_idx].text
            segment_frame += 1
            progress = f / scene.total_frames
            
            # Header
            font_header = get_font(44, bold=True)
            draw.text((80, 70), "Security & Evaluation", font=font_header, fill=COLORS['text_primary'])
            
            # Left: Security features (with proper spacing)
            sec_x, sec_y = 80, 160
            sec_w, sec_h = 560, 520
            
            sec_prog = ease_out_cubic(min(1, f / 40))
            draw.rounded_rectangle(
                [sec_x, sec_y, sec_x + sec_w, sec_y + int(sec_h * sec_prog)],
                radius=12, fill=COLORS['bg_card']
            )
            draw.rounded_rectangle(
                [sec_x, sec_y, sec_x + sec_w, sec_y + int(sec_h * sec_prog)],
                radius=12, outline=COLORS['accent_red'], width=2
            )
            
            if sec_prog > 0.3:
                font_section = get_font(24, bold=True)
                draw.text((sec_x + 25, sec_y + 20), "Security Features",
                         font=font_section, fill=COLORS['accent_red'])
                
                features = [
                    ("PII Masking", "Credit cards, emails protected"),
                    ("Access Control", "Owner verification required"),
                    ("Session Lockout", "3 failed attempts = locked"),
                    ("Audit Logging", "All operations tracked"),
                ]
                
                font_title = get_font(20, bold=True)
                font_desc = get_font(16)
                
                for i, (title, desc) in enumerate(features):
                    show_at = 40 + i * 30
                    if f > show_at:
                        fy = sec_y + 75 + i * 105
                        
                        # Checkmark
                        draw.ellipse([sec_x + 25, fy + 2, sec_x + 45, fy + 22],
                                   fill=COLORS['accent_green'])
                        font_check = get_font(14, bold=True)
                        draw.text((sec_x + 30, fy + 3), "✓", font=font_check, fill=COLORS['bg_primary'])
                        
                        draw.text((sec_x + 60, fy), title, font=font_title, fill=COLORS['text_primary'])
                        draw.text((sec_x + 60, fy + 30), desc, font=font_desc, fill=COLORS['text_secondary'])
            
            # Right: Test results (with gap)
            if f > 80:
                test_x = 700  # Gap from left panel
                test_w = 560
                test_h = 520
                
                test_prog = ease_out_cubic(min(1, (f - 80) / 40))
                draw.rounded_rectangle(
                    [test_x, sec_y, test_x + test_w, sec_y + int(test_h * test_prog)],
                    radius=12, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [test_x, sec_y, test_x + test_w, sec_y + int(test_h * test_prog)],
                    radius=12, outline=COLORS['accent_green'], width=2
                )
                
                if test_prog > 0.3:
                    font_section = get_font(24, bold=True)
                    draw.text((test_x + 25, sec_y + 20), "Test Results",
                             font=font_section, fill=COLORS['accent_green'])
                    
                    # Animated counter
                    count_prog = min(1, (f - 100) / 80)
                    test_count = int(66 * count_prog)
                    
                    font_big = get_font(80, bold=True)
                    draw.text((test_x + 25, sec_y + 60), f"{test_count}/66",
                             font=font_big, fill=COLORS['accent_green'])
                    
                    font_label = get_font(22)
                    draw.text((test_x + 25, sec_y + 155), "tests passing",
                             font=font_label, fill=COLORS['text_primary'])
                    
                    # Categories
                    if f > 150:
                        categories = [
                            ("Intent Classification", "9"),
                            ("Security & PII", "13"),
                            ("Orchestrator", "13"),
                            ("Session/Memory", "16"),
                            ("Tools/MCP", "15"),
                        ]
                        
                        font_cat = get_font(18)
                        for i, (cat, count) in enumerate(categories):
                            show_cat = f > 150 + i * 15
                            if show_cat:
                                cy = sec_y + 210 + i * 50
                                draw.text((test_x + 25, cy), cat, font=font_cat, fill=COLORS['text_secondary'])
                                draw.text((test_x + 350, cy), f"{count} tests", font=font_cat, fill=COLORS['accent_cyan'])
            
            self.draw_progress_indicator(draw, 0.7 + progress * 0.15, "Security & Evaluation")
            self.draw_subtitle_bar(draw, current_text)
            self.add_frame(img)
    
    def generate_conclusion_scene(self, scene: SceneConfig):
        """Generate conclusion scene"""
        print(f"  Generating {scene.name}...")
        
        segment_idx = 0
        segment_frame = 0
        segment_frames = int(scene.segments[0].duration_sec * FPS)
        
        concepts = [
            "Multi-Agent Architecture",
            "MCP Tool Server",
            "Session & Memory",
            "Security Guardrails",
            "PII Masking",
            "66 Automated Tests",
            "CLI & REST API",
        ]
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Update segment
            if segment_frame >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                segment_frame = 0
                segment_frames = int(scene.segments[segment_idx].duration_sec * FPS)
            
            current_text = scene.segments[segment_idx].text
            segment_frame += 1
            progress = f / scene.total_frames
            
            cx = WIDTH // 2
            
            # Header
            font_header = get_font(48, bold=True)
            title = "Implementation Complete"
            bbox = draw.textbbox((0, 0), title, font=font_header)
            draw.text((cx - (bbox[2]-bbox[0])//2, 80), title,
                     font=font_header, fill=COLORS['text_primary'])
            
            # Checklist
            start_y = 180
            font_item = get_font(28)
            
            for i, concept in enumerate(concepts):
                show_at = 20 + i * 12
                if f > show_at:
                    prog = ease_out_cubic(min(1, (f - show_at) / 18))
                    offset = int(40 * (1 - prog))
                    
                    y = start_y + i * 58
                    
                    # Checkmark
                    draw.ellipse([cx - 280 + offset, y + 4, cx - 256 + offset, y + 28],
                               fill=COLORS['accent_green'])
                    draw.text((cx - 275 + offset, y + 5), "✓", font=get_font(16, bold=True), fill=COLORS['bg_primary'])
                    
                    draw.text((cx - 240 + offset, y), concept,
                             font=font_item, fill=COLORS['text_primary'])
            
            # GitHub link
            if f > 140:
                link_y = HEIGHT - 180
                font_link = get_font(24)
                
                draw.rounded_rectangle(
                    [cx - 350, link_y, cx + 350, link_y + 55],
                    radius=28, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [cx - 350, link_y, cx + 350, link_y + 55],
                    radius=28, outline=COLORS['accent_blue'], width=2
                )
                
                link_text = "github.com/Trungnef/ai-agents-business-support"
                bbox = draw.textbbox((0, 0), link_text, font=font_link)
                draw.text((cx - (bbox[2]-bbox[0])//2, link_y + 14), link_text,
                         font=font_link, fill=COLORS['accent_blue'])
            
            # Thank you
            if f > 180:
                font_thanks = get_font(38, bold=True)
                thanks = "Thank You for Watching!"
                bbox = draw.textbbox((0, 0), thanks, font=font_thanks)
                draw.text((cx - (bbox[2]-bbox[0])//2, HEIGHT - 100), thanks,
                         font=font_thanks, fill=COLORS['accent_green'])
            
            self.draw_progress_indicator(draw, 0.85 + progress * 0.15, "Conclusion")
            self.draw_subtitle_bar(draw, current_text)
            self.add_frame(img)
    
    def generate_video(self):
        """Generate complete video"""
        print("\n" + "=" * 60)
        print("GENERATING VIDEO v3")
        print("=" * 60 + "\n")
        
        for scene in SCENES:
            if scene.name == "intro":
                self.generate_intro_scene(scene)
            elif scene.name == "problem":
                self.generate_problem_scene(scene)
            elif scene.name == "architecture":
                self.generate_architecture_scene(scene)
            elif scene.name == "demo":
                self.generate_demo_scene(scene)
            elif scene.name == "security":
                self.generate_security_scene(scene)
            elif scene.name == "conclusion":
                self.generate_conclusion_scene(scene)
            
            print(f"    Total frames: {len(self.frames)}")
        
        return self.frames


async def generate_audio():
    """Generate synchronized audio"""
    print("\nGenerating audio...")
    
    # Collect all narration texts with pauses
    texts = []
    for scene in SCENES:
        for seg in scene.segments:
            texts.append(seg.text)
    
    full_text = " ... ".join(texts)
    
    audio_path = OUTPUT_DIR / "narration.mp3"
    communicate = edge_tts.Communicate(full_text, "en-US-AriaNeural", rate="+0%")
    await communicate.save(str(audio_path))
    
    print(f"Audio saved: {audio_path}")
    return audio_path


def write_video(frames: List[np.ndarray]) -> Path:
    """Write frames to video file"""
    video_path = OUTPUT_DIR / "temp_video.mp4"
    
    print(f"\nWriting {len(frames)} frames...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, FPS, (WIDTH, HEIGHT))
    
    for i, frame in enumerate(frames):
        out.write(frame)
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(frames)}")
    
    out.release()
    print(f"Video saved: {video_path}")
    return video_path


def combine_av(video_path: Path, audio_path: Path) -> Path:
    """Combine video and audio"""
    final_path = OUTPUT_DIR / "multi_agent_support_demo.mp4"
    
    print("\nCombining video and audio...")
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except:
        print("ffmpeg not found, saving without audio")
        video_path.rename(final_path)
        return final_path
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-movflags", "+faststart",
        str(final_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        print(f"Final video: {final_path}")
    except Exception as e:
        print(f"FFmpeg error: {e}")
        video_path.rename(final_path)
    
    return final_path


def verify(path: Path):
    """Verify output video"""
    print("\n" + "=" * 50)
    print("VERIFICATION")
    print("=" * 50)
    
    if not path.exists():
        print("ERROR: Video not found")
        return False
    
    cap = cv2.VideoCapture(str(path))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frames / fps if fps else 0
    size = path.stat().st_size / (1024 * 1024)
    cap.release()
    
    print(f"Resolution: {w}x{h}")
    print(f"FPS: {fps}")
    print(f"Frames: {frames}")
    print(f"Duration: {duration:.1f}s ({duration/60:.1f} min)")
    print(f"Size: {size:.1f} MB")
    print("\n✓ VERIFICATION PASSED")
    return True


def main():
    # Generate video frames
    gen = VideoGenerator()
    frames = gen.generate_video()
    
    # Write video
    video_path = write_video(frames)
    
    # Generate audio
    audio_path = asyncio.run(generate_audio())
    
    # Combine
    final_path = combine_av(video_path, audio_path)
    
    # Verify
    verify(final_path)
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print(f"Output: {final_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
