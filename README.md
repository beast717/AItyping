# Web Automation with Playwright

## What the Script Does

The `automation.py` script provides interactive browser control:

1. Launches Microsoft Edge browser once
2. Gives you a menu to:
   - Navigate to any website you want
   - Get current page information
   - Close browser when you're ready
3. Keeps the browser open until you decide to close it
4. Allows multiple website visits in the same session

## Features

### Profile Support
- **Use existing Edge profile**: Stay logged into all your websites automatically
- **Fresh session option**: Start with a clean browser if needed
- **Automatic detection**: Finds your Edge profile automatically

### Human-Like Typing
- **Variable typing speed**: Random delays between keystrokes (±40% variation)
- **Realistic typos**: Simulates accidental typos based on keyboard layout
- **Smart pauses**: Longer delays after punctuation, spaces, and newlines
- **Thinking pauses**: Random occasional pauses (2% chance for 3-5x longer delay)
- **Customizable settings**: Save your preferred typing speed, typo chance, and pause behavior

### Batch Operations
- **Batch fill inputs**: Select multiple input fields and fill them with different texts in one go
- **Batch type textareas**: Select multiple textareas and type with human-like behavior in all of them
- **Time-saving**: Perfect for forms with multiple rating justifications or comments

### Session Management
- **Recording mode**: Record your actions as you interact with elements
- **Session replay**: Save and load sessions to repeat workflows
- **JSON storage**: Sessions saved in `sessions/` folder

### Stealth Mode
- **Anti-bot detection**: Spoofs navigator.webdriver and other automation indicators
- **Profile persistence**: Uses real Edge profile to avoid detection
- **Human-like behavior**: Random typing variation makes interactions more natural

### Interactive Menu
- **Navigate to websites**: Enter any URL (google.com, youtube.com, etc.)
- **Free browsing**: Use browser normally, script detects navigation
- **Page information**: Get current page title and URL
- **Element scanning**: Find all interactive elements (buttons, forms, links, etc.)
- **Element interaction**: Click buttons, fill forms, select options automatically
- **Browse monitoring**: Real-time detection of page changes
- **Browser control**: Close browser when you want

### When You Run the Script

You'll be asked to choose:
1. **Use existing Edge profile** - Recommended! You'll stay logged into Gmail, Facebook, etc.
2. **Fresh session** - Clean browser with no saved data

### Element Scanning Features

The script can automatically find and interact with:
- **Buttons**: Click any button on the page
- **Links**: Navigate by clicking links  
- **Input fields**: Fill text, email, password fields
- **Forms**: Submit forms and fill out data
- **Dropdowns**: Select options from dropdown menus
- **Checkboxes & Radio buttons**: Check/select options
- **Text areas**: Fill multi-line text fields

### Customization Options

You can modify the script to:
- **Run in headless mode**: Change `headless=False` to `headless=True`
- **Scan specific elements**: Modify `element_types` in `scan_page_elements()`
- **Auto-interact**: Build workflows that interact with elements automatically
- **Set default websites**: Add a startup menu with favorite sites
- **Force profile usage**: Set `use_profile=True` directly in the code