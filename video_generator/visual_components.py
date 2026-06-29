"""
Visual Components Generator
Creates professional slides, animations, and visual elements for video
"""
import numpy as np
from pathlib import Path
from typing import Optional

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

from .config import VideoConfig


class SlideGenerator:
    """Generates professional slide images and video clips"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self.width = config.width
        self.height = config.height
    
    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _draw_gradient(self, draw, width, height, colors=None):
        """Draw vertical gradient on image"""
        if colors is None:
            colors = [self.config.background_color, "#1a1a2e"]
        c1 = self._hex_to_rgb(colors[0])
        c2 = self._hex_to_rgb(colors[1])
        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    def _get_font(self, font_path: str, size: int):
        """Load font with fallback"""
        try:
            return ImageFont.truetype(font_path, size)
        except:
            return ImageFont.load_default()
    
    def create_title_slide(self, title: str, subtitle: str = "", 
                           duration: float = 5.0) -> ImageClip:
        """Create a title slide"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        self._draw_gradient(draw, self.width, self.height)
        
        title_font = self._get_font(self.config.title_font, self.config.title_font_size)
        
        # Draw title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((title_x, self.height // 3), title, 
                  fill=self._hex_to_rgb(self.config.text_color), font=title_font)
        
        # Accent line
        accent_color = self._hex_to_rgb(self.config.primary_color)
        line_y = self.height // 3 + 90
        line_width = 200
        line_x = (self.width - line_width) // 2
        draw.rectangle([(line_x, line_y), (line_x + line_width, line_y + 4)], fill=accent_color)
        
        # Subtitle
        if subtitle:
            sub_font = self._get_font(self.config.body_font, self.config.heading_font_size)
            bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
            sub_x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((sub_x, self.height // 2 + 30), subtitle,
                      fill=self._hex_to_rgb(self.config.text_secondary), font=sub_font)
        
        return ImageClip(np.array(img)).with_duration(duration)
    
    def create_stat_slide(self, stat: str, description: str,
                          duration: float = 5.0) -> ImageClip:
        """Create a slide highlighting a key statistic"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        self._draw_gradient(draw, self.width, self.height)
        
        stat_font = self._get_font(self.config.title_font, 140)
        desc_font = self._get_font(self.config.body_font, self.config.body_font_size)
        
        # Big stat
        bbox = draw.textbbox((0, 0), stat, font=stat_font)
        stat_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((stat_x, self.height // 3), stat,
                  fill=self._hex_to_rgb(self.config.primary_color), font=stat_font)
        
        # Description
        bbox = draw.textbbox((0, 0), description, font=desc_font)
        desc_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((desc_x, self.height // 2 + 80), description,
                  fill=self._hex_to_rgb(self.config.text_color), font=desc_font)
        
        return ImageClip(np.array(img)).with_duration(duration)
    
    def create_bullet_slide(self, title: str, bullets: list[str],
                            duration: float = 10.0) -> ImageClip:
        """Create a slide with bullet points"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        self._draw_gradient(draw, self.width, self.height)
        
        title_font = self._get_font(self.config.title_font, self.config.heading_font_size)
        bullet_font = self._get_font(self.config.body_font, self.config.body_font_size - 4)
        
        # Title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((title_x, 80), title,
                  fill=self._hex_to_rgb(self.config.primary_color), font=title_font)
        
        # Bullets
        y_pos = 200
        for bullet in bullets:
            text = f"•  {bullet}"
            draw.text((120, y_pos), text,
                      fill=self._hex_to_rgb(self.config.text_color), font=bullet_font)
            y_pos += 70
        
        return ImageClip(np.array(img)).with_duration(duration)
    
    def create_architecture_slide(self, mermaid_svg_path: Optional[Path] = None,
                                   duration: float = 10.0) -> ImageClip:
        """Create architecture diagram slide"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        self._draw_gradient(draw, self.width, self.height)
        
        title_font = self._get_font(self.config.title_font, self.config.heading_font_size)
        code_font = self._get_font(self.config.code_font, 22)
        small_font = self._get_font(self.config.body_font, 20)
        
        # Title
        title = "System Architecture"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((title_x, 40), title, fill=self._hex_to_rgb(self.config.primary_color), font=title_font)
        
        # Colors
        box_color = self._hex_to_rgb("#2d2d4d")
        border_color = self._hex_to_rgb(self.config.primary_color)
        text_color = self._hex_to_rgb(self.config.text_color)
        
        # Customer Message box
        self._draw_box(draw, 710, 130, 500, 50, "Customer Message", box_color, border_color, text_color, code_font)
        
        # Arrow
        draw.polygon([(960, 185), (950, 200), (970, 200)], fill=border_color)
        
        # Orchestrator box
        draw.rectangle([(460, 220), (1460, 420)], outline=border_color, width=2, fill=box_color)
        draw.text((480, 230), "Support Orchestrator", fill=border_color, font=code_font)
        
        # Agents
        agents = ["Intent\nClassifier", "Data\nRetrieval", "Response\nGenerator", "Quality\nSafety"]
        agent_x = 500
        for agent in agents:
            draw.rectangle([(agent_x, 280), (agent_x + 200, 390)], 
                          outline=self._hex_to_rgb("#4a4a6a"), width=1, 
                          fill=self._hex_to_rgb("#1a1a3e"))
            lines = agent.split('\n')
            for j, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=small_font)
                text_x = agent_x + (200 - (bbox[2] - bbox[0])) // 2
                draw.text((text_x, 310 + j * 30), line, fill=text_color, font=small_font)
            if agent != agents[-1]:
                draw.text((agent_x + 210, 330), "→", fill=border_color, font=code_font)
            agent_x += 240
        
        # Arrow
        draw.polygon([(960, 425), (950, 440), (970, 440)], fill=border_color)
        
        # MCP box
        draw.rectangle([(460, 460), (1460, 580)], outline=border_color, width=2, fill=box_color)
        draw.text((480, 470), "MCP Tool Server", fill=border_color, font=code_font)
        
        # Tools
        tools = ["get_order", "get_policy", "get_customer", "create_ticket", "mask_pii", "audit"]
        tool_x = 490
        for tool in tools:
            draw.rectangle([(tool_x, 510), (tool_x + 145, 560)],
                          outline=self._hex_to_rgb("#4a4a6a"), width=1,
                          fill=self._hex_to_rgb("#1a1a3e"))
            bbox = draw.textbbox((0, 0), tool, font=small_font)
            text_x = tool_x + (145 - (bbox[2] - bbox[0])) // 2
            draw.text((text_x, 525), tool, fill=text_color, font=small_font)
            tool_x += 160
        
        return ImageClip(np.array(img)).with_duration(duration)
    
    def _draw_box(self, draw, x, y, w, h, text, fill, outline, text_color, font):
        """Draw a box with centered text"""
        draw.rectangle([(x, y), (x + w, y + h)], outline=outline, width=2, fill=fill)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_x = x + (w - (bbox[2] - bbox[0])) // 2
        text_y = y + (h - (bbox[3] - bbox[1])) // 2
        draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    def create_terminal_slide(self, commands_and_outputs: list[tuple[str, str]],
                               duration: float = 10.0) -> ImageClip:
        """Create a terminal simulation slide"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Terminal background
        draw.rectangle([(0, 0), (self.width, self.height)], fill=self._hex_to_rgb(self.config.terminal_bg))
        
        # Header
        draw.rectangle([(0, 0), (self.width, 40)], fill=self._hex_to_rgb("#2d2d3d"))
        for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
            draw.ellipse([(20 + i * 25 - 6, 14), (20 + i * 25 + 6, 26)], fill=self._hex_to_rgb(color))
        
        code_font = self._get_font(self.config.code_font, self.config.code_font_size)
        
        y_pos = 60
        prompt_color = self._hex_to_rgb(self.config.terminal_prompt_color)
        output_color = self._hex_to_rgb(self.config.terminal_output_color)
        
        for cmd, output in commands_and_outputs:
            draw.text((30, y_pos), f"$ {cmd}", fill=prompt_color, font=code_font)
            y_pos += 35
            if output:
                for line in output.split('\n')[:15]:  # Limit lines
                    draw.text((30, y_pos), line, fill=output_color, font=code_font)
                    y_pos += 28
            y_pos += 10
        
        return ImageClip(np.array(img)).with_duration(duration)
    
    def create_summary_slide(self, title: str, items: list[tuple[str, str]],
                             duration: float = 10.0) -> ImageClip:
        """Create a summary slide"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        self._draw_gradient(draw, self.width, self.height)
        
        title_font = self._get_font(self.config.title_font, self.config.heading_font_size)
        body_font = self._get_font(self.config.body_font, self.config.body_font_size - 4)
        
        # Title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((title_x, 60), title, fill=self._hex_to_rgb(self.config.primary_color), font=title_font)
        
        # Items (2 columns)
        cols = 2
        item_width = (self.width - 200) // cols
        start_y = 180
        row_height = 100
        
        check_color = self._hex_to_rgb(self.config.success_color)
        text_color = self._hex_to_rgb(self.config.text_color)
        
        for i, (icon, text) in enumerate(items):
            col = i % cols
            row = i // cols
            x = 120 + col * item_width
            y = start_y + row * row_height
            draw.text((x, y), icon, fill=check_color, font=body_font)
            draw.text((x + 50, y), text, fill=text_color, font=body_font)
        
        return ImageClip(np.array(img)).with_duration(duration)
    
    def create_thank_you_slide(self, github_url: str = "",
                                duration: float = 5.0) -> ImageClip:
        """Create a thank you slide"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        self._draw_gradient(draw, self.width, self.height)
        
        title_font = self._get_font(self.config.title_font, self.config.title_font_size)
        body_font = self._get_font(self.config.body_font, self.config.body_font_size)
        
        # Thank you
        text = "Thank You!"
        bbox = draw.textbbox((0, 0), text, font=title_font)
        x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((x, self.height // 3), text, fill=self._hex_to_rgb(self.config.primary_color), font=title_font)
        
        # URL
        if github_url:
            bbox = draw.textbbox((0, 0), github_url, font=body_font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, self.height // 2 + 20), github_url, 
                      fill=self._hex_to_rgb(self.config.text_secondary), font=body_font)
        
        # Feedback
        text = "Questions and feedback welcome!"
        small_font = self._get_font(self.config.body_font, self.config.body_font_size - 6)
        bbox = draw.textbbox((0, 0), text, font=small_font)
        x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((x, self.height // 2 + 100), text,
                  fill=self._hex_to_rgb(self.config.text_secondary), font=small_font)
        
        return ImageClip(np.array(img)).with_duration(duration)


class TransitionEffects:
    """Video transition effects"""
    
    @staticmethod
    def crossfade(clip1, clip2, duration: float = 0.5):
        """Crossfade transition"""
        return concatenate_videoclips([clip1, clip2], method="compose", padding=-duration)
