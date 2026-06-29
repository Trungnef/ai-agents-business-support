"""
Terminal Recording Simulator
Creates animated terminal sequences for demo videos
"""
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont

from .config import VideoConfig


@dataclass
class TerminalCommand:
    """Represents a terminal command and its output"""
    command: str
    output: str
    typing_speed: float = 0.05  # seconds per character
    output_delay: float = 0.3   # delay before showing output
    is_chat_message: bool = False  # For chat-style messages


@dataclass
class ChatMessage:
    """Represents a chat interaction"""
    user_message: str
    bot_response: str
    intent: Optional[str] = None
    tools_used: Optional[list[str]] = None
    processing_time: Optional[float] = None


class TerminalSimulator:
    """Simulates terminal interactions for video"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self.width = config.width
        self.height = config.height
        
        # Terminal styling
        self.terminal_padding = 30
        self.line_height = 32
        self.header_height = 45
        
    def create_terminal_frame(self, lines: list[tuple[str, str]], 
                               cursor_line: Optional[int] = None,
                               cursor_pos: Optional[int] = None) -> Image.Image:
        """
        Create a single terminal frame
        
        Args:
            lines: List of (text, color_type) tuples
            cursor_line: Line number for cursor (if showing)
            cursor_pos: Character position for cursor
        
        Returns:
            PIL Image of the terminal frame
        """
        img = Image.new('RGB', (self.width, self.height), 
                        self._hex_to_rgb(self.config.terminal_bg))
        draw = ImageDraw.Draw(img)
        
        # Draw header bar
        draw.rectangle(
            [(0, 0), (self.width, self.header_height)],
            fill=self._hex_to_rgb("#2d2d3d")
        )
        
        # Draw window buttons
        button_colors = ["#ff5f56", "#ffbd2e", "#27c93f"]
        for i, color in enumerate(button_colors):
            x = 20 + i * 25
            y = self.header_height // 2
            draw.ellipse(
                [(x - 6, y - 6), (x + 6, y + 6)],
                fill=self._hex_to_rgb(color)
            )
        
        # Draw title
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        title = "AI Customer Support Demo"
        bbox = draw.textbbox((0, 0), title, font=font)
        title_x = (self.width - (bbox[2] - bbox[0])) // 2
        draw.text((title_x, 12), title, 
                  fill=self._hex_to_rgb(self.config.text_secondary), font=font)
        
        # Draw terminal content
        try:
            code_font = ImageFont.truetype("consola.ttf", self.config.code_font_size)
        except:
            try:
                code_font = ImageFont.truetype("Consolas.ttf", self.config.code_font_size)
            except:
                code_font = ImageFont.load_default()
        
        y = self.header_height + self.terminal_padding
        
        color_map = {
            "prompt": self.config.terminal_prompt_color,
            "command": self.config.text_color,
            "output": self.config.terminal_output_color,
            "error": self.config.terminal_error_color,
            "info": self.config.primary_color,
            "dim": self.config.text_secondary,
            "highlight": self.config.highlight_color,
            "success": self.config.success_color,
        }
        
        for line_idx, (text, color_type) in enumerate(lines):
            color = self._hex_to_rgb(color_map.get(color_type, self.config.text_color))
            
            # Handle line wrapping for long lines
            max_chars = (self.width - 2 * self.terminal_padding) // 14  # Approximate char width
            wrapped_lines = self._wrap_text(text, max_chars)
            
            for wrapped_line in wrapped_lines:
                # Draw cursor if on this line
                if cursor_line == line_idx and cursor_pos is not None:
                    cursor_x = self.terminal_padding + cursor_pos * 14
                    draw.rectangle(
                        [(cursor_x, y), (cursor_x + 10, y + self.line_height - 4)],
                        fill=self._hex_to_rgb(self.config.primary_color)
                    )
                
                draw.text((self.terminal_padding, y), wrapped_line, fill=color, font=code_font)
                y += self.line_height
                
            if y > self.height - self.terminal_padding:
                break  # Stop if we've run out of space
        
        return img
    
    def create_typing_animation(self, command: str, existing_lines: list[tuple[str, str]],
                                 prompt: str = "You: ", duration: float = None,
                                 fps: int = 30) -> list[Image.Image]:
        """Create frames for typing animation"""
        frames = []
        
        if duration:
            # Calculate typing speed based on duration
            chars_per_second = len(command) / (duration * 0.7)  # Leave 30% for pauses
            char_interval = 1.0 / chars_per_second
        else:
            char_interval = 0.05
        
        frames_per_char = max(1, int(char_interval * fps))
        
        # Create frames for each character being typed
        current_text = ""
        for char in command:
            current_text += char
            
            # Add variation to typing speed
            variation_frames = frames_per_char + random.randint(-1, 2)
            
            for _ in range(max(1, variation_frames)):
                lines = existing_lines + [(f"{prompt}{current_text}", "command")]
                frame = self.create_terminal_frame(lines, cursor_line=len(lines)-1, 
                                                    cursor_pos=len(prompt) + len(current_text))
                frames.append(frame)
        
        return frames
    
    def create_output_reveal(self, output_lines: list[tuple[str, str]], 
                              existing_lines: list[tuple[str, str]],
                              reveal_speed: float = 0.1,
                              fps: int = 30) -> list[Image.Image]:
        """Create frames for output appearing"""
        frames = []
        frames_per_line = max(1, int(reveal_speed * fps))
        
        current_lines = list(existing_lines)
        
        for line in output_lines:
            current_lines.append(line)
            
            for _ in range(frames_per_line):
                frame = self.create_terminal_frame(current_lines)
                frames.append(frame)
        
        return frames
    
    def create_chat_sequence(self, messages: list[ChatMessage], 
                              fps: int = 30) -> CompositeVideoClip:
        """Create a full chat sequence video clip"""
        all_frames = []
        terminal_lines: list[tuple[str, str]] = []
        
        # Initial prompt
        terminal_lines.append(("python -m src.cli chat --verbose", "prompt"))
        terminal_lines.append(("", "output"))
        terminal_lines.append(("🤖 AI Customer Support Assistant", "info"))
        terminal_lines.append(("Type /help for commands, /quit to exit", "dim"))
        terminal_lines.append(("", "output"))
        
        # Quick initial frame (0.3s)
        for _ in range(int(fps * 0.3)):
            frame = self.create_terminal_frame(terminal_lines)
            all_frames.append(frame)
        
        for msg in messages:
            # Type user message (fast - 1s)
            typing_frames = self.create_typing_animation(
                msg.user_message,
                terminal_lines,
                prompt="You: ",
                duration=1.0,
                fps=fps
            )
            all_frames.extend(typing_frames)
            
            # Add the complete user message
            terminal_lines.append((f"You: {msg.user_message}", "command"))
            
            # Brief thinking animation (0.4s)
            thinking_frames = self._create_thinking_animation(terminal_lines, fps, duration=0.4)
            all_frames.extend(thinking_frames)
            
            # Build response lines
            response_lines = []
            
            if msg.intent:
                response_lines.append((f"[Intent: {msg.intent}]", "dim"))
            
            # Split bot response into lines (limit to keep it fast)
            for line in msg.bot_response.split('\n')[:8]:
                if line.strip():
                    response_lines.append((f"{line}", "output"))
            
            if msg.tools_used:
                tools_str = ", ".join(msg.tools_used[:3])
                response_lines.append((f"[Tools: {tools_str}]", "dim"))
            
            # Fast reveal (0.04s per line)
            reveal_frames = self.create_output_reveal(
                response_lines,
                terminal_lines,
                reveal_speed=0.04,
                fps=fps
            )
            all_frames.extend(reveal_frames)
            
            # Add response to terminal
            terminal_lines.extend(response_lines)
            
            # Brief pause (0.5s) - just enough to see result
            for _ in range(int(fps * 0.5)):
                frame = self.create_terminal_frame(terminal_lines)
                all_frames.append(frame)
        
        # Convert frames to video clip
        from moviepy import ImageSequenceClip
        duration = len(all_frames) / fps
        
        # Convert PIL images to numpy arrays
        import numpy as np
        frames_array = [np.array(f) for f in all_frames]
        
        clip = ImageSequenceClip(frames_array, fps=fps)
        return clip
    
    def _create_thinking_animation(self, existing_lines: list[tuple[str, str]],
                                    fps: int, duration: float = 0.8) -> list[Image.Image]:
        """Create a thinking/processing animation"""
        frames = []
        num_frames = int(duration * fps)
        
        thinking_states = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        for i in range(num_frames):
            state_idx = i % len(thinking_states)
            lines = list(existing_lines)
            lines.append((f"{thinking_states[state_idx]} Processing...", "info"))
            frame = self.create_terminal_frame(lines)
            frames.append(frame)
        
        return frames
    
    def _wrap_text(self, text: str, max_chars: int) -> list[str]:
        """Wrap text to fit within max characters"""
        if len(text) <= max_chars:
            return [text]
        
        lines = []
        current = ""
        
        for word in text.split():
            if len(current) + len(word) + 1 <= max_chars:
                current = current + " " + word if current else word
            else:
                if current:
                    lines.append(current)
                current = word
        
        if current:
            lines.append(current)
        
        return lines
    
    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# Pre-defined demo sequences - synchronized with narration in config.py
# Each demo shows exactly what the narrator describes
DEMO_SEQUENCES = {
    # Demo 1: Order Status - matches narration about setting email and asking order status
    "order_status": [
        ChatMessage(
            user_message="/email alice.johnson@email.com",
            bot_response="Email verified: alice.johnson@email.com",
            processing_time=0.12
        ),
        ChatMessage(
            user_message="Where is my order ORD-2024-002?",
            bot_response="""Your order ORD-2024-002 status: SHIPPED

