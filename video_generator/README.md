# Video Generator

Tự động tạo video demo chuyên nghiệp với lồng tiếng TTS (Text-to-Speech) từ VIDEO_SCRIPT.md.

## 🎬 Tính năng

- **TTS Narration**: Hỗ trợ nhiều engine TTS (Edge TTS, gTTS, pyttsx3)
- **Professional Slides**: Tự động tạo slide chuyên nghiệp với animation
- **Terminal Simulation**: Mô phỏng terminal với hiệu ứng typing
- **Multi-section Video**: Chia video theo các phần trong script
- **Customizable**: Dễ dàng tùy chỉnh màu sắc, font, timing

## 📦 Cài đặt

### 1. Cài đặt dependencies

```bash
# Cài đặt Python packages
pip install -r video_generator/requirements.txt

# QUAN TRỌNG: Cần cài FFmpeg
# Windows (dùng Chocolatey):
choco install ffmpeg

# Hoặc tải từ: https://ffmpeg.org/download.html
# Thêm vào PATH sau khi cài
```

### 2. Kiểm tra cài đặt

```bash
# Kiểm tra FFmpeg
ffmpeg -version

# Kiểm tra Python packages
python -c "from moviepy import VideoFileClip; print('MoviePy OK')"
python -c "import edge_tts; print('Edge TTS OK')"
```

## 🚀 Sử dụng

### Tạo video đầy đủ

```bash
# Chạy từ thư mục gốc của project
python -m video_generator.video_generator

# Hoặc với các tùy chọn
python -m video_generator.video_generator --output my_demo.mp4 --tts-engine edge
```

### Chỉ tạo audio narration

```bash
python -m video_generator.video_generator --narration-only
```

### Tùy chọn command line

```
--output, -o       : Tên file output (default: demo_video.mp4)
--output-dir, -d   : Thư mục output (default: output)
--tts-engine, -t   : Engine TTS: edge, gtts, pyttsx3 (default: edge)
--width, -W        : Chiều rộng video (default: 1920)
--height, -H       : Chiều cao video (default: 1080)
--fps              : Frames per second (default: 30)
--narration-only   : Chỉ tạo file audio
```

## 🎨 Cấu trúc Project

```
video_generator/
├── __init__.py           # Package init
├── config.py             # Cấu hình video và sections
├── tts_engine.py         # TTS engines (Edge, gTTS, pyttsx3)
├── visual_components.py  # Tạo slides và visual elements
├── terminal_recorder.py  # Mô phỏng terminal animations
├── video_generator.py    # Main generator script
├── requirements.txt      # Python dependencies
└── README.md            # Documentation
```

## 🎙️ TTS Engines

### Edge TTS (Khuyến nghị)
- Chất lượng cao nhất
- Nhiều giọng đọc chuyên nghiệp
- Miễn phí, cần internet
- Voice: `en-US-DavisNeural` (professional male)

### gTTS (Google TTS)
- Chất lượng tốt
- Miễn phí, cần internet
- Dễ sử dụng

### pyttsx3
- Hoạt động offline
- Chất lượng thấp hơn
- Tốc độ nhanh

## 🎨 Tùy chỉnh

### Thay đổi màu sắc

Chỉnh sửa trong `config.py`:

```python
@dataclass
class VideoConfig:
    # Color scheme
    background_color: str = "#0a0a0f"   # Nền
    primary_color: str = "#00d4aa"       # Màu chính (teal)
    secondary_color: str = "#7c3aed"     # Màu phụ (purple)
    text_color: str = "#ffffff"          # Chữ
    highlight_color: str = "#fbbf24"     # Highlight (amber)
```

### Thay đổi nội dung narration

Chỉnh sửa `VIDEO_SECTIONS` trong `config.py`:

```python
Section(
    id="intro",
    title="Problem & Business Value",
    start_time=0.0,
    duration=30.0,
    narration="Your narration text here...",
    visuals=["title_slide", "problem_stats"]
)
```

### Thay đổi demo sequences

Chỉnh sửa `DEMO_SEQUENCES` trong `terminal_recorder.py`:

```python
DEMO_SEQUENCES = {
    "order_status": [
        ChatMessage(
            user_message="Where is my order?",
            bot_response="Your order is shipped...",
            intent="ORDER_STATUS",
            tools_used=["get_order_details"],
            processing_time=0.45
        ),
    ],
}
```

## 📝 Output

Sau khi chạy, video sẽ được lưu tại:

```
output/
├── demo_video.mp4        # Video hoàn chỉnh
└── audio/
    ├── intro_narration.mp3
    ├── architecture_narration.mp3
    ├── demo_order_narration.mp3
    └── ...
```

## ⚠️ Troubleshooting

### FFmpeg not found
```bash
# Kiểm tra FFmpeg đã cài chưa
ffmpeg -version

# Windows: Thêm FFmpeg vào PATH
# Hoặc cài lại: choco install ffmpeg
```

### Font errors
```bash
# Linux: Cài fonts
sudo apt install fonts-dejavu-core fonts-liberation

# Windows: Fonts Arial/Consolas có sẵn
```

### Edge TTS connection error
```bash
# Kiểm tra internet connection
# Hoặc dùng engine khác
python -m video_generator.video_generator --tts-engine gtts
```

### Memory issues với video dài
```python
# Giảm FPS hoặc resolution
python -m video_generator.video_generator --fps 24 --width 1280 --height 720
```

## 📊 Video Structure

Video được chia thành các section theo VIDEO_SCRIPT.md:

| Section | Duration | Content |
|---------|----------|---------|
| Intro | ~30s | Problem & Business Value |
| Architecture | ~45s | System Architecture Diagram |
| Demo 1 | ~30s | Order Status Query |
| Demo 2 | ~30s | Refund Follow-up |
| Demo 3 | ~25s | Security Block |
| Demo 4 | ~15s | Suspended Account |
| Demo 5 | ~20s | Human Escalation |
| Tests | ~55s | Security & Evaluation |
| Conclusion | ~35s | Summary & Future Work |

**Total: ~4:45** (under 5 minutes target)

## 🔧 Advanced Usage

### Custom TTS Voice

```python
from video_generator.tts_engine import EdgeTTSEngine

# Sử dụng giọng khác
engine = EdgeTTSEngine(
    voice="en-GB-RyanNeural",  # British male
    rate="-10%",               # Slower
    pitch="+5Hz"               # Higher pitch
)
```

### Programmatic Usage

```python
from pathlib import Path
from video_generator.video_generator import DemoVideoGenerator
from video_generator.config import VideoConfig

# Custom config
config = VideoConfig(
    width=1280,
    height=720,
    fps=24,
    primary_color="#ff6b6b"
)

# Generate
generator = DemoVideoGenerator(
    config=config,
    output_dir=Path("my_output"),
    tts_engine="edge"
)

generator.generate_full_video("my_custom_video.mp4")
```

## 📜 License

MIT License - Sử dụng tự do cho mục đích cá nhân và thương mại.
