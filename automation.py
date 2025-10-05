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
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    print("⚠ pyperclip not installed. Clipboard features disabled. Install with: pip install pyperclip")

# Global variable to store scanned elements
page_elements = {}
# Global variable to store recorded actions
recorded_actions = []
is_recording = False
# Global variable to store user preferences
user_preferences = {
    'typing_speed': 100,
    'enable_typos': True,
    'typo_chance': 0.05,
    'pause_after_punctuation': True,
    'thinking_pauses': True,
    'max_retries': 3,
    'retry_delay': 1.0,
    'auto_wait_timeout': 30000,
    'verify_actions': True,
    'auto_scan': True,
    'last_url': ''
}

def get_clipboard_text():
    """Get text from clipboard if available"""
    if CLIPBOARD_AVAILABLE:
        try:
            return pyperclip.paste()
        except Exception:
            return None
    return None

def find_element_by_text(page, element_type, text, exact_match=False):
    """
    Find an element by its visible text
    Returns the element or None if not found
    """
    try:
        if exact_match:
            # Exact text match
            if element_type == 'button':
                selector = f"button:has-text('{text}'), input[type='button']:has-text('{text}'), input[type='submit']:has-text('{text}')"
            elif element_type == 'link':
                selector = f"a:has-text('{text}')"
            else:
                selector = f"{element_type}:has-text('{text}')"
        else:
            # Partial text match (case-insensitive)
            if element_type == 'button':
                selector = f"button:text-is('{text}'), input[type='button'][value*='{text}' i], input[type='submit'][value*='{text}' i]"
            elif element_type == 'link':
                selector = f"a:text-is('{text}')"
            else:
                selector = f"{element_type}:text-is('{text}')"
        
        # Try exact match first
        element = page.locator(f"text='{text}'").first
        if element.count() > 0:
            return element
        
        # Try partial match
        element = page.locator(f"text=/{text}/i").first
        if element.count() > 0:
            return element
            
        return None
    except Exception as e:
        print(f"  ⚠ Error finding element by text: {e}")
        return None

def find_element_by_selector(page, selector, selector_type='css'):
    """
    Find an element by CSS selector or XPath
    Returns the element or None if not found
    """
    try:
        if selector_type == 'xpath':
            element = page.locator(f"xpath={selector}").first
        else:  # css
            element = page.locator(selector).first
        
        if element.count() > 0:
            return element
        return None
    except Exception as e:
        print(f"  ⚠ Error finding element by selector: {e}")
        return None

def get_element_with_fallback(page, element_list, index, element_type='element'):
    """
    Try to get element by index, with smart fallback if it fails
    Returns (element, error_message) tuple
    """
    try:
        # Try direct index access
        if 0 <= index < len(element_list):
            elem = element_list[index]
            # Verify element is still valid
            elem.count()  # This will throw if element is stale
            return (elem, None)
        else:
            return (None, f"Index {index} out of range (0-{len(element_list)-1})")
    except Exception as e:
        # Element is stale or invalid - try to recover
        error_msg = str(e).lower()
        
        if 'stale' in error_msg or 'detached' in error_msg:
            print(f"  ⚠ Element [{index}] is stale. Attempting to recover...")
            
            # Try to get element attributes before it became stale
            try:
                # Re-scan the same element type
                print(f"  🔄 Re-scanning {element_type}s...")
                return (None, f"Element became stale. Please try option 3 to re-scan, or use 'Find by text' (option 11)")
            except:
                pass
        
        return (None, str(e))

