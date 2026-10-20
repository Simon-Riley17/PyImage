#!/usr/bin/env python3
"""
PyImage - Interactive Image Stitcher
=====================================
Stitch 50+ images into grid-style frames so you can drop them into any AI
chat tool (ChatGPT, Claude, Gemini) without hitting upload limits.

Just type `pyimage` in any folder containing images.
The script will:
  1. Auto-detect images in the current folder
  2. Show you grid recommendations with ASCII previews
  3. Let you navigate with < > and pick one with Enter
  4. Ask a few quick questions (with smart defaults)
  5. Stitch and save frames to ./stitched_frames/

INSTALL (one-time setup on Linux):
  chmod +x pyimage.py
  mkdir -p ~/.local/bin
  ln -sf "$(pwd)/pyimage.py" ~/.local/bin/pyimage
  # ~/.local/bin is already in PATH on most Ubuntu/Debian systems.
  # If not, add this line to ~/.bashrc:
  #   export PATH="$HOME/.local/bin:$PATH"
  # Then reload:  source ~/.bashrc

USAGE:
  pyimage                    # interactive, uses current folder
  pyimage /path/to/images    # interactive, uses given folder
  pyimage --yes              # use all defaults (no prompts)

For full docs, see: https://github.com/Simon-Riley17/PyImage
"""

import argparse
import os
import sys
import termios
import tty
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# --------------------------------------------------------------------------- #
# Color support (ANSI escape codes - works on all modern Linux terminals)
# --------------------------------------------------------------------------- #
class C:
    """ANSI color codes. Use via:  print(C.RED + 'text' + C.RESET)"""
    RED       = '\033[91m'   # prompts, headers (read carefully)
    GREEN     = '\033[92m'   # success, results, completed work
    YELLOW    = '\033[93m'   # warnings, defaults, hints
    BLUE      = '\033[94m'   # info lines (scanning, found images)
    MAGENTA   = '\033[95m'   # numbers, values
    CYAN      = '\033[96m'   # section dividers, banners
    WHITE     = '\033[97m'   # plain body text
    BOLD      = '\033[1m'
    DIM       = '\033[2m'
    RESET     = '\033[0m'


# Global flag - set to True to disable colors (e.g. --no-color flag)
_no_color = False


def paint(text, *colors):
    """Wrap text in colors. Returns plain text if --no-color is set."""
    if _no_color or not colors:
        return text
    return ''.join(colors) + text + C.RESET


def disable_colors():
    global _no_color
    _no_color = True


