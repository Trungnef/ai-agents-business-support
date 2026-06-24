"""
Professional Demo Video Generator v4
====================================
PERFECT VOICE-SUBTITLE SYNCHRONIZATION
- Audio generated PER SEGMENT with exact duration measurement
- Video frames calculated from ACTUAL audio duration
- Beautiful diagrams with proper spacing and animations
"""

import asyncio
import os
import subprocess
import math
import wave
import struct
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from io import BytesIO

# Install packages
def install_packages():
    packages = ["pillow", "numpy", "opencv-python", "edge-tts", "pydub"]
    for pkg in packages:
        try:
            if pkg == "pydub":
                __import__("pydub")
            elif pkg == "opencv-python":
                __import__("cv2")
            elif pkg == "edge-tts":
                __import__("edge_tts")
            else:
                __import__(pkg.replace("-", "_"))
        except ImportError:
            subprocess.run(["pip", "install", pkg, "-q"], check=False)

install_packages()

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import edge_tts
from pydub import AudioSegment

# ============== CONFIGURATION ==============
WIDTH, HEIGHT = 1920, 1080
FPS = 30
OUTPUT_DIR = Path(__file__).parent
AUDIO_DIR = OUTPUT_DIR / "audio_segments_v4"
AUDIO_DIR.mkdir(exist_ok=True)

# Modern color palette (GitHub Dark style)
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
    'accent_pink': (219, 97, 162),
    # Gradient colors
    'gradient_blue': [(56, 139, 253), (88, 166, 255), (121, 192, 255)],
    'gradient_green': [(35, 134, 54), (63, 185, 80), (87, 195, 107)],
    'gradient_purple': [(130, 80, 223), (163, 113, 247), (196, 146, 255)],
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


# ============== NARRATION DATA ==============
@dataclass
class NarrationSegment:
    text: str
    audio_path: Optional[Path] = None
    actual_duration: float = 0.0  # Will be set after audio generation
    
@dataclass  
class SceneConfig:
    name: str
    segments: List[NarrationSegment]
    
    @property
    def total_duration(self) -> float:
        return sum(s.actual_duration for s in self.segments)
    
    @property
    def total_frames(self) -> int:
        return int(self.total_duration * FPS)


# Scene definitions
SCENES = [
    SceneConfig("intro", [
        NarrationSegment("Welcome to Multi-Agent Customer Support Assistant."),
        NarrationSegment("A production-ready AI system for small businesses."),
        NarrationSegment("Built for the Kaggle Gen AI Intensive Capstone."),
        NarrationSegment("Track: Agents for Business."),
    ]),
    SceneConfig("problem", [
        NarrationSegment("Small businesses face a major support challenge."),
        NarrationSegment("Eighty percent of support tickets are repetitive."),
        NarrationSegment("Customers wait hours for simple answers."),
        NarrationSegment("Our solution responds in under one second."),
        NarrationSegment("With twenty-four seven availability."),
    ]),
    SceneConfig("architecture", [
        NarrationSegment("The system uses a multi-agent architecture."),
        NarrationSegment("Four specialized agents work together seamlessly."),
        NarrationSegment("Intent Classifier understands customer needs with high accuracy."),
        NarrationSegment("Data Retrieval Agent fetches information through secure MCP tools."),
        NarrationSegment("Response Generator creates helpful, personalized replies."),
        NarrationSegment("Quality Agent ensures safety and masks all PII data."),
        NarrationSegment("Six MCP tools handle all business operations."),
    ]),
    SceneConfig("demo", [
        NarrationSegment("Let me demonstrate the system in action."),
        NarrationSegment("First, we set the customer email for session context."),
        NarrationSegment("Now asking: Where is my order?"),
        NarrationSegment("Intent classified as order status with high confidence."),
        NarrationSegment("Access validated. Order details retrieved successfully."),
        NarrationSegment("Now testing session memory capabilities."),
        NarrationSegment("Asking: Can I refund it? Without specifying the order."),
        NarrationSegment("The system remembers the previous order automatically."),
        NarrationSegment("Context resolution happens seamlessly in the background."),
        NarrationSegment("Now testing the security guardrails."),
        NarrationSegment("Trying to access another customer's order."),
        NarrationSegment("Access denied. Security violation has been logged."),
    ]),
    SceneConfig("security", [
        NarrationSegment("Security is built into every layer of the system."),
        NarrationSegment("PII masking protects all sensitive customer data."),
        NarrationSegment("Credit card numbers, emails, and phone numbers are automatically masked."),
        NarrationSegment("Sixty-six automated tests verify every security claim."),
        NarrationSegment("All security features are thoroughly tested and verified."),
    ]),
    SceneConfig("conclusion", [
        NarrationSegment("To summarize our implementation."),
        NarrationSegment("All seven course concepts have been completed."),
        NarrationSegment("Multi-agent architecture with MCP tool integration."),
        NarrationSegment("Persistent session memory and security guardrails."),
        NarrationSegment("The code is fully open source on GitHub."),
        NarrationSegment("Thank you for watching!"),
    ]),
]


# ============== AUDIO GENERATION (PER SEGMENT) ==============
async def generate_segment_audio(segment: NarrationSegment, idx: int) -> float:
    """Generate audio for a single segment and return actual duration"""
    audio_path = AUDIO_DIR / f"segment_{idx:03d}.mp3"
    
    # Generate TTS
    communicate = edge_tts.Communicate(
        segment.text, 
        "en-US-AriaNeural",
        rate="-5%",  # Slightly slower for clarity
        pitch="+0Hz"
    )
    await communicate.save(str(audio_path))
    
    # Get actual duration using pydub
    audio = AudioSegment.from_mp3(audio_path)
    duration = len(audio) / 1000.0  # Convert ms to seconds
    
    # Add small padding for natural pauses
    duration += 0.3
    
    segment.audio_path = audio_path
    segment.actual_duration = duration
    
    return duration


async def generate_all_audio():
    """Generate audio for all segments and measure actual durations"""
    print("\n" + "=" * 60)
    print("GENERATING AUDIO (Per Segment for Perfect Sync)")
    print("=" * 60)
    
    idx = 0
    total_duration = 0
    
    for scene in SCENES:
        print(f"\n[{scene.name.upper()}]")
        for seg in scene.segments:
            duration = await generate_segment_audio(seg, idx)
            total_duration += duration
            print(f"  Segment {idx}: {duration:.2f}s - \"{seg.text[:50]}...\"")
            idx += 1
    
    print(f"\nTotal audio duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    return total_duration


def combine_audio_segments() -> Path:
    """Combine all segment audio files into one"""
    print("\nCombining audio segments...")
    
    combined = AudioSegment.empty()
    
    for scene in SCENES:
        for seg in scene.segments:
            if seg.audio_path and seg.audio_path.exists():
                audio = AudioSegment.from_mp3(seg.audio_path)
                # Add segment audio
                combined += audio
                # Add padding silence
                silence = AudioSegment.silent(duration=300)  # 300ms pause
                combined += silence
    
    output_path = OUTPUT_DIR / "combined_narration_v4.mp3"
    combined.export(output_path, format="mp3", bitrate="192k")
    print(f"Combined audio: {output_path} ({len(combined)/1000:.1f}s)")
    
    return output_path


# ============== ANIMATION UTILITIES ==============
def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)

