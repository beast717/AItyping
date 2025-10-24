# Quick Start - Priority 1 Features

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the automation:**
```bash
python automation.py
```

## Feature Activation

### Enable All Priority 1 Features
When you first run the script:
1. Choose Menu Option **#8** (Save preferences)
2. Answer the prompts:
   - Enable global hotkeys? **y**
   - Enable clipboard auto-suggest? **y**
3. Save as profile name: **default**

## Quick Examples

### 🔄 Save & Restore Context
```
1. Navigate to any form website
2. Fill out half the form
3. Menu #11 → Save context
4. Close browser (#15)
5. Restart automation
6. Resume? (y) → Restore context? (y)
7. ✅ Everything restored!
```

### 📚 Use Templates
```
1. Navigate to login page
2. Menu #12 (Use template)
3. Select: login
4. Enter username when prompted
5. Enter password when prompted
6. ✅ Auto-logs in!
```

### ⌨️ Global Hotkeys
```
1. Menu #14 → Enable hotkeys
2. Browse websites normally
3. Press Ctrl+Shift+R (from anywhere!)
4. Actions are now being recorded
5. Press Ctrl+Shift+R again to stop
6. Menu #6 → Save session
```

## Tips

- **Templates with clipboard:** Copy your email/password first, template will offer to paste
- **Context auto-save:** The script asks before closing if you want to save context
- **Hotkeys anywhere:** Works even when VS Code, browser, or other apps are active
- **Form fields cached:** All input values automatically saved with context

## Troubleshooting

**Hotkeys not working?**
```bash
pip install pynput
# Then Menu #14 to enable
```

**Context not restoring?**
- Make sure you save context (Menu #11) before closing
- Check that form fields haven't changed (same page structure needed)

**Template not finding fields?**
- Templates use fuzzy matching (searches by label, name, placeholder)
- Try using the generic "form_fill" template for custom forms

Enjoy the automation! 🚀
