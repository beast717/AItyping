"""
Web Automation with Playwright
Interactive browser control script
"""

from playwright.sync_api import sync_playwright
import os
import time
import random
import json
from datetime import datetime

# Global variable to store scanned elements
page_elements = {}
# Global variable to store recorded actions
recorded_actions = []
is_recording = False

def get_edge_profile_path():
    """Get the default Edge profile path for the current user"""
    user_profile = os.environ.get('USERPROFILE')
    edge_profile = os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data')
    
    if os.path.exists(edge_profile):
        return edge_profile
    return None

def scan_page_elements(page):
    """Scan and display interactive elements on the current page"""
    print("\n🔍 Scanning page for interactive elements...")
    
    element_types = {
        'buttons': 'button, input[type="button"], input[type="submit"]',
        'links': 'a[href]',
        'inputs': 'input[type="text"], input[type="email"], input[type="password"]',
        'textareas': 'textarea',
        'selects': 'select',
        'checkboxes': 'input[type="checkbox"]',
        'radios': 'input[type="radio"]'
    }
    
    # Store all elements globally for interaction
    global page_elements
    page_elements = {}
    
    for element_type, selector in element_types.items():
        elements = page.locator(selector).all()
        page_elements[element_type] = elements
        
        print(f"\n{element_type.upper()} ({len(elements)} found):")
        for i, elem in enumerate(elements[:20]):  # Show first 20
            try:
                text = elem.inner_text()[:50] if elem.inner_text() else ''
                name = elem.get_attribute('name') or ''
                id_attr = elem.get_attribute('id') or ''
                placeholder = elem.get_attribute('placeholder') or ''
                
                info = f"  [{i}] "
                if text:
                    info += f"'{text}'"
                elif name:
                    info += f"name='{name}'"
                elif id_attr:
                    info += f"id='{id_attr}'"
                elif placeholder:
                    info += f"placeholder='{placeholder}'"
                else:
                    info += "(no label)"
                
                print(info)
            except:
                print(f"  [{i}] (could not read)")
        
        if len(elements) > 20:
            print(f"  ... and {len(elements) - 20} more")
    
    return page_elements