def get_edge_profile_path():
    """Get the default Edge profile path for the current user"""
    user_profile = os.environ.get('USERPROFILE')
    edge_profile = os.path.join(user_profile, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data')
    
    if os.path.exists(edge_profile):
        return edge_profile
    return None

def smart_wait_for_element(page, selector, timeout=None):
    """
    Intelligently wait for an element to be ready (visible and stable)
    Returns the element or None if not found
    """
    if timeout is None:
        timeout = user_preferences.get('auto_wait_timeout', 30000)
    
    try:
        # Wait for element to be visible and stable
        element = page.wait_for_selector(selector, state='visible', timeout=timeout)
        # Small delay to ensure element is fully loaded
        time.sleep(0.2)
        return element
    except Exception as e:
        return None

def retry_with_backoff(func, max_retries=None, initial_delay=None, description="Action"):
    """
    Retry a function with exponential backoff
    Returns (success: bool, result: any, error: str)
    """
    if max_retries is None:
        max_retries = user_preferences.get('max_retries', 3)
    if initial_delay is None:
        initial_delay = user_preferences.get('retry_delay', 1.0)
    
    for attempt in range(max_retries):
        try:
            result = func()
            if user_preferences.get('verify_actions', True):
                print(f"  ✓ {description} succeeded")
            return (True, result, None)
        except Exception as e:
            error_msg = str(e)
            
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                print(f"  ⚠ Attempt {attempt + 1} failed: {error_msg}")
                print(f"  🔄 Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                print(f"  ✗ {description} failed after {max_retries} attempts: {error_msg}")
                return (False, None, error_msg)
    
    return (False, None, "Max retries exceeded")

def safe_click(element, description="Click"):
    """
    Safely click an element with retry and error recovery
    Works with both Locator and ElementHandle objects
    """
    def click_action():
        # Locator objects don't have wait_for_element_state
        # They wait automatically when performing actions
        try:
            element.scroll_into_view_if_needed()
        except:
            pass  # Locator objects handle this automatically
        time.sleep(0.1)
        element.click()
        return True
    
    return retry_with_backoff(click_action, description=description)

def safe_fill(element, value, description="Fill"):
    """
    Safely fill an element with retry and error recovery
    Works with both Locator and ElementHandle objects
    """
    def fill_action():
        try:
            element.scroll_into_view_if_needed()
        except:
            pass  # Locator objects handle this automatically
        
        # Clear and fill
        try:
            element.clear()
        except:
            element.fill('')  # Alternative clear method
        
        element.fill(value)
        
        # Verify the value was set
        if user_preferences.get('verify_actions', True):
            actual_value = element.input_value()
            if actual_value != value:
                raise Exception(f"Verification failed: expected '{value}', got '{actual_value}'")
        
        return True
    
    return retry_with_backoff(fill_action, description=description)

def safe_type(element, value, delay=100, description="Type"):
    """
    Safely type into an element with retry and error recovery
    Works with both Locator and ElementHandle objects
    """
    def type_action():
        try:
            element.scroll_into_view_if_needed()
        except:
            pass  # Locator objects handle this automatically
        
        # Clear field
        try:
            element.clear()
        except:
            element.fill('')  # Alternative clear method
        
        # Type with human-like behavior
        for char in value:
            element.type(char, delay=delay)
        
        # Verify the value was set
        if user_preferences.get('verify_actions', True):
            time.sleep(0.2)
            actual_value = element.input_value()
            if actual_value != value:
                raise Exception(f"Verification failed: expected '{value}', got '{actual_value}'")
        
        return True
    
    return retry_with_backoff(type_action, description=description)

def handle_common_errors(error, element_description="element"):
    """
    Provide helpful error messages and recovery suggestions
    """
    error_str = str(error).lower()
    
    if 'timeout' in error_str:
        return f"⏱️ Timeout: {element_description} took too long to load. Try increasing timeout or check your internet connection."
    elif 'not found' in error_str or 'no element' in error_str:
        return f"🔍 Not found: {element_description} doesn't exist on the page. The page structure may have changed."
    elif 'detached' in error_str or 'stale' in error_str:
        return f"🔄 Stale element: {element_description} changed. The page was updated. Retrying should fix this."
    elif 'not visible' in error_str:
        return f"👁️ Hidden: {element_description} is not visible. It may be hidden or off-screen."
    elif 'not clickable' in error_str:
        return f"🚫 Not clickable: {element_description} is blocked by another element or disabled."
    else:
        return f"❌ Error with {element_description}: {error}"

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
        print("\n🔍 No elements found. Auto-scanning page...")
        scan_page_elements(page)
        if not page_elements:
            print("\n⚠ No interactive elements found on this page!")
            return
    
    print("\n🎯 Element Interaction")
    print("1. Click a button")
    print("2. Click a link")
    print("3. Fill an input field (instant)")
    print("4. Type in input field (human-like)")
    print("5. Fill textarea (instant)")
    print("6. Type in textarea (human-like)")
    print("7. Select from dropdown")
    print("8. Check/uncheck checkbox")
    print("9. 🔄 Batch fill multiple inputs")
    print("10. 🔄 Batch type in multiple textareas")
    print("11. 🔍 Click element by text (e.g., 'Submit')")
    print("12. 🔍 Type in input by label/placeholder")
    print("13. 🔍 Find by CSS selector or XPath")
    print("14. Back to main menu")
    
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
            success, _, error = safe_click(page_elements['buttons'][idx], f"Click button [{idx}]")
            
            if success:
                if is_recording:
                    recorded_actions.append({
                        'type': 'click_button',
                        'index': idx,
                        'description': f'Click button {idx}'
                    })
            else:
                print(handle_common_errors(error, f"button [{idx}]"))
        except (ValueError, IndexError):
            print(f"✗ Invalid button number")
        except Exception as e:
            print(handle_common_errors(e, f"button operation"))
    
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
            success, _, error = safe_click(page_elements['links'][idx], f"Click link [{idx}]")
            
            if success:
                if is_recording:
                    recorded_actions.append({
                        'type': 'click_link',
                        'index': idx,
                        'description': f'Click link {idx}'
                    })
            else:
                print(handle_common_errors(error, f"link [{idx}]"))
        except (ValueError, IndexError):
            print(f"✗ Invalid link number")
        except Exception as e:
            print(handle_common_errors(e, f"link operation"))
    
    elif choice == '3':
        if 'inputs' not in page_elements or not page_elements['inputs']:
            print("⚠ No input fields found on this page!")
            return
        index = input(f"Enter input number [0-{len(page_elements['inputs'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        
        # Check clipboard
        clipboard_text = get_clipboard_text()
        if clipboard_text:
            use_clipboard = input(f"📋 Clipboard contains: '{clipboard_text[:50]}...' Use it? (y/n): ").strip().lower()
            if use_clipboard == 'y':
                value = clipboard_text
            else:
                value = input("Enter value to fill: ").strip()
        else:
            value = input("Enter value to fill: ").strip()
        try:
            idx = int(index)
            success, _, error = safe_fill(page_elements['inputs'][idx], value, f"Fill input [{idx}]")
            
            if success:
                if is_recording:
                    recorded_actions.append({
                        'type': 'fill_input',
                        'index': idx,
                        'value': value,
                        'description': f'Fill input {idx}'
                    })
            else:
                print(handle_common_errors(error, f"input [{idx}]"))
        except (ValueError, IndexError):
            print(f"✗ Invalid input number")
        except Exception as e:
            print(handle_common_errors(e, f"input operation"))
    
    elif choice == '4':
        if 'inputs' not in page_elements or not page_elements['inputs']:
            print("⚠ No input fields found on this page!")
            return
        index = input(f"Enter input number [0-{len(page_elements['inputs'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        
        # Check clipboard
        clipboard_text = get_clipboard_text()
        if clipboard_text:
            use_clipboard = input(f"📋 Clipboard contains: '{clipboard_text[:50]}...' Use it? (y/n): ").strip().lower()
            if use_clipboard == 'y':
                value = clipboard_text
            else:
                value = input("Enter text to type: ").strip()
        else:
            value = input("Enter text to type: ").strip()
        
        # Ask if user wants to use saved preferences
        use_prefs = input(f"Use saved preferences? (y/n, current speed: {user_preferences['typing_speed']}ms): ").strip().lower()
        
        if use_prefs == 'y':
            base_delay = user_preferences['typing_speed']
            enable_typos = user_preferences['enable_typos']
            print(f"✓ Using preferences: {base_delay}ms, typos: {'on' if enable_typos else 'off'}")
        else:
            speed = input("Enter base typing speed in ms (50-200, default 100): ").strip()
            typo_chance = input("Enable typos? (y/n, default y): ").strip().lower()
            base_delay = int(speed) if speed else 100
            enable_typos = typo_chance != 'n'
        
        try:
            idx = int(index)
            
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
        if 'textareas' not in page_elements or not page_elements['textareas']:
            print("⚠ No textarea fields found on this page!")
            return
        index = input(f"Enter textarea number [0-{len(page_elements['textareas'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        
        # Check clipboard
        clipboard_text = get_clipboard_text()
        if clipboard_text:
            use_clipboard = input(f"📋 Clipboard contains: '{clipboard_text[:50]}...' Use it? (y/n): ").strip().lower()
            if use_clipboard == 'y':
                value = clipboard_text
            else:
                value = input("Enter value to fill: ").strip()
        else:
            value = input("Enter value to fill: ").strip()
        try:
            idx = int(index)
            page_elements['textareas'][idx].fill(value)
            print(f"✓ Filled textarea [{idx}] with '{value}'")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'fill_textarea',
                    'index': idx,
                    'value': value,
                    'description': f'Fill textarea {idx}'
                })
        except (ValueError, IndexError):
            print(f"✗ Invalid textarea number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '6':
        if 'textareas' not in page_elements or not page_elements['textareas']:
            print("⚠ No textarea fields found on this page!")
            return
        index = input(f"Enter textarea number [0-{len(page_elements['textareas'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        
        # Check clipboard
        clipboard_text = get_clipboard_text()
        if clipboard_text:
            use_clipboard = input(f"📋 Clipboard contains: '{clipboard_text[:50]}...' Use it? (y/n): ").strip().lower()
            if use_clipboard == 'y':
                value = clipboard_text
            else:
                value = input("Enter text to type: ").strip()
        else:
            value = input("Enter text to type: ").strip()
        
        # Ask if user wants to use saved preferences
        use_prefs = input(f"Use saved preferences? (y/n, current speed: {user_preferences['typing_speed']}ms): ").strip().lower()
        
        if use_prefs == 'y':
            base_delay = user_preferences['typing_speed']
            enable_typos = user_preferences['enable_typos']
            print(f"✓ Using preferences: {base_delay}ms, typos: {'on' if enable_typos else 'off'}")
        else:
            speed = input("Enter base typing speed in ms (50-200, default 100): ").strip()
            typo_chance = input("Enable typos? (y/n, default y): ").strip().lower()
            base_delay = int(speed) if speed else 100
            enable_typos = typo_chance != 'n'
        
        try:
            idx = int(index)
            
            # Clear field first
            page_elements['textareas'][idx].clear()
            
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
                    page_elements['textareas'][idx].type(typo_char, delay=typo_delay)
                    
                    # Pause (noticing the mistake)
                    time.sleep(base_delay * random.uniform(0.3, 0.6) / 1000)
                    
                    # Delete the typo
                    page_elements['textareas'][idx].press('Backspace')
                    time.sleep(base_delay * 0.5 / 1000)
                
                # Add random variation: ±40% of base speed
                variation = random.uniform(-0.4, 0.4)
                delay = int(base_delay * (1 + variation))
                
                # Longer pauses after punctuation and spaces (more human)
                if char in '.,!?;:':
                    delay = int(delay * random.uniform(1.5, 2.5))
                elif char == ' ':
                    delay = int(delay * random.uniform(1.2, 1.8))
                elif char == '\n':  # New line pause
                    delay = int(delay * random.uniform(2.0, 3.0))
                
                # Occasional longer "thinking" pauses (1-2% chance)
                if random.random() < 0.02:
                    delay = int(delay * random.uniform(3, 5))
                
                page_elements['textareas'][idx].type(char, delay=delay)
            
            print(" ✓ Done!")
            
            if is_recording:
                recorded_actions.append({
                    'type': 'type_textarea',
                    'index': idx,
                    'value': value,
                    'base_delay': base_delay,
                    'description': f'Type in textarea {idx}'
                })
            
        except (ValueError, IndexError):
            print(f"✗ Invalid textarea number")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '7':
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
            
            def select_action():
                try:
                    page_elements['selects'][idx].scroll_into_view_if_needed()
                except:
                    pass  # Locator objects handle this automatically
                page_elements['selects'][idx].select_option(value)
                return True
            
            success, _, error = retry_with_backoff(select_action, description=f"Select dropdown [{idx}]")
            
            if success:
                if is_recording:
                    recorded_actions.append({
                        'type': 'select_option',
                        'index': idx,
                        'value': value,
                        'description': f'Select dropdown {idx}'
                    })
            else:
                print(handle_common_errors(error, f"dropdown [{idx}]"))
        except (ValueError, IndexError):
            print(f"✗ Invalid dropdown number")
        except Exception as e:
            print(handle_common_errors(e, f"dropdown operation"))
    
    elif choice == '8':
        if 'checkboxes' not in page_elements or not page_elements['checkboxes']:
            print("⚠ No checkboxes found on this page!")
            return
        index = input(f"Enter checkbox number [0-{len(page_elements['checkboxes'])-1}] (or 'c' to cancel): ").strip()
        if index.lower() == 'c':
            print("Cancelled.")
            return
        try:
            idx = int(index)
            
            def check_action():
                try:
                    page_elements['checkboxes'][idx].scroll_into_view_if_needed()
                except:
                    pass  # Locator objects handle this automatically
                page_elements['checkboxes'][idx].check()
                return True
            
            success, _, error = retry_with_backoff(check_action, description=f"Check checkbox [{idx}]")
            
            if success:
                if is_recording:
                    recorded_actions.append({
                        'type': 'check_checkbox',
                        'index': idx,
                        'description': f'Check checkbox {idx}'
                    })
            else:
                print(handle_common_errors(error, f"checkbox [{idx}]"))
        except (ValueError, IndexError):
            print(f"✗ Invalid checkbox number")
        except Exception as e:
            print(handle_common_errors(e, f"checkbox operation"))
    
    elif choice == '9':
        # Batch fill multiple inputs
        if 'inputs' not in page_elements or not page_elements['inputs']:
            print("⚠ No input fields found on this page!")
            return
        
        print("\n🔄 Batch Fill Multiple Inputs")
        indices_input = input(f"Enter input numbers separated by commas (e.g., 0,2,5) [0-{len(page_elements['inputs'])-1}]: ").strip()
        
        if not indices_input:
            print("Cancelled.")
            return
        
        try:
            indices = [int(x.strip()) for x in indices_input.split(',')]
            
            # Collect text for each input
            input_texts = {}
            for idx in indices:
                if 0 <= idx < len(page_elements['inputs']):
                    text = input(f"Enter text for input [{idx}]: ").strip()
                    input_texts[idx] = text
                else:
                    print(f"⚠ Skipping invalid index: {idx}")
            
            # Ask for preferences
            use_prefs = input(f"\nUse saved preferences for all? (y/n, current: {user_preferences['typing_speed']}ms): ").strip().lower()
            
            if use_prefs == 'y':
                base_delay = user_preferences['typing_speed']
                enable_typos = user_preferences['enable_typos']
                print(f"✓ Using preferences: {base_delay}ms, typos: {'on' if enable_typos else 'off'}")
            else:
                speed = input("Enter typing speed in ms (50-200, default 100): ").strip()
                typo_chance = input("Enable typos? (y/n, default y): ").strip().lower()
                base_delay = int(speed) if speed else 100
                enable_typos = typo_chance != 'n'
            
            # Type in each input
            print(f"\n⌨️  Typing in {len(input_texts)} inputs...")
            for idx, text in input_texts.items():
                print(f"\n[{idx}] Typing: '{text[:50]}...'")
                page_elements['inputs'][idx].fill(text)
                print(f"✓ Filled input [{idx}]")
                time.sleep(0.3)  # Small delay between fields
            
            print(f"\n✓ All {len(input_texts)} inputs filled!")
            
        except ValueError:
            print("✗ Invalid input format")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '10':
        # Batch type in multiple textareas
        if 'textareas' not in page_elements or not page_elements['textareas']:
            print("⚠ No textarea fields found on this page!")
            return
        
        print("\n🔄 Batch Type in Multiple Textareas")
        indices_input = input(f"Enter textarea numbers separated by commas (e.g., 0,1,2) [0-{len(page_elements['textareas'])-1}]: ").strip()
        
        if not indices_input:
            print("Cancelled.")
            return
        
        try:
            indices = [int(x.strip()) for x in indices_input.split(',')]
            
            # Collect text for each textarea
            textarea_texts = {}
            for idx in indices:
                if 0 <= idx < len(page_elements['textareas']):
                    print(f"\n--- Textarea [{idx}] ---")
                    text = input(f"Enter text for textarea [{idx}]: ").strip()
                    textarea_texts[idx] = text
                else:
                    print(f"⚠ Skipping invalid index: {idx}")
            
            # Ask for preferences
            use_prefs = input(f"\nUse saved preferences for all? (y/n, current: {user_preferences['typing_speed']}ms): ").strip().lower()
            
            if use_prefs == 'y':
                base_delay = user_preferences['typing_speed']
                enable_typos = user_preferences['enable_typos']
                print(f"✓ Using preferences: {base_delay}ms, typos: {'on' if enable_typos else 'off'}")
            else:
                speed = input("Enter typing speed in ms (50-200, default 100): ").strip()
                typo_chance = input("Enable typos? (y/n, default y): ").strip().lower()
                base_delay = int(speed) if speed else 100
                enable_typos = typo_chance != 'n'
            
            # Type in each textarea with human-like behavior
            print(f"\n⌨️  Typing in {len(textarea_texts)} textareas...")
            for idx, text in textarea_texts.items():
                print(f"\n[{idx}] Typing: '{text[:50]}...'")
                
                # Clear field first
                page_elements['textareas'][idx].clear()
                
                # Type character by character with human-like variation
                for i, char in enumerate(text):
                    # Random typo chance
                    if enable_typos and i > 0 and char != ' ' and random.random() < user_preferences.get('typo_chance', 0.05):
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
                        page_elements['textareas'][idx].type(typo_char, delay=typo_delay)
                        time.sleep(base_delay * random.uniform(0.3, 0.6) / 1000)
                        page_elements['textareas'][idx].press('Backspace')
                        time.sleep(base_delay * 0.5 / 1000)
                    
                    # Add random variation
                    variation = random.uniform(-0.4, 0.4)
                    delay = int(base_delay * (1 + variation))
                    
                    # Longer pauses after punctuation and spaces
                    if user_preferences.get('pause_after_punctuation', True):
                        if char in '.,!?;:':
                            delay = int(delay * random.uniform(1.5, 2.5))
                        elif char == ' ':
                            delay = int(delay * random.uniform(1.2, 1.8))
                        elif char == '\n':
                            delay = int(delay * random.uniform(2.0, 3.0))
                    
                    # Occasional thinking pauses
                    if user_preferences.get('thinking_pauses', True) and random.random() < 0.02:
                        delay = int(delay * random.uniform(3, 5))
                    
                    page_elements['textareas'][idx].type(char, delay=delay)
                
                print(f"✓ Typed in textarea [{idx}]")
                time.sleep(0.5)  # Small delay between textareas
            
            print(f"\n✓ All {len(textarea_texts)} textareas completed!")
            
        except ValueError:
            print("✗ Invalid input format")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    elif choice == '11':
        # Click element by text
        text = input("\n🔍 Enter text to find (e.g., 'Submit', 'Login', 'Next'): ").strip()
        if not text:
            print("Cancelled.")
            return
        
        element_type = input("Element type? (button/link/any) [default: any]: ").strip().lower() or 'any'
        
        try:
            print(f"Searching for element with text '{text}'...")
            
            # Try finding by text
            if element_type == 'any':
                # Try multiple strategies
                element = page.get_by_text(text, exact=False).first
                if element.count() == 0:
                    element = page.get_by_role("button", name=text).first
                if element.count() == 0:
                    element = page.get_by_role("link", name=text).first
            else:
                if element_type == 'button':
                    element = page.get_by_role("button", name=text).first
                elif element_type == 'link':
                    element = page.get_by_role("link", name=text).first
                else:
                    element = page.get_by_text(text, exact=False).first
            
            if element.count() > 0:
                success, _, error = safe_click(element, f"Click element '{text}'")
                if success and is_recording:
                    recorded_actions.append({
                        'type': 'click_by_text',
                        'text': text,
                        'element_type': element_type,
                        'description': f"Click '{text}'"
                    })
            else:
                print(f"✗ Could not find element with text '{text}'")
                print("💡 Tip: Try being more specific or use CSS selector (option 13)")
        except Exception as e:
            print(handle_common_errors(e, f"element with text '{text}'"))
    
    elif choice == '12':
        # Type in input by label/placeholder
        label = input("\n🔍 Enter label or placeholder text (e.g., 'Email', 'Search'): ").strip()
        if not label:
            print("Cancelled.")
            return
        
        # Check clipboard
        clipboard_text = get_clipboard_text()
        if clipboard_text:
            use_clipboard = input(f"📋 Clipboard contains: '{clipboard_text[:50]}...' Use it? (y/n): ").strip().lower()
            if use_clipboard == 'y':
                value = clipboard_text
            else:
                value = input("Enter text to type: ").strip()
        else:
            value = input("Enter text to type: ").strip()
        
        if not value:
            print("Cancelled.")
            return
        
        try:
            print(f"Searching for input with label/placeholder '{label}'...")
            
            # Try multiple strategies, prioritizing actual input fields
            element = None
            
            # Strategy 1: Try placeholder first (most reliable for input fields)
            try:
                element = page.get_by_placeholder(label, exact=False).first
                if element.count() > 0:
                    # Verify it's an input/textarea
                    tag = element.evaluate("el => el.tagName.toLowerCase()")
                    if tag in ['input', 'textarea']:
                        print(f"  ✓ Found by placeholder")
                    else:
                        element = None
            except:
                pass
            
            # Strategy 2: Try finding input/textarea with label attribute
            if not element or element.count() == 0:
                try:
                    # Get inputs/textareas with matching aria-label
                    element = page.locator(f"input[aria-label*='{label}' i], textarea[aria-label*='{label}' i]").first
                    if element.count() > 0:
                        print(f"  ✓ Found by aria-label")
                except:
                    pass
            
            # Strategy 3: Try get_by_label but filter for inputs only
            if not element or element.count() == 0:
                try:
                    all_matches = page.get_by_label(label, exact=False).all()
                    for match in all_matches:
                        tag = match.evaluate("el => el.tagName.toLowerCase()")
                        if tag in ['input', 'textarea']:
                            element = match
                            print(f"  ✓ Found by label")
                            break
                except:
                    pass
            
            # Strategy 4: Try name attribute
            if not element or element.count() == 0:
                try:
                    element = page.locator(f"input[name*='{label}' i], textarea[name*='{label}' i]").first
                    if element.count() > 0:
                        print(f"  ✓ Found by name attribute")
                except:
                    pass
            
            # Strategy 5: Try title attribute
            if not element or element.count() == 0:
                try:
                    element = page.locator(f"input[title*='{label}' i], textarea[title*='{label}' i]").first
                    if element.count() > 0:
                        print(f"  ✓ Found by title attribute")
                except:
                    pass
            
            if element and element.count() > 0:
                # Ask for typing preferences
                use_prefs = input(f"Use saved preferences? (y/n, current speed: {user_preferences['typing_speed']}ms): ").strip().lower()
                
                if use_prefs == 'y':
                    base_delay = user_preferences['typing_speed']
                    enable_typos = user_preferences['enable_typos']
                    print(f"✓ Using preferences: {base_delay}ms, typos: {'on' if enable_typos else 'off'}")
                else:
                    speed = input("Enter base typing speed in ms (50-200, default 100): ").strip()
                    typo_choice = input("Enable typos? (y/n, default y): ").strip().lower()
                    base_delay = int(speed) if speed else 100
                    enable_typos = typo_choice != 'n'
                
                success, _, error = safe_type(element, value, base_delay, f"Type in '{label}'")
                
                if success and is_recording:
                    recorded_actions.append({
                        'type': 'type_by_label',
                        'label': label,
                        'value': value,
                        'base_delay': base_delay,
                        'description': f"Type in '{label}'"
                    })
            else:
                print(f"✗ Could not find input with label/placeholder '{label}'")
                print("💡 Tip: Try the exact label text or use CSS selector (option 13)")
        except Exception as e:
            print(handle_common_errors(e, f"input '{label}'"))
    
    elif choice == '13':
        # Find by CSS selector or XPath
        print("\n🔍 Advanced Selector")
        print("1. CSS Selector (e.g., '#submit-btn', '.login-form input')")
        print("2. XPath (e.g., '//button[@id=\"submit\"]')")
        
        selector_choice = input("Choose selector type (1/2): ").strip()
        
        if selector_choice not in ['1', '2']:
            print("Invalid choice.")
            return
        
        selector = input("Enter selector: ").strip()
        if not selector:
            print("Cancelled.")
            return
        
        action = input("Action? (click/fill/type) [default: click]: ").strip().lower() or 'click'
        
        try:
            selector_type = 'css' if selector_choice == '1' else 'xpath'
            print(f"Searching for element with {selector_type} selector...")
            
            element = find_element_by_selector(page, selector, selector_type)
            
            if element and element.count() > 0:
                if action == 'click':
                    success, _, error = safe_click(element, f"Click element")
                    if success and is_recording:
                        recorded_actions.append({
                            'type': 'click_by_selector',
                            'selector': selector,
                            'selector_type': selector_type,
                            'description': f"Click by {selector_type}"
                        })
                
                elif action in ['fill', 'type']:
                    # Check clipboard
                    clipboard_text = get_clipboard_text()
                    if clipboard_text:
                        use_clipboard = input(f"📋 Clipboard contains: '{clipboard_text[:50]}...' Use it? (y/n): ").strip().lower()
                        if use_clipboard == 'y':
                            value = clipboard_text
                        else:
                            value = input("Enter text: ").strip()
                    else:
                        value = input("Enter text: ").strip()
                    
                    if action == 'fill':
                        success, _, error = safe_fill(element, value, f"Fill element")
                    else:  # type
                        base_delay = user_preferences['typing_speed']
                        success, _, error = safe_type(element, value, base_delay, f"Type in element")
                    
                    if success and is_recording:
                        recorded_actions.append({
                            'type': f'{action}_by_selector',
                            'selector': selector,
                            'selector_type': selector_type,
                            'value': value,
                            'description': f"{action.capitalize()} by {selector_type}"
                        })
            else:
                print(f"✗ Could not find element with selector '{selector}'")
                print("💡 Tip: Check your selector syntax or inspect the page elements")
        except Exception as e:
            print(handle_common_errors(e, f"selector '{selector}'"))
    
    elif choice == '14':
        # Back to main menu
        return

def save_preferences():
    """Save user preferences to a file"""
    global user_preferences
    
    print("\n⚙️  Configure Your Preferences")
    print("=" * 50)
    
    # Typing speed
    speed_input = input(f"Typing speed in ms (50-200, current: {user_preferences['typing_speed']}): ").strip()
    if speed_input:
        try:
            user_preferences['typing_speed'] = int(speed_input)
        except ValueError:
            print("⚠ Invalid speed, keeping current value")
    
    # Enable typos
    typo_input = input(f"Enable typos? (y/n, current: {'yes' if user_preferences['enable_typos'] else 'no'}): ").strip().lower()
    if typo_input in ['y', 'n']:
        user_preferences['enable_typos'] = typo_input == 'y'
    
    # Typo chance
    if user_preferences['enable_typos']:
        chance_input = input(f"Typo chance 1-10% (current: {int(user_preferences['typo_chance']*100)}%): ").strip()
        if chance_input:
            try:
                user_preferences['typo_chance'] = int(chance_input) / 100
            except ValueError:
                print("⚠ Invalid chance, keeping current value")
    
    # Pause after punctuation
    punct_input = input(f"Smart pauses after punctuation? (y/n, current: {'yes' if user_preferences['pause_after_punctuation'] else 'no'}): ").strip().lower()
    if punct_input in ['y', 'n']:
        user_preferences['pause_after_punctuation'] = punct_input == 'y'
    
    # Thinking pauses
    think_input = input(f"Random thinking pauses? (y/n, current: {'yes' if user_preferences['thinking_pauses'] else 'no'}): ").strip().lower()
    if think_input in ['y', 'n']:
        user_preferences['thinking_pauses'] = think_input == 'y'
    
    print("\n🔄 Intelligent Automation Settings")
    print("-" * 50)
    
    # Max retries
    retry_input = input(f"Max retries for failed actions (1-10, current: {user_preferences['max_retries']}): ").strip()
    if retry_input:
        try:
            retries = int(retry_input)
            if 1 <= retries <= 10:
                user_preferences['max_retries'] = retries
            else:
                print("⚠ Invalid value, keeping current")
        except ValueError:
            print("⚠ Invalid value, keeping current")
    
    # Retry delay
    delay_input = input(f"Initial retry delay in seconds (0.5-5.0, current: {user_preferences['retry_delay']}): ").strip()
    if delay_input:
        try:
            delay = float(delay_input)
            if 0.5 <= delay <= 5.0:
                user_preferences['retry_delay'] = delay
            else:
                print("⚠ Invalid value, keeping current")
        except ValueError:
            print("⚠ Invalid value, keeping current")
    
    # Auto-wait timeout
    timeout_input = input(f"Auto-wait timeout in ms (5000-60000, current: {user_preferences['auto_wait_timeout']}): ").strip()
    if timeout_input:
        try:
            timeout = int(timeout_input)
            if 5000 <= timeout <= 60000:
                user_preferences['auto_wait_timeout'] = timeout
            else:
                print("⚠ Invalid value, keeping current")
        except ValueError:
            print("⚠ Invalid value, keeping current")
    
    # Verify actions
    verify_input = input(f"Verify actions succeed? (y/n, current: {'yes' if user_preferences['verify_actions'] else 'no'}): ").strip().lower()
    if verify_input in ['y', 'n']:
        user_preferences['verify_actions'] = verify_input == 'y'
    
    # Auto-scan after navigation
    auto_scan_input = input(f"Auto-scan after navigation? (y/n, current: {'yes' if user_preferences.get('auto_scan', True) else 'no'}): ").strip().lower()
    if auto_scan_input in ['y', 'n']:
        user_preferences['auto_scan'] = auto_scan_input == 'y'
    
    # Save to file
    if not os.path.exists('settings'):
        os.makedirs('settings')
    
    profile_name = input("\nSave as profile name (e.g., 'fast', 'careful', 'default'): ").strip()
    if not profile_name:
        profile_name = 'default'
    
    filepath = f"settings/{profile_name}.json"
    
    try:
        with open(filepath, 'w') as f:
            json.dump(user_preferences, f, indent=2)
        print(f"✓ Preferences saved to '{filepath}'")
        print(f"\n📋 Current Settings:")
        print(f"  • Typing speed: {user_preferences['typing_speed']}ms")
        print(f"  • Typos: {'Enabled' if user_preferences['enable_typos'] else 'Disabled'}")
        if user_preferences['enable_typos']:
            print(f"  • Typo chance: {int(user_preferences['typo_chance']*100)}%")
        print(f"  • Smart pauses: {'Enabled' if user_preferences['pause_after_punctuation'] else 'Disabled'}")
        print(f"  • Thinking pauses: {'Enabled' if user_preferences['thinking_pauses'] else 'Disabled'}")
        print(f"\n🔄 Intelligent Automation:")
        print(f"  • Max retries: {user_preferences['max_retries']}")
        print(f"  • Retry delay: {user_preferences['retry_delay']}s")
        print(f"  • Auto-wait timeout: {user_preferences['auto_wait_timeout']}ms")
        print(f"  • Verify actions: {'Enabled' if user_preferences['verify_actions'] else 'Disabled'}")
        print(f"  • Auto-scan pages: {'Enabled' if user_preferences.get('auto_scan', True) else 'Disabled'}")
    except Exception as e:
        print(f"✗ Error saving preferences: {e}")

def load_preferences():
    """Load user preferences from a file"""
    global user_preferences
    
    if not os.path.exists('settings'):
        print("⚠ No settings folder found!")
        return
    
    # List available profiles
    profiles = [f for f in os.listdir('settings') if f.endswith('.json')]
    
    if not profiles:
        print("⚠ No saved profiles found!")
        return
    
    print("\n📁 Available Profiles:")
    for i, profile in enumerate(profiles):
        profile_name = profile.replace('.json', '')
        print(f"  [{i}] {profile_name}")
    
    choice = input(f"\nEnter profile number [0-{len(profiles)-1}] (or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        print("Cancelled.")
        return
    
    try:
        idx = int(choice)
        filepath = f"settings/{profiles[idx]}"
        
        with open(filepath, 'r') as f:
            user_preferences = json.load(f)
        
        print(f"✓ Loaded profile: {profiles[idx].replace('.json', '')}")
        print(f"\n📋 Current Settings:")
        print(f"  • Typing speed: {user_preferences['typing_speed']}ms")
        print(f"  • Typos: {'Enabled' if user_preferences['enable_typos'] else 'Disabled'}")
        if user_preferences['enable_typos']:
            print(f"  • Typo chance: {int(user_preferences['typo_chance']*100)}%")
        print(f"  • Smart pauses: {'Enabled' if user_preferences['pause_after_punctuation'] else 'Disabled'}")
        print(f"  • Thinking pauses: {'Enabled' if user_preferences['thinking_pauses'] else 'Disabled'}")
        print(f"\n🔄 Intelligent Automation:")
        print(f"  • Max retries: {user_preferences.get('max_retries', 3)}")
        print(f"  • Retry delay: {user_preferences.get('retry_delay', 1.0)}s")
        print(f"  • Auto-wait timeout: {user_preferences.get('auto_wait_timeout', 30000)}ms")
        print(f"  • Verify actions: {'Enabled' if user_preferences.get('verify_actions', True) else 'Disabled'}")
        print(f"  • Auto-scan pages: {'Enabled' if user_preferences.get('auto_scan', True) else 'Disabled'}")
        
    except (ValueError, IndexError):
        print("✗ Invalid profile number")
    except Exception as e:
        print(f"✗ Error loading preferences: {e}")

def view_current_preferences():
    """Display current preferences"""
    global user_preferences
    
    print(f"\n📋 Current Settings:")
    print("=" * 50)
    print(f"  • Typing speed: {user_preferences['typing_speed']}ms")
    print(f"  • Typos: {'Enabled' if user_preferences['enable_typos'] else 'Disabled'}")
    if user_preferences['enable_typos']:
        print(f"  • Typo chance: {int(user_preferences['typo_chance']*100)}%")
    print(f"  • Smart pauses: {'Enabled' if user_preferences['pause_after_punctuation'] else 'Disabled'}")
    print(f"  • Thinking pauses: {'Enabled' if user_preferences['thinking_pauses'] else 'Disabled'}")
    print(f"\n🔄 Intelligent Automation:")
    print(f"  • Max retries: {user_preferences.get('max_retries', 3)}")
    print(f"  • Retry delay: {user_preferences.get('retry_delay', 1.0)}s")
    print(f"  • Auto-wait timeout: {user_preferences.get('auto_wait_timeout', 30000)}ms")
    print(f"  • Verify actions: {'Enabled' if user_preferences.get('verify_actions', True) else 'Disabled'}")
    print(f"  • Auto-scan pages: {'Enabled' if user_preferences.get('auto_scan', True) else 'Disabled'}")
    print("=" * 50)

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
    print("8. ⚙️  Save preferences")
    print("9. 📂 Load preferences")
    print("10. 📋 View current preferences")
    print("11. Close browser and exit")
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
        
        # Auto-load default preferences if they exist
        if os.path.exists('settings/default.json'):
            try:
                with open('settings/default.json', 'r') as f:
                    loaded_prefs = json.load(f)
                    user_preferences.update(loaded_prefs)
                print(f"✓ Loaded default preferences (typing speed: {user_preferences['typing_speed']}ms)")
            except Exception as e:
                print(f"⚠ Could not load default preferences: {e}")
        
        # Offer to resume last URL
        last_url = user_preferences.get('last_url', '')
        if last_url:
            resume = input(f"\n🔖 Resume last session? ({last_url}) (y/n): ").strip().lower()
            if resume == 'y':
                try:
                    print(f"Navigating to {last_url}...")
                    page.goto(last_url)
                    print(f"✓ Loaded: {page.title()}")
                    
                    # Auto-scan if enabled
                    if user_preferences.get('auto_scan', True):
                        print("\n🔍 Auto-scanning page elements...")
                        time.sleep(0.5)
                        scan_page_elements(page)
                except Exception as e:
                    print(f"⚠ Could not load last URL: {e}")
        
        # Interactive menu loop
        while True:
            show_menu()
            choice = input("\nEnter your choice (1-11): ").strip()
            
            if choice == '1':
                url = input("\n🔗 Enter website URL (e.g., google.com): ").strip()
                if not url.startswith('http'):
                    url = 'https://' + url
                try:
                    print(f"Navigating to {url}...")
                    page.goto(url)
                    print(f"✓ Loaded: {page.title()}")
                    
                    # Save last URL
                    user_preferences['last_url'] = url
                    
                    # Auto-scan if enabled
                    if user_preferences.get('auto_scan', True):
                        print("\n🔍 Auto-scanning page elements...")
                        time.sleep(0.5)  # Small delay to ensure page is fully loaded
                        scan_page_elements(page)
                    
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
                save_preferences()
            
            elif choice == '9':
                load_preferences()
            
            elif choice == '10':
                view_current_preferences()
            
            elif choice == '11':
                print("\n👋 Closing browser...")
                context.close()
                print("✓ Browser closed. Goodbye!")
                break
            
            else:
                print("⚠ Invalid choice. Please enter 1-11.")

if __name__ == "__main__":
    main()
