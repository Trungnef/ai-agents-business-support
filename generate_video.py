#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Video Generator Script
Run this to generate the demo video with TTS narration.

Usage:
    python generate_video.py
    python generate_video.py --quick    # Lower quality, faster
    python generate_video.py --audio    # Audio only
"""
import argparse
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    
    try:
        import moviepy
    except ImportError:
        missing.append("moviepy")
    
    try:
        import edge_tts
    except ImportError:
        missing.append("edge-tts")
    
    try:
        from pydub import AudioSegment
    except ImportError:
        missing.append("pydub")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n📦 Install with:")
        print("   pip install -r video_generator/requirements.txt")
        return False
    
    # Check FFmpeg
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found!")
        print("\n📦 Install FFmpeg:")
        print("   Windows: choco install ffmpeg")
        print("   macOS:   brew install ffmpeg")
        print("   Linux:   sudo apt install ffmpeg")
        return False
    
    print("✅ All dependencies installed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate professional demo video with TTS"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick mode: 720p, 24fps"
    )
    parser.add_argument(
        "--audio", "-a",
        action="store_true",
        help="Generate audio narration only"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="demo_video.mp4",
        help="Output filename"
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="en-US-GuyNeural",
        choices=["en-US-GuyNeural", "en-US-AriaNeural", "en-US-JennyNeural", "en-GB-RyanNeural"],
        help="TTS voice selection"
    )
    parser.add_argument(
        "--no-subtitles",
        action="store_true",
        help="Disable burned-in subtitles"
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="Skip dependency check"
    )
    
    args = parser.parse_args()
    
    print("🎬 AI Customer Support Demo Video Generator")
    print("=" * 50)
    
    # Check dependencies
    if not args.skip_check:
        if not check_dependencies():
            sys.exit(1)
    
    # Import after dependency check
    from video_generator.video_generator import DemoVideoGenerator
    from video_generator.config import VideoConfig
    
    # Configure based on mode
    if args.quick:
        print("⚡ Quick mode: 720p @ 24fps")
        config = VideoConfig(
            width=1280,
            height=720,
            fps=24,
            output_filename=args.output
        )
    else:
        print("🎥 Full quality: 1080p @ 30fps")
        config = VideoConfig(
            width=1920,
            height=1080,
            fps=30,
            output_filename=args.output
        )
    
    # Create generator
    generator = DemoVideoGenerator(
        config=config,
        output_dir=Path("output"),
        tts_engine="edge",
        enable_subtitles=not args.no_subtitles
    )
    
    # Generate
    if args.audio:
        print("\n🎙️ Generating audio narration only...")
        generator.generate_all_narration()
        print("\n✅ Audio files saved to output/audio/")
    else:
        print("\n🎬 Generating full video...")
        output_path = generator.generate_full_video()
        print(f"\n✅ Video saved to: {output_path}")
    
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