def interact_with_element(page):
    """Allow user to interact with page elements"""
    global page_elements, recorded_actions, is_recording
    
    if not page_elements:
        print("\n⚠ Please scan the page first (Option 3) to see available elements!")
        return
    
    print("\n🎯 Element Interaction")
    print("1. Click a button")
    print("2. Click a link")
    print("3. Fill an input field (instant)")
    print("4. Type in input field (human-like)")
    print("5. Select from dropdown")
    print("6. Check/uncheck checkbox")
    print("7. Back to main menu")
    
    choice = input("\nChoose action: ").strip()
    
    if choice == '1':
        if 'buttons' not in page_elements or not page_elements['buttons']:
            print("⚠ No buttons found on this page!")
            return
        index = input(f"Enter button number [0-{len(page_elements['buttons'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        try:
            idx = int(index)
            page_elements['buttons'][idx].click()
            print(f"✓ Clicked button [{idx}]")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'click_button',
                    'index': idx,
                    'description': f'Click button {idx}'
                })
        except (ValueError, IndexError):
            print(f"✗ Invalid button number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '2':
        if 'links' not in page_elements or not page_elements['links']:
            print("⚠ No links found on this page!")
            return
        index = input(f"Enter link number [0-{len(page_elements['links'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        try:
            idx = int(index)
            page_elements['links'][idx].click()
            print(f"✓ Clicked link [{idx}]")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'click_link',
                    'index': idx,
                    'description': f'Click link {idx}'
                })
        except (ValueError, IndexError):
            print(f"✗ Invalid link number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '3':
        if 'inputs' not in page_elements or not page_elements['inputs']:
            print("⚠ No input fields found on this page!")
            return
        index = input(f"Enter input number [0-{len(page_elements['inputs'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        value = input("Enter value to fill: ").strip()
        try:
            idx = int(index)
            page_elements['inputs'][idx].fill(value)
            print(f"✓ Filled input [{idx}] with '{value}'")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'fill_input',
                    'index': idx,
                    'value': value,
                    'description': f'Fill input {idx}'
                })
        except (ValueError, IndexError):
            print(f"✗ Invalid input number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '4':
        if 'inputs' not in page_elements or not page_elements['inputs']:
            print("⚠ No input fields found on this page!")
            return
        index = input(f"Enter input number [0-{len(page_elements['inputs'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        value = input("Enter text to type: ").strip()
        speed = input("Enter base typing speed in ms (50-200, default 100): ").strip()
        typo_chance = input("Enable typos? (y/n, default y): ").strip().lower()
        
        try:
            idx = int(index)
            base_delay = int(speed) if speed else 100
            enable_typos = typo_chance != 'n'
            
            # Clear field first
            page_elements['inputs'][idx].clear()
            
            # Type character by character with human-like variation
            print(f"⌨️  Typing '{value}'...", end='', flush=True)
            for i, char in enumerate(value):
                # Random typo chance (5% if enabled, skip spaces and first char)
                if enable_typos and i > 0 and char != ' ' and random.random() < 0.05:
                    # Make a typo - type a random nearby key
                    keyboard_nearby = {
                        'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsd',
                        'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'uojk', 'j': 'huikm',
                        'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iplk',
                        'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'awedxz', 't': 'ryfg',
                        'u': 'yihj', 'v': 'cfgb', 'w': 'qeas', 'x': 'zsdc', 'y': 'tugh',
                        'z': 'asx'
                    }
                    
                    typo_char = char
                    if char.lower() in keyboard_nearby:
                        nearby_keys = keyboard_nearby[char.lower()]
                        typo_char = random.choice(nearby_keys)
                        if char.isupper():
                            typo_char = typo_char.upper()
                    
                    # Type the typo
                    typo_delay = int(base_delay * random.uniform(0.8, 1.2))
                    page_elements['inputs'][idx].type(typo_char, delay=typo_delay)
                    
                    # Pause (noticing the mistake)
                    time.sleep(base_delay * random.uniform(0.3, 0.6) / 1000)
                    
                    # Delete the typo
                    page_elements['inputs'][idx].press('Backspace')
                    time.sleep(base_delay * 0.5 / 1000)
                
                # Add random variation: ±40% of base speed
                variation = random.uniform(-0.4, 0.4)
                delay = int(base_delay * (1 + variation))
                
                # Longer pauses after punctuation and spaces (more human)
                if char in '.,!?;:':
                    delay = int(delay * random.uniform(1.5, 2.5))
                elif char == ' ':
                    delay = int(delay * random.uniform(1.2, 1.8))
                
                # Occasional longer "thinking" pauses (1-2% chance)
                if random.random() < 0.02:
                    delay = int(delay * random.uniform(3, 5))
                
                page_elements['inputs'][idx].type(char, delay=delay)
            
            print(" ✓ Done!")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'type_input',
                    'index': idx,
                    'value': value,
                    'base_delay': base_delay,
                    'description': f'Type in input {idx}'
                })
            
        except (ValueError, IndexError):
            print(f"✗ Invalid input number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '5':
        if 'selects' not in page_elements or not page_elements['selects']:
            print("⚠ No dropdown menus found on this page!")
            return
        index = input(f"Enter dropdown number [0-{len(page_elements['selects'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        value = input("Enter option value or text: ").strip()
        try:
            idx = int(index)
            page_elements['selects'][idx].select_option(value)
            print(f"✓ Selected '{value}' in dropdown [{idx}]")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'select_option',
                    'index': idx,
                    'value': value,
                    'description': f'Select dropdown {idx}'
                })
        except (ValueError, IndexError):
            print(f"✗ Invalid dropdown number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '6':
        if 'checkboxes' not in page_elements or not page_elements['checkboxes']:
            print("⚠ No checkboxes found on this page!")
            return
        index = input(f"Enter checkbox number [0-{len(page_elements['checkboxes'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        try:
            idx = int(index)
            page_elements['checkboxes'][idx].check()
            print(f"✓ Checked checkbox [{idx}]")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'check_checkbox',
                    'index': idx,
                    'description': f'Check checkbox {idx}'
                })
        except (ValueError, IndexError):
            print(f"✗ Invalid checkbox number")
        except Exception as e:
            print(f"✗ Error: {e}")