Order Details:
- Items: Wireless Mouse, USB-C Hub  
- Total: $89.99
- Tracking: TRACK123456789
- Expected: June 28, 2024""",
            intent="ORDER_STATUS",
            tools_used=["get_order_details", "get_customer_profile"],
            processing_time=0.45
        ),
    ],
    
    # Demo 2: Refund Follow-up - demonstrates session memory with "it" reference
    "refund_followup": [
        ChatMessage(
            user_message="Can I refund it?",
            bot_response="""Checking refund policy for ORD-2024-002...

Refund Status: ELIGIBLE
- Order within 30-day return window
- Policy: Full refund available

Would you like to proceed with the refund?""",
            intent="REFUND_REQUEST",
            tools_used=["get_order_details", "get_refund_policy"],
            processing_time=0.52
        ),
        ChatMessage(
            user_message="/session",
            bot_response="""Session Info:
- ID: sess_abc123
- Email: alice.johnson@email.com  
- Messages: 3
- Context: ORD-2024-002
- Intents: [ORDER_STATUS, REFUND_REQUEST]""",
            processing_time=0.05
        ),
    ],
    
    # Demo 3: Security Block - cross-customer access attempt
    "security_block": [
        ChatMessage(
            user_message="Show me order ORD-2024-003",
            bot_response="""ACCESS DENIED

