<div align="center">

# 🖼️ PyImage

**Stitch 50+ images into grid-style frames so you can drop them into any AI chat without hitting upload limits.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](#installation)
[![Pillow](https://img.shields.io/badge/Pillow-11.0+-green.svg)](https://python-pillow.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [Use Cases](#-use-cases)
- [CLI Reference](#-cli-reference)
- [Examples](#-examples)
- [How AI Models See Your Frames](#-how-ai-models-see-your-frames)
- [Roadmap](#-roadmap)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🐛 The Problem

AI chat tools like **ChatGPT, Claude, and Gemini** limit you to roughly **5–20 images per conversation**. Once you exceed that limit, you hit a wall:

- ❌ "Too many attachments" errors
- ❌ Context dilution — the AI "forgets" earlier images
- ❌ Token-cost explosion — every image burns hundreds to thousands of tokens
- ❌ Slow responses or timeouts on large batches

**What if you have more?**

| Image count | What happens |
|---|---|
| 1–10 | Fine — just attach them all |
| 10–30 | Starts to break — upload limits, slow responses |
| 30–50 | Hard limit on most chat tools |
| **50–150** | **Completely impossible in a single chat** |
| 150–900+ | Forget about it — switch to a script |

So you're stuck. Either:
- Send batches one at a time (lose cross-batch context)
- Write a script (technical barrier)
- Give up

---

## 💡 The Solution

**PyImage** stitches your images into grid-style **frames** — one PNG containing 10, 12, 15, or however many images you want, packed tightly together. The AI sees one image; you've actually sent 10.

```
50 images  →  5 frames of 10 each  →  drop 5 PNGs into ChatGPT
150 images →  15 frames of 10 each →  drop 15 PNGs into ChatGPT  
900 images →  90 frames of 10 each →  batch script (still possible)
```

### Why it works

Modern vision models are **trained on long screenshots, infographics, and charts** — they handle dense single images natively. A long screenshot is essentially a *vertically stitched montage*, and AI handles it perfectly. PyImage uses the same principle: stitch many images into one, send that one image.

---

## ✨ Features

### 🎯 Interactive UX
- **Just type `pyimage`** in any folder — auto-scans for images
- **No flags to memorize** — friendly prompts walk you through every choice
- **Smart defaults** — press Enter through everything and get great results
- **Colorized output** — red prompts, green success, cyan headers (no more white-wall-of-text confusion)

### 🧠 Smart Grid Recommendations
- Analyzes your image count + aspect ratio
- Suggests **10 reasonable grid layouts** (e.g., 5×2, 3×4, 2×5, 6×3...)
- Shows **ASCII visual preview** for each layout — see exactly what you'll get
- One grid per screen with `<` `>` arrow navigation (no crowded tables)
- Multi-frame grids show both **first frame + last frame** previews
- Empty cells marked with `·` so you know what's wasted

### 🕒 EXIF-Based Smart Labels
- Reads **`DateTimeOriginal`** from your photos' EXIF metadata
- Picks the best labeling mode automatically:
  - **`auto`** → smart pick based on time span
  - **`offset`** → `+0s`, `+10s`, `+1m 30s` (perfect for bursts & timelapses)
  - **`time`** → `12:00:10`, `12:01:10` (perfect for events)
  - **`sequence`** → `1`, `2`, `3`, ... (fallback when no EXIF)
  - **`none`** → no labels (cleanest visual)
- Falls back gracefully when no EXIF is available

### 🎨 Polished Visual Output
- **Pill-shaped labels** in bottom-right corner (rounded, dark navy + shadow + white text)
- **Smart grid separator lines** that auto-pick contrast color:
  - Dark images → white lines (visible against dark content)
  - Bright images → black lines
  - Medium brightness → opposite of background
- **Three fit modes**:
  - `fit` → letterbox (preserve aspect, white padding)
  - `fill` → crop-to-cover (NO white space — recommended)
  - `stretch` → distort to fill (for thumbnails)
- **Adaptive font sizing** — labels scale with cell size

### ⚙️ Flexible Configuration
- Configurable grid: `--cols N --rows N`
- Configurable gap: `--gap 0` for seamless, `--gap 20` for classic look
- Configurable cell size: `--cell-size 800 800`
- Configurable line color: `--line-color smart/auto/white/black`
- Configurable line width: `--line-width 3`
- Auto-detects dominant aspect ratio (1:1, 4:3, 16:9, 9:16, custom)
- Supports `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff`

### 🚀 Power-User Modes
- **`pyimage --yes`** → use all defaults (great for scripting)
- **`pyimage --no-color`** → disable ANSI colors (for logging)
- **`pyimage --no-labels`** → clean montage without numbers
- **`pyimage --no-title`** → no title strip on frames
- **`pyimage --no-grid-lines`** → no separator lines
- **`pyimage --label-mode time`** → force timestamp labels
- **`pyimage --fit-mode fill --gap 0`** → tightest possible packing

---

## 📦 Installation

### Prerequisites

- **Python 3.8+**
- **Pillow** (`pip install pillow`)
- Linux or macOS (Windows support planned — see [Roadmap](#-roadmap))

### One-time setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/PyImage.git
cd PyImage

# 2. Install Pillow (only dependency)
pip3 install pillow --user

# 3. Make the script executable
chmod +x pyimage.py

# 4. Create a symlink in your PATH
mkdir -p ~/.local/bin
ln -sf "$(pwd)/pyimage.py" ~/.local/bin/pyimage

# 5. Reload your shell (or restart terminal)
source ~/.bashrc   # or: source ~/.zshrc

# 6. Verify it works
pyimage --help
```

> **Note:** On Ubuntu/Debian, `~/.local/bin` is already in your `PATH` by default. If `pyimage --help` says "command not found", add this to `~/.bashrc`:
> ```bash
> export PATH="$HOME/.local/bin:$PATH"
> ```
> Then run `source ~/.bashrc`.

### Alternative: bash alias (if symlinks confuse you)

```bash
echo "alias pyimage='python3 ~/path/to/PyImage/pyimage.py'" >> ~/.bashrc
source ~/.bashrc
```

---

## 🚀 Quick Start

```bash
# Navigate to a folder with images
cd ~/Pictures/my_vacation

# Just type pyimage
pyimage
```

You'll see:

```
  ╔════════════════════════════════════════════════════════════════╗
  ║              PYTHONIMAGE — Interactive Image Stitcher          ║
  ╚════════════════════════════════════════════════════════════════╝

  Scanning: /home/you/Pictures/my_vacation
  Found 50 images
  Detected dominant aspect: 4:3 (1.333)

  Loaded 10 grid recommendations. Press > or < to navigate, Enter to select.
  (For each grid, you'll see an ASCII preview of the layout.)

  ╔════════════════════════════════════════════════════════════════╗
  ║                GRID 1 OF 10  ·  3 × 6                          ║
  ╚════════════════════════════════════════════════════════════════╝

          ┌────┬────┬────┐
          │   1│   2│   3│
          │   4│   5│   6│      ← First frame (fully filled)
          ...
          └────┴────┴────┘
          ↑ Frame 1 of 3 (full)

          ┌────┬────┬────┐
          │   1│   2│   3│
          │   4│   5│   6│      ← Last frame (partial, with · marks)
          ...
          └────┴────┴────┘
          ↑ Last frame (14/18 cells filled)

          18 cells  ·  3 frame(s)  ·  8% waste  ·  aspect 0.80

  ──────────────────────────────────────────────────────────────────
          < prev      > next      ⏎ select      q quit
```

**Press `>`** to compare layouts side-by-side in your head.
**Press `Enter`** to pick one.
**Walk through fit/gap/label/lines prompts** (smart defaults — just press Enter).
**Get stitched PNGs** in `./stitched_frames/`.

Then drag those PNGs into ChatGPT, Claude, or Gemini. Done. 🎉

---

## 🔧 How It Works

### Step 1: Scan & Analyze
PyImage scans the current folder for images (`.jpg`, `.png`, `.webp`, etc.), sorts them by filename, and samples the first 30 to detect the dominant aspect ratio (1:1, 4:3, 16:9, 9:16, or custom).

### Step 2: Grid Recommendations
For `N` images, PyImage tries every `(rows × cols)` combination and scores each:
- **Waste penalty** (×3) — empty cells are costly
- **Aspect distance** (×1.5) — how close is the frame shape to a square
- **Cell-count preference** (×0.15) — favors 4–15 cells per frame for best AI attention
- **Triviality penalty** (×1.5) — discourages 1×N and N×1 layouts for large N

Top 10 suggestions are shown one at a time with ASCII previews.

### Step 3: Stitching
For each frame, PyImage:
1. Creates a blank canvas of size `(cols × cell_w + gap × (cols+1)) × (rows × cell_h + gap × (rows+1))`
2. Pastes each image into its cell using the chosen fit mode:
   - **`fit`** → letterbox (preserve aspect, pad with background)
   - **`fill`** → center-crop to cover (no padding, may lose edges)
   - **`stretch`** → resize to exact cell size (may distort)
3. Draws smart separator lines at cell boundaries (auto-contrast color)
4. Draws polished pill labels in bottom-right of each cell (dark navy + shadow + white text)

### Step 4: Save
Each frame is saved as `frame_01.png`, `frame_02.png`, etc. in the output folder. PNG is used (not JPEG) to preserve text sharpness for AI vision models.

---

## 🎯 Use Cases

### 📸 Burst Photo Analysis
"I took 50 photos of the sunset in 5 minutes — find the best 5."
```bash
cd ~/Pictures/sunset_burst
pyimage
# Select offset label mode → see +0s, +6s, +12s, ... on each cell
# Drop stitched frames into AI: "Which of these 50 sunset photos has the best composition?"
```

### 🎬 Animation Frame QA
"I extracted 150 frames from a GIF — check if the animation is smooth."
```bash
cd ~/Downloads/ezgif_frames
pyimage
# Get 15 frames of 10 each → drop into AI
# Ask: "Does frame #7 of each batch show a smooth transition from #6?"
```

### 🛍️ Product Photo Review
"I have 80 product photos — find any with defects."
```bash
cd ~/Pictures/products
pyimage --fit-mode fill --gap 0  # tightest packing
# Get 8 frames of 10 each → drop into AI
# Ask: "For each cell, flag any product with visible defects."
```

### 📷 Timelapse Summary
"30 days of webcam photos — what changed?"
```bash
cd ~/Pictures/webcam_daily
pyimage --label-mode time
# Get 3 frames of 10 each with absolute timestamps
# Ask: "Summarize the visible changes across these 30 timestamps."
```

### 🖼️ Document Scanning
"20 pages of a handwritten notebook — transcribe them."
```bash
cd ~/Pictures/notebook_scans
pyimage --cols 4 --rows 5 --cell-size 1000 1000  # large cells for readability
# Get 1 frame with all 20 pages → drop into AI
# Ask: "Transcribe each numbered cell in order."
```

### 🎨 Design Asset Review
"50 logo variations — group similar ones."
```bash
cd ~/Designs/logos
pyimage --no-labels  # clean montage, no numbers
# Get 5 frames of 10 each → drop into AI
# Ask: "Group these logos by visual similarity."
```

---

## 📚 CLI Reference

### Basic usage
```bash
pyimage                    # interactive, uses current folder
pyimage /path/to/images    # interactive, custom folder
pyimage --yes              # use all defaults (no prompts)
```

### All flags

| Flag | Description | Default |
|---|---|---|
| `input_folder` | Folder containing images (positional, optional) | `.` (current dir) |
| `-o, --output` | Output folder for stitched frames | `./stitched_frames` |
| `-n, --batch-size` | Images per frame | `10` |
| `--cols N` | Grid columns | `5` |
| `--rows N` | Grid rows | `2` |
| `--cell-size W H` | Cell size in pixels | `600 600` |
| `--gap N` | Gap between cells in pixels | `20` |
| `--fit-mode` | `fit` / `fill` / `stretch` | `fit` |
| `--auto-aspect` | Auto-shape cells to match images | off |
| `--base-size N` | Base cell dimension for auto-aspect | `600` |
| `--background` | `white` / `black` | `white` |
| `--no-labels` | Hide numbered labels | off |
| `--no-title` | Hide title strip | off |
| `--no-color` | Disable ANSI colors | off |
| `--no-grid-lines` | Disable separator lines | off |
| `--label-mode` | `auto` / `time` / `offset` / `sequence` / `none` | `auto` |
| `--line-color` | `smart` / `auto` / `white` / `black` | `smart` |
| `--line-width N` | Grid line width in pixels | `3` |
| `--prefix NAME` | Output filename prefix | `frame` |
| `--yes` | Use all defaults, no prompts | off |

### Power-user combos

```bash
# Tightest possible packing (no white space at all)
pyimage --auto-grid --fit-mode fill --gap 0

# Auto-detect aspect + smart labels + dark background
pyimage --auto-aspect --label-mode auto --background black

# Scripted batch processing (no prompts)
pyimage ~/Pictures/batch_001 --yes -o ~/output/batch_001
pyimage ~/Pictures/batch_002 --yes -o ~/output/batch_002
pyimage ~/Pictures/batch_003 --yes -o ~/output/batch_003

# Large cells for document readability
pyimage --cols 4 --rows 5 --cell-size 1200 1600 --fit-mode fit --gap 10

# Pure montage, no labels or title (cleanest visual)
pyimage --no-labels --no-title --fit-mode fill --gap 0
```

---

## 🖥️ Examples

### 50 images → 5 frames of 10 (5×2 grid)

```bash
cd ~/Pictures/50_vacation_photos
pyimage --yes
```

Output:
```
./stitched_frames/
├── frame_01.png   (10 images, #1-10)
├── frame_02.png   (10 images, #11-20)
├── frame_03.png   (10 images, #21-30)
├── frame_04.png   (10 images, #31-40)
└── frame_05.png   (10 images, #41-50)
```

Each frame: `3120 × 1340 px`, ~750–900 KB PNG, with numbered pill labels and separator lines.

### 150 animation frames → 15 frames of 10

```bash
cd ~/Downloads/animation_frames
pyimage --fit-mode fill --gap 0 --background black
# 15 frames generated, each packed with 10 dark images tightly
# Smart line color picks white (visible against dark content)
```

### Custom grid: 4×3 with larger cells

```bash
pyimage --cols 4 --rows 3 --cell-size 1000 1000 --fit-mode fill --gap 5
# 12 cells per frame, each cell is 1000×1000 px
# Perfect for high-detail product photos
```

---

## 🤖 How AI Models See Your Frames

When you drop a stitched frame into ChatGPT, Claude, or Gemini, the AI:

1. **Receives a single image** (no upload limit issue)
2. **Parses the grid layout** using its vision encoder
3. **Detects separator lines** (which is why we add them — they make cell boundaries crystal clear)
4. **Reads the pill labels** (numbers, timestamps, or offsets)
5. **Processes each cell** as a distinct sub-image

### The prompt to use

When you drop stitched frames into a chat, use this prompt template:

> *"I'm sending N frames. Each is a `cols × rows` grid of `cells_per_frame` images, numbered 1-N (top-left to bottom-right, restarting each frame). [Your actual question here]"*

Example:
> *"I'm sending 5 frames. Each is a 5×2 grid of 10 images, numbered 1-10. For each cell, flag any photo with motion blur and tell me the cell number."*

### Why this beats sending individual images

| Approach | Images sent | AI attention per image | Cost |
|---|---|---|---|
| 50 individual images | 50 (blocked) | High (but upload limit hit) | $$$ |
| 1 mega-montage of 50 | 1 | Very low (cells too small) | $ |
| **5 stitched frames of 10** | **5** | **High (sweet spot)** | **$$** |

---

## 🗺️ Roadmap

- [x] Interactive CLI with `<` `>` navigation
- [x] EXIF-based smart labels (offset / time / sequence)
- [x] Smart grid separator lines (auto-contrast)
- [x] Three fit modes (fit / fill / stretch)
- [x] Polished pill labels with shadow
- [x] Multi-frame preview (first + last frame)
- [ ] **Web UI** — drag-and-drop web interface built with Next.js
- [ ] **Video frame extraction** — take a video file as input, auto-extract frames with ffmpeg
- [ ] **Two-tier super-frame stitching** — stitch 10→1, then stitch those into super-frames for 900+ images
- [ ] **Built-in AI analysis** — call vision API directly on stitched frames and produce a report
- [ ] **Windows support** — currently Linux/macOS only (needs `msvcrt` for single-key input)
- [ ] **Batch folders** — process multiple folders in one run
- [ ] **Custom label formats** — user-defined label templates
- [ ] **HEIC support** — for iPhone photos

See the [open issues](https://github.com/YOUR_USERNAME/PyImage/issues) for a full list.

---

## ❓ FAQ

**Q: Does this work on Windows?**
A: Not yet. The interactive mode uses `termios` for single-key input, which is Linux/macOS only. Windows support is on the roadmap. For now, Windows users can use WSL.

**Q: What image formats are supported?**
A: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff`. HEIC support is planned.

**Q: What's the maximum number of images PyImage can handle?**
A: There's no hard limit, but for 900+ images you're better off writing a batch script. PyImage will still work — it just produces more frames. See the [Use Cases](#-use-cases) section.

**Q: Do I need to install anything besides PyImage?**
A: Just Pillow (`pip install pillow`). No other dependencies.

**Q: Will the AI see the separator lines and pill labels?**
A: Yes. The separator lines are explicitly designed to help AI vision models parse the grid. The pill labels (numbers, timestamps) are also readable — AI models can reference "image #7" or "the +2m offset image" naturally.

**Q: What if my images don't have EXIF data?**
A: PyImage detects this automatically and falls back to sequential numbering (1, 2, 3, ...). You can also force a label mode with `--label-mode sequence`.

**Q: Can I use this in a script (non-interactive)?**
A: Yes — use `pyimage --yes` to accept all defaults. Combine with `-o` to specify output folder.

**Q: Why PNG and not JPEG for output?**
A: PNG preserves text sharpness (no JPEG compression artifacts around the labels and separator lines), which helps AI vision models read the labels and detect cell boundaries.

**Q: What's the recommended batch size?**
A: 10 per frame is the sweet spot — small enough for AI to give each image full attention, large enough to keep total frame count manageable. For high-detail images (documents, text-heavy), use 6 per frame with larger cells.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---

## 💬 Acknowledgments

- [Pillow](https://python-pillow.org/) — the imaging library that makes this possible
- [piexif](https://github.com/hMatoba/Piexif) — for EXIF metadata handling in tests
- The open-source community for inspiration and feedback

---

## ⭐ Show your support

If PyImage saved you time today, give it a ⭐ on GitHub — it helps others discover it!

[![Star History](https://img.shields.io/github/stars/YOUR_USERNAME/PyImage?style=social)](https://github.com/YOUR_USERNAME/PyImage/stargazers)

---

<div align="center">

**Built with ❤️ for everyone who's ever hit "too many attachments" on ChatGPT.**

</div>