def save_session():
    """Save recorded actions to a file"""
    global recorded_actions
    
    if not recorded_actions:
        print("⚠ No actions recorded yet!")
        return
    
    # Create sessions directory if it doesn't exist
    if not os.path.exists('sessions'):
        os.makedirs('sessions')
    
    filename = input("\nEnter session name (e.g., 'login_flow'): ").strip()
    if not filename:
        filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    filepath = f"sessions/{filename}.json"
    
    try:
        with open(filepath, 'w') as f:
            json.dump(recorded_actions, f, indent=2)
        print(f"✓ Session saved to '{filepath}' ({len(recorded_actions)} actions)")
    except Exception as e:
        print(f"✗ Error saving session: {e}")

def load_session(page):
    """Load and replay a saved session"""
    global page_elements
    
    if not os.path.exists('sessions'):
        print("⚠ No sessions folder found!")
        return
    
    # List available sessions
    sessions = [f for f in os.listdir('sessions') if f.endswith('.json')]
    
    if not sessions:
        print("⚠ No saved sessions found!")
        return
    
    print("\n📁 Available Sessions:")
    for i, session in enumerate(sessions):
        print(f"  [{i}] {session}")
    
    choice = input(f"\nEnter session number [0-{len(sessions)-1}] (or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        print("Cancelled.")
        return
    
    try:
        idx = int(choice)
        filepath = f"sessions/{sessions[idx]}"
        
        with open(filepath, 'r') as f:
            actions = json.load(f)
        
        print(f"\n🎬 Replaying session '{sessions[idx]}' ({len(actions)} actions)...")
        print("Press Ctrl+C to stop at any time\n")
        
        for i, action in enumerate(actions):
            print(f"[{i+1}/{len(actions)}] {action['type']}: {action.get('description', '')}")
            
            try:
                if action['type'] == 'navigate':
                    page.goto(action['url'])
                    time.sleep(1)
                
                elif action['type'] == 'click_button':
                    # Re-scan to get fresh elements
                    page_elements['buttons'] = page.locator('button, input[type="button"], input[type="submit"]').all()
                    page_elements['buttons'][action['index']].click()
                    time.sleep(0.5)
                
                elif action['type'] == 'click_link':
                    page_elements['links'] = page.locator('a[href]').all()
                    page_elements['links'][action['index']].click()
                    time.sleep(0.5)
                
                elif action['type'] == 'fill_input':
                    page_elements['inputs'] = page.locator('input[type="text"], input[type="email"], input[type="password"]').all()
                    page_elements['inputs'][action['index']].fill(action['value'])
                    time.sleep(0.3)
                
                elif action['type'] == 'type_input':
                    page_elements['inputs'] = page.locator('input[type="text"], input[type="email"], input[type="password"]').all()
                    elem = page_elements['inputs'][action['index']]
                    elem.clear()
                    
                    # Type with human-like behavior
                    for char in action['value']:
                        variation = random.uniform(-0.4, 0.4)
                        delay = int(action.get('base_delay', 100) * (1 + variation))
                        elem.type(char, delay=delay)
                
                elif action['type'] == 'select_option':
                    page_elements['selects'] = page.locator('select').all()
                    page_elements['selects'][action['index']].select_option(action['value'])
                    time.sleep(0.3)
                
                elif action['type'] == 'check_checkbox':
                    page_elements['checkboxes'] = page.locator('input[type="checkbox"]').all()
                    page_elements['checkboxes'][action['index']].check()
                    time.sleep(0.3)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                retry = input("  Continue with next action? (y/n): ").strip().lower()
                if retry != 'y':
                    break
        
        print("\n✓ Session replay completed!")
        
    except (ValueError, IndexError):
        print("✗ Invalid session number")
    except Exception as e:
        print(f"✗ Error loading session: {e}")

def toggle_recording():
    """Toggle session recording on/off"""
    global is_recording, recorded_actions
    
    if is_recording:
        is_recording = False
        print(f"⏸️  Recording stopped. {len(recorded_actions)} actions recorded.")
        print("Use 'Save session' to save your workflow.")
    else:
        is_recording = True
        recorded_actions = []
        print("⏺️  Recording started! All actions will be saved.")

def show_menu():
    """Display the interactive menu"""
    global is_recording
    
    print("\n" + "="*50)
    print("🌐 WEB AUTOMATION MENU")
    if is_recording:
        print(f"⏺️  RECORDING ({len(recorded_actions)} actions)")
    print("="*50)
    print("1. Navigate to website")
    print("2. Get page information")
    print("3. Scan page elements")
    print("4. Interact with elements")
    print("5. Toggle recording (save workflow)")
    print("6. Save session")
    print("7. Load & replay session")
    print("8. Close browser and exit")
    print("="*50)

def main():
    """Main automation script"""
    print("🚀 Web Automation with Playwright")
    print("-" * 50)
    
    # Ask user about profile preference
    print("\nProfile Options:")
    print("1. Use existing Edge profile (stay logged in)")
    print("2. Fresh session (clean browser)")
    
    profile_choice = input("\nChoose option (1 or 2): ").strip()
    use_profile = profile_choice == '1'
    
    with sync_playwright() as p:
        # Launch browser
        print("\n🌐 Launching Microsoft Edge...")
        
        if use_profile:
            profile_path = get_edge_profile_path()
            if profile_path:
                print(f"✓ Found Edge profile: {profile_path}")
                print("⚠ Note: Close Edge browser if it's currently running...")
                try:
                    context = p.chromium.launch_persistent_context(
                        profile_path,
                        headless=False,
                        channel="msedge",
                        args=[
                            '--disable-blink-features=AutomationControlled'
                        ]
                    )
                    page = context.pages[0] if context.pages else context.new_page()
                    
                    # Remove automation detection
                    page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        // Remove automation indicators
                        window.navigator.chrome = {
                            runtime: {}
                        };
                        
                        // Overwrite the `plugins` property to use a custom getter
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        
                        // Overwrite the `languages` property to use a custom getter
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                    """)
                    
                    print("✓ Browser launched with profile (stealth mode)!")
                except Exception as e:
                    print(f"⚠ Could not use profile (Edge might be running): {str(e)[:100]}")
                    print("✓ Using fresh session instead...")
                    browser = p.chromium.launch(
                        headless=False,
                        channel="msedge",
                        args=[
                            '--disable-blink-features=AutomationControlled'
                        ]
                    )
                    context = browser.new_context()
                    page = context.new_page()
                    
                    # Remove automation detection
                    page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        window.navigator.chrome = {
                            runtime: {}
                        };
                        
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                    """)
            else:
                print("⚠ Profile not found, using fresh session")
                browser = p.chromium.launch(
                    headless=False,
                    channel="msedge",
                    args=[
                        '--disable-blink-features=AutomationControlled'
                    ],
                    ignore_default_args=['--enable-automation']
                )
                context = browser.new_context()
                page = context.new_page()
                
                # Remove automation detection
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    window.navigator.chrome = {
                        runtime: {}
                    };
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                """)
        else:
            browser = p.chromium.launch(
                headless=False,
                channel="msedge",
                args=[
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            context = browser.new_context()
            page = context.new_page()
            
            # Remove automation detection
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                window.navigator.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
        
        print("✓ Browser launched successfully (stealth mode)!")
        
        # Interactive menu loop
        while True:
            show_menu()
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                url = input("\n🔗 Enter website URL (e.g., google.com): ").strip()
                if not url.startswith('http'):
                    url = 'https://' + url
                try:
                    print(f"Navigating to {url}...")
                    page.goto(url)
                    print(f"✓ Loaded: {page.title()}")
                    
                    if is_recording:
                        recorded_actions.append({
                            'type': 'navigate',
                            'url': url,
                            'description': f'Navigate to {url}'
                        })
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '2':
                try:
                    print(f"\n📄 Current Page Info:")
                    print(f"  Title: {page.title()}")
                    print(f"  URL: {page.url}")
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '3':
                try:
                    scan_page_elements(page)
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '4':
                try:
                    interact_with_element(page)
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '5':
                toggle_recording()
            
            elif choice == '6':
                save_session()
            
            elif choice == '7':
                try:
                    load_session(page)
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '8':
                print("\n👋 Closing browser...")
                context.close()
                print("✓ Browser closed. Goodbye!")
                break
            
            else:
                print("⚠ Invalid choice. Please enter 1-8.")

if __name__ == "__main__":
    main()
