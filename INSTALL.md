# Installation Guide

## Quick Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install msedge
   ```

3. **Run the script:**
   ```bash
   python automation.py
   ```

## Dependencies

- **playwright** (>=1.39.0) - Browser automation
- **pyperclip** (>=1.8.2) - Clipboard integration for seamless copy-paste

## Troubleshooting

### Clipboard not working?
If you see "⚠ pyperclip not installed", install it with:
```bash
pip install pyperclip
```

The script will still work without pyperclip, but clipboard features will be disabled.

### Playwright issues?
If you have issues with Playwright, try:
```bash
pip install playwright==1.39.0
playwright install msedge
```

### Windows-specific
Make sure you're using PowerShell or Command Prompt with admin privileges for installation.

## What's New

### Latest Features (Auto-Scan & Clipboard)
✅ Clipboard integration - Paste directly from clipboard  
✅ Auto-scan pages - No more manual scanning  
✅ Session resume - Pick up where you left off  
✅ Intelligent automation - Smart retries and error handling  

Enjoy seamless web automation! 🚀
