"""
Main Video Generator - Precise Timing Version
Creates demo video with TTS narration and synchronized subtitles
Video duration matches exactly with audio - no early scene changes
"""
import argparse
import time
from pathlib import Path
from typing import Optional

import numpy as np
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    concatenate_audioclips,
)
from PIL import Image, ImageDraw, ImageFont

from .config import VIDEO_SECTIONS, Section, VideoConfig
from .terminal_recorder import DEMO_SEQUENCES, TerminalSimulator
from .tts_engine import EdgeTTSEngine, NarrationGenerator, get_tts_engine
from .visual_components import SlideGenerator
from .subtitles import SubtitleGenerator, SubtitleSegment


class DemoVideoGenerator:
    """Video generator with precise audio-video synchronization"""
    
    def __init__(self, config: Optional[VideoConfig] = None, 
                 output_dir: Optional[Path] = None,
                 tts_engine: str = "edge",
                 enable_subtitles: bool = True):
        self.config = config or VideoConfig()
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.enable_subtitles = enable_subtitles
        
        # Initialize components
        self.slide_gen = SlideGenerator(self.config)
        self.terminal_sim = TerminalSimulator(self.config)
        self.subtitle_gen = SubtitleGenerator(self.config)
        
        # Initialize TTS
        if tts_engine == "edge":
            self.tts = EdgeTTSEngine(voice="en-US-GuyNeural", rate="+0%")
        else:
            self.tts = get_tts_engine(tts_engine)
        
        self.narration_gen = NarrationGenerator(self.tts, self.output_dir / "audio")
        
        # Track assets
        self.audio_files: dict[str, tuple[Path, float]] = {}
        self.all_subtitles: dict[str, list[SubtitleSegment]] = {}
    
    def generate_all_narration(self) -> dict[str, tuple[Path, float]]:
        """Generate TTS audio for all sections"""
        print("\n🎙️ Generating TTS narration...")
        
        for section in VIDEO_SECTIONS:
            print(f"  📢 Section: {section.id}")
            audio_path, duration = self.narration_gen.generate_section_audio(
                section.id, section.narration
            )
            self.audio_files[section.id] = (audio_path, duration)
            print(f"     Duration: {duration:.1f}s")
            
            # Generate subtitles
            if self.enable_subtitles:
                subtitles = self.subtitle_gen.generate_subtitles_from_section(section.id, duration)
                self.all_subtitles[section.id] = subtitles
                print(f"     Subtitles: {len(subtitles)} segments")
        
        return self.audio_files
    
    def _get_duration(self, section_id: str) -> float:
        """Get exact audio duration - video must match this exactly"""
        _, duration = self.audio_files.get(section_id, (None, 30.0))
        return duration
    
    def _create_section_with_duration(self, slides: list[ImageClip], 
                                       total_duration: float) -> ImageClip:
        """
        Create a section ensuring total duration matches audio exactly
        Slides are distributed proportionally within the duration
        """
        if not slides:
            # Return blank clip if no slides
            return self._create_blank_clip(total_duration)
        
        if len(slides) == 1:
            # Single slide - just set its duration
            return slides[0].with_duration(total_duration)
        
        # Calculate proportional durations
        # Each slide gets duration based on its original duration ratio
        original_durations = [clip.duration for clip in slides]
        total_original = sum(original_durations)
        
        adjusted_clips = []
        for clip, orig_dur in zip(slides, original_durations):
            # Proportional duration
            new_dur = (orig_dur / total_original) * total_duration
            new_dur = max(new_dur, 1.0)  # Minimum 1 second per slide
            adjusted_clips.append(clip.with_duration(new_dur))
        
        # Concatenate and ensure exact duration
        result = concatenate_videoclips(adjusted_clips, method="compose")
        
        # Final adjustment if needed
        if abs(result.duration - total_duration) > 0.1:
            result = result.with_duration(total_duration)
        
        return result
    
    def _create_blank_clip(self, duration: float) -> ImageClip:
        """Create a blank clip with background color"""
        img = Image.new('RGB', (self.config.width, self.config.height))
        draw = ImageDraw.Draw(img)
        # Gradient background
        c1 = (10, 10, 15)
        c2 = (26, 26, 46)
        for y in range(self.config.height):
            ratio = y / self.config.height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (self.config.width, y)], fill=(r, g, b))
        return ImageClip(np.array(img)).with_duration(duration)
    
    def create_intro_section(self) -> ImageClip:
        """Section 1: Problem & Business Value - EXACT audio duration"""
        duration = self._get_duration("intro")
        
        # Create slides with relative weights
        slides = [
            (self.slide_gen.create_title_slide(
                "Multi-Agent Customer Support",
                "AI Assistant for SMBs",
                5.0
            ), 0.20),  # 20% of time
            (self.slide_gen.create_stat_slide(
                "80%",
                "of support tickets are repetitive questions",
                7.0
            ), 0.35),  # 35% of time
            (self.slide_gen.create_bullet_slide(
                "The Problem We Solve",
                [
                    "Order tracking & status updates",
                    "Refund requests & policy lookup",
                    "Account access issues",
                    "Instant, secure, accurate responses"
                ],
                10.0
            ), 0.45),  # 45% of time
        ]
        
        # Adjust durations to match audio exactly
        adjusted_slides = []
        for clip, weight in slides:
            slide_duration = duration * weight
            adjusted_slides.append(clip.with_duration(slide_duration))
        
        return concatenate_videoclips(adjusted_slides, method="compose")
    
    def create_architecture_section(self) -> ImageClip:
        """Section 2: Architecture - EXACT audio duration"""
        duration = self._get_duration("architecture")
        
        slides = [
            (self.slide_gen.create_title_slide(
                "System Architecture",
                "5-Day AI Agents Course Concepts",
                3.0
            ), 0.08),
            (self.slide_gen.create_architecture_slide(duration=15.0), 0.35),
            (self.slide_gen.create_bullet_slide(
                "Course Concepts Implemented",
                [
                    "Multi-agent architecture (4 specialized agents)",
                    "MCP Tool Server (6 business tools)",
                    "Session & Memory (SQLite-backed)",
                    "Security Guardrails (PII masking)",
                    "Structured Outputs (Pydantic schemas)",
                    "Comprehensive Evaluation (67 tests)"
                ],
                20.0
            ), 0.57),
        ]
        
        adjusted_slides = []
        for clip, weight in slides:
            slide_duration = duration * weight
            adjusted_slides.append(clip.with_duration(slide_duration))
        
        return concatenate_videoclips(adjusted_slides, method="compose")
    
    def create_demo_section(self, section_id: str, demo_key: str) -> ImageClip:
        """Demo section with terminal - EXACT audio duration"""
        duration = self._get_duration(section_id)
        
        messages = DEMO_SEQUENCES.get(demo_key, [])
        
        if not messages:
            return self.slide_gen.create_terminal_slide(
                [("python -m src.cli chat --verbose", "Demo...")],
                duration
            )
        
        # Create terminal animation
        terminal_clip = self.terminal_sim.create_chat_sequence(messages, fps=self.config.fps)
        
        # IMPORTANT: Adjust terminal animation to match audio duration exactly
        if abs(terminal_clip.duration - duration) > 0.5:
            if terminal_clip.duration < duration:
                # Extend by holding last frame
                terminal_clip = terminal_clip.with_duration(duration)
            else:
                # Speed up to fit
                speed_factor = terminal_clip.duration / duration
                terminal_clip = terminal_clip.with_speed(speed_factor)
        
        return terminal_clip.with_duration(duration)
    
    def create_test_section(self) -> ImageClip:
        """Section: Tests - EXACT audio duration"""
        duration = self._get_duration("tests")
        
        slides = [
            (self.slide_gen.create_title_slide(
                "Security & Evaluation",
                "67 Automated Tests",
                3.0
            ), 0.08),
            (self.slide_gen.create_terminal_slide(
                [
                    ("pytest tests/ -v", ""),
                    ("test_intent.py::test_order", "PASSED"),
                    ("test_intent.py::test_refund", "PASSED"),
                    ("test_security.py::test_mask_cc", "PASSED"),
                    ("test_security.py::test_mask_email", "PASSED"),
                    ("test_security.py::test_access", "PASSED"),
                    ("test_orchestrator.py::test_flow", "PASSED"),
                    ("", "67 passed in 2.34s"),
                ],
                15.0
            ), 0.40),
            (self.slide_gen.create_summary_slide(
                "PII Masking & Security",
                [
                    ("✓", "Credit cards: ****-****-****-1234"),
                    ("✓", "Emails: a***@email.com"),
                    ("✓", "Phone: ***-***-####"),
                    ("✓", "Internal IDs: [REDACTED]"),
                    ("✓", "Cross-customer blocked"),
                    ("✓", "Session lockout (3 fails)"),
                ],
                15.0
            ), 0.52),
        ]
        
        adjusted_slides = []
        for clip, weight in slides:
            slide_duration = duration * weight
            adjusted_slides.append(clip.with_duration(slide_duration))
        
        return concatenate_videoclips(adjusted_slides, method="compose")
    
    def create_conclusion_section(self) -> ImageClip:
        """Section: Conclusion - EXACT audio duration"""
        duration = self._get_duration("conclusion")
        
        slides = [
            (self.slide_gen.create_summary_slide(
                "Course Concepts Applied",
                [
                    ("✓", "Multi-agent architecture"),
                    ("✓", "MCP tool integration"),
                    ("✓", "Persistent sessions"),
                    ("✓", "Security guardrails"),
                    ("✓", "Structured outputs"),
                    ("✓", "Comprehensive testing"),
                ],
                12.0
            ), 0.38),
            (self.slide_gen.create_bullet_slide(
                "Future Enhancements",
                [
                    "Voice integration for phone support",
                    "Analytics dashboard",
                    "Slack & WhatsApp deployment",
                    "Real-time sentiment analysis"
                ],
                10.0
            ), 0.35),
            (self.slide_gen.create_thank_you_slide(
                "github.com/your-repo/ai-agents-business-support",
                8.0
            ), 0.27),
        ]
        
        adjusted_slides = []
        for clip, weight in slides:
            slide_duration = duration * weight
            adjusted_slides.append(clip.with_duration(slide_duration))
        
        return concatenate_videoclips(adjusted_slides, method="compose")
    
    def _create_subtitle_clips(self, section_id: str, time_offset: float) -> list[ImageClip]:
        """Create subtitle clips for a section with time offset"""
        if not self.enable_subtitles or section_id not in self.all_subtitles:
            return []
        
        clips = []
        for segment in self.all_subtitles[section_id]:
            clip = self._create_single_subtitle(segment)
            # Offset start time for concatenated video
            clip = clip.with_start(segment.start_time + time_offset)
            clips.append(clip)
        
        return clips
    
    def _create_single_subtitle(self, segment: SubtitleSegment) -> ImageClip:
        """Create a single subtitle overlay clip"""
        img = Image.new('RGBA', (self.config.width, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        text = segment.text
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = max(10, (self.config.width - text_width) // 2)
        y = 30
        
        # Background
        padding = 15
        bg_x1 = max(0, x - padding)
        bg_x2 = min(self.config.width, x + text_width + padding)
        draw.rectangle([(bg_x1, y - 10), (bg_x2, y + 50)], fill=(0, 0, 0, 200))
        
        # Text with slight shadow
        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0, 150))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        clip = ImageClip(np.array(img), transparent=True)
        clip = clip.with_duration(segment.duration)
        clip = clip.with_position(('center', self.config.height - 130))
        
        return clip
    
    def generate_full_video(self, output_filename: str = None) -> Path:
        """Generate complete video with precise audio-video sync"""
        output_filename = output_filename or self.config.output_filename
        output_path = self.output_dir / output_filename
        
        print("\n🎬 Starting video generation...")
        
        # Step 1: Generate audio first (determines all timing)
        self.generate_all_narration()
        
        # Step 2: Create video sections matching audio durations
        print("\n🎥 Creating video sections (matched to audio)...")
        
        section_creators = [
            ("intro", self.create_intro_section),
            ("architecture", self.create_architecture_section),
            ("demo_order", lambda: self.create_demo_section("demo_order", "order_status")),
            ("demo_refund", lambda: self.create_demo_section("demo_refund", "refund_followup")),
            ("demo_security", lambda: self.create_demo_section("demo_security", "security_block")),
            ("demo_suspended", lambda: self.create_demo_section("demo_suspended", "suspended_account")),
            ("demo_escalation", lambda: self.create_demo_section("demo_escalation", "escalation")),
            ("tests", self.create_test_section),
            ("conclusion", self.create_conclusion_section),
        ]
        
        video_clips = []
        audio_clips = []
        all_subtitle_clips = []
        cumulative_time = 0.0
        
        for section_id, create_func in section_creators:
            print(f"  📹 {section_id}: ", end="")
            
            try:
                # Get audio duration first
                audio_path, audio_duration = self.audio_files.get(section_id, (None, 30.0))
                
                # Create video matching audio duration
                video_clip = create_func()
                
                # FORCE exact duration match
                video_clip = video_clip.with_duration(audio_duration)
                video_clips.append(video_clip)
                
                print(f"{audio_duration:.1f}s ✓")
                
                # Subtitles with offset
                sub_clips = self._create_subtitle_clips(section_id, cumulative_time)
                all_subtitle_clips.extend(sub_clips)
                
                # Audio
                if audio_path and audio_path.exists():
                    audio_clips.append(AudioFileClip(str(audio_path)))
                
                cumulative_time += audio_duration
                
            except Exception as e:
                print(f"ERROR: {e}")
                # Fallback
                duration = self._get_duration(section_id)
                placeholder = self._create_blank_clip(duration)
                video_clips.append(placeholder)
                cumulative_time += duration
        
        # Step 3: Compose video
        print("\n🔧 Composing final video...")
        
        base_video = concatenate_videoclips(video_clips, method="compose")
        print(f"  Base video: {base_video.duration:.1f}s")
        
        # Add subtitles
        if all_subtitle_clips:
            print(f"  📝 Adding {len(all_subtitle_clips)} subtitles...")
            final_video = CompositeVideoClip([base_video] + all_subtitle_clips)
        else:
            final_video = base_video
        
        # Add audio
        if audio_clips:
            combined_audio = concatenate_audioclips(audio_clips)
            print(f"  Audio: {combined_audio.duration:.1f}s")
            final_video = final_video.with_audio(combined_audio)
        
        # Export SRT
        if self.enable_subtitles:
            srt_path = output_path.with_suffix('.srt')
            self._export_all_srt(srt_path)
            print(f"  📄 SRT: {srt_path}")
        
        # Step 4: Export video
        print(f"\n💾 Exporting to {output_path}...")
        print(f"   Duration: {final_video.duration:.1f}s ({final_video.duration/60:.1f}min)")
        
        final_video.write_videofile(
            str(output_path),
            fps=self.config.fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4,
            remove_temp=False
        )
        
        # Cleanup temp files
        try:
            time.sleep(0.5)
            temp_audio = Path(str(output_path).replace('.mp4', 'TEMP_MPY_wvf_snd.mp4'))
            if temp_audio.exists():
                temp_audio.unlink()
        except:
            pass
        
        print(f"\n✅ Video generated: {output_path}")
        return output_path
    
    def _export_all_srt(self, output_path: Path):
        """Export all subtitles to SRT"""
        all_segments = []
        cumulative_time = 0.0
        
        section_order = [
            "intro", "architecture", "demo_order", "demo_refund",
            "demo_security", "demo_suspended", "demo_escalation",
            "tests", "conclusion"
        ]
        
        for section_id in section_order:
            if section_id in self.all_subtitles:
                for seg in self.all_subtitles[section_id]:
                    all_segments.append(SubtitleSegment(
                        text=seg.text,
                        start_time=seg.start_time + cumulative_time,
                        end_time=seg.end_time + cumulative_time
                    ))
                
                _, duration = self.audio_files.get(section_id, (None, 0))
                cumulative_time += duration
        
        self.subtitle_gen.export_srt(all_segments, output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate demo video")
    parser.add_argument("--output", "-o", default="demo_video.mp4")
    parser.add_argument("--output-dir", "-d", default="output")
    parser.add_argument("--tts-engine", "-t", choices=["edge", "gtts", "pyttsx3"], default="edge")
    parser.add_argument("--width", "-W", type=int, default=1920)
    parser.add_argument("--height", "-H", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--no-subtitles", action="store_true")
    parser.add_argument("--narration-only", "-n", action="store_true")
    
    args = parser.parse_args()
    
    config = VideoConfig(
        width=args.width,
        height=args.height,
        fps=args.fps,
        output_filename=args.output
    )
    
    generator = DemoVideoGenerator(
        config=config,
        output_dir=Path(args.output_dir),
        tts_engine=args.tts_engine,
        enable_subtitles=not args.no_subtitles
    )
    
    if args.narration_only:
        generator.generate_all_narration()
        print("\n✅ Audio saved to output/audio/")
    else:
        generator.generate_full_video()


if __name__ == "__main__":
    main()
