"""
Text-to-Speech Engine for Video Narration
Supports multiple TTS backends: gTTS, pyttsx3, edge-tts
"""
import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from pydub import AudioSegment


class TTSEngine(ABC):
    """Abstract base class for TTS engines"""
    
    @abstractmethod
    def generate_audio(self, text: str, output_path: Path) -> Path:
        """Generate audio file from text"""
        pass
    
    @abstractmethod
    def get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds"""
        pass


class GTTSEngine(TTSEngine):
    """Google Text-to-Speech engine (free, requires internet)"""
    
    def __init__(self, lang: str = "en", slow: bool = False):
        self.lang = lang
        self.slow = slow
        
    def generate_audio(self, text: str, output_path: Path) -> Path:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang=self.lang, slow=self.slow)
        tts.save(str(output_path))
        return output_path
    
    def get_audio_duration(self, audio_path: Path) -> float:
        audio = AudioSegment.from_file(str(audio_path))
        return len(audio) / 1000.0  # Convert milliseconds to seconds


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS (free, high quality, requires internet)"""
    
    # Voice options for professional narration
    VOICES = {
        "en-US-male": "en-US-GuyNeural",
        "en-US-female": "en-US-JennyNeural",
        "en-US-professional": "en-US-GuyNeural",  # Professional male voice
        "en-GB-male": "en-GB-RyanNeural",
        "en-GB-female": "en-GB-SoniaNeural",
    }
    
    def __init__(self, voice: str = "en-US-GuyNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        """
        Initialize Edge TTS engine
        
        Args:
            voice: Voice name or key from VOICES dict
            rate: Speech rate (e.g., "-10%", "+20%")
            pitch: Voice pitch (e.g., "-5Hz", "+10Hz")
        """
        self.voice = self.VOICES.get(voice, voice)
        self.rate = rate
        self.pitch = pitch
    
    def generate_audio(self, text: str, output_path: Path) -> Path:
        import subprocess
        
        # Clean text - remove problematic characters
        clean_text = text.strip().replace('\n', ' ').replace('"', "'")
        if not clean_text:
            clean_text = "Audio placeholder."
        
        # Limit text length
        clean_text = clean_text[:2000]
        
        try:
            # Use edge-tts CLI directly (more reliable than Python API)
            result = subprocess.run(
                [
                    "edge-tts",
                    "--voice", self.voice,
                    "--text", clean_text,
                    "--write-media", str(output_path)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"Edge TTS CLI error: {result.stderr}")
                raise Exception(result.stderr)
                
        except Exception as e:
            print(f"TTS failed, creating silent audio: {e}")
            # Create silent audio as fallback
            silence = AudioSegment.silent(duration=5000)  # 5 seconds
            silence.export(str(output_path), format="mp3")
        
        return output_path
    
    def get_audio_duration(self, audio_path: Path) -> float:
        audio = AudioSegment.from_file(str(audio_path))
        return len(audio) / 1000.0


class Pyttsx3Engine(TTSEngine):
    """Offline TTS using pyttsx3 (works offline, lower quality)"""
    
    def __init__(self, rate: int = 150, volume: float = 1.0, voice_id: Optional[int] = None):
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
    
    def generate_audio(self, text: str, output_path: Path) -> Path:
        import pyttsx3
        
        engine = pyttsx3.init()
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)
        
        if self.voice_id is not None:
            voices = engine.getProperty('voices')
            if self.voice_id < len(voices):
                engine.setProperty('voice', voices[self.voice_id].id)
        
        # pyttsx3 outputs wav
        wav_path = output_path.with_suffix('.wav')
        engine.save_to_file(text, str(wav_path))
        engine.runAndWait()
        
        # Convert to mp3 if needed
        if output_path.suffix.lower() == '.mp3':
            audio = AudioSegment.from_wav(str(wav_path))
            audio.export(str(output_path), format='mp3')
            wav_path.unlink()  # Remove temp wav
        else:
            wav_path.rename(output_path)
        
        return output_path
    
    def get_audio_duration(self, audio_path: Path) -> float:
        audio = AudioSegment.from_file(str(audio_path))
        return len(audio) / 1000.0


class NarrationGenerator:
    """Generates narration audio for video sections"""
    
    def __init__(self, engine: TTSEngine, output_dir: Path):
        self.engine = engine
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_section_audio(self, section_id: str, text: str) -> tuple[Path, float]:
        """
        Generate audio for a section
        
        Returns:
            Tuple of (audio_path, duration_seconds)
        """
        output_path = self.output_dir / f"{section_id}_narration.mp3"
        
        # Clean up text for better TTS
        clean_text = self._preprocess_text(text)
        
        # Generate audio
        self.engine.generate_audio(clean_text, output_path)
        
        # Get duration
        duration = self.engine.get_audio_duration(output_path)
        
        return output_path, duration
    
    def generate_all_sections(self, sections: list[dict]) -> dict[str, tuple[Path, float]]:
        """
        Generate audio for all sections
        
        Returns:
            Dict mapping section_id to (audio_path, duration)
        """
        results = {}
        for section in sections:
            section_id = section['id'] if isinstance(section, dict) else section.id
            narration = section['narration'] if isinstance(section, dict) else section.narration
            
            print(f"Generating audio for section: {section_id}")
            audio_path, duration = self.generate_section_audio(section_id, narration)
            results[section_id] = (audio_path, duration)
            print(f"  Duration: {duration:.1f}s")
        
        return results
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better TTS output"""
        # Remove markdown formatting
        text = text.replace('**', '')
        text = text.replace('*', '')
        text = text.replace('`', '')
        
        # Add pauses for better pacing
        text = text.replace(' - ', ', ')  # Em dash to comma
        text = text.replace('-', ', ')
        
        # Improve pronunciation of technical terms
        replacements = {
            'MCP': 'M.C.P.',
            'CLI': 'C.L.I.',
            'API': 'A.P.I.',
            'PII': 'P.I.I.',
            'SQLite': 'S.Q.L. lite',
            'Pydantic': 'Pie-dantic',
            'LLM': 'L.L.M.',
            'ORD-': 'order number ',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def concatenate_audio(self, audio_paths: list[Path], output_path: Path, 
                          gap_ms: int = 500) -> Path:
        """Concatenate multiple audio files with gaps"""
        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=gap_ms)
        
        for i, path in enumerate(audio_paths):
            audio = AudioSegment.from_file(str(path))
            combined += audio
            if i < len(audio_paths) - 1:
                combined += silence
        
        combined.export(str(output_path), format='mp3')
        return output_path


def get_tts_engine(engine_type: str = "edge", **kwargs) -> TTSEngine:
    """
    Factory function to get TTS engine
    
    Args:
        engine_type: "edge", "gtts", or "pyttsx3"
        **kwargs: Engine-specific arguments
    """
    engines = {
        "edge": EdgeTTSEngine,
        "gtts": GTTSEngine,
        "pyttsx3": Pyttsx3Engine
    }
    
    if engine_type not in engines:
        raise ValueError(f"Unknown engine type: {engine_type}. Choose from: {list(engines.keys())}")
    
    return engines[engine_type](**kwargs)