def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_back(t: float) -> float:
    c1, c3 = 1.70158, c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def draw_gradient_rect(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int,
                       color1: tuple, color2: tuple, vertical: bool = True):
    """Draw a simple gradient rectangle"""
    steps = y2 - y1 if vertical else x2 - x1
    for i in range(max(1, steps)):
        t = i / max(1, steps - 1)
        r = int(lerp(color1[0], color2[0], t))
        g = int(lerp(color1[1], color2[1], t))
        b = int(lerp(color1[2], color2[2], t))
        if vertical:
            draw.line([(x1, y1 + i), (x2, y1 + i)], fill=(r, g, b))
        else:
            draw.line([(x1 + i, y1), (x1 + i, y2)], fill=(r, g, b))


# ============== VIDEO GENERATOR CLASS ==============
class VideoGenerator:
    def __init__(self):
        self.frames: List[np.ndarray] = []
        self.frame_idx = 0
        
    def create_frame(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new('RGB', (WIDTH, HEIGHT), COLORS['bg_primary'])
        draw = ImageDraw.Draw(img)
        return img, draw
    
    def add_frame(self, img: Image.Image, count: int = 1):
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        for _ in range(count):
            self.frames.append(frame)
            self.frame_idx += 1
    
    def draw_subtitle_bar(self, draw: ImageDraw.ImageDraw, text: str, progress: float = 0.0):
        """Beautiful subtitle bar at bottom"""
        if not text:
            return
        
        bar_height = 85
        bar_y = HEIGHT - bar_height - 25
        bar_margin = 80
        
        # Outer glow effect
        for i in range(3):
            alpha = 30 - i * 10
            draw.rounded_rectangle(
                [(bar_margin - i*2, bar_y - i*2), (WIDTH - bar_margin + i*2, bar_y + bar_height + i*2)],
                radius=15 + i,
                fill=(*COLORS['bg_tertiary'][:3],)
            )
        
        # Main background
        draw.rounded_rectangle(
            [(bar_margin, bar_y), (WIDTH - bar_margin, bar_y + bar_height)],
            radius=14,
            fill=(*COLORS['bg_secondary'][:3],)
        )
        
        # Border
        draw.rounded_rectangle(
            [(bar_margin, bar_y), (WIDTH - bar_margin, bar_y + bar_height)],
            radius=14,
            outline=COLORS['border_light'],
            width=1
        )
        
        # Progress indicator line at bottom
        if progress > 0:
            prog_w = int((WIDTH - 2 * bar_margin - 20) * progress)
            draw.rounded_rectangle(
                [(bar_margin + 10, bar_y + bar_height - 6), 
                 (bar_margin + 10 + prog_w, bar_y + bar_height - 3)],
                radius=2,
                fill=COLORS['accent_cyan']
            )
        
        # Centered text with shadow
        font = get_font(30)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (WIDTH - text_w) // 2
        
        # Text shadow
        draw.text((x + 2, bar_y + 27), text, font=font, fill=(0, 0, 0))
        # Main text
        draw.text((x, bar_y + 25), text, font=font, fill=COLORS['text_primary'])
    
    def draw_progress_bar(self, draw: ImageDraw.ImageDraw, progress: float, section: str):
        """Top progress bar"""
        bar_y = 18
        bar_h = 5
        
        # Background
        draw.rounded_rectangle([(50, bar_y), (WIDTH - 50, bar_y + bar_h)], 
                               radius=3, fill=COLORS['border'])
        
        # Progress
        prog_w = int((WIDTH - 100) * progress)
        if prog_w > 4:
            draw.rounded_rectangle([(50, bar_y), (50 + prog_w, bar_y + bar_h)],
                                   radius=3, fill=COLORS['accent_blue'])
        
        # Section label
        font = get_font(13)
        draw.text((50, bar_y + 12), section.upper(), font=font, fill=COLORS['text_muted'])
    
    def draw_node_box(self, draw: ImageDraw.ImageDraw, 
                      x: int, y: int, w: int, h: int,
                      title: str, icon: str, color: tuple, 
                      desc: str = "", active: bool = False, progress: float = 1.0):
        """Draw a beautiful node box for architecture diagram"""
        if progress <= 0:
            return
        
        scale = ease_out_cubic(min(1.0, progress))
        actual_w = int(w * scale)
        actual_h = int(h * scale)
        actual_x = x + (w - actual_w) // 2
        actual_y = y + (h - actual_h) // 2
        
        if actual_w < 20:
            return
        
        # Shadow
        if progress > 0.5:
            draw.rounded_rectangle(
                [actual_x + 4, actual_y + 4, actual_x + actual_w + 4, actual_y + actual_h + 4],
                radius=12, fill=(0, 0, 0)
            )
        
        # Main box
        draw.rounded_rectangle(
            [actual_x, actual_y, actual_x + actual_w, actual_y + actual_h],
            radius=12, fill=COLORS['bg_card']
        )
        
        # Active glow or border
        border_color = color if active else COLORS['border']
        border_width = 3 if active else 2
        draw.rounded_rectangle(
            [actual_x, actual_y, actual_x + actual_w, actual_y + actual_h],
            radius=12, outline=border_color, width=border_width
        )
        
        # Top accent bar
        draw.rounded_rectangle(
            [actual_x, actual_y, actual_x + actual_w, actual_y + 8],
            radius=12, fill=color
        )
        draw.rectangle(
            [actual_x, actual_y + 4, actual_x + actual_w, actual_y + 8],
            fill=color
        )
        
        if progress > 0.4:
            # Icon circle
            icon_size = 38
            icon_x = actual_x + 18
            icon_y = actual_y + 25
            draw.ellipse(
                [icon_x, icon_y, icon_x + icon_size, icon_y + icon_size],
                fill=color
            )
            font_icon = get_font(20, bold=True)
            draw.text((icon_x + 11, icon_y + 8), icon, font=font_icon, fill=COLORS['bg_primary'])
            
            # Title
            font_title = get_font(20, bold=True)
            draw.text((icon_x + icon_size + 12, icon_y + 8), title, 
                     font=font_title, fill=COLORS['text_primary'])
        
        if progress > 0.7 and desc:
            font_desc = get_font(15)
            draw.text((actual_x + 18, actual_y + 75), desc,
                     font=font_desc, fill=COLORS['text_secondary'])
    
    def draw_arrow(self, draw: ImageDraw.ImageDraw, 
                   x1: int, y1: int, x2: int, y2: int, 
                   color: tuple, animated: bool = False, frame: int = 0):
        """Draw animated arrow"""
        # Main line
        draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
        
        # Arrowhead
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 12
        arrow_angle = math.pi / 6
        
        ax1 = x2 - arrow_len * math.cos(angle - arrow_angle)
        ay1 = y2 - arrow_len * math.sin(angle - arrow_angle)
        ax2 = x2 - arrow_len * math.cos(angle + arrow_angle)
        ay2 = y2 - arrow_len * math.sin(angle + arrow_angle)
        
        draw.polygon([(x2, y2), (ax1, ay1), (ax2, ay2)], fill=color)
        
        # Animated dot
        if animated:
            t = (frame % 60) / 60
            dot_x = int(lerp(x1, x2, t))
            dot_y = int(lerp(y1, y2, t))
            draw.ellipse([dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5], fill=COLORS['accent_cyan'])
    
    def draw_terminal(self, draw: ImageDraw.ImageDraw,
                      x: int, y: int, w: int, h: int,
                      title: str, lines: List[Tuple[str, tuple]],
                      typing: str = "", cursor_visible: bool = True):
        """Professional terminal window"""
        # Shadow
        draw.rounded_rectangle([x+5, y+5, x+w+5, y+h+5], radius=14, fill=(0, 0, 0))
        
        # Main window
        draw.rounded_rectangle([x, y, x+w, y+h], radius=14, fill=COLORS['bg_secondary'])
        draw.rounded_rectangle([x, y, x+w, y+h], radius=14, outline=COLORS['border'], width=2)
        
        # Title bar
        title_h = 46
        draw.rounded_rectangle([x, y, x+w, y+title_h], radius=14, fill=COLORS['bg_tertiary'])
        draw.rectangle([x, y+title_h-14, x+w, y+title_h], fill=COLORS['bg_tertiary'])
        
        # Traffic lights
        btn_y = y + title_h // 2
        draw.ellipse([x+18, btn_y-7, x+32, btn_y+7], fill=COLORS['accent_red'])
        draw.ellipse([x+44, btn_y-7, x+58, btn_y+7], fill=COLORS['accent_yellow'])
        draw.ellipse([x+70, btn_y-7, x+84, btn_y+7], fill=COLORS['accent_green'])
        
        # Title
        font_title = get_font(15, bold=True)
        draw.text((x + 100, y + 14), title, font=font_title, fill=COLORS['text_secondary'])
        
        # Content
        font_mono = get_font(18, mono=True)
        content_y = y + title_h + 15
        line_h = 26
        max_lines = (h - title_h - 40) // line_h
        
        visible = lines[-max_lines:] if len(lines) > max_lines else lines
        
        for i, (text, color) in enumerate(visible):
            max_chars = (w - 50) // 11
            display = text[:max_chars] + "..." if len(text) > max_chars else text
            draw.text((x + 20, content_y + i * line_h), display, font=font_mono, fill=color)
        
        # Typing line with cursor
        if typing or cursor_visible:
            typing_y = content_y + len(visible) * line_h + 10
            cursor = "█" if cursor_visible and (self.frame_idx % 16 < 8) else " "
            draw.text((x + 20, typing_y), f"$ {typing}{cursor}", font=font_mono, fill=COLORS['text_primary'])

    # ============== SCENE GENERATORS ==============
    
    def generate_intro_scene(self, scene: SceneConfig):
        """Generate intro with perfect sync"""
        print(f"  Generating {scene.name} ({scene.total_frames} frames, {scene.total_duration:.1f}s)...")
        
        # Track which segment we're in
        segment_idx = 0
        frames_in_segment = 0
        segment_frames = int(scene.segments[0].actual_duration * FPS)
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            # Check if we need to move to next segment
            if frames_in_segment >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                frames_in_segment = 0
                segment_frames = int(scene.segments[segment_idx].actual_duration * FPS)
            
            current_subtitle = scene.segments[segment_idx].text
            segment_progress = frames_in_segment / max(1, segment_frames)
            frames_in_segment += 1
            
            total_progress = f / max(1, scene.total_frames - 1)
            
            # Background particles
            for i in range(20):
                px = int((i * 97 + f * 0.5) % WIDTH)
                py = int((i * 73 + f * 0.3) % HEIGHT)
                size = 2 + (i % 4)
                brightness = 20 + int(15 * math.sin(f * 0.04 + i * 0.5))
                color = (*COLORS['accent_blue'][:3],)
                draw.ellipse([px, py, px+size, py+size], fill=color)
            
            cx, cy = WIDTH // 2, HEIGHT // 2
            
            # Badge animation
            if f > 20:
                badge_prog = ease_out_cubic(min(1, (f - 20) / 30))
                badge_y = int(cy - 180 - 30 * (1 - badge_prog))
                
                badge_text = "KAGGLE CAPSTONE 2026"
                font_badge = get_font(22, bold=True)
                bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
                badge_w = bbox[2] - bbox[0] + 60
                
                # Badge background with glow
                for i in range(3):
                    draw.rounded_rectangle(
                        [cx - badge_w//2 - i*2, badge_y - i*2, cx + badge_w//2 + i*2, badge_y + 44 + i*2],
                        radius=22 + i, fill=COLORS['accent_blue'] if i == 0 else (*COLORS['accent_blue'][:3],)
                    )
                
                draw.text((cx - badge_w//2 + 30, badge_y + 10), badge_text,
                         font=font_badge, fill=COLORS['bg_primary'])
            
            # Main title with animation
            if f > 40:
                title_prog = ease_out_cubic(min(1, (f - 40) / 35))
                title_y = int(cy - 70 + 40 * (1 - title_prog))
                
                title1 = "Multi-Agent Customer Support"
                title2 = "Assistant for SMBs"
                font_title = get_font(62, bold=True)
                
                # Shadow
                bbox1 = draw.textbbox((0, 0), title1, font=font_title)
                draw.text((cx - (bbox1[2]-bbox1[0])//2 + 3, title_y + 3), title1,
                         font=font_title, fill=(0, 0, 0))
                draw.text((cx - (bbox1[2]-bbox1[0])//2, title_y), title1,
                         font=font_title, fill=COLORS['text_primary'])
                
                bbox2 = draw.textbbox((0, 0), title2, font=font_title)
                draw.text((cx - (bbox2[2]-bbox2[0])//2 + 3, title_y + 75 + 3), title2,
                         font=font_title, fill=(0, 0, 0))
                draw.text((cx - (bbox2[2]-bbox2[0])//2, title_y + 75), title2,
                         font=font_title, fill=COLORS['text_primary'])
            
            # Animated underline
            if f > 80:
                line_prog = ease_out_cubic(min(1, (f - 80) / 30))
                line_w = int(400 * line_prog)
                draw.rounded_rectangle(
                    [cx - line_w//2, cy + 90, cx + line_w//2, cy + 97],
                    radius=4, fill=COLORS['accent_cyan']
                )
            
            # Subtitle text
            if f > 100:
                track_text = "Track: Agents for Business"
                font_track = get_font(28)
                bbox = draw.textbbox((0, 0), track_text, font=font_track)
                draw.text((cx - (bbox[2]-bbox[0])//2, cy + 130), track_text,
                         font=font_track, fill=COLORS['text_secondary'])
            
            self.draw_progress_bar(draw, total_progress * 0.1, "Introduction")
            self.draw_subtitle_bar(draw, current_subtitle, segment_progress)
            self.add_frame(img)
    
    def generate_problem_scene(self, scene: SceneConfig):
        """Generate problem/solution with better diagrams"""
        print(f"  Generating {scene.name} ({scene.total_frames} frames, {scene.total_duration:.1f}s)...")
        
        segment_idx = 0
        frames_in_segment = 0
        segment_frames = int(scene.segments[0].actual_duration * FPS)
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            if frames_in_segment >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                frames_in_segment = 0
                segment_frames = int(scene.segments[segment_idx].actual_duration * FPS)
            
            current_subtitle = scene.segments[segment_idx].text
            segment_progress = frames_in_segment / max(1, segment_frames)
            frames_in_segment += 1
            total_progress = f / max(1, scene.total_frames - 1)
            
            # Header
            font_header = get_font(48, bold=True)
            draw.text((90, 85), "Problem & Solution", font=font_header, fill=COLORS['text_primary'])
            
            # Layout: Two cards side by side with proper gap
            panel_w = 780
            panel_h = 500
            panel_y = 170
            gap = 100
            left_x = (WIDTH - 2 * panel_w - gap) // 2
            right_x = left_x + panel_w + gap
            
            # Left panel - Problem (slides in from left)
            left_prog = ease_out_cubic(min(1, f / 50))
            actual_left_x = int(-panel_w + (panel_w + left_x) * left_prog)
            
            # Problem card shadow
            draw.rounded_rectangle(
                [actual_left_x + 5, panel_y + 5, actual_left_x + panel_w + 5, panel_y + panel_h + 5],
                radius=18, fill=(0, 0, 0)
            )
            # Problem card
            draw.rounded_rectangle(
                [actual_left_x, panel_y, actual_left_x + panel_w, panel_y + panel_h],
                radius=18, fill=COLORS['bg_card']
            )
            draw.rounded_rectangle(
                [actual_left_x, panel_y, actual_left_x + panel_w, panel_y + panel_h],
                radius=18, outline=COLORS['accent_red'], width=3
            )
            
            # Problem header bar
            draw.rounded_rectangle(
                [actual_left_x, panel_y, actual_left_x + panel_w, panel_y + 55],
                radius=18, fill=COLORS['accent_red']
            )
            draw.rectangle([actual_left_x, panel_y + 40, actual_left_x + panel_w, panel_y + 55], 
                          fill=COLORS['accent_red'])
            
            font_section = get_font(24, bold=True)
            draw.text((actual_left_x + 30, panel_y + 14), "THE PROBLEM",
                     font=font_section, fill=COLORS['bg_primary'])
            
            # Animated statistic
            if f > 35:
                stat_prog = ease_out_cubic(min(1, (f - 35) / 60))
                stat_val = int(80 * stat_prog)
                font_big = get_font(120, bold=True)
                draw.text((actual_left_x + 40, panel_y + 75), f"{stat_val}%",
                         font=font_big, fill=COLORS['accent_red'])
                
                font_label = get_font(26)
                draw.text((actual_left_x + 40, panel_y + 210), "of tickets are repetitive",
                         font=font_label, fill=COLORS['text_primary'])
            
            # Problem list with animated items
            problems = [
                ("📦", "Order tracking inquiries"),
                ("💰", "Refund and return requests"),
                ("🔑", "Password reset issues"),
                ("❓", "Common FAQ questions")
            ]
            font_item = get_font(22)
            for i, (icon, prob) in enumerate(problems):
                show_at = 60 + i * 18
                if f > show_at:
                    item_prog = ease_out_cubic(min(1, (f - show_at) / 20))
                    item_y = panel_y + 270 + i * 52
                    offset = int(30 * (1 - item_prog))
                    
                    draw.ellipse([actual_left_x + 40 + offset, item_y + 2, actual_left_x + 60 + offset, item_y + 22],
                               fill=COLORS['accent_red'])
                    draw.text((actual_left_x + 75 + offset, item_y), prob,
                             font=font_item, fill=COLORS['text_secondary'])
            
            # Right panel - Solution (slides in from right after delay)
            if f > 55:
                right_prog = ease_out_cubic(min(1, (f - 55) / 50))
                actual_right_x = int(WIDTH + (right_x - WIDTH) * right_prog)
                
                # Solution card shadow
                draw.rounded_rectangle(
                    [actual_right_x + 5, panel_y + 5, actual_right_x + panel_w + 5, panel_y + panel_h + 5],
                    radius=18, fill=(0, 0, 0)
                )
                # Solution card
                draw.rounded_rectangle(
                    [actual_right_x, panel_y, actual_right_x + panel_w, panel_y + panel_h],
                    radius=18, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [actual_right_x, panel_y, actual_right_x + panel_w, panel_y + panel_h],
                    radius=18, outline=COLORS['accent_green'], width=3
                )
                
                # Solution header bar
                draw.rounded_rectangle(
                    [actual_right_x, panel_y, actual_right_x + panel_w, panel_y + 55],
                    radius=18, fill=COLORS['accent_green']
                )
                draw.rectangle([actual_right_x, panel_y + 40, actual_right_x + panel_w, panel_y + 55],
                              fill=COLORS['accent_green'])
                
                draw.text((actual_right_x + 30, panel_y + 14), "OUR SOLUTION",
                         font=font_section, fill=COLORS['bg_primary'])
                
                # Solution metrics in 2x2 grid
                solutions = [
                    ("< 1 sec", "Response Time", COLORS['accent_cyan']),
                    ("24/7", "Availability", COLORS['accent_purple']),
                    ("100%", "PII Protection", COLORS['accent_green']),
                    ("10x", "Scalability", COLORS['accent_orange']),
                ]
                
                metric_w, metric_h = 340, 180
                for i, (val, label, color) in enumerate(solutions):
                    show_at = 90 + i * 20
                    if f > show_at:
                        row, col = i // 2, i % 2
                        mx = actual_right_x + 35 + col * (metric_w + 30)
                        my = panel_y + 75 + row * (metric_h + 20)
                        
                        # Metric box
                        draw.rounded_rectangle(
                            [mx, my, mx + metric_w, my + metric_h],
                            radius=12, fill=COLORS['bg_tertiary']
                        )
                        draw.rounded_rectangle(
                            [mx, my, mx + metric_w, my + 6],
                            radius=12, fill=color
                        )
                        draw.rectangle([mx, my + 3, mx + metric_w, my + 6], fill=color)
                        
                        font_val = get_font(48, bold=True)
                        font_lbl = get_font(20)
                        draw.text((mx + 25, my + 40), val, font=font_val, fill=color)
                        draw.text((mx + 25, my + 110), label, font=font_lbl, fill=COLORS['text_secondary'])
            
            self.draw_progress_bar(draw, 0.1 + total_progress * 0.12, "Problem & Solution")
            self.draw_subtitle_bar(draw, current_subtitle, segment_progress)
            self.add_frame(img)
    
    def generate_architecture_scene(self, scene: SceneConfig):
        """Generate architecture diagram with beautiful flow"""
        print(f"  Generating {scene.name} ({scene.total_frames} frames, {scene.total_duration:.1f}s)...")
        
        segment_idx = 0
        frames_in_segment = 0
        segment_frames = int(scene.segments[0].actual_duration * FPS)
        
        agents = [
            ("1", "Intent Classifier", "Understands needs", COLORS['accent_blue']),
            ("2", "Data Retrieval", "Fetches via MCP", COLORS['accent_cyan']),
            ("3", "Response Generator", "Creates replies", COLORS['accent_green']),
            ("4", "Quality Agent", "Safety & PII", COLORS['accent_purple']),
        ]
        
        tools = [
            "get_order_details",
            "get_refund_policy", 
            "get_customer_profile",
            "create_support_ticket",
            "mask_sensitive_data",
            "audit_log_event"
        ]
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            if frames_in_segment >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                frames_in_segment = 0
                segment_frames = int(scene.segments[segment_idx].actual_duration * FPS)
            
            current_subtitle = scene.segments[segment_idx].text
            segment_progress = frames_in_segment / max(1, segment_frames)
            frames_in_segment += 1
            total_progress = f / max(1, scene.total_frames - 1)
            
            # Header
            font_header = get_font(46, bold=True)
            draw.text((90, 70), "Multi-Agent Architecture", font=font_header, fill=COLORS['text_primary'])
            
            font_sub = get_font(22)
            draw.text((90, 130), "Four specialized agents working in orchestrated sequence",
                     font=font_sub, fill=COLORS['text_secondary'])
            
            # Agent flow diagram - horizontal layout
            box_w, box_h = 380, 105
            start_x = 90
            start_y = 195
            gap_y = 125
            
            for i, (num, title, desc, color) in enumerate(agents):
                show_at = 30 + i * 40
                if f > show_at:
                    prog = min(1, (f - show_at) / 35)
                    is_active = segment_idx >= 2 + i and segment_idx <= 2 + i + 1
                    
                    y = start_y + i * gap_y
                    self.draw_node_box(draw, start_x, y, box_w, box_h, title, num, color, desc, is_active, prog)
            
            # Connection arrows between agents (vertical)
            if f > 110:
                for i in range(3):
                    arrow_y1 = start_y + box_h + i * gap_y + 5
                    arrow_y2 = start_y + (i + 1) * gap_y - 5
                    arrow_x = start_x + box_w // 2
                    
                    if f > 110 + i * 30:
                        self.draw_arrow(draw, arrow_x, arrow_y1, arrow_x, arrow_y2, 
                                       COLORS['accent_cyan'], animated=True, frame=f)
            
            # MCP Tools section - right side
            if f > 180:
                tools_prog = ease_out_cubic(min(1, (f - 180) / 45))
                tools_x = 550
                tools_y = 195
                tools_w = 520
                tools_h = 480
                
                actual_x = int(WIDTH + (tools_x - WIDTH) * tools_prog)
                
                # Shadow
                draw.rounded_rectangle(
                    [actual_x + 5, tools_y + 5, actual_x + tools_w + 5, tools_y + tools_h + 5],
                    radius=16, fill=(0, 0, 0)
                )
                # Main card
                draw.rounded_rectangle(
                    [actual_x, tools_y, actual_x + tools_w, tools_y + tools_h],
                    radius=16, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [actual_x, tools_y, actual_x + tools_w, tools_y + tools_h],
                    radius=16, outline=COLORS['accent_orange'], width=3
                )
                
                # Header bar
                draw.rounded_rectangle(
                    [actual_x, tools_y, actual_x + tools_w, tools_y + 55],
                    radius=16, fill=COLORS['accent_orange']
                )
                draw.rectangle([actual_x, tools_y + 40, actual_x + tools_w, tools_y + 55],
                              fill=COLORS['accent_orange'])
                
                font_section = get_font(22, bold=True)
                draw.text((actual_x + 25, tools_y + 15), "MCP Tool Server (6 Tools)",
                         font=font_section, fill=COLORS['bg_primary'])
                
                # Tool items
                font_tool = get_font(18, mono=True)
                for i, tool in enumerate(tools):
                    show_at = 200 + i * 12
                    if f > show_at:
                        ty = tools_y + 75 + i * 65
                        
                        draw.rounded_rectangle(
                            [actual_x + 20, ty, actual_x + tools_w - 20, ty + 50],
                            radius=8, fill=COLORS['bg_tertiary']
                        )
                        draw.rounded_rectangle(
                            [actual_x + 20, ty, actual_x + 26, ty + 50],
                            radius=8, fill=COLORS['accent_cyan']
                        )
                        draw.rectangle([actual_x + 23, ty, actual_x + 26, ty + 50], fill=COLORS['accent_cyan'])
                        
                        draw.text((actual_x + 45, ty + 14), tool,
                                 font=font_tool, fill=COLORS['accent_cyan'])
            
            # Data flow visualization on far right
            if f > 280:
                flow_x = 1130
                flow_y = 195
                flow_w = 310
                flow_h = 480
                
                flow_prog = ease_out_cubic(min(1, (f - 280) / 40))
                
                draw.rounded_rectangle(
                    [flow_x, flow_y, flow_x + flow_w, flow_y + int(flow_h * flow_prog)],
                    radius=14, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [flow_x, flow_y, flow_x + flow_w, flow_y + int(flow_h * flow_prog)],
                    radius=14, outline=COLORS['accent_purple'], width=2
                )
                
                if flow_prog > 0.4:
                    font_flow = get_font(18, bold=True)
                    draw.text((flow_x + 20, flow_y + 18), "Data Flow",
                             font=font_flow, fill=COLORS['accent_purple'])
                    
                    # Flow steps
                    steps = ["Customer Query", "Intent Analysis", "Data Fetch", "Response Gen", "Quality Check", "Final Reply"]
                    font_step = get_font(15)
                    
                    for i, step in enumerate(steps):
                        step_y = flow_y + 60 + i * 68
                        
                        if step_y < flow_y + flow_h * flow_prog - 40:
                            # Step circle
                            draw.ellipse([flow_x + 25, step_y, flow_x + 45, step_y + 20],
                                       fill=COLORS['accent_purple'])
                            draw.text((flow_x + 31, step_y + 2), str(i+1), 
                                     font=get_font(12, bold=True), fill=COLORS['bg_primary'])
                            
                            draw.text((flow_x + 60, step_y), step,
                                     font=font_step, fill=COLORS['text_secondary'])
                            
                            # Connecting line
                            if i < 5 and step_y + 50 < flow_y + flow_h * flow_prog - 20:
                                draw.line([(flow_x + 35, step_y + 22), (flow_x + 35, step_y + 60)],
                                         fill=COLORS['border_light'], width=2)
            
            self.draw_progress_bar(draw, 0.22 + total_progress * 0.18, "Architecture")
            self.draw_subtitle_bar(draw, current_subtitle, segment_progress)
            self.add_frame(img)
    
    def generate_demo_scene(self, scene: SceneConfig):
        """Generate CLI demo with perfect timing"""
        print(f"  Generating {scene.name} ({scene.total_frames} frames, {scene.total_duration:.1f}s)...")
        
        segment_idx = 0
        frames_in_segment = 0
        segment_frames = int(scene.segments[0].actual_duration * FPS)
        
        # Calculate frame ranges for each demo step based on segment timing
        cumulative_frames = []
        total = 0
        for seg in scene.segments:
            cumulative_frames.append(total)
            total += int(seg.actual_duration * FPS)
        
        # Demo events tied to segments
        demo_commands = [
            None,  # 0: "Let me demonstrate..."
            ("/email alice.johnson@email.com", [  # 1: "First, we set the customer email..."
                ("[SESSION] Customer email set: alice.johnson@email.com", COLORS['accent_green']),
            ]),
            ("Where is my order ORD-2024-002?", [  # 2: "Now asking: Where is my order?"
                ("[INTENT] ORDER_STATUS (confidence: 0.94)", COLORS['accent_purple']),
            ]),
            None,  # 3: "Intent classified..."
            (None, [  # 4: "Access validated..."
                ("[AUTH] Access: OWNER VERIFIED", COLORS['accent_green']),
                ("[MCP] get_order_details('ORD-2024-002')", COLORS['accent_cyan']),
                ("", COLORS['text_primary']),
                ("Your order ORD-2024-002 is currently SHIPPED.", COLORS['text_primary']),
                ("Expected delivery: Tomorrow by 5 PM", COLORS['text_primary']),
            ]),
            None,  # 5: "Now testing session memory..."
            ("Can I get a refund for it?", [  # 6: "Asking: Can I refund it?"
                ("[INTENT] REFUND_REQUEST (confidence: 0.91)", COLORS['accent_purple']),
            ]),
            (None, [  # 7: "The system remembers..."
                ("[MEMORY] Resolving 'it' -> ORD-2024-002", COLORS['accent_yellow']),
            ]),
            (None, [  # 8: "Context resolution..."
                ("[MCP] get_refund_policy()", COLORS['accent_cyan']),
                ("", COLORS['text_primary']),
                ("Yes! This order is eligible for a full refund.", COLORS['text_primary']),
                ("Still within 30-day return window.", COLORS['text_primary']),
            ]),
            None,  # 9: "Now testing security..."
            ("Show me order ORD-2024-001", [  # 10: "Trying to access another..."
                ("[INTENT] ORDER_STATUS (confidence: 0.92)", COLORS['accent_purple']),
            ]),
            (None, [  # 11: "Access denied..."
                ("[AUTH] Access: DENIED - Owner mismatch", COLORS['accent_red']),
                ("[SECURITY] Violation logged: Attempt #1/3", COLORS['accent_red']),
                ("", COLORS['text_primary']),
                ("I cannot access order ORD-2024-001.", COLORS['accent_red']),
                ("This order belongs to a different customer.", COLORS['accent_red']),
            ]),
        ]
        
        terminal_lines = [
            ("$ python -m src.cli chat", COLORS['text_primary']),
            ("Starting Multi-Agent Support CLI v2.0...", COLORS['accent_cyan']),
            ("[OK] Session store initialized", COLORS['accent_green']),
            ("[OK] MCP server ready (6 tools loaded)", COLORS['accent_green']),
            ("", COLORS['text_primary']),
        ]
        current_cmd = ""
        typing_idx = 0
        output_idx = 0
        state = "idle"  # idle, typing, output
        last_segment_idx = -1
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            if frames_in_segment >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                frames_in_segment = 0
                segment_frames = int(scene.segments[segment_idx].actual_duration * FPS)
            
            current_subtitle = scene.segments[segment_idx].text
            segment_progress = frames_in_segment / max(1, segment_frames)
            frames_in_segment += 1
            total_progress = f / max(1, scene.total_frames - 1)
            
            # Trigger demo events on segment change
            if segment_idx != last_segment_idx:
                last_segment_idx = segment_idx
                
                if segment_idx < len(demo_commands) and demo_commands[segment_idx] is not None:
                    cmd_data = demo_commands[segment_idx]
                    if cmd_data[0] is not None:  # Has command to type
                        current_cmd = cmd_data[0]
                        typing_idx = 0
                        state = "typing"
                    else:  # Just outputs
                        state = "output"
                        output_idx = 0
            
            # Process state machine
            if state == "typing":
                if typing_idx < len(current_cmd):
                    typing_idx += 2  # Type 2 chars per frame
                else:
                    # Command done typing, add to terminal and show outputs
                    prefix = "$ " if not current_cmd.startswith("/") else ""
                    terminal_lines.append((f"{prefix}{current_cmd}", COLORS['text_primary']))
                    current_cmd = ""
                    typing_idx = 0
                    
                    # Start showing outputs
                    cmd_data = demo_commands[segment_idx]
                    if cmd_data and len(cmd_data) > 1 and cmd_data[1]:
                        state = "output"
                        output_idx = 0
                    else:
                        state = "idle"
            
            elif state == "output":
                cmd_data = demo_commands[segment_idx]
                if cmd_data and len(cmd_data) > 1:
                    outputs = cmd_data[1]
                    if output_idx < len(outputs):
                        if frames_in_segment % 8 == 0:  # Show output every 8 frames
                            terminal_lines.append(outputs[output_idx])
                            output_idx += 1
                    else:
                        state = "idle"
            
            # Header
            font_header = get_font(40, bold=True)
            draw.text((100, 60), "Live System Demonstration", font=font_header, fill=COLORS['text_primary'])
            
            # Terminal
            typing_text = current_cmd[:typing_idx] if state == "typing" else ""
            self.draw_terminal(
                draw, 100, 130, WIDTH - 200, HEIGHT - 270,
                "Terminal — Multi-Agent Support CLI",
                terminal_lines, typing_text, cursor_visible=(state in ["typing", "idle"])
            )
            
            self.draw_progress_bar(draw, 0.4 + total_progress * 0.3, "Live Demo")
            self.draw_subtitle_bar(draw, current_subtitle, segment_progress)
            self.add_frame(img)
    
    def generate_security_scene(self, scene: SceneConfig):
        """Generate security scene with better visuals"""
        print(f"  Generating {scene.name} ({scene.total_frames} frames, {scene.total_duration:.1f}s)...")
        
        segment_idx = 0
        frames_in_segment = 0
        segment_frames = int(scene.segments[0].actual_duration * FPS)
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            if frames_in_segment >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                frames_in_segment = 0
                segment_frames = int(scene.segments[segment_idx].actual_duration * FPS)
            
            current_subtitle = scene.segments[segment_idx].text
            segment_progress = frames_in_segment / max(1, segment_frames)
            frames_in_segment += 1
            total_progress = f / max(1, scene.total_frames - 1)
            
            # Header
            font_header = get_font(46, bold=True)
            draw.text((90, 70), "Security & Evaluation", font=font_header, fill=COLORS['text_primary'])
            
            # Two-column layout with proper gap
            col_w = 600
            col_h = 530
            col_y = 155
            gap = 80
            left_x = (WIDTH - 2 * col_w - gap) // 2
            right_x = left_x + col_w + gap
            
            # Left column - Security features
            sec_prog = ease_out_cubic(min(1, f / 45))
            
            # Shadow
            draw.rounded_rectangle(
                [left_x + 5, col_y + 5, left_x + col_w + 5, col_y + int(col_h * sec_prog) + 5],
                radius=16, fill=(0, 0, 0)
            )
            draw.rounded_rectangle(
                [left_x, col_y, left_x + col_w, col_y + int(col_h * sec_prog)],
                radius=16, fill=COLORS['bg_card']
            )
            draw.rounded_rectangle(
                [left_x, col_y, left_x + col_w, col_y + int(col_h * sec_prog)],
                radius=16, outline=COLORS['accent_red'], width=3
            )
            
            if sec_prog > 0.3:
                # Header
                draw.rounded_rectangle(
                    [left_x, col_y, left_x + col_w, col_y + 55],
                    radius=16, fill=COLORS['accent_red']
                )
                draw.rectangle([left_x, col_y + 40, left_x + col_w, col_y + 55], fill=COLORS['accent_red'])
                
                font_section = get_font(22, bold=True)
                draw.text((left_x + 25, col_y + 15), "Security Features",
                         font=font_section, fill=COLORS['bg_primary'])
                
                features = [
                    ("🔒", "PII Masking", "Automatic data protection"),
                    ("🛡️", "Access Control", "Owner verification required"),
                    ("⚠️", "Session Lockout", "3 failed attempts = locked"),
                    ("📋", "Audit Logging", "All operations tracked"),
                ]
                
                font_title = get_font(22, bold=True)
                font_desc = get_font(17)
                
                for i, (icon, title, desc) in enumerate(features):
                    show_at = 50 + i * 30
                    if f > show_at:
                        fy = col_y + 80 + i * 110
                        
                        # Feature row with background
                        draw.rounded_rectangle(
                            [left_x + 20, fy, left_x + col_w - 20, fy + 90],
                            radius=10, fill=COLORS['bg_tertiary']
                        )
                        
                        # Checkmark circle
                        draw.ellipse([left_x + 35, fy + 15, left_x + 65, fy + 45],
                                   fill=COLORS['accent_green'])
                        font_check = get_font(18, bold=True)
                        draw.text((left_x + 43, fy + 18), "✓", font=font_check, fill=COLORS['bg_primary'])
                        
                        draw.text((left_x + 80, fy + 18), title, font=font_title, fill=COLORS['text_primary'])
                        draw.text((left_x + 80, fy + 52), desc, font=font_desc, fill=COLORS['text_secondary'])
            
            # Right column - Test results
            if f > 80:
                test_prog = ease_out_cubic(min(1, (f - 80) / 45))
                
                draw.rounded_rectangle(
                    [right_x + 5, col_y + 5, right_x + col_w + 5, col_y + int(col_h * test_prog) + 5],
                    radius=16, fill=(0, 0, 0)
                )
                draw.rounded_rectangle(
                    [right_x, col_y, right_x + col_w, col_y + int(col_h * test_prog)],
                    radius=16, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [right_x, col_y, right_x + col_w, col_y + int(col_h * test_prog)],
                    radius=16, outline=COLORS['accent_green'], width=3
                )
                
                if test_prog > 0.3:
                    # Header
                    draw.rounded_rectangle(
                        [right_x, col_y, right_x + col_w, col_y + 55],
                        radius=16, fill=COLORS['accent_green']
                    )
                    draw.rectangle([right_x, col_y + 40, right_x + col_w, col_y + 55], fill=COLORS['accent_green'])
                    
                    draw.text((right_x + 25, col_y + 15), "Test Coverage",
                             font=font_section, fill=COLORS['bg_primary'])
                    
                    # Animated counter
                    count_prog = min(1, (f - 100) / 90) if f > 100 else 0
                    test_count = int(66 * count_prog)
                    
                    font_big = get_font(90, bold=True)
                    draw.text((right_x + 40, col_y + 70), f"{test_count}/66",
                             font=font_big, fill=COLORS['accent_green'])
                    
                    font_label = get_font(26)
                    draw.text((right_x + 40, col_y + 175), "tests passing",
                             font=font_label, fill=COLORS['text_primary'])
                    
                    # Progress bar
                    bar_y = col_y + 220
                    draw.rounded_rectangle(
                        [right_x + 40, bar_y, right_x + col_w - 40, bar_y + 16],
                        radius=8, fill=COLORS['border']
                    )
                    bar_w = int((col_w - 80) * count_prog)
                    if bar_w > 4:
                        draw.rounded_rectangle(
                            [right_x + 40, bar_y, right_x + 40 + bar_w, bar_y + 16],
                            radius=8, fill=COLORS['accent_green']
                        )
                    
                    # Categories
                    if f > 160:
                        categories = [
                            ("Intent Classification", 9, COLORS['accent_blue']),
                            ("Security & PII", 13, COLORS['accent_red']),
                            ("Orchestrator", 13, COLORS['accent_purple']),
                            ("Session/Memory", 16, COLORS['accent_yellow']),
                            ("Tools/MCP", 15, COLORS['accent_cyan']),
                        ]
                        
                        font_cat = get_font(18)
                        for i, (cat, count, color) in enumerate(categories):
                            show_cat = f > 160 + i * 15
                            if show_cat:
                                cy = col_y + 265 + i * 48
                                
                                draw.ellipse([right_x + 45, cy + 4, right_x + 59, cy + 18], fill=color)
                                draw.text((right_x + 70, cy), cat, font=font_cat, fill=COLORS['text_secondary'])
                                draw.text((right_x + 360, cy), f"{count} tests", font=font_cat, fill=color)
            
            self.draw_progress_bar(draw, 0.7 + total_progress * 0.15, "Security & Evaluation")
            self.draw_subtitle_bar(draw, current_subtitle, segment_progress)
            self.add_frame(img)
    
    def generate_conclusion_scene(self, scene: SceneConfig):
        """Generate conclusion scene"""
        print(f"  Generating {scene.name} ({scene.total_frames} frames, {scene.total_duration:.1f}s)...")
        
        segment_idx = 0
        frames_in_segment = 0
        segment_frames = int(scene.segments[0].actual_duration * FPS)
        
        concepts = [
            ("✓", "Multi-Agent Architecture", COLORS['accent_blue']),
            ("✓", "MCP Tool Server", COLORS['accent_cyan']),
            ("✓", "Session & Memory", COLORS['accent_yellow']),
            ("✓", "Security Guardrails", COLORS['accent_red']),
            ("✓", "PII Masking", COLORS['accent_purple']),
            ("✓", "66 Automated Tests", COLORS['accent_green']),
            ("✓", "CLI & REST API", COLORS['accent_orange']),
        ]
        
        for f in range(scene.total_frames):
            img, draw = self.create_frame()
            
            if frames_in_segment >= segment_frames and segment_idx < len(scene.segments) - 1:
                segment_idx += 1
                frames_in_segment = 0
                segment_frames = int(scene.segments[segment_idx].actual_duration * FPS)
            
            current_subtitle = scene.segments[segment_idx].text
            segment_progress = frames_in_segment / max(1, segment_frames)
            frames_in_segment += 1
            total_progress = f / max(1, scene.total_frames - 1)
            
            cx = WIDTH // 2
            
            # Header
            font_header = get_font(52, bold=True)
            title = "Implementation Complete"
            bbox = draw.textbbox((0, 0), title, font=font_header)
            
            # Shadow
            draw.text((cx - (bbox[2]-bbox[0])//2 + 3, 83), title, font=font_header, fill=(0, 0, 0))
            draw.text((cx - (bbox[2]-bbox[0])//2, 80), title, font=font_header, fill=COLORS['text_primary'])
            
            # Checklist with animations
            list_y = 175
            font_item = get_font(30)
            
            for i, (check, concept, color) in enumerate(concepts):
                show_at = 25 + i * 15
                if f > show_at:
                    prog = ease_out_cubic(min(1, (f - show_at) / 20))
                    offset = int(50 * (1 - prog))
                    
                    y = list_y + i * 58
                    
                    # Checkmark circle
                    draw.ellipse([cx - 300 + offset, y + 4, cx - 270 + offset, y + 34],
                               fill=color)
                    font_check = get_font(18, bold=True)
                    draw.text((cx - 292 + offset, y + 8), check, font=font_check, fill=COLORS['bg_primary'])
                    
                    draw.text((cx - 250 + offset, y + 2), concept,
                             font=font_item, fill=COLORS['text_primary'])
            
            # GitHub link box
            if f > 160:
                link_prog = ease_out_cubic(min(1, (f - 160) / 30))
                link_y = HEIGHT - 200
                link_w = 700
                link_h = 60
                
                # Shadow
                draw.rounded_rectangle(
                    [cx - link_w//2 + 4, link_y + 4, cx + link_w//2 + 4, link_y + link_h + 4],
                    radius=30, fill=(0, 0, 0)
                )
                draw.rounded_rectangle(
                    [cx - link_w//2, link_y, cx + link_w//2, link_y + link_h],
                    radius=30, fill=COLORS['bg_card']
                )
                draw.rounded_rectangle(
                    [cx - link_w//2, link_y, cx + link_w//2, link_y + link_h],
                    radius=30, outline=COLORS['accent_blue'], width=2
                )
                
                font_link = get_font(24)
                link_text = "github.com/Trungnef/ai-agents-business-support"
                bbox = draw.textbbox((0, 0), link_text, font=font_link)
                draw.text((cx - (bbox[2]-bbox[0])//2, link_y + 17), link_text,
                         font=font_link, fill=COLORS['accent_blue'])
            
            # Thank you message
            if f > 200:
                thanks_prog = ease_out_cubic(min(1, (f - 200) / 30))
                font_thanks = get_font(42, bold=True)
                thanks = "Thank You for Watching!"
                bbox = draw.textbbox((0, 0), thanks, font=font_thanks)
                
                thanks_y = HEIGHT - 110 + int(30 * (1 - thanks_prog))
                draw.text((cx - (bbox[2]-bbox[0])//2 + 2, thanks_y + 2), thanks,
                         font=font_thanks, fill=(0, 0, 0))
                draw.text((cx - (bbox[2]-bbox[0])//2, thanks_y), thanks,
                         font=font_thanks, fill=COLORS['accent_green'])
            
            self.draw_progress_bar(draw, 0.85 + total_progress * 0.15, "Conclusion")
            self.draw_subtitle_bar(draw, current_subtitle, segment_progress)
            self.add_frame(img)
    
    def generate_video(self):
        """Generate all scenes"""
        print("\n" + "=" * 60)
        print("GENERATING VIDEO FRAMES")
        print("=" * 60)
        
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
            
            print(f"    Total frames so far: {len(self.frames)}")
        
        return self.frames


def write_video(frames: List[np.ndarray]) -> Path:
    """Write frames to video file"""
    video_path = OUTPUT_DIR / "temp_video_v4.mp4"
    
    print(f"\nWriting {len(frames)} frames to video...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, FPS, (WIDTH, HEIGHT))
    
    for i, frame in enumerate(frames):
        out.write(frame)
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(frames)} frames written")
    
    out.release()
    print(f"Temp video saved: {video_path}")
    return video_path


def combine_av(video_path: Path, audio_path: Path) -> Path:
    """Combine video and audio with ffmpeg"""
    final_path = OUTPUT_DIR / "multi_agent_support_demo.mp4"
    
    print("\nCombining video and audio...")
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except:
        print("ffmpeg not found, saving video without audio")
        video_path.rename(final_path)
        return final_path
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",  # Higher quality
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",  # Match shortest stream
        "-movflags", "+faststart",
        str(final_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        video_path.unlink(missing_ok=True)
        print(f"Final video: {final_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        print(f"stderr: {e.stderr.decode()}")
        video_path.rename(final_path)
    
    return final_path


def cleanup_temp_files():
    """Clean up temporary audio files"""
    print("\nCleaning up temporary files...")
    for f in AUDIO_DIR.glob("segment_*.mp3"):
        f.unlink(missing_ok=True)
    
    combined = OUTPUT_DIR / "combined_narration_v4.mp3"
    if combined.exists():
        combined.unlink()


def verify(path: Path):
    """Verify output video"""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    if not path.exists():
        print("ERROR: Video file not found!")
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
    
    # Calculate expected vs actual
    total_expected = sum(scene.total_duration for scene in SCENES)
    print(f"\nExpected duration: {total_expected:.1f}s")
    print(f"Actual duration: {duration:.1f}s")
    print(f"Difference: {abs(duration - total_expected):.1f}s")
    
    print("\n✓ VERIFICATION COMPLETE")
    return True


async def main():
    print("\n" + "=" * 60)
    print("VIDEO GENERATOR v4 - Perfect Voice-Subtitle Sync")
    print("=" * 60)
    
    # Step 1: Generate audio for each segment
    await generate_all_audio()
    
    # Step 2: Combine audio segments
    audio_path = combine_audio_segments()
    
    # Step 3: Generate video frames (using actual audio durations)
    gen = VideoGenerator()
    frames = gen.generate_video()
    
    # Step 4: Write video
    video_path = write_video(frames)
    
    # Step 5: Combine video and audio
    final_path = combine_av(video_path, audio_path)
    
    # Step 6: Verify
    verify(final_path)
    
    # Step 7: Cleanup
    cleanup_temp_files()
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print(f"Output: {final_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
