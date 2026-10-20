# Use Cases — PyImage

Real-world scenarios where PyImage shines. Each walkthrough shows the exact commands and prompt to use.

## 📋 Table of Contents

- [Burst Photo Analysis](#-burst-photo-analysis)
- [Animation Frame QA](#-animation-frame-qa)
- [Product Photo Review](#-product-photo-review)
- [Timelapse Summary](#-timelapse-summary)
- [Document Scanning](#-document-scanning)
- [Design Asset Review](#-design-asset-review)

---

## 📸 Burst Photo Analysis

**Scenario**: You took 50 photos of a sunset in 5 minutes and want to find the best 5.

```bash
cd ~/Pictures/sunset_burst
pyimage
```

When prompted:
- **Grid**: pick 5×2 (10 per frame → 5 frames)
- **Fit mode**: `fill` (no white space)
- **Gap**: `0` (seamless)
- **Label mode**: `auto` → PyImage detects EXIF timestamps and picks `offset` mode

Output: 5 stitched frames, each labeled with `+0s`, `+6s`, `+12s`, `+18s`, `+24s`, etc.

**AI prompt** (drop the 5 frames into ChatGPT/Claude):
> *"I'm sending 5 frames. Each is a 5×2 grid of 10 images, numbered top-left to bottom-right with `+Ns` offset labels showing seconds elapsed from the first shot. Which 5 photos have the best composition, lighting, and exposure? Give me the offset label of each."*

---

## 🎬 Animation Frame QA

**Scenario**: You extracted 150 frames from a GIF and want to check if the animation is smooth.

```bash
cd ~/Downloads/ezgif_frames
pyimage --fit-mode fill --gap 0
```

Output: 15 stitched frames of 10 each, dark cells with white separator lines (smart color picker).

**AI prompt**:
> *"I'm sending 15 frames. Each is a 5×2 grid of 10 sequential animation frames (1-10, 11-20, ..., 141-150). For each batch, check if frame N to N+1 shows a smooth transition. Flag any jumps, dropped frames, or visual glitches with the cell number."*

---

## 🛍️ Product Photo Review

**Scenario**: You have 80 product photos and need to find any with defects before publishing.

```bash
cd ~/Pictures/products
pyimage --fit-mode fill --gap 0 --background white
```

Output: 8 frames of 10 each, tightly packed.

**AI prompt**:
> *"I'm sending 8 frames. Each is a 5×2 grid of 10 product photos, numbered 1-10. For each cell, flag any product with visible defects (scratches, dents, color issues, missing parts). Give me the frame number + cell number for each issue."*

---

## ⏱️ Timelapse Summary

**Scenario**: You have 30 days of daily webcam photos and want to summarize what changed.

```bash
cd ~/Pictures/webcam_daily
pyimage --label-mode time --cols 6 --rows 5
```

Output: 1 frame with all 30 photos, each labeled with absolute time (e.g., `14:30`, `15:30`).

**AI prompt**:
> *"I'm sending 1 frame containing a 6×5 grid of 30 webcam photos taken daily at 14:30. Each cell shows a timestamp label. Summarize the visible changes across the 30-day period, referencing specific timestamps when changes occurred."*

---

## 📄 Document Scanning

**Scenario**: You scanned 20 pages of a handwritten notebook and need transcription.

```bash
cd ~/Pictures/notebook_scans
pyimage --cols 4 --rows 5 --cell-size 1200 1600 --fit-mode fit --gap 10
```

Output: 1 frame with all 20 pages in a 4×5 grid, large cells for readability.

**AI prompt**:
> *"I'm sending 1 frame containing a 4×5 grid of 20 handwritten notebook pages, numbered 1-20. Transcribe each page in order, preserving the original layout. Output as markdown with page breaks."*

---

## 🎨 Design Asset Review

**Scenario**: You have 50 logo variations and want to group similar ones.

```bash
cd ~/Designs/logos
pyimage --no-labels --fit-mode fill --gap 0
```

Output: 5 frames of 10 each, clean montage without numbers (less visual noise).

**AI prompt**:
> *"I'm sending 5 frames. Each is a 5×2 grid of 10 logo variations. Group them by visual similarity (e.g., minimalist, geometric, illustrative). For each group, describe the shared characteristics."*

---

## 💡 Tips for best results

### Choose the right grid for your content

| Content type | Recommended grid | Why |
|---|---|---|
| Square product photos | `5×2` (10 cells) | Standard, balanced aspect |
| Portrait phone photos | `2×5` (10 cells) | Tall frame matches portrait shape |
| Landscape photos | `5×2` or `4×3` | Wide frame matches landscape |
| Document scans | `4×5` with large cells | More space per page for text |
| Dark animation frames | `5×2` + `--background black` | Smart lines auto-pick white |

### Choose the right label mode

| Scenario | Recommended mode |
|---|---|
| Burst photos (< 10 min span) | `offset` (`+0s`, `+10s`, `+1m`) |
| Event photos (> 1 hour span) | `time` (`14:30`, `15:45`) |
| Document scans | `sequence` (`1`, `2`, `3`) |
| Clean montage (no labels) | `none` |
| Let PyImage decide | `auto` (default) |

### Choose the right fit mode

| Content type | Fit mode | Why |
|---|---|---|
| Photos (preserve composition) | `fit` (letterbox) | Don't crop important parts |
| Product photos (fill frame) | `fill` (cover) | Tighter packing, no waste |
| Thumbnails / icons | `stretch` | Distortion doesn't matter |

---

## 🎯 The AI prompt template

When you drop stitched frames into any AI chat, use this template:

> *"I'm sending **N frames**. Each is a **cols × rows** grid of **cells_per_frame** images, **numbered/labeled** [explanation of labels]. **[Your actual question here]**"*

**Examples**:
- *"I'm sending 5 frames. Each is a 5×2 grid of 10 images, numbered 1-10. Which has the best lighting?"*
- *"I'm sending 1 frame. It's a 4×5 grid of 20 pages with timestamps. Transcribe each."*
- *"I'm sending 15 frames of 10 animation frames each. Flag any frame where motion looks janky."*

The clearer your prompt, the better the AI can use the grid structure to give precise answers.
