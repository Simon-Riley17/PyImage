# Contributing to PyImage

First off — **thank you** for taking the time to contribute! 🎉

This document outlines how to contribute to PyImage.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

Be kind. Be respectful. We're all here to build something useful.

---

## Getting Started

### Prerequisites

- Python 3.8+
- Pillow (`pip install pillow`)
- Git

### Setup

```bash
# Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/PyImage.git
cd PyImage

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/PyImage.git

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pillow

# Make the script executable
chmod +x pyimage.py

# Verify it works
python3 pyimage.py --help
```

---

## Development Workflow

1. **Create a branch** for your feature/fix:
   ```bash
   git checkout -b feature/my-new-feature
   # or: fix/bug-description
   ```

2. **Make your changes** — keep commits focused and atomic.

3. **Test your changes**:
   ```bash
   # Test with sample images
   mkdir test_images
   # (drop some test images in)
   python3 pyimage.py test_images --yes

   # Test interactive mode
   python3 pyimage.py test_images
   ```

4. **Commit with a clear message** following conventional commits:
   ```
   feat: add HEIC image format support
   fix: handle edge case when all images are landscape
   docs: improve README installation section
   refactor: extract grid scoring into separate function
   test: add tests for EXIF label generation
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Open a Pull Request** on GitHub.

---

## Coding Standards

- **Python style**: Follow [PEP 8](https://pep8.org/). Use `flake8` or `black` to enforce.
- **Line length**: 100 characters max
- **Imports**: Standard library first, then third-party, then local
- **Comments**: Use docstrings for all functions (Google style preferred)
- **Type hints**: Encouraged for new code
- **Naming**:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- **Error handling**: Use specific exceptions, not bare `except:`
- **No emojis in code** — they're reserved for user-facing output

### Example function docstring

```python
def suggest_grids(n_images, image_aspect=1.0, target=1.0):
    """Suggest reasonable grid configurations for n_images.

    Args:
        n_images: Number of images to arrange.
        image_aspect: Aspect ratio of source images (width/height).
        target: Desired frame aspect ratio (1.0 = square).

    Returns:
        List of dicts sorted by score (best first). Each dict has:
        - rows, cols, cells, n_frames, wasted, frame_aspect, desc, score

    Raises:
        ValueError: If n_images is 0 or negative.
    """
```

---

## Pull Request Process

1. **Update the README** if your change adds new features or changes behavior.
2. **Update the CLI Reference table** in the README if you add/remove/change flags.
3. **Bump version** in `pyimage.py` if appropriate (we use [SemVer](https://semver.org/)).
4. **Test thoroughly** — verify both interactive and `--yes` modes work.
5. **Squash commits** before merging if you have many small "wip" commits.
6. **Write a clear PR description** — what changed, why, how to test.

A maintainer will review your PR within a few days. We may suggest changes — please be patient and responsive.

---

## Reporting Bugs

Bugs are tracked as [GitHub issues](https://github.com/YOUR_USERNAME/PyImage/issues).

**Before creating a bug report**, please search existing issues to avoid duplicates.

When you create a bug report, include:

1. **A clear title** — `"Navigation broken when only 1 grid available"`
2. **What you expected to happen**
3. **What actually happened** (paste the output)
4. **Steps to reproduce**:
   ```bash
   cd /path/to/images
   pyimage
   # Press: > then Enter
   ```
5. **Your environment**:
   - OS: (e.g., Ubuntu 22.04)
   - Python version: `python3 --version`
   - Pillow version: `pip show pillow | grep Version`
   - PyImage version: `pyimage --version` or git commit hash
6. **Screenshots** if applicable

---

## Suggesting Features

Feature suggestions are welcome! Please:

1. Check the [Roadmap](README.md#-roadmap) and existing issues first.
2. Open a new issue with the `enhancement` label.
3. Explain:
   - What problem does this feature solve?
   - How would it work from the user's perspective?
   - Any alternative solutions you've considered?

---

## Areas That Need Help

- 🪟 **Windows support** — needs `msvcrt` for single-key input on Windows
- 🌐 **Web UI** — Next.js app wrapping the Python script
- 🎬 **Video frame extraction** — ffmpeg integration
- 🧪 **Test suite** — currently no automated tests
- 📦 **PyPI package** — make PyImage `pip install`-able
- 🌍 **Internationalization** — translate prompts to other languages

If you'd like to tackle any of these, please open an issue first to discuss the approach.

---

Thank you for contributing! 🙌
