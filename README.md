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

### 📋 Smart Form Auto-Fill (NEWEST!)
- **Auto-detect Forms**: Automatically finds all forms on the page with their fields
- **Intelligent Field Detection**: Identifies fields by label, placeholder, name, or aria-label
- **One-Command Fill**: Fill entire forms with a single menu option
- **Clipboard Integration**: Use clipboard for each field during form filling
- **Field Summary**: Shows all fields with labels before filling
- **Skip Optional Fields**: Press Enter to skip fields you don't want to fill
- **Works Without Forms**: Even detects individual fields when no `<form>` tag exists
- **Type Support**: Handles text, email, password, textarea, select dropdowns, and more
- **Auto-Click Buttons**: After filling, automatically detects and offers to click Next/Submit/Continue buttons
- **Multi-Step Support**: Automatically chains through multi-page forms
- **Smart Button Detection**: Prioritizes common buttons (Next, Submit, Continue)
- **Flexible Selection**: Click buttons by text or index number

### 🚀 Priority 1 Features - Maximum Productivity! (BRAND NEW!)
- **🔄 Full Context Resume**: Save and restore scroll position AND form field values when resuming sessions
  - No more losing your work when you close the browser
  - Automatically saves your progress on any page
  - Restore exactly where you left off with one command
- **⌨️ Global Hotkeys**: Control automation from anywhere on your computer
  - `Ctrl+Shift+R`: Toggle recording on/off instantly
  - `Ctrl+Shift+P`: Replay last saved session
  - Works even when browser is in background
- **📚 Session Templates**: Pre-built workflows for common tasks
  - Login template (username + password + submit)
  - Search template (query + search button)
  - Contact form template (name + email + message)
  - Generic form fill (auto-detects all fields)
  - Use variables like `{{username}}` for dynamic values
- **💡 Smart Clipboard**: Enhanced clipboard integration
  - Auto-suggests clipboard content when filling forms
  - Intelligently matches clipboard to field context
  - One-click paste for maximum speed

### 👁️ Watch & Learn - AI Pattern Detection! (NEWEST!)
- **Automatic Pattern Detection**: Watches your actions and detects when you repeat things
  - Detects sequences of 2-5 actions that you repeat
  - Triggers after 2 repetitions automatically
  - Real-time notification when pattern is found
- **One-Click Automation**: Instantly convert patterns into reusable workflows
  - "I noticed you repeated this 3 times, automate it?" prompt
  - Creates session files automatically
  - Save as templates for future use
- **Smart Matching**: Intelligently compares actions ignoring variable data
  - Recognizes same field even if values differ
  - Matches clicks by element position
  - Tracks navigation patterns
