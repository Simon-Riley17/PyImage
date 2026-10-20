<div align="center">

# 🖼️ PyImage

**Stitch 50+ images into grid-style frames for AI chat tools that have upload limits.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](#installation)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## 🐛 Why?

AI chat tools like **ChatGPT, Claude, and Gemini** cap you at ~15 images per conversation. But what if you have 50 vacation photos? 150 animation frames? 900 product shots?

You're stuck — until now. PyImage packs your images into grid-style "frames" (one PNG = 10 images tightly stitched). Drop 5 frames into a chat instead of 50 individual files.

```
50 images  →  5 frames of 10  →  drop 5 PNGs into ChatGPT ✅
150 images →  15 frames of 10 →  drop 15 PNGs into Claude ✅
```

---

## ✨ Features

- **Interactive CLI** — just type `pyimage` in any folder with images
- **Smart grid recommendations** with ASCII visual previews
- **`<` `>` arrow navigation** between 10 layout options
- **EXIF-based smart labels** — `+0s`, `+10s`, `+2m` for bursts; `12:00:10` for events
- **Smart separator lines** — auto-picks white for dark images, black for bright
- **Polished pill labels** — rounded, dark navy + shadow + white text
- **3 fit modes** — `fit` (letterbox), `fill` (crop-to-cover), `stretch`
- **Colorized output** — red prompts, green success, cyan headers
- **`--yes` mode** for non-interactive scripting

---

## 📦 Installation

```bash
git clone https://github.com/Simon-Riley17/PyImage.git
cd PyImage
pip3 install pillow --user
chmod +x pyimage.py
mkdir -p ~/.local/bin
ln -sf "$(pwd)/pyimage.py" ~/.local/bin/pyimage
source ~/.bashrc
```

> **Note**: On Ubuntu/Debian, `~/.local/bin` is already in your PATH. If `pyimage` says "command not found" after install, add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc` and reload.

---

## 🚀 Quick Start

```bash
cd ~/Pictures/my_vacation    # any folder with images
pyimage
```

You'll get an interactive prompt:
1. Pick a grid layout (use `<` `>` to navigate, `Enter` to select)
2. Pick fit mode, gap, background, label mode (just press Enter for smart defaults)
3. Confirm — get stitched PNGs in `./stitched_frames/`

Drag those PNGs into ChatGPT/Claude/Gemini. Done. 🎉

**Non-interactive mode** (for scripts):
```bash
pyimage --yes                                    # all defaults
pyimage --auto-grid --fit-mode fill --gap 0     # tightest packing
pyimage ~/Pictures/batch_001 --yes -o ~/output  # scripted
```

---

## 🎯 Use Cases

| Scenario | Why PyImage? |
|---|---|
| **Burst photos** (50 sunset shots) | AI compares all 50 in one view, with `+Ns` timestamps |
| **Animation QA** (150 frames from GIF) | Check transitions across 15 stitched frames |
| **Product review** (80 product photos) | Find defects in 8 frames instead of 80 attachments |
| **Document scanning** (20 notebook pages) | Transcribe all pages in one AI request |
| **Timelapse review** (30 daily webcam shots) | See all timestamps at a glance |

See [`docs/USE_CASES.md`](docs/USE_CASES.md) for detailed walkthroughs.

---

## ⚙️ CLI Reference

| Flag | Default | Description |
|---|---|---|
| `input_folder` | `.` | Folder with images (positional) |
| `-o, --output` | `./stitched_frames` | Output folder |
| `-n, --batch-size` | `10` | Images per frame |
| `--cols N` | `5` | Grid columns |
| `--rows N` | `2` | Grid rows |
| `--cell-size W H` | `600 600` | Cell size in pixels |
| `--gap N` | `20` | Gap between cells (use `0` for seamless) |
| `--fit-mode` | `fit` | `fit` / `fill` / `stretch` |
| `--label-mode` | `auto` | `auto` / `time` / `offset` / `sequence` / `none` |
| `--line-color` | `smart` | `smart` / `auto` / `white` / `black` |
| `--line-width N` | `3` | Grid line width |
| `--background` | `white` | `white` / `black` |
| `--auto-aspect` | off | Auto-shape cells to match images |
| `--no-labels` | off | Hide numbered labels |
| `--no-title` | off | Hide title strip |
| `--no-color` | off | Disable ANSI colors |
| `--no-grid-lines` | off | Disable separator lines |
| `--yes` | off | Use all defaults, no prompts |

Run `pyimage --help` for the full list.

---

## 🛣️ Roadmap

- [x] Interactive CLI with `<` `>` navigation
- [x] EXIF-based smart labels
- [x] Smart grid separator lines
- [x] Three fit modes
- [ ] Web UI (Next.js + drag-and-drop)
- [ ] Video frame extraction (ffmpeg)
- [ ] Two-tier super-frame stitching for 900+ images
- [ ] Built-in AI analysis (call vision API directly)
- [ ] Windows support
- [ ] PyPI package (`pip install pyimage`)

See the [open issues](https://github.com/Simon-Riley17/PyImage/issues) for the full list.

---

## ❓ FAQ

**Q: Does this work on Windows?**  
A: Not yet — interactive mode uses `termios`. Windows support is on the roadmap. For now, use WSL.

**Q: What image formats are supported?**  
A: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff`. HEIC is planned.

**Q: Will the AI see the labels and separator lines?**  
A: Yes — they're explicitly designed to help AI vision models parse the grid and reference individual cells.

**Q: What if my images have no EXIF?**  
A: Falls back to sequential numbers (1, 2, 3, ...). You can force it with `--label-mode sequence`.

**Q: What's the max image count?**  
A: No hard limit, but for 900+ images you're better off with a batch script. See [`docs/DETAILED_GUIDE.md`](docs/DETAILED_GUIDE.md) for scaling strategies.

---

## 🤝 Contributing

PRs welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

1. Fork → branch → commit → push → PR
2. Follow conventional commits (`feat:`, `fix:`, `docs:`, etc.)
3. Keep PEP 8 style, 100-char line limit

---

## 📄 License

MIT — see [`LICENSE`](LICENSE).

---

## 📚 More docs

- [`docs/DETAILED_GUIDE.md`](docs/DETAILED_GUIDE.md) — full deep-dive (how it works, AI vision insights, scaling strategies)
- [`docs/USE_CASES.md`](docs/USE_CASES.md) — detailed walkthroughs for each use case
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — dev setup + PR process

---

<div align="center">

**Built for everyone who's ever hit "too many attachments" on ChatGPT.** ⭐

</div>