# --------------------------------------------------------------------------- #
# Terminal input (single-key press without Enter, for < > navigation)
# --------------------------------------------------------------------------- #
def read_key():
    """Read a single keypress on Linux/Mac without requiring Enter.
    Handles both 'ESC [ X' (normal mode) and 'ESC O X' (application mode)
    arrow key sequences — different terminals send different ones.
    Returns: 'LEFT', 'RIGHT', 'UP', 'DOWN', 'ENTER', 'ESC', 'q', etc.
    Falls back to line input if stdin is not a TTY (e.g. piped).
    """
    if not sys.stdin.isatty():
        # Piped input - read a line
        try:
            line = input().strip().lower()
            if line in ('<', 'left', 'prev', 'p', 'b', 'h'):
                return 'LEFT'
            if line in ('>', 'r', 'right', 'next', 'n', ' ', 'space', 'f', 'd', 'l'):
                return 'RIGHT'
            if line in ('q', 'quit', 'exit'):
                return 'q'
            return 'ENTER'
        except EOFError:
            return 'ENTER'
    try:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
    except (termios.error, ValueError, AttributeError):
        try:
            line = input().strip().lower()
            if line in ('<', 'left', 'prev', 'p', 'b', 'h'):
                return 'LEFT'
            if line in ('>', 'r', 'right', 'next', 'n', ' ', 'space', 'f', 'd', 'l'):
                return 'RIGHT'
            if line == 'q':
                return 'q'
            return 'ENTER'
        except EOFError:
            return 'ENTER'
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # ESC sequence (arrow keys, etc.)
            # Read next char with a small buffer for terminals that send ESC alone
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                # Normal mode: ESC [ X
                ch3 = sys.stdin.read(1)
                # Handle 'ESC [ ~' sequences (Home, End, PageUp, PageDown)
                if ch3 == '~':
                    return 'ESC'
                return {'D': 'LEFT', 'C': 'RIGHT', 'A': 'UP', 'B': 'DOWN'}.get(ch3, 'ESC')
            elif ch2 == 'O':
                # Application mode: ESC O X (some terminals use this)
                ch3 = sys.stdin.read(1)
                return {'D': 'LEFT', 'C': 'RIGHT', 'A': 'UP', 'B': 'DOWN'}.get(ch3, 'ESC')
            elif ch2 in ('\r', '\n'):
                return 'ENTER'
            else:
                # Alt+key or just ESC alone
                return 'ESC'
        if ch in ('\r', '\n'):
            return 'ENTER'
        if ch == ' ':
            return 'SPACE'
        if ch == '\x03':  # Ctrl-C
            raise KeyboardInterrupt
        if ch == '\x7f':  # Backspace/Delete
            return 'BACKSPACE'
        return ch.lower() if ch.isalpha() else ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear_screen():
    """Clear the terminal screen reliably.
    Uses os.system('clear') as primary method (works on all Linux/Mac terminals),
    falls back to ANSI escape sequences if os.system is unavailable.
    """
    if not sys.stdout.isatty():
        return
    # Primary: use the system's clear command (most reliable)
    try:
        import os
        os.system('clear 2>/dev/null')
        return
    except Exception:
        pass
    # Fallback: ANSI escape sequences (clear screen + scrollback + move home)
    try:
        sys.stdout.write('\033[3J\033[H\033[2J')
        sys.stdout.flush()
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# ASCII grid visualization
# --------------------------------------------------------------------------- #
def render_grid_ascii(cols, rows, n_filled, max_width=68, max_height=20):
    """Render an ASCII art of a grid layout.
    Cells with index <= n_filled show their number, others show '·' (empty).
    Truncates columns/rows if the layout is too large for the terminal.
    """
    total_cells = cols * rows
    # Min cell width = enough for the biggest number + padding
    min_cell_w = max(3, len(str(total_cells)) + 2)

    # Determine how many cols we can actually display
    full_w = cols * (min_cell_w + 1) + 1
    if full_w <= max_width:
        cols_to_display = cols
        cell_w = min_cell_w
        trunc_cols = False
    else:
        # Shrink cell width, then if still too wide, truncate columns
        cell_w = max(2, (max_width - 1) // cols - 1)
        if cell_w < 2:
            # Even minimum doesn't fit - truncate columns
            cell_w = min_cell_w
            cols_to_display = max(2, (max_width - 3) // (min_cell_w + 1))
            trunc_cols = True
        else:
            cols_to_display = cols
            trunc_cols = False

    # Determine how many rows to display
    # Each row takes 2 lines (content + separator). +1 for top border.
    max_rows_display = max(2, (max_height - 1) // 2)
    if rows > max_rows_display:
        rows_to_display = max_rows_display
        trunc_rows = True
    else:
        rows_to_display = rows
        trunc_rows = False

    lines = []

    def hline(left, mid, right, fill='─'):
        parts = [fill * cell_w for _ in range(cols_to_display)]
        s = left + mid.join(parts) + right
        if trunc_cols:
            s = s[:-1] + '┄' + right
        return s

    # Top border
    lines.append(hline('┌', '┬', '┐'))

    for r in range(rows_to_display):
        # Cell content for this row
        cells = []
        for c in range(cols_to_display):
            num = r * cols + c + 1
            if num <= n_filled:
                s = str(num).rjust(cell_w)
            else:
                s = ('·'.rjust(cell_w - 1)).rjust(cell_w)
            cells.append('│' + s)
        if trunc_cols:
            cells.append('│┄')
        else:
            cells.append('│')
        lines.append(''.join(cells))

        # Row separator (between rows, not after last)
        if r < rows_to_display - 1:
            lines.append(hline('├', '┼', '┤'))

    # Bottom border or truncation indicator
    if trunc_rows:
        bot = hline('┆', '┆', '┆', fill='▔')
        lines.append(bot)
        lines.append(f'    ⋮ {rows} rows total, showing first {rows_to_display}')
    else:
        lines.append(hline('└', '┴', '┘'))

    if trunc_cols:
        lines.append(f'    ⋯ {cols} columns total, showing first {cols_to_display}')

    return '\n'.join(lines)


def interactive_grid_picker(options, n_images):
    """Show grid options ONE AT A TIME with ASCII visuals.
    Clean, spacious layout: banner → ASCII grid → 1-line info → navigation.
    Navigate with < > (or arrow keys), select with Enter, quit with q.
    """
    if not options:
        return None
    current_idx = 0
    while True:
        opt = options[current_idx]
        cols, rows = opt['cols'], opt['rows']
        cells_per_frame = cols * rows

        # Clear screen for a clean slate (uses os.system('clear') for reliability)
        clear_screen()

        # ── Banner (grid number + dimensions in one line) ──
        print()
        print('  ' + paint('╔════════════════════════════════════════════════════════════════╗', C.CYAN, C.BOLD))
        header = f'GRID {current_idx + 1} OF {len(options)}  ·  {cols} × {rows}'
        print('  ' + paint('║', C.CYAN, C.BOLD) +
              paint(header.center(66), C.CYAN, C.BOLD) +
              paint('║', C.CYAN, C.BOLD))
        print('  ' + paint('╚════════════════════════════════════════════════════════════════╝', C.CYAN, C.BOLD))
        print()
        print()

        # ── ASCII grid visuals (first frame + last frame preview for multi-frame grids) ──
        if opt['n_frames'] > 1:
            # Multi-frame: ALWAYS show first frame + last frame (even if last is also full)
            first_grid = render_grid_ascii(cols, rows, cells_per_frame)
            for line in first_grid.split('\n'):
                print('          ' + paint(line, C.WHITE))
            print()
            print('          ' + paint(f'↑ Frame 1 of {opt["n_frames"]} (full)', C.BLUE))
            print()
            print()

            # Last frame preview - always show for multi-frame grids
            leftover = n_images - (opt['n_frames'] - 1) * cells_per_frame
            if leftover == 0:
                # Exact fit - last frame is also full
                leftover = cells_per_frame
                last_caption = paint(f'↑ Last frame (also full, {cells_per_frame}/{cells_per_frame} cells filled)',
                                      C.YELLOW)
            else:
                # Partial last frame
                last_caption = paint(f'↑ Last frame ({leftover}/{cells_per_frame} cells filled)',
                                      C.YELLOW)
            last_grid = render_grid_ascii(cols, rows, leftover)
            for line in last_grid.split('\n'):
                print('          ' + paint(line, C.DIM))
            print()
            print(last_caption)
        else:
            # Single frame — show it (may have empty cells marked with ·)
            ascii_grid = render_grid_ascii(cols, rows, n_images)
            for line in ascii_grid.split('\n'):
                print('          ' + paint(line, C.WHITE))
            print()
            leftover = 0  # no multi-frame concept

        print()
        print()

        # ── One-line summary (replaces the 5-line stats block) ──
        # Format: "10 cells · 1 frame · 0% waste · aspect 2.500 · [EXACT]"
        summary_parts = [
            paint(f'{cells_per_frame}', C.MAGENTA, C.BOLD) + paint(' cells', C.WHITE),
            paint(f'{opt["n_frames"]}', C.MAGENTA, C.BOLD) + paint(' frame(s)', C.WHITE),
        ]
        if opt['wasted_ratio'] > 0:
            wc = C.YELLOW if opt['wasted_ratio'] <= 0.15 else C.RED
            summary_parts.append(paint(f'{opt["wasted_ratio"]*100:.0f}%', wc) + paint(' waste', C.WHITE))
        else:
            summary_parts.append(paint('0%', C.GREEN) + paint(' waste', C.WHITE))
        summary_parts.append(paint(f'aspect {opt["frame_aspect"]:.2f}', C.MAGENTA))
        if opt['is_exact']:
            summary_parts.append(paint('[EXACT FIT]', C.GREEN, C.BOLD))

        print('          ' + '  ·  '.join(summary_parts))

        print()
        print()
        print()

        # ── Navigation footer (one clean line) ──
        print('  ' + paint('─' * 66, C.DIM))
        print()
        nav = []
        if current_idx > 0:
            nav.append(paint('<', C.YELLOW, C.BOLD) + paint(' prev', C.WHITE))
        else:
            nav.append(paint('<', C.DIM) + paint(' prev', C.DIM))
        if current_idx < len(options) - 1:
            nav.append(paint('>', C.YELLOW, C.BOLD) + paint(' next', C.WHITE))
        else:
            nav.append(paint('>', C.DIM) + paint(' next', C.DIM))
        nav.append(paint('⏎', C.GREEN, C.BOLD) + paint(' select', C.WHITE))
        nav.append(paint('q', C.RED) + paint(' quit', C.WHITE))
        print('          ' + '      '.join(nav))
        print()

        # Read a key
        key = read_key()

        if key in ('q', 'ESC'):
            print()
            print('  ' + paint('Cancelled.', C.YELLOW))
            sys.exit(0)
        elif key in ('ENTER', 'SPACE'):
            print()
            print('  ' + paint(f'✓ Selected: {cols} × {rows}', C.GREEN, C.BOLD))
            print()
            return opt
        elif key in ('RIGHT', '>', 'n', 'd', 'f', 'l'):
            # Advance to next grid
            current_idx = min(current_idx + 1, len(options) - 1)
        elif key in ('LEFT', '<', 'p', 'b', 'h'):
            # Go to previous grid
            current_idx = max(current_idx - 1, 0)
        elif key == 'BACKSPACE':
            current_idx = max(current_idx - 1, 0)
        # Otherwise (unknown key), ignore and refresh


# --------------------------------------------------------------------------- #
# Loading & detection (carried over from v3)
# --------------------------------------------------------------------------- #
def load_images(input_folder, extensions=('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff')):
    folder = Path(input_folder)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {input_folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {input_folder}")
    found = []
    for ext in extensions:
        found.extend(folder.glob(f'*{ext}'))
        found.extend(folder.glob(f'*{ext.upper()}'))
    seen = set()
    unique = []
    for p in found:
        key = str(p.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    unique.sort(key=lambda p: p.name.lower())
    if not unique:
        raise ValueError(f"No images found in: {input_folder}")
    return unique


def detect_dominant_aspect(image_paths, sample_size=30):
    from collections import Counter
    counts = Counter()
    sample = image_paths[:sample_size]
    for p in sample:
        try:
            with Image.open(p) as img:
                ratio = img.width / img.height
                if 0.74 <= ratio <= 0.76:
                    bucket = '4:3-portrait'
                elif 1.32 <= ratio <= 1.35:
                    bucket = '4:3'
                elif 0.55 <= ratio <= 0.57:
                    bucket = '9:16'
                elif 1.77 <= ratio <= 1.79:
                    bucket = '16:9'
                elif 0.99 <= ratio <= 1.01:
                    bucket = '1:1'
                else:
                    bucket = f'custom:{ratio:.3f}'
                counts[bucket] += 1
        except Exception:
            continue
    if not counts:
        return None, 1.0
    best = counts.most_common(1)[0][0]
    if best.startswith('custom:'):
        return best, float(best.split(':')[1])
    ratios = {
        '1:1': 1.0, '4:3': 4/3, '4:3-portrait': 3/4,
        '16:9': 16/9, '9:16': 9/16,
    }
    return best, ratios.get(best, 1.0)


# --------------------------------------------------------------------------- #
# Image fit modes
# --------------------------------------------------------------------------- #
def fit_letterbox(img, cell_size, bg=(255, 255, 255)):
    cw, ch = cell_size
    img = img.convert('RGB')
    r = img.width / img.height
    cr = cw / ch
    if r > cr:
        nw, nh = cw, max(1, int(cw / r))
    else:
        nh, nw = ch, max(1, int(ch / r))
    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGB', cell_size, bg)
    canvas.paste(resized, ((cw - nw) // 2, (ch - nh) // 2))
    return canvas


def fit_cover(img, cell_size):
    cw, ch = cell_size
    img = img.convert('RGB')
    r = img.width / img.height
    cr = cw / ch
    if r > cr:
        nh = img.height
        nw = int(img.height * cr)
        left = (img.width - nw) // 2
        img = img.crop((left, 0, left + nw, nh))
    else:
        nw = img.width
        nh = int(img.width / cr)
        top = (img.height - nh) // 2
        img = img.crop((0, top, nw, top + nh))
    return img.resize(cell_size, Image.LANCZOS)


def fit_stretch(img, cell_size):
    return img.convert('RGB').resize(cell_size, Image.LANCZOS)


def fit_image(img, cell_size, mode, bg):
    if mode == 'fill':
        return fit_cover(img, cell_size)
    if mode == 'stretch':
        return fit_stretch(img, cell_size)
    return fit_letterbox(img, cell_size, bg)


def cell_size_from_aspect(aspect_str, base=600):
    sizes = {
        '1:1':           (base, base),
        '4:3':           (base, int(base * 0.75)),
        '4:3-portrait':  (int(base * 0.75), base),
        '16:9':          (base, int(base * 9 / 16)),
        '9:16':          (int(base * 9 / 16), base),
    }
    if aspect_str in sizes:
        return sizes[aspect_str]
    if aspect_str and aspect_str.startswith('custom:'):
        r = float(aspect_str.split(':')[1])
        if r >= 1:
            return (base, int(base / r))
        return (int(base * r), base)
    return (base, base)


# --------------------------------------------------------------------------- #
# EXIF timestamp extraction + smart labeling
# --------------------------------------------------------------------------- #
def get_exif_datetime(image_path):
    """Extract DateTimeOriginal from an image's EXIF metadata.
    Returns a datetime object, or None if not available.
    """
    from datetime import datetime
    try:
        with Image.open(image_path) as img:
            exif_data = None
            try:
                exif_data = img._getexif()
            except (AttributeError, KeyError, TypeError):
                exif_data = None
            if not exif_data:
                return None
            # Try DateTimeOriginal (tag 36867) first, then DateTime (tag 306)
            dt_str = exif_data.get(36867) or exif_data.get(306)
            if not dt_str:
                return None
            # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
    except Exception:
        return None


def make_smart_labels(image_paths, mode='auto'):
    """Generate smart labels for each image based on its EXIF timestamp.
    Modes:
      auto     - pick best format based on data (time if EXIF present, else sequence)
      time     - absolute time "12:00:10"
      offset   - relative offset from first image "+0s", "+60s", "+2m"
      sequence - simple numbers "1", "2", "3"
      none     - empty labels
    Returns: (labels list, mode_used, has_timestamps)
    """
    from datetime import datetime, timedelta
    n = len(image_paths)

    if mode == 'none':
        return [''] * n, 'none', False

    if mode == 'sequence':
        return [str(i + 1) for i in range(n)], 'sequence', False

    # Extract timestamps
    timestamps = [get_exif_datetime(p) for p in image_paths]
    has_any = any(t is not None for t in timestamps)
    has_all = all(t is not None for t in timestamps)

    # If no timestamps at all, fall back to sequence
    if not has_any:
        return [str(i + 1) for i in range(n)], 'sequence', False

    if mode == 'time':
        labels = [t.strftime('%H:%M:%S') if t else '?' for t in timestamps]
        return labels, 'time', True

    if mode == 'offset':
        if not has_all:
            # Can't compute offsets without all timestamps; fall back to time
            labels = [t.strftime('%H:%M:%S') if t else '?' for t in timestamps]
            return labels, 'time', True
        ref = timestamps[0]
        labels = []
        for t in timestamps:
            diff = int((t - ref).total_seconds())
            if diff < 0:
                diff = abs(diff)
                prefix = '-'
            else:
                prefix = '+'
            if diff < 60:
                labels.append(f'{prefix}{diff}s')
            elif diff < 3600:
                m, s = divmod(diff, 60)
                labels.append(f'{prefix}{m}m' + (f'{s}s' if s else ''))
            else:
                h, rem = divmod(diff, 3600)
                m, _ = divmod(rem, 60)
                labels.append(f'{prefix}{h}h{m}m')
        return labels, 'offset', True

    # mode == 'auto' — pick the best format based on the data
    if has_all:
        ref = timestamps[0]
        # Compute total span
        max_t = max(timestamps)
        total_span = (max_t - ref).total_seconds()
        if total_span < 600:  # under 10 minutes: use offsets
            return make_smart_labels(image_paths, mode='offset')
        elif total_span < 3600:
            # Under 1 hour: use MM:SS format
            labels = [t.strftime('%M:%S') for t in timestamps]
            return labels, 'time', True
        else:
            # Over 1 hour: use HH:MM:SS
            labels = [t.strftime('%H:%M:%S') for t in timestamps]
            return labels, 'time', True
    else:
        # Some images have EXIF, some don't — use absolute time, ? for missing
        labels = [t.strftime('%H:%M:%S') if t else '?' for t in timestamps]
        return labels, 'time', True


# --------------------------------------------------------------------------- #
# Grid recommender (simplified)
# --------------------------------------------------------------------------- #
def suggest_grids(n, image_aspect=1.0, target=1.0, max_waste=0.25, max_options=10):
    options = []
    for rows in range(1, n + 1):
        for cols in range(1, n + 1):
            cells = rows * cols
            if cells > n * 2 and cells > n + 5:
                continue
            if rows > 1 and cols > 1 and cells > n * 1.5:
                continue
            if cells >= n:
                n_frames = 1
                wasted = cells - n
                wr = wasted / n if n else 0
                if wr > max_waste and wasted > 0:
                    continue
                desc = f'{cols}x{rows}, single frame' if wasted == 0 else \
                       f'{cols}x{rows}, 1 frame, {wasted} empty'
            else:
                full = n // cells
                leftover = n % cells
                n_frames = full + (1 if leftover else 0)
                if leftover:
                    wasted = cells - leftover
                    wr = wasted / n
                    if wr > max_waste:
                        continue
                    desc = f'{cols}x{rows}, {full} full + 1 with {leftover}/{cells}'
                else:
                    wasted = 0
                    wr = 0
                    desc = f'{cols}x{rows}, {n_frames} full frames'
            frame_aspect = (cols / rows) * image_aspect
            aspect_dist = abs(frame_aspect - target) / max(target, 0.01)
            trivial = 1.5 if ((rows == 1 or cols == 1) and n > 5) else 0
            # v3.1: prefer cells_per_frame in the 4-15 range for better AI attention
            cells_per_frame = cells if cells <= n else (n - full * cells)
            # actually cells IS the per-frame cell count
            cell_pref = 0
            if cells > 20:
                cell_pref = (cells - 20) * 0.15   # heavy penalty for huge batches
            elif cells < 4:
                cell_pref = (4 - cells) * 0.5
            score = wr * 3 + aspect_dist * 1.5 + trivial + (n_frames - 1) * 0.3 + cell_pref
            options.append({
                'rows': rows, 'cols': cols, 'cells': cells, 'n_frames': n_frames,
                'wasted': wasted, 'wasted_ratio': wr, 'frame_aspect': frame_aspect,
                'desc': desc, 'score': score,
                'is_exact': (wasted == 0 and n_frames == 1),
            })
    # Sort by score only (cell-pref penalty pushes huge grids down)
    options.sort(key=lambda x: x['score'])
    return options[:max_options]


# --------------------------------------------------------------------------- #
# Stitching
# --------------------------------------------------------------------------- #
def get_font(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
              '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf']:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def stitch_frame(image_paths, output_path, grid_cols, grid_rows, cell_size,
                 gap, fit_mode, frame_title, start_idx, labels, bg,
                 show_grid_lines=True, line_color=(30, 30, 30), line_width=3):
    """Stitch images into a grid. `labels` is a list of label strings (one per image)."""
    n_cells = grid_cols * grid_rows
    if len(image_paths) > n_cells:
        raise ValueError(f"Too many images for grid")
    cw, ch = cell_size
    th = 70 if frame_title else 0
    fw = grid_cols * cw + (grid_cols + 1) * gap
    fh = grid_rows * ch + (grid_rows + 1) * gap + th
    frame = Image.new('RGB', (fw, fh), bg)
    draw = ImageDraw.Draw(frame)
    if frame_title:
        draw.rectangle([0, 0, fw, th], fill=(30, 41, 59))
        draw.text((gap, 20), frame_title, fill=(255, 255, 255), font=get_font(26))

    # Adaptive font size based on cell size (smaller cells = smaller labels)
    label_font_size = max(16, min(28, cw // 30))
    lf = get_font(label_font_size)

    for i, p in enumerate(image_paths):
        try:
            img = Image.open(p)
        except Exception as e:
            print(f"  [!] Could not open {p.name}: {e}")
            continue
        cell = fit_image(img, cell_size, fit_mode, bg)
        col = i % grid_cols
        row = i // grid_cols
        x = gap + col * (cw + gap)
        y = th + gap + row * (ch + gap)
        frame.paste(cell, (x, y))

        # Polished pill label (bottom-right corner)
        label = labels[start_idx - 1 + i] if labels and (start_idx - 1 + i) < len(labels) else ''
        if label:
            draw_label_pill(draw, label, x, y, cw, ch, lf)

    # Smart grid separator lines — drawn AFTER all cells pasted so they sit on top
    if show_grid_lines:
        draw_separator_lines(draw, grid_cols, grid_rows, cw, ch, gap,
                             th, line_color, line_width)

    frame.save(output_path, 'PNG', optimize=True)
    return fw, fh


def draw_label_pill(draw, label, cell_x, cell_y, cell_w, cell_h, font):
    """Draw a polished rounded-pill label in the bottom-right of a cell.
    Dark semi-opaque background + white bold text + subtle border.
    """
    # Measure text
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x = 14
    pad_y = 7
    pill_w = text_w + 2 * pad_x
    pill_h = text_h + 2 * pad_y
    margin = 8

    # Position in bottom-right of cell
    pill_x = cell_x + cell_w - pill_w - margin
    pill_y = cell_y + cell_h - pill_h - margin

    # Soft shadow (offset down-right)
    shadow_offset = 2
    draw.rounded_rectangle(
        [pill_x + shadow_offset, pill_y + shadow_offset,
         pill_x + pill_w + shadow_offset, pill_y + pill_h + shadow_offset],
        radius=pill_h // 2,
        fill=(0, 0, 0),  # solid shadow
    )

    # Main pill — dark navy background
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=pill_h // 2,
        fill=(15, 23, 42),  # slate-900
        outline=(255, 255, 255),  # subtle white outline
        width=1,
    )

    # Text — centered in pill
    text_x = pill_x + pad_x - bbox[0]
    text_y = pill_y + pad_y - bbox[1]
    draw.text((text_x, text_y), label, fill=(255, 255, 255), font=font)


# --------------------------------------------------------------------------- #
# Smart grid separator lines
# --------------------------------------------------------------------------- #
def sample_avg_brightness(image_paths, sample_size=5):
    """Sample average brightness of the first N images (0-255)."""
    if not image_paths:
        return 128
    sample = image_paths[:sample_size]
    brightness_sum = 0
    count = 0
    for p in sample:
        try:
            with Image.open(p) as img:
                # Resize small for speed, convert to grayscale
                thumb = img.convert('L').resize((50, 50))
                # Average pixel value
                pixels = list(thumb.getdata())
                brightness_sum += sum(pixels) / len(pixels)
                count += 1
        except Exception:
            continue
    if count == 0:
        return 128
    return brightness_sum / count


def pick_line_color(line_color_arg, bg_color, image_paths):
    """Decide the grid line color based on user choice or smart sampling.
    Returns RGB tuple.
    """
    if line_color_arg == 'white':
        return (255, 255, 255)
    if line_color_arg == 'black':
        return (0, 0, 0)
    # 'auto' — pick opposite of background
    if line_color_arg == 'auto_bg':
        if sum(bg_color) >= 384:  # white background → dark lines
            return (30, 30, 30)
        else:
            return (240, 240, 240)
    # 'smart' (default) — sample image brightness, use opposite
    avg = sample_avg_brightness(image_paths)
    if avg < 100:        # cells are dark → use white lines (visible against dark content)
        return (255, 255, 255)
    elif avg > 180:      # cells are bright → use dark lines
        return (20, 20, 20)
    else:                # medium — pick opposite of background
        if sum(bg_color) >= 384:
            return (30, 30, 30)
        return (240, 240, 240)


def draw_separator_lines(draw, grid_cols, grid_rows, cell_w, cell_h, gap,
                          title_height, line_color, line_width):
    """Draw visible separator lines between adjacent cells.
    Lines run along the boundary between cells, so they work even with gap=0.
    """
    half = line_width // 2
    # Top of grid content area
    top_y = title_height + gap
    # Total grid content height (rows of cells + gaps between them)
    grid_h = grid_rows * cell_h + (grid_rows - 1) * gap
    bottom_y = top_y + grid_h - 1

    # Vertical separator lines (between columns)
    for c in range(1, grid_cols):
        # Boundary between col c-1 and col c
        right_of_prev = gap + (c - 1) * (cell_w + gap) + cell_w
        left_of_curr = gap + c * (cell_w + gap)
        boundary_x = (right_of_prev + left_of_curr) // 2
        # Draw filled rectangle as a line
        draw.rectangle(
            [boundary_x - half, top_y, boundary_x + half, bottom_y],
            fill=line_color,
        )

    # Horizontal separator lines (between rows)
    left_x = gap
    grid_w = grid_cols * cell_w + (grid_cols - 1) * gap
    right_x = left_x + grid_w - 1
    for r in range(1, grid_rows):
        bottom_of_prev = title_height + gap + (r - 1) * (cell_h + gap) + cell_h
        top_of_curr = title_height + gap + r * (cell_h + gap)
        boundary_y = (bottom_of_prev + top_of_curr) // 2
        draw.rectangle(
            [left_x, boundary_y - half, right_x, boundary_y + half],
            fill=line_color,
        )


# --------------------------------------------------------------------------- #
# Interactive prompts
# --------------------------------------------------------------------------- #
def banner():
    print()
    print('  ' + paint('╔══════════════════════════════════════════════════════════════╗', C.CYAN, C.BOLD))
    print('  ' + paint('║', C.CYAN, C.BOLD) +
          paint('              PYIMAGE — Interactive Image Stitcher                ', C.CYAN, C.BOLD) +
          paint('║', C.CYAN, C.BOLD))
    print('  ' + paint('╚══════════════════════════════════════════════════════════════╝', C.CYAN, C.BOLD))
    print()


def prompt(label, default=None, choices=None):
    """Interactive prompt with default and optional choice list."""
    if choices:
        hint = '/'.join(str(c) for c in choices)
        if default is not None:
            hint = f'{hint} [default: {default}]'
        s = input('  ' + paint(label, C.RED, C.BOLD) +
                  paint(f' ({hint}): ', C.YELLOW)).strip()
    else:
        if default is not None:
            s = input('  ' + paint(label, C.RED, C.BOLD) +
                      paint(f' [default: {default}]: ', C.YELLOW)).strip()
        else:
            s = input('  ' + paint(label, C.RED, C.BOLD) + ': ').strip()
    if not s and default is not None:
        return default
    return s


def prompt_menu(label, options, default_idx=0):
    """Show a numbered menu and return chosen option."""
    print('\n  ' + paint(label, C.RED, C.BOLD))
    for i, opt in enumerate(options, 1):
        if i == default_idx + 1:
            marker = paint('  <- default', C.YELLOW, C.DIM)
        else:
            marker = ''
        print('    ' + paint(f'{i})', C.MAGENTA, C.BOLD) + ' ' + paint(opt, C.WHITE) + marker)
    while True:
        s = input('  ' + paint('Pick', C.RED, C.BOLD) +
                  paint(f' (1-{len(options)}) [{default_idx + 1}]: ', C.YELLOW)).strip()
        if not s:
            return options[default_idx]
        try:
            idx = int(s) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print('  ' + paint('[!] Invalid choice, try again.', C.RED, C.BOLD))


# --------------------------------------------------------------------------- #
# Main interactive flow
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description='PyImage - interactive image stitcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('input_folder', nargs='?', default='.',
                        help='Folder with images (default: current directory)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output folder (default: ./stitched_frames in current dir)')
    parser.add_argument('--yes', action='store_true',
                        help='Use all defaults, no prompts')
    parser.add_argument('--no-labels', action='store_true')
    parser.add_argument('--no-title', action='store_true')
    parser.add_argument('--no-color', action='store_true',
                        help='Disable colored output (for terminals without ANSI support)')
    parser.add_argument('--label-mode', choices=['auto', 'time', 'offset', 'sequence', 'none'],
                        default='auto',
                        help='Label mode: auto/time/offset/sequence/none (default: auto)')
    parser.add_argument('--no-grid-lines', action='store_true',
                        help='Disable separator lines between cells')
    parser.add_argument('--line-color', choices=['smart', 'auto', 'white', 'black'],
                        default='smart',
                        help='Grid line color: smart (auto-pick contrast), auto (opposite of bg), white, black (default: smart)')
    parser.add_argument('--line-width', type=int, default=3,
                        help='Grid line width in pixels (default: 3)')
    args = parser.parse_args()

    if args.no_color:
        disable_colors()

    banner()

    # 1) Scan folder
    folder = Path(args.input_folder).resolve()
    print('  ' + paint('Scanning: ', C.BLUE) + paint(str(folder), C.WHITE))
    try:
        images = load_images(folder)
    except Exception as e:
        print('  ' + paint(f'[ERROR] {e}', C.RED, C.BOLD))
        sys.exit(1)
    n_images = len(images)
    print('  ' + paint('Found ', C.BLUE) +
          paint(f'{n_images}', C.MAGENTA, C.BOLD) +
          paint(' images', C.BLUE))

    # 2) Detect aspect
    aspect_str, aspect_num = detect_dominant_aspect(images)
    if aspect_str:
        print('  ' + paint('Detected dominant aspect: ', C.BLUE) +
              paint(f'{aspect_str} ({aspect_num:.3f})', C.MAGENTA))
    else:
        aspect_str = '1:1'
        aspect_num = 1.0

    # 3) Show grid recommendations
    options = suggest_grids(n_images, image_aspect=aspect_num, target=1.0)
    if not options:
        print('  ' + paint('[ERROR] No suitable grid found.', C.RED, C.BOLD))
        sys.exit(1)

    # 4) Pick grid — interactive navigator with ASCII visuals (or auto for --yes)
    if args.yes:
        best = options[0]
        print('  ' + paint('[yes-mode] ', C.YELLOW) +
              paint('Using best: ', C.BLUE) +
              paint(f'{best["cols"]}x{best["rows"]}', C.MAGENTA, C.BOLD))
    else:
        print()
        print('  ' + paint('Loaded ', C.BLUE) +
              paint(f'{len(options)}', C.MAGENTA, C.BOLD) +
              paint(' grid recommendations. Press ', C.BLUE) +
              paint('> ', C.YELLOW, C.BOLD) +
              paint('or ', C.BLUE) +
              paint('< ', C.YELLOW, C.BOLD) +
              paint('to navigate, ', C.BLUE) +
              paint('Enter', C.GREEN, C.BOLD) +
              paint(' to select.', C.BLUE))
        print('  ' + paint('(For each grid, you\'ll see an ASCII preview of the layout.)', C.DIM))
        best = interactive_grid_picker(options, n_images)

    cols, rows = best['cols'], best['rows']
    batch_size = cols * rows

    # 5) Fit mode
    if args.yes:
        fit_mode = 'fill'
    else:
        fit_mode = prompt_menu(
            'How should each image fill its cell?',
            [
                'fill     — crop to cover, NO white space (recommended)',
                'fit      — letterbox, preserve aspect (white padding)',
                'stretch — distort to fill (only for thumbnails)',
            ],
            default_idx=0,
        ).split()[0]

    # 6) Gap
    if args.yes:
        gap = 0
    else:
        gap_choice = prompt_menu(
            'Gap between cells?',
            ['0 pixels  — seamless (recommended)', '10 pixels — small gap',
             '20 pixels — classic look', '40 pixels — large gap'],
            default_idx=0,
        )
        gap = int(gap_choice.split()[0])

    # 7) Background color
    if args.yes:
        bg_choice = 'white' if aspect_num >= 0.8 else 'black'
    else:
        bg_choice = prompt_menu(
            'Background color for padding (only matters in fit mode)?',
            ['white — light padding', 'black — dark padding (for dark images)'],
            default_idx=0,
        ).split()[0]
    bg_color = (255, 255, 255) if bg_choice == 'white' else (0, 0, 0)

    # 8) Smart labeling — use EXIF timestamps when available
    if args.no_labels:
        label_mode = 'none'
    elif args.label_mode != 'auto':
        label_mode = args.label_mode
    elif args.yes:
        label_mode = 'auto'
    else:
        # Check if any EXIF timestamps exist before asking
        sample_ts = [get_exif_datetime(p) for p in images[:5]]
        has_exif = any(t is not None for t in sample_ts)
        if has_exif:
            label_choice = prompt_menu(
                'How should each image be labeled?',
                ['auto      — smart pick (offsets if burst, time otherwise) [recommended]',
                 'offset    — relative: +0s, +60s, +2m  (great for bursts/timelapses)',
                 'time      — absolute time: 12:00:10, 12:01:10  (great for events)',
                 'sequence — plain numbers: 1, 2, 3, ...',
                 'none     — no labels (cleanest visual)'],
                default_idx=0,
            )
            label_mode = label_choice.split()[0]
        else:
            print('  ' + paint('No EXIF timestamps detected in your images — using sequential labels.',
                               C.YELLOW))
            label_choice = prompt_menu(
                'How should each image be labeled?',
                ['sequence — plain numbers: 1, 2, 3, ...  [recommended]',
                 'none     — no labels (cleanest visual)'],
                default_idx=0,
            )
            label_mode = label_choice.split()[0]

    # Generate labels for all images
    labels, mode_used, has_ts = make_smart_labels(images, mode=label_mode)
    if has_ts:
        print('  ' + paint(f'Label mode: ', C.BLUE) +
              paint(f'{mode_used}', C.MAGENTA, C.BOLD) +
              paint(f'  (sample: {labels[0]}, {labels[1] if len(labels) > 1 else "..."}, ...)',
                    C.YELLOW))
    else:
        print('  ' + paint(f'Label mode: ', C.BLUE) +
              paint(f'{mode_used}', C.MAGENTA, C.BOLD))

    # 8b) Grid separator lines
    if args.no_grid_lines:
        show_grid_lines = False
        line_color_choice = 'none'
        line_color = (0, 0, 0)
    elif args.line_color != 'smart' or args.yes:
        show_grid_lines = True
        line_color_choice = args.line_color
        line_color = pick_line_color(line_color_choice, bg_color, images)
    else:
        # Interactive: sample brightness first to show smart suggestion
        avg_brightness = sample_avg_brightness(images)
        if avg_brightness < 100:
            suggestion = 'white (cells look dark — white lines will be visible)'
        elif avg_brightness > 180:
            suggestion = 'black (cells look bright — black lines will be visible)'
        else:
            suggestion = f'{"black" if sum(bg_color) >= 384 else "white"} (medium brightness, opposite of bg)'

        line_choice = prompt_menu(
            f'Grid separator lines? (auto-suggest: {suggestion})',
            ['yes — smart color (auto-pick best contrast)  [recommended]',
             'yes — white lines',
             'yes — black lines',
             'no  — no separator lines'],
            default_idx=0,
        )
        if line_choice.startswith('no'):
            show_grid_lines = False
            line_color = (0, 0, 0)
        elif 'white' in line_choice:
            show_grid_lines = True
            line_color = (255, 255, 255)
        elif 'black' in line_choice:
            show_grid_lines = True
            line_color = (0, 0, 0)
        else:  # smart
            show_grid_lines = True
            line_color = pick_line_color('smart', bg_color, images)

    # 9) Output folder
    if args.output:
        out_folder = Path(args.output)
    elif args.yes:
        out_folder = Path('./stitched_frames')
    else:
        out = prompt('Output folder', default='./stitched_frames')
        out_folder = Path(out)
    out_folder = out_folder.resolve()
    out_folder.mkdir(parents=True, exist_ok=True)

    # 10) Cell size — auto-shape to match images
    cell_size = cell_size_from_aspect(aspect_str, base=600)

    # 10) Show plan & confirm
    print()
    print('  ' + paint('┌────────────────────────────────────────────────────────────────────┐', C.CYAN, C.BOLD))
    print('  ' + paint('│', C.CYAN, C.BOLD) +
          paint('                         STITCH PLAN                                ', C.CYAN, C.BOLD) +
          paint('│', C.CYAN, C.BOLD))
    print('  ' + paint('└────────────────────────────────────────────────────────────────────┘', C.CYAN, C.BOLD))
    print('    ' + paint('Images:        ', C.RED) + paint(f'{n_images}', C.MAGENTA, C.BOLD))
    print('    ' + paint('Grid:           ', C.RED) +
          paint(f'{cols}x{rows} ', C.MAGENTA, C.BOLD) +
          paint(f'({batch_size} per frame, {best["n_frames"]} frame(s))', C.WHITE))
    print('    ' + paint('Fit mode:       ', C.RED) + paint(f'{fit_mode}', C.MAGENTA))
    print('    ' + paint('Gap:            ', C.RED) + paint(f'{gap} px', C.MAGENTA))
    print('    ' + paint('Cell size:      ', C.RED) +
          paint(f'{cell_size[0]}x{cell_size[1]} px', C.MAGENTA))
    print('    ' + paint('Background:     ', C.RED) + paint(f'{bg_choice}', C.MAGENTA))
    print('    ' + paint('Output folder:  ', C.RED) + paint(f'{out_folder}', C.MAGENTA))

    if not args.yes:
        confirm = prompt('\nRun with these settings? (y/n)', default='y')
        if confirm.lower() not in ('y', 'yes', ''):
            print('  ' + paint('Aborted.', C.YELLOW))
            return

    # 11) Run it
    print()
    batches = [images[i:i + batch_size] for i in range(0, n_images, batch_size)]
    print('  ' + paint(f'Stitching {len(batches)} frame(s)...\n', C.BLUE))
    total_idx = 1
    for i, batch in enumerate(batches, 1):
        end_idx = total_idx + len(batch) - 1
        title = None if args.no_title else (
            f'Frame {i} of {len(batches)}  |  {len(batch)} images  |  #{total_idx}-{end_idx}'
        )
        out_path = out_folder / f'frame_{i:02d}.png'
        print('  ' + paint(f'[Frame {i}] ', C.YELLOW, C.BOLD) +
              paint(f'{len(batch)} images (#{total_idx}-{end_idx})', C.WHITE))
        fw, fh = stitch_frame(
            batch, out_path, cols, rows, cell_size, gap, fit_mode,
            title, total_idx, labels, bg_color,
            show_grid_lines=show_grid_lines,
            line_color=line_color,
            line_width=args.line_width,
        )
        print('    ' + paint('-> ', C.GREEN) +
              paint(f'{out_path.name} ', C.GREEN, C.BOLD) +
              paint(f'({fw}x{fh})', C.WHITE))
        total_idx += len(batch)

    print()
    print('  ' + paint('┌────────────────────────────────────────────────────────────────────┐', C.GREEN, C.BOLD))
    print('  ' + paint('│', C.GREEN, C.BOLD) +
          paint('                           DONE!                                    ', C.GREEN, C.BOLD) +
          paint('│', C.GREEN, C.BOLD))
    print('  ' + paint('└────────────────────────────────────────────────────────────────────┘', C.GREEN, C.BOLD))
    print('    ' + paint(f'{len(batches)} frame(s) saved to: ', C.GREEN) +
          paint(f'{out_folder}', C.MAGENTA, C.BOLD))
    print()
    print('  ' + paint('Next steps:', C.CYAN, C.BOLD))
    print('    1. ' + paint('Open the PNG files in the output folder', C.WHITE))
    print('    2. ' + paint('Drag them into your AI chat tool (ChatGPT, Claude, Gemini)', C.WHITE))
    print('    3. ' + paint(f'Prompt: "Sending {len(batches)} frames. Each is a {cols}x{rows} grid, '
                          f'numbered 1-{batch_size} (top-left to bottom-right). [Your question]"', C.WHITE))
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n  ' + paint('Aborted.', C.YELLOW))
        sys.exit(130)
    except Exception as e:
        print('\n  ' + paint(f'[ERROR] {e}', C.RED, C.BOLD), file=sys.stderr)
        sys.exit(1)