- **Zero Configuration**: Works automatically in the background
  - Enabled by default (toggle with Menu #15)
  - No setup required
  - Learns from your browsing naturally
- **Pattern Management**: View and manage all detected patterns
  - Menu #16 to see all detected patterns
  - Create automation from any pattern
  - Track repetition count and timestamps

### 🧠 Intelligent Workflow Learning! (BRAND NEW!)
- **Automatic Error Handling**: Adds retry logic and error recovery to all sessions
  - Configurable retry attempts (1-10 times)
  - Exponential backoff between retries
  - Smart error recovery strategies
  - Continue, stop, or skip on error
- **Conditional Logic**: If/else branches based on page state
  - Check if element exists before action
  - Verify page state before continuing
  - Multi-path workflows (try alternatives)
- **Loop Support**: Repeat actions until condition met
  - Pagination automation (click "Next" until button disappears)
  - Process multiple items automatically
  - Safety limits to prevent infinite loops
- **Workflow Analysis**: AI analyzes your workflow and suggests improvements
  - Detects login flows and adds session checks
  - Identifies form patterns and adds validation
  - Recognizes pagination and suggests loops
  - Multi-page navigation with breadcrumb tracking
- **Smart Workflow Builder**: Interactive builder with AI assistance
  - Choose workflow type (linear, conditional, loop, multi-path)
  - AI adds appropriate error handling automatically
  - Guided configuration for complex workflows
- **Enhanced Session Format**: Sessions now include metadata and logic
  - Backward compatible with old sessions
  - Error handling configuration per action
  - Conditional execution rules
  - Fallback actions for failures

**Example:**
```
You do this manually:
1. Click "Next Page" button
2. Fill search field with query
3. Click "Search" button

After doing it twice, you'll see:
🔍 PATTERN DETECTED! (Watch & Learn)
I noticed you've repeated this sequence 2 times
Would you like me to automate this for you?
→ Press 'y' and never do it manually again!
```

**Smart Enhancement Example:**
```
When saving a session:
🧠 Add intelligent error handling and logic? (y)

🧠 Analyzing Workflow...
💡 Found 2 improvement opportunities:
1. Login Flow (confidence: 90%)
   💡 Add session persistence check to skip login if already logged in
2. Multi-Field Form (confidence: 85%)
   💡 Add validation checks after each field to ensure values are accepted

🚀 Apply intelligent enhancements? (y)
✓ Enhanced 5 actions with intelligent logic
  • Auto-retry on failures
  • Smart error recovery
  • Conditional checks
```

### 🤖 Gemini AI Auto-Rating! (BRAND NEW!)
Automatically rate model responses using Google's Gemini AI - no more manual evaluation!

**Two Rating Modes:**

#### 🔢 Simple Rating Click (Menu #18)
- **Quick Rating**: Click rating buttons 1, 2, or 3 with one command
- **Smart Detection**: Automatically finds and clicks rating buttons
- **Multiple Methods**: Tries role-based, text-based, and selector-based clicking
- **Instant Feedback**: Confirms button click immediately
- **Zero Setup**: Works out of the box, no API key needed

**Usage:**
```bash
1. Navigate to rating page
2. Select Menu #18 (Simple rating click)
3. Enter rating: 1 (Major Issues), 2 (Minor Issues), or 3 (No Issues)
4. Done! Button clicked automatically
```

#### 🤖 Auto-Rate with Gemini AI (Menu #19)
- **Full Automation**: Extract response text → Send to Gemini → Get rating → Auto-click button
- **AI Evaluation**: Gemini analyzes response quality across multiple dimensions
  - Localization: Language appropriateness
  - Instruction Following: Requirement compliance
  - Truthfulness: Information accuracy
  - Overall Quality: Grammar, coherence, helpfulness
- **Category Support**: Rate multiple categories automatically
  - Auto-detect categories from page
  - Rate all at once or choose specific category
  - Intelligent category matching
- **Smart Extraction**: Automatically finds and extracts model response text
- **One-Click Rating**: Complete evaluation + click in seconds
- **Reasoning Included**: See why Gemini gave each rating

**Setup (One-Time):**
```bash
1. Get API key from: https://makersuite.google.com/app/apikey
2. Install dependency: pip install google-generativeai
3. Run Menu #19 first time - you'll be prompted for API key
4. API key saved to preferences automatically
```

**Full Workflow:**
```bash
# One-time setup
pip install google-generativeai

# Using Gemini Auto-Rating
1. Navigate to rating page with model response visible
2. Select Menu #19 (Auto-rate with Gemini AI)
3. Enter API key (first time only)
4. Choose: Rate all categories OR specific category
5. Gemini extracts response, analyzes, and returns rating
6. Preview: "✓ Gemini rated: 3 → No Issues"
7. Confirm: "Click rating button '3'? (y/n)"
8. Done! Rating submitted automatically
```

**Example Output:**
```
🤖 Gemini Auto-Rating
============================================================
📝 Extracting response text...
✓ Extracted 1,247 characters
Preview: The model response begins with accurate information...

📊 Rating Categories:
✓ Found 3 categories: Localization, Instruction Following, Truthfulness

⏳ Getting Gemini rating for 'Localization'...
✓ Gemini rated: 3
  → No Issues

🖱️  Click rating button '3' for Localization? (y/n): y
✓ Clicked rating 3

⏳ Getting Gemini rating for 'Instruction Following'...
✓ Gemini rated: 2
  → Minor Issues

🖱️  Click rating button '2' for Instruction Following? (y/n): y
✓ Clicked rating 2

✅ Auto-rating complete!
```

**Benefits:**
- **Save 80% Time**: No more manual reading and rating
- **Consistent Ratings**: AI uses same criteria every time
- **Batch Processing**: Rate multiple categories in one flow
- **Audit Trail**: See AI's reasoning for each rating
- **Configurable Model**: Use gemini-pro or gemini-1.5-pro
- **Clipboard-Free**: No copying/pasting needed

**Configuration:**
```json
{
  "gemini_api_key": "your-api-key-here",
  "gemini_model": "gemini-pro"  // or "gemini-1.5-pro"
}
```

**Safety Features:**
- Requires manual confirmation before clicking each button
- Preview of extracted text to verify accuracy
- Shows Gemini's rating before clicking
- Graceful fallback if API fails

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

---

## 🆕 **PRIORITY 1: IMMEDIATE IMPACT FEATURES**

### 🔄 **Auto-Resume with Full Context**
- **Scroll Position Restore**: Automatically restores your exact scroll position on page
- **Form Field Cache**: Remembers all filled form fields and offers to restore them
- **Smart Resume**: Option to restore both URL, scroll position, and form data together
- **Auto-Save Context**: Prompts to save page context before closing browser
- **Usage**: Navigate to site → Fill forms → Save context (Menu #11) → Next time, restore everything!

### ⌨️ **Global Hotkeys**
- **Ctrl+Shift+R**: Toggle recording from anywhere (even when VS Code is active)
- **Ctrl+Shift+P**: Replay last saved session instantly
- **Always Available**: Works even when browser window isn't focused
- **Toggle On/Off**: Menu option #14 to enable/disable hotkeys
- **Cross-Application**: Control automation without switching windows

### 📋 **Enhanced Clipboard Monitoring**
- **Auto-Detect**: Automatically detects clipboard content when filling forms
- **Smart Suggestions**: Offers clipboard paste for relevant fields
- **Template Integration**: Use clipboard values for template variables
- **One-Key Paste**: Just press Enter to use clipboard content
- **Toggle**: Enable/disable in preferences (Menu #8)

### 📚 **Session Templates Library**
- **Pre-Built Templates**: Ready-to-use templates for common tasks
  - **Login Form**: Generic username/password with auto-login
  - **Search**: Enter query and click search
  - **Contact Form**: Name, email, message fields
  - **Generic Form Fill**: Auto-detect and fill any form
- **Variable Support**: Templates use placeholders like `{{username}}`, `{{email}}`
- **Clipboard Integration**: Smart suggestions for template variables
- **Custom Templates**: Easy to extend with your own workflows
- **Usage**: Menu #12 to use template, #13 to list all templates

### ⚡ **Quick Access**
- **Menu Options**:
  - #11: Save page context (scroll + form fields)
  - #12: Use session template
  - #13: List all available templates
  - #14: Toggle global hotkeys
- **Faster Workflows**: Complete tasks in 50% less time
- **No Manual Scanning**: Context restoration eliminates repetitive actions

### 🎯 **Quick Start Guide for Priority 1 Features**

**Example Workflow:**
```bash
1. Navigate to a form website
2. Fill out the form halfway
3. Save context (Menu #11) - saves scroll + field values
4. Close browser
5. Restart automation
6. Resume last URL (y) → Restore context (y)
7. Everything is exactly as you left it!
```

**Using Templates:**
```bash
1. Navigate to login page
2. Select "Use session template" (Menu #12)
3. Choose 'login' template
4. Enter credentials when prompted
5. Template auto-fills and clicks login - done in 10 seconds!
```

**Using Hotkeys:**
```bash
1. Enable hotkeys (Menu #14)
2. Start using automation normally
3. Press Ctrl+Shift+R anywhere to toggle recording
4. Press Ctrl+Shift+P anywhere to replay last session
5. No need to switch to terminal!
```

**Using Watch & Learn (NEW!):**
```bash
1. Just use the automation normally (it's watching by default)
2. Repeat any sequence 2+ times (e.g., click button → type text → click submit)
3. You'll see: "🔍 PATTERN DETECTED!"
4. Press 'y' to create automation
5. Pattern is saved and can be replayed anytime!
6. View all patterns with Menu #16
```

---

4. Your last URL is saved automatically in preferences

## Smart Form Auto-Fill

### 📋 How It Works

The script can automatically detect and fill entire forms on any webpage!

**Option 14: Auto-fill entire form**

#### Step-by-Step Process:

1. **Detection Phase:**
   ```
   🔍 Detecting forms on the page...
   📋 Found 1 form(s):
     [0] Login Form
         Fields: 3
         Action: /login
   ```

2. **Field Discovery:**
   ```
   📝 Form: Login Form
   ====================================
   [0] Email (required)
       Type: email
   [1] Password (required)
       Type: password
   [2] Remember me (optional)
       Type: checkbox
   ====================================
   ```

3. **Interactive Filling:**
   ```
   ✏️  Enter values for each field:
   💡 Clipboard detection is active!
   
   [0] Email
       📋 Use clipboard? ('user@example.com') (y/n/skip): y
   
   [1] Password
       Enter value: ********
   
   [2] Remember me
       Enter value (or Enter to skip): [Enter]
   ```

4. **Confirmation & Execution:**
   ```
   📊 Summary: 2 fields will be filled
   Proceed with auto-fill? (y/n): y
   
   ⌨️  Filling form...
   [0] Email: typing...
   [1] Password: typing...
   
   ✅ Form auto-fill completed!
   💡 Review the form before submitting!
   ```

5. **Auto-Click Buttons (NEW!):**
   ```
   🔍 Looking for continue buttons...
   
   🔘 Found 3 button(s):
     ⭐ [0] Next Step
     ⭐ [1] Submit
        [2] Cancel
   
   ====================================
   Options:
     • Type button text (e.g., 'Next')
     • Type number (e.g., '0')
     • Press Enter to skip
   ====================================
   
   🔘 Click button: Next
   
   🖱️  Clicking 'Next Step'...
     ✓ Button clicked!
     ⏳ Waiting for page to load...
     🔍 Checking for new forms...
     ✓ Found 1 new form(s)
   
   Continue filling forms? (y/n): y
   ```

### What Gets Detected

**Form Fields:**
- Text inputs (text, email, password, tel, url, number)
- Textareas (multi-line text)
- Select dropdowns
- Checkboxes and radio buttons (coming soon)

**Field Identification:**
- Associated `<label>` tags
- `placeholder` attributes
- `aria-label` attributes
- `name` and `id` attributes

**Works With:**
- ✅ Standard HTML forms with `<form>` tags
- ✅ Modern web apps without form tags (detects individual fields)
- ✅ Multiple forms on same page (select which one to fill)
- ✅ Required and optional fields

### Example Use Cases

**Login Form:**
```
1. Navigate to login page (auto-scans)
2. Option 4 → Interact
3. Option 14 → Auto-fill form
4. Fill email and password
5. Done! Use Option 11 to click "Login"
```

**Registration Form:**
```
1. Navigate to signup page
2. Option 14 → Auto-fill form
3. Copy each value before prompted
4. Clipboard automatically detected
5. All fields filled with human-like typing!
```

**Contact Form:**
```
Multiple fields (name, email, subject, message):
- Auto-detects all fields
- Shows field labels clearly
- Skip optional fields with Enter
- Fills in one go!
```

**Multi-Step Form (NEW!):**
```
Step 1: Personal Info
- Fill name, email, phone
- Auto-detects "Next" button
- Click to continue

Step 2: Address
- Fill address fields
- Click "Next" again

Step 3: Payment
- Fill payment info
- Click "Submit"

All automated in one workflow! 🎉
```

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