Order ORD-2024-003 is not linked to your account.
This order belongs to a different customer.

[Security: Failed verification logged]
[Warning: 1/3 attempts before lockout]""",
            intent="ORDER_STATUS",
            tools_used=["get_order_details", "validate_access"],
            processing_time=0.31
        ),
    ],
    
    # Demo 4: Suspended Account - Frank Miller
    "suspended_account": [
        ChatMessage(
            user_message="/email frank.miller@email.com",
            bot_response="Email set: frank.miller@email.com",
            processing_time=0.1
        ),
        ChatMessage(
            user_message="Show me order ORD-2024-008",
            bot_response="""ACCOUNT SUSPENDED

Your account access has been restricted.
Contact support: support@company.com
Phone: 1-800-555-0123

Ref: ACC-SUSPENDED-FM001""",
            intent="ORDER_STATUS",
            tools_used=["get_customer_profile"],
            processing_time=0.28
        ),
    ],
    
    # Demo 5: Human Escalation - creates support ticket
    "escalation": [
        ChatMessage(
            user_message="/email alice.johnson@email.com",
            bot_response="Email verified: alice.johnson@email.com",
            processing_time=0.1
        ),
        ChatMessage(
            user_message="Let me speak to a manager",
            bot_response="""I understand you'd like to speak with a human agent.

📝 Support Ticket Created:
  Ticket ID: TKT-2024-0891
  Priority: High
  Status: Escalated to Human Agent
  
A customer service representative will contact you 
within 2 hours at alice.johnson@email.com.

Is there anything else I can help document for them?""",
            intent="HUMAN_ESCALATION",
            tools_used=["create_support_ticket"],
            processing_time=0.67
        ),
    ],
}
