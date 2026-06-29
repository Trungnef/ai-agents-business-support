"""
Subtitle Generator with Word-Level Timing
Uses edge-tts word boundaries for precise subtitle synchronization
"""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip

from .config import VideoConfig, VIDEO_SECTIONS


@dataclass
class SubtitleSegment:
    """A single subtitle segment with precise timing"""
    text: str
    start_time: float
    end_time: float
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass 
class WordTiming:
    """Word with precise timing from TTS"""
    word: str
    start_ms: int
    end_ms: int


class SubtitleGenerator:
    """Generates precisely timed subtitles"""
    
    MAX_CHARS_PER_SUBTITLE = 80  # Max characters per subtitle line
    MIN_SUBTITLE_DURATION = 1.5  # Minimum seconds per subtitle
    MAX_SUBTITLE_DURATION = 5.0  # Maximum seconds per subtitle
    
    def __init__(self, config: VideoConfig):
        self.config = config
    
    def generate_subtitles_with_edge_tts(self, text: str, voice: str = "en-US-GuyNeural") -> tuple[Path, float, list[SubtitleSegment]]:
        """
        Generate audio and word-timed subtitles using edge-tts
        
        Returns:
            (audio_path, duration, subtitles)
        """
        import tempfile
        import asyncio
        
        clean_text = self._preprocess_text(text)
        
        # Create temp files
        temp_dir = Path(tempfile.mkdtemp())
        audio_path = temp_dir / "audio.mp3"
        subs_path = temp_dir / "subs.json"
        
        try:
            # Run edge-tts with word boundary output
            result = subprocess.run(
                [
                    "edge-tts",
                    "--voice", voice,
                    "--text", clean_text,
                    "--write-media", str(audio_path),
                    "--write-subtitles", str(subs_path.with_suffix('.vtt'))
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise Exception(f"edge-tts failed: {result.stderr}")
            
            # Parse VTT to get timing
            subtitles = self._parse_vtt_file(subs_path.with_suffix('.vtt'))
            
            # Get audio duration
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            duration = len(audio) / 1000.0
            
            return audio_path, duration, subtitles
            
        except Exception as e:
            print(f"Error generating subtitles: {e}")
            # Fallback to estimated timing
            subtitles = self._generate_estimated_subtitles(clean_text, 30.0)
            return None, 30.0, subtitles
    
    def _parse_vtt_file(self, vtt_path: Path) -> list[SubtitleSegment]:
        """Parse VTT subtitle file from edge-tts"""
        if not vtt_path.exists():
            return []
        
        segments = []
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse VTT format
        # Format: 00:00:00.000 --> 00:00:01.000
        #         Text here
        pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?=\n\n|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for start_str, end_str, text in matches:
            start_time = self._vtt_time_to_seconds(start_str)
            end_time = self._vtt_time_to_seconds(end_str)
            text = text.strip()
            
            if text and not text.startswith('WEBVTT'):
                segments.append(SubtitleSegment(
                    text=text,
                    start_time=start_time,
                    end_time=end_time
                ))
        
        # Merge short segments into readable chunks
        return self._merge_segments(segments)
    
    def _vtt_time_to_seconds(self, time_str: str) -> float:
        """Convert VTT timestamp to seconds"""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def _merge_segments(self, segments: list[SubtitleSegment]) -> list[SubtitleSegment]:
        """Merge short segments into readable subtitle chunks"""
        if not segments:
            return []
        
        merged = []
        current_text = ""
        current_start = segments[0].start_time
        current_end = segments[0].end_time
        
        for seg in segments:
            potential_text = (current_text + " " + seg.text).strip() if current_text else seg.text
            potential_duration = seg.end_time - current_start
            
            # Check if we should start a new segment
            should_split = (
                len(potential_text) > self.MAX_CHARS_PER_SUBTITLE or
                potential_duration > self.MAX_SUBTITLE_DURATION or
                seg.text.endswith(('.', '!', '?', ':'))  # Natural sentence break
            )
            
            if should_split and current_text:
                merged.append(SubtitleSegment(
                    text=current_text.strip(),
                    start_time=current_start,
                    end_time=current_end
                ))
                current_text = seg.text
                current_start = seg.start_time
                current_end = seg.end_time
            else:
                current_text = potential_text
                current_end = seg.end_time
        
        # Don't forget the last segment
        if current_text:
            merged.append(SubtitleSegment(
                text=current_text.strip(),
                start_time=current_start,
                end_time=current_end
            ))
        
        return merged
    
    def generate_subtitles_from_section(self, section_id: str, 
                                         audio_duration: float) -> list[SubtitleSegment]:
        """Generate subtitle segments for a section"""
        section = next((s for s in VIDEO_SECTIONS if s.id == section_id), None)
        if not section:
            return []
        
        return self._generate_estimated_subtitles(section.narration, audio_duration)
    
    def _generate_estimated_subtitles(self, text: str, total_duration: float) -> list[SubtitleSegment]:
        """Generate subtitles with estimated timing based on word count"""
        clean_text = self._preprocess_text(text)
        sentences = self._split_into_sentences(clean_text)
        
        if not sentences:
            return []
        
        # Calculate total words
        total_words = sum(len(s.split()) for s in sentences)
        if total_words == 0:
            return []
        
        time_per_word = total_duration / total_words
        
        segments = []
        current_time = 0.0
        
        for sentence in sentences:
            chunks = self._split_into_chunks(sentence)
            
            for chunk in chunks:
                word_count = len(chunk.split())
                duration = word_count * time_per_word
                
                # Ensure minimum/maximum duration
                duration = max(self.MIN_SUBTITLE_DURATION, min(duration, self.MAX_SUBTITLE_DURATION))
                
                end_time = min(current_time + duration, total_duration)
                
                segments.append(SubtitleSegment(
                    text=chunk.strip(),
                    start_time=current_time,
                    end_time=end_time
                ))
                
                current_time = end_time
        
        # Adjust last segment to match total duration
        if segments and segments[-1].end_time < total_duration:
            segments[-1] = SubtitleSegment(
                text=segments[-1].text,
                start_time=segments[-1].start_time,
                end_time=total_duration
            )
        
        return segments
    
    def _preprocess_text(self, text: str) -> str:
        """Clean text for TTS and subtitles"""
        text = text.replace('\n', ' ').strip()
        text = re.sub(r'\s+', ' ', text)
        # Remove markdown
        text = text.replace('**', '').replace('*', '').replace('`', '')
        return text
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_into_chunks(self, sentence: str) -> list[str]:
        """Split long sentences into readable chunks"""
        if len(sentence) <= self.MAX_CHARS_PER_SUBTITLE:
            return [sentence]
        
        chunks = []
        words = sentence.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_len = len(word) + 1
            
            if current_length + word_len > self.MAX_CHARS_PER_SUBTITLE and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += word_len
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def create_subtitle_clip(self, segment: SubtitleSegment, 
                             width: int, height: int) -> ImageClip:
        """Create a video clip for a single subtitle"""
        # Create transparent image
        img = Image.new('RGBA', (width, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        text = segment.text
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = 30
        
        # Background box
        padding = 15
        bg_x1 = max(0, x - padding)
        bg_x2 = min(width, x + text_width + padding)
        draw.rectangle([(bg_x1, y - 10), (bg_x2, y + 45)], fill=(0, 0, 0, 200))
        
        # Text
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        # Create clip
        clip = ImageClip(np.array(img), transparent=True)
        clip = clip.with_duration(segment.duration)
        clip = clip.with_start(segment.start_time)
        clip = clip.with_position(('center', height - 120))
        
        return clip
    
    def export_srt(self, segments: list[SubtitleSegment], output_path: Path) -> Path:
        """Export subtitles to SRT format"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start = self._format_srt_time(seg.start_time)
                end = self._format_srt_time(seg.end_time)
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{seg.text}\n\n")
        
        return output_path
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
