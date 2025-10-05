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

### 🧠 Intelligent Automation (NEW!)
- **Smart Retry**: Automatically retries failed actions with exponential backoff (configurable 1-10 attempts)
- **Auto-wait for elements**: Waits for elements to be visible and stable before interacting
- **Error recovery**: Detects and handles common errors (timeout, element not found, stale elements)
- **Success verification**: Verifies that actions completed successfully (text entered, elements clicked)
- **Helpful error messages**: Clear descriptions of what went wrong and how to fix it
- **Configurable settings**: Customize max retries, retry delay, and auto-wait timeout

### ✨ Seamless Workflow (NEWEST!)
- **📋 Clipboard Integration**: Automatically detects clipboard content and offers to paste when filling fields
- **🔍 Auto-scan Pages**: Automatically scans page elements after navigating to a new URL
- **🔖 Session Resume**: Remembers your last visited URL and offers to resume where you left off
- **⚡ Quick Start**: Jump right back into your work without manual scanning

### 🔍 Selector Alternatives (NEW!)
- **Find by Text**: Click buttons or links by their visible text (e.g., "Submit", "Login", "Next")
- **Find by Label**: Type in inputs by their label or placeholder text (e.g., "Email", "Password")
- **CSS Selectors**: Use powerful CSS selectors for precise element targeting
- **XPath Support**: Advanced XPath queries for complex element finding
- **Smart Fallback**: Helpful error messages if elements can't be found
- **No Index Needed**: Find elements without memorizing numerical indices

## How to Use the New Features

### 📋 Clipboard Integration
1. Copy any text to your clipboard (Ctrl+C)
2. When filling an input/textarea, the script will detect your clipboard
3. It will ask: "📋 Clipboard contains: 'your text...' Use it? (y/n)"
4. Press 'y' to paste instantly, or 'n' to type manually
5. Works with all text input operations (fill, type, batch)

### 🔍 Auto-Scan After Navigation
1. Navigate to any website (Menu option 1)
2. The page automatically scans for elements when loaded
3. No need to manually select "Scan page elements"
4. You can immediately interact with elements
5. Toggle this feature on/off in preferences (Menu option 8)

### 🔖 Session Resume
1. On startup, if you visited a URL in your last session, you'll see:
   "🔖 Resume last session? (https://example.com) (y/n)"
2. Press 'y' to instantly navigate to that page with auto-scan
3. Press 'n' to start fresh
4. Your last URL is saved automatically in preferences

## Intelligent Automation

### 🔍 Selector Alternatives - Easy Element Finding

Instead of using numerical indices, you can now find elements in multiple intuitive ways:

#### Option 11: Click Element by Text
```
Example: Click the "Submit" button
- Enter text: Submit
- Element type: button (or 'any' to search all elements)
- Works with partial matches and case-insensitive
```

**Use cases:**
- Click "Login", "Sign Up", "Next", "Previous" buttons
- Click "Learn More", "Read More" links
- No need to remember which index number

#### Option 12: Type in Input by Label/Placeholder
```
Example: Fill the email field
- Enter label: Email
- The script finds the input with label or placeholder "Email"
- Supports clipboard paste
```

**Use cases:**
- Fill "Username", "Email", "Password" fields by name
- Find "Search" box without scanning
- Works with form labels and placeholders

#### Option 13: Find by CSS Selector or XPath
```
CSS Examples:
- #submit-btn (element with id="submit-btn")
- .login-form input (input inside class="login-form")
- button[type="submit"] (submit buttons)

XPath Examples:
- //button[@id="submit"]
- //input[@placeholder="Email"]
- //a[contains(text(), "Click here")]
```

**Use cases:**
- Precise targeting when multiple similar elements exist
- Dynamic pages where indices change
- Complex element hierarchies

#### Why Use Selectors Instead of Indices?

**Before (Index-based):**
```
1. Scan page
2. Remember button [5] is the Submit button
3. If page changes, index might be different
4. Need to re-scan and find the new index
```

**After (Text/Selector-based):**
```
1. Just click element with text "Submit"
2. Works every time, even if page changes
3. More readable and maintainable
4. No scanning required
```

### Real-World Examples

#### Example 1: Login to a Website
```
Old way (by index):
1. Scan page
2. Fill input [0] with "user@example.com"
3. Fill input [1] with "password123"
4. Click button [2]

New way (by selector):
1. Type in "Email" → user@example.com
2. Type in "Password" → password123
3. Click "Login"
```

#### Example 2: Submit a Form
```
Without selectors:
1. Navigate to form
2. Scan (remember indices)
3. Fill input [0], [1], [2]...
4. Click button [5]

With selectors:
1. Navigate to form (auto-scans)
2. Type in "Name" → John Doe
3. Type in "Email" → john@example.com
4. Click "Submit"
```

#### Example 3: Dynamic Content
```
Problem: A page adds/removes elements, changing indices

Solution with CSS:
- Use selector: button.submit-btn
- Or find by text: "Submit Form"
- Always works, regardless of index changes
```

## Intelligent Automation Features

#### How It Works:
When you click a button, fill a form, or interact with any element, the script will:
1. **Wait** for the element to be ready (visible and stable)
2. **Scroll** the element into view if needed
3. **Try** to perform the action
4. **Verify** the action succeeded (for form fills)
5. **Retry** automatically if it fails (with increasing delays)
6. **Report** exactly what happened with helpful error messages

#### Configuration Options:
- `max_retries`: How many times to retry failed actions (default: 3)
- `retry_delay`: Initial delay between retries in seconds (default: 1.0s, uses exponential backoff)
- `auto_wait_timeout`: Maximum time to wait for elements in milliseconds (default: 30000ms)
- `verify_actions`: Whether to verify actions succeeded (default: enabled)

### Session Management
- **Recording mode**: Record your actions as you interact with elements
- **Session replay**: Save and load sessions to repeat workflows
- **JSON storage**: Sessions saved in `sessions/` folder
- **Auto-load preferences**: Default preferences automatically loaded on startup

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