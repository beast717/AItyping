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

try:
    from pynput import keyboard
    HOTKEYS_AVAILABLE = True
except ImportError:
    HOTKEYS_AVAILABLE = False
    print("⚠ pynput not installed. Global hotkeys disabled. Install with: pip install pynput")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠ google-generativeai not installed. Gemini features disabled. Install with: pip install google-generativeai")


# Global variable to store scanned elements
page_elements = {}
# Global variable to store recorded actions
recorded_actions = []
is_recording = False

# Hotkey state
hotkey_listener = None
hotkey_action_queue = []

# Watch & Learn state
action_history = []  # Stores recent actions for pattern detection
detected_patterns = []  # Stores detected repetitive patterns
watch_and_learn_enabled = True  # Enable by default
pattern_threshold = 2  # Number of repetitions needed to detect pattern

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
    'last_url': '',
    'last_scroll_position': 0,
    'form_field_cache': {},
    'enable_hotkeys': False,
    'hotkey_record': 'ctrl+shift+r',
    'hotkey_replay': 'ctrl+shift+p',
    'clipboard_auto_suggest': True,
    'gemini_api_key': '',  # Set via preferences
    'gemini_model': 'gemini-2.0-flash-exp',  # Free and fast model
    'gemini_custom_instructions': '',  # Saved custom rating instructions
    'gemini_saved_instructions': [],  # List of previously used instructions
    'gemini_last_categories': []  # Last used rating categories with scales
}

def get_clipboard_text():
    """Get text from clipboard if available"""
    if CLIPBOARD_AVAILABLE:
        try:
            return pyperclip.paste()
        except Exception:
            return None
    return None

def save_page_context(page):
    """Save current page context for resuming later"""
    try:
        context = {
            'url': page.url,
            'scroll_position': page.evaluate('window.pageYOffset'),
            'form_fields': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Save all input values
        inputs = page.locator('input[type="text"], input[type="email"], input[type="password"], input[type="tel"], input[type="url"], input[type="number"]').all()
        for i, inp in enumerate(inputs):
            try:
                value = inp.input_value()
                if value:
                    selector = f"input:nth-of-type({i+1})"
                    context['form_fields'][selector] = value
            except:
                continue
        
        # Save textarea values
        textareas = page.locator('textarea').all()
        for i, ta in enumerate(textareas):
            try:
                value = ta.input_value()
                if value:
                    selector = f"textarea:nth-of-type({i+1})"
                    context['form_fields'][selector] = value
            except:
                continue
        
        user_preferences['last_scroll_position'] = context['scroll_position']
        user_preferences['form_field_cache'] = context['form_fields']
        
        return context
    except Exception as e:
        print(f"⚠ Could not save page context: {e}")
        return None

def restore_page_context(page, context=None):
    """Restore saved page context"""
    try:
        if context is None:
            # Use saved preferences
            scroll_pos = user_preferences.get('last_scroll_position', 0)
            form_fields = user_preferences.get('form_field_cache', {})
        else:
            scroll_pos = context.get('scroll_position', 0)
            form_fields = context.get('form_fields', {})
        
        # Restore scroll position
        if scroll_pos > 0:
            page.evaluate(f'window.scrollTo(0, {scroll_pos})')
            print(f"✓ Restored scroll position: {scroll_pos}px")
        
        # Restore form field values
        restored_count = 0
        for selector, value in form_fields.items():
            try:
                element = page.locator(selector).first
                if element.count() > 0:
                    element.fill(value)
                    restored_count += 1
            except:
                continue
        
        if restored_count > 0:
            print(f"✓ Restored {restored_count} form field(s)")
        
        return True
    except Exception as e:
        print(f"⚠ Could not restore page context: {e}")
        return False

def setup_hotkeys():
    """Setup global hotkeys for automation control"""
    global hotkey_listener, hotkey_action_queue
    
    if not HOTKEYS_AVAILABLE:
        return None
    
    def on_activate_record():
        """Hotkey callback for recording toggle"""
        hotkey_action_queue.append('toggle_record')
        print("\n🔥 Hotkey: Toggle Recording")
    
    def on_activate_replay():
        """Hotkey callback for replay last session"""
        hotkey_action_queue.append('replay_last')
        print("\n🔥 Hotkey: Replay Last Session")
    
    # Parse hotkey strings
    try:
        from pynput.keyboard import HotKey, Key, KeyCode
        
        # Create hotkey combinations
        record_keys = {Key.ctrl, Key.shift, KeyCode.from_char('r')}
        replay_keys = {Key.ctrl, Key.shift, KeyCode.from_char('p')}
        
        record_hotkey = HotKey(record_keys, on_activate_record)
        replay_hotkey = HotKey(replay_keys, on_activate_replay)
        
        def for_canonical(f):
            return lambda k: f(listener.canonical(k))
        
        # Start listener
        listener = keyboard.Listener(
            on_press=for_canonical(lambda key: (
                record_hotkey.press(key),
                replay_hotkey.press(key)
            )),
            on_release=for_canonical(lambda key: (
                record_hotkey.release(key),
                replay_hotkey.release(key)
            ))
        )
        
        listener.start()
        hotkey_listener = listener
        
        print("✓ Global hotkeys enabled:")
        print("  • Ctrl+Shift+R - Toggle Recording")
        print("  • Ctrl+Shift+P - Replay Last Session")
        
        return listener
    except Exception as e:
        print(f"⚠ Could not setup hotkeys: {e}")
        return None

def stop_hotkeys():
    """Stop global hotkey listener"""
    global hotkey_listener
    if hotkey_listener:
        try:
            hotkey_listener.stop()
            hotkey_listener = None
            print("✓ Hotkeys disabled")
        except:
            pass

def process_hotkey_actions():
    """Process queued hotkey actions"""
    global hotkey_action_queue
    
    actions = hotkey_action_queue.copy()
    hotkey_action_queue.clear()
    
    return actions

def track_action(action_type, details):
    """
    Track user actions for pattern detection (Watch & Learn)
    """
    global action_history
    
    if not watch_and_learn_enabled:
        return
    
    # Create action record
    action_record = {
        'type': action_type,
        'details': details,
        'timestamp': datetime.now().isoformat(),
        'sequence_id': len(action_history)
    }
    
    action_history.append(action_record)
    
    # Keep only last 50 actions to avoid memory issues
    if len(action_history) > 50:
        action_history = action_history[-50:]
    
    # Check for patterns after each action
    detect_patterns()

def detect_patterns():
    """
    Detect repetitive patterns in action history
    """
    global action_history, detected_patterns, pattern_threshold
    
    if len(action_history) < 4:  # Need at least 4 actions to detect pattern
        return
    
    # Look for sequences of 2-5 actions that repeat
    for sequence_length in range(2, min(6, len(action_history) // 2 + 1)):
        # Get the most recent sequence
        recent_sequence = action_history[-sequence_length:]
        
        # Check if this sequence appeared before
        for i in range(len(action_history) - sequence_length * 2, -1, -1):
            candidate_sequence = action_history[i:i + sequence_length]
            
            # Compare sequences (ignoring timestamps and IDs)
            if sequences_match(recent_sequence, candidate_sequence):
                # Found a pattern!
                pattern_key = sequence_to_key(recent_sequence)
                
                # Check if we already detected this pattern
                existing_pattern = None
                for p in detected_patterns:
                    if p['key'] == pattern_key:
                        existing_pattern = p
                        break
                
                if existing_pattern:
                    existing_pattern['count'] += 1
                    existing_pattern['last_seen'] = datetime.now().isoformat()
                    
                    # Offer automation after threshold repetitions
                    if existing_pattern['count'] == pattern_threshold and not existing_pattern.get('offered'):
                        existing_pattern['offered'] = True
                        notify_pattern_detected(existing_pattern)
                else:
                    # New pattern detected
                    new_pattern = {
                        'key': pattern_key,
                        'sequence': [a.copy() for a in recent_sequence],
                        'count': 2,  # We found it twice (current + previous)
                        'first_seen': candidate_sequence[0]['timestamp'],
                        'last_seen': datetime.now().isoformat(),
                        'offered': False
                    }
                    detected_patterns.append(new_pattern)
                
                return  # Only detect one pattern at a time

def sequences_match(seq1, seq2):
    """
    Check if two action sequences match (ignoring timestamps and IDs)
    """
    if len(seq1) != len(seq2):
        return False
    
    for a1, a2 in zip(seq1, seq2):
        # Compare action types
        if a1['type'] != a2['type']:
            return False
        
        # Compare key details (ignore values that might change)
        d1 = a1['details']
        d2 = a2['details']
        
        # For different action types, compare different fields
        if a1['type'] in ['click_button', 'click_link']:
            # For clicks, compare element index
            if d1.get('index') != d2.get('index'):
                return False
        elif a1['type'] in ['type_by_label', 'fill_input']:
            # For typing, compare label/field but not value
            if d1.get('label') != d2.get('label') and d1.get('index') != d2.get('index'):
                return False
        elif a1['type'] == 'navigate':
            # For navigation, compare URL
            if d1.get('url') != d2.get('url'):
                return False
    
    return True

def sequence_to_key(sequence):
    """
    Convert action sequence to a unique key for identification
    """
    key_parts = []
    for action in sequence:
        action_type = action['type']
        details = action['details']
        
        if action_type in ['click_button', 'click_link']:
            key_parts.append(f"{action_type}_{details.get('index', 'unknown')}")
        elif action_type in ['type_by_label', 'fill_input']:
            key_parts.append(f"{action_type}_{details.get('label', details.get('index', 'unknown'))}")
        elif action_type == 'navigate':
            key_parts.append(f"{action_type}_{details.get('url', 'unknown')}")
        else:
            key_parts.append(action_type)
    
    return "->".join(key_parts)

def notify_pattern_detected(pattern):
    """
    Notify user that a repetitive pattern was detected
    """
    print("\n" + "="*60)
    print("🔍 PATTERN DETECTED! (Watch & Learn)")
    print("="*60)
    print(f"I noticed you've repeated this sequence {pattern['count']} times:")
    print()
    
    for i, action in enumerate(pattern['sequence'], 1):
        action_desc = get_action_description(action)
        print(f"  {i}. {action_desc}")
    
    print()
    print("💡 Would you like me to automate this for you?")
    print("   • Type 'y' to create an automation")
    print("   • Type 'n' to ignore this pattern")
    print("   • Type 's' to save as a template")
    print("="*60)

def get_action_description(action):
    """
    Get human-readable description of an action
    """
    action_type = action['type']
    details = action['details']
    
    descriptions = {
        'click_button': f"Click button [{details.get('index', '?')}]",
        'click_link': f"Click link [{details.get('index', '?')}]",
        'fill_input': f"Fill input [{details.get('index', '?')}] with text",
        'type_input': f"Type in input [{details.get('index', '?')}]",
        'type_by_label': f"Type in field '{details.get('label', '?')}'",
        'fill_textarea': f"Fill textarea [{details.get('index', '?')}]",
        'type_textarea': f"Type in textarea [{details.get('index', '?')}]",
        'navigate': f"Navigate to {details.get('url', '?')}",
        'click_by_text': f"Click '{details.get('text', '?')}'",
        'auto_fill_form': "Auto-fill form"
    }
    
    return descriptions.get(action_type, f"{action_type}")

def create_automation_from_pattern(pattern, name=None):
    """
    Create a reusable automation from a detected pattern
    """
    if name is None:
        name = input("\nEnter name for this automation: ").strip()
        if not name:
            name = f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Convert pattern to session format
    session_actions = []
    for action in pattern['sequence']:
        session_actions.append({
            'type': action['type'],
            **action['details'],
            'description': get_action_description(action)
        })
    
    # Save as session
    if not os.path.exists('sessions'):
        os.makedirs('sessions')
    
    filepath = f"sessions/{name}.json"
    
    try:
        with open(filepath, 'w') as f:
            json.dump(session_actions, f, indent=2)
        
        print(f"\n✅ Automation saved as '{name}'")
        print(f"   File: {filepath}")
        print(f"   Actions: {len(session_actions)}")
        print(f"\n💡 You can replay this anytime with Menu Option #7")
        
        return True
    except Exception as e:
        print(f"\n✗ Error saving automation: {e}")
        return False

def check_for_pattern_prompts():
    """
    Check if there are any patterns that need user attention
    Returns True if user wants to create automation
    """
    global detected_patterns
    
    for pattern in detected_patterns:
        if pattern.get('offered') and not pattern.get('handled'):
            notify_pattern_detected(pattern)
            
            response = input("\nYour choice (y/n/s): ").strip().lower()
            pattern['handled'] = True
            
            if response == 'y':
                # Create automation
                create_automation_from_pattern(pattern)
                return True
            elif response == 's':
                # Save as template
                create_automation_from_pattern(pattern)
                return True
            elif response == 'n':
                print("Pattern ignored. I'll keep watching for other patterns.")
    
    return False

def toggle_watch_and_learn():
    """Toggle Watch & Learn feature on/off"""
    global watch_and_learn_enabled
    
    watch_and_learn_enabled = not watch_and_learn_enabled
    
    if watch_and_learn_enabled:
        print("\n👁️ Watch & Learn ENABLED")
        print("   I'll observe your actions and detect repetitive patterns")
        print("   When I notice you repeating something, I'll offer to automate it")
    else:
        print("\n👁️ Watch & Learn DISABLED")
        print("   Pattern detection turned off")

def view_detected_patterns():
    """View all detected patterns"""
    global detected_patterns
    
    if not detected_patterns:
        print("\n📊 No patterns detected yet")
        print("   Keep working and I'll watch for repetitive actions!")
        return
    
    print("\n📊 Detected Patterns:")
    print("="*60)
    
    for i, pattern in enumerate(detected_patterns):
        print(f"\n[{i}] Pattern (repeated {pattern['count']} times):")
        for j, action in enumerate(pattern['sequence'], 1):
            print(f"    {j}. {get_action_description(action)}")
        
        if pattern.get('handled'):
            print("    Status: ✓ Handled")
        elif pattern.get('offered'):
            print("    Status: ⏳ Waiting for response")
        else:
            print("    Status: 👁️ Watching")
    
    print("="*60)
    
    # Offer to create automation from any pattern
    create_choice = input("\nCreate automation from pattern? (enter number or 'n'): ").strip()
    
    if create_choice.isdigit():
        idx = int(create_choice)
        if 0 <= idx < len(detected_patterns):
            create_automation_from_pattern(detected_patterns[idx])

# ============================================================================
# INTELLIGENT WORKFLOW LEARNING
# ============================================================================

def add_conditional_logic_to_session(session_actions):
    """
    Add intelligent conditional logic to session actions
    """
    print("\n🧠 Intelligent Workflow Enhancement")
    print("="*60)
    print("Adding smart error handling and conditional logic...")
    
    enhanced_actions = []
    
    for i, action in enumerate(session_actions):
        # Wrap each action with error handling
        enhanced_action = action.copy()
        enhanced_action['error_handling'] = {
            'max_retries': 3,
            'retry_delay': 1.0,
            'on_error': 'continue',  # continue, stop, or skip
            'fallback_actions': []
        }
        
        # Add conditional checks based on action type
        if action['type'] in ['click_button', 'click_link', 'click_by_text']:
            enhanced_action['conditions'] = {
                'wait_for_visible': True,
                'wait_for_clickable': True,
                'timeout': 10000
            }
            # Add fallback: try alternative selectors
            enhanced_action['error_handling']['fallback_actions'].append({
                'type': 'find_similar',
                'description': 'Try to find similar element by text'
            })
        
        elif action['type'] in ['type_by_label', 'fill_input']:
            enhanced_action['conditions'] = {
                'wait_for_enabled': True,
                'clear_before_type': True,
                'verify_value': True
            }
            # Add fallback: try to find field by different attributes
            enhanced_action['error_handling']['fallback_actions'].append({
                'type': 'find_by_placeholder',
                'description': 'Try finding by placeholder if label fails'
            })
        
        elif action['type'] == 'navigate':
            enhanced_action['conditions'] = {
                'wait_for_load': True,
                'verify_url': True,
                'load_timeout': 30000
            }
            # Add retry on network errors
            enhanced_action['error_handling']['max_retries'] = 5
            enhanced_action['error_handling']['on_error'] = 'retry'
        
        enhanced_actions.append(enhanced_action)
    
    print(f"✓ Enhanced {len(enhanced_actions)} actions with intelligent logic")
    return enhanced_actions

def detect_workflow_patterns(session_actions):
    """
    Detect common workflow patterns and suggest improvements
    """
    patterns_found = []
    
    # Detect login pattern
    if any('password' in str(a.get('label', '')).lower() or 
           a.get('type') == 'fill_input' for a in session_actions):
        has_username = any('user' in str(a.get('label', '')).lower() or 
                          'email' in str(a.get('label', '')).lower() for a in session_actions)
        has_submit = any('click' in a.get('type', '') for a in session_actions)
        
        if has_username and has_submit:
            patterns_found.append({
                'name': 'Login Flow',
                'confidence': 0.9,
                'suggestion': 'Add session persistence check to skip login if already logged in'
            })
    
    # Detect form fill pattern
    type_actions = [a for a in session_actions if 'type' in a.get('type', '') or 'fill' in a.get('type', '')]
    if len(type_actions) >= 3:
        patterns_found.append({
            'name': 'Multi-Field Form',
            'confidence': 0.85,
            'suggestion': 'Add validation checks after each field to ensure values are accepted'
        })
    
    # Detect navigation pattern
    nav_actions = [a for a in session_actions if a.get('type') == 'navigate']
    if len(nav_actions) > 1:
        patterns_found.append({
            'name': 'Multi-Page Navigation',
            'confidence': 0.8,
            'suggestion': 'Add breadcrumb tracking to resume from last successful page'
        })
    
    # Detect repetitive clicks (pagination)
    click_actions = [a for a in session_actions if 'click' in a.get('type', '')]
    if len(click_actions) >= 3:
        similar_clicks = sum(1 for i in range(len(click_actions)-1) 
                           if click_actions[i].get('text') == click_actions[i+1].get('text'))
        if similar_clicks >= 2:
            patterns_found.append({
                'name': 'Repetitive Clicking (Pagination?)',
                'confidence': 0.75,
                'suggestion': 'Convert to loop that continues until element disappears'
            })
    
    return patterns_found

def suggest_workflow_improvements(session_actions):
    """
    Analyze session and suggest intelligent improvements
    """
    print("\n🧠 Analyzing Workflow...")
    patterns = detect_workflow_patterns(session_actions)
    
    if not patterns:
        print("✓ No obvious improvements detected")
        return session_actions
    
    print(f"\n💡 Found {len(patterns)} improvement opportunities:")
    print("="*60)
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\n{i}. {pattern['name']} (confidence: {pattern['confidence']*100:.0f}%)")
        print(f"   💡 {pattern['suggestion']}")
    
    print("="*60)
    
    enhance = input("\n🚀 Apply intelligent enhancements? (y/n): ").strip().lower()
    
    if enhance == 'y':
        return add_conditional_logic_to_session(session_actions)
    
    return session_actions

def create_loop_workflow(action_sequence, loop_condition):
    """
    Create a workflow that loops until a condition is met
    """
    loop_workflow = {
        'type': 'loop',
        'actions': action_sequence,
        'condition': loop_condition,
        'max_iterations': 100,  # Safety limit
        'description': f'Repeat actions until {loop_condition["type"]}'
    }
    
    return loop_workflow

def add_error_recovery(action, common_errors):
    """
    Add intelligent error recovery based on common error patterns
    """
    recovery_strategies = {
        'element_not_found': [
            {'action': 'wait', 'duration': 2000, 'description': 'Wait for dynamic content'},
            {'action': 'scroll_into_view', 'description': 'Scroll element into viewport'},
            {'action': 'refresh_page', 'description': 'Refresh and retry'}
        ],
        'timeout': [
            {'action': 'increase_timeout', 'multiplier': 2, 'description': 'Double the timeout'},
            {'action': 'check_network', 'description': 'Check for slow network'}
        ],
        'stale_element': [
            {'action': 're_scan', 'description': 'Re-scan page for fresh elements'},
            {'action': 'retry', 'description': 'Retry action immediately'}
        ],
        'not_clickable': [
            {'action': 'wait_for_overlay', 'description': 'Wait for overlay to disappear'},
            {'action': 'force_click', 'description': 'Use JavaScript click as fallback'}
        ]
    }
    
    action['error_recovery'] = {}
    for error_type, strategies in recovery_strategies.items():
        if error_type in common_errors:
            action['error_recovery'][error_type] = strategies
    
    return action

def chain_workflows(workflow1, workflow2, condition=None):
    """
    Chain two workflows together with optional condition
    """
    chained = {
        'type': 'chained_workflow',
        'workflows': [workflow1, workflow2],
        'condition': condition or {'type': 'always'},
        'description': f'Chain: {workflow1.get("name", "Workflow 1")} → {workflow2.get("name", "Workflow 2")}'
    }
    
    return chained

def smart_workflow_builder():
    """
    Interactive workflow builder with intelligent suggestions
    """
    print("\n🎯 Smart Workflow Builder")
    print("="*60)
    print("I'll help you build an intelligent workflow with:")
    print("  • Automatic error handling")
    print("  • Conditional logic")
    print("  • Loop support")
    print("  • Multi-path navigation")
    print("="*60)
    
    workflow_type = input("\nWorkflow type?\n  1. Linear (step by step)\n  2. Conditional (if/else)\n  3. Loop (repeat until condition)\n  4. Multi-path (try alternatives)\nChoice: ").strip()
    
    if workflow_type == '1':
        print("\n📝 Linear workflow - I'll add smart error handling automatically")
        return 'linear'
    elif workflow_type == '2':
        print("\n🔀 Conditional workflow - Define your conditions")
        condition = input("If what condition? (e.g., 'element exists', 'text contains'): ").strip()
        return {'type': 'conditional', 'condition': condition}
    elif workflow_type == '3':
        print("\n🔄 Loop workflow - Define stop condition")
        stop_condition = input("Stop when? (e.g., 'button disappears', 'page number > 10'): ").strip()
        return {'type': 'loop', 'stop_condition': stop_condition}
    elif workflow_type == '4':
        print("\n🌐 Multi-path workflow - I'll try alternatives if primary fails")
        return 'multi_path'
    else:
        print("Invalid choice, using linear workflow")
        return 'linear'

# ============================================================================
# GEMINI API INTEGRATION FOR AUTO-RATING
# ============================================================================

def setup_gemini_api():
    """Configure Gemini API with user's key"""
    global user_preferences
    
    if not GEMINI_AVAILABLE:
        print("\n⚠ Gemini API not available")
        print("Install with: pip install google-generativeai")
        return False
    
    api_key = user_preferences.get('gemini_api_key', '')
    
    if not api_key:
        print("\n🔑 Gemini API Key Setup")
        print("="*60)
        print("Get your API key from: https://makersuite.google.com/app/apikey")
        api_key = input("Enter your Gemini API key: ").strip()
        
        if api_key:
            user_preferences['gemini_api_key'] = api_key
            print("✓ API key saved to preferences")
        else:
            print("✗ No API key provided")
            return False
    
    # Ask about model selection
    print("\n🤖 Gemini Model Selection:")
    print("="*60)
    print("Available models:")
    print("1. gemini-2.0-flash-exp (Recommended - Fast & Free)")
    print("2. gemini-1.5-flash (Fast & Free)")
    print("3. gemini-1.5-pro (More powerful)")
    print("4. gemini-2.5-pro (Most powerful)")
    print(f"\nCurrent model: {user_preferences.get('gemini_model', 'gemini-2.0-flash-exp')}")
    
    change_model = input("\nChange model? (y/n): ").strip().lower()
    
    if change_model == 'y':
        model_choice = input("Enter choice (1-4): ").strip()
        model_map = {
            "1": "gemini-2.0-flash-exp",
            "2": "gemini-1.5-flash",
            "3": "gemini-1.5-pro",
            "4": "gemini-2.5-pro"
        }
        
        if model_choice in model_map:
            user_preferences['gemini_model'] = model_map[model_choice]
            print(f"✓ Model set to: {model_map[model_choice]}")
    
    try:
        genai.configure(api_key=api_key)
        print("✓ Gemini API configured")
        return True
    except Exception as e:
        print(f"✗ Error configuring Gemini API: {e}")
        return False

def auto_detect_rating_categories(page):
    """Auto-detect rating categories from the page"""
    print("\n🔍 Auto-detecting rating categories...")
    
    detected_categories = []
    
    try:
        # Common category keywords to look for
        category_keywords = [
            'localization', 'instruction following', 'truthfulness', 
            'helpfulness', 'harmlessness', 'honesty', 'accuracy',
            'relevance', 'completeness', 'clarity', 'coherence',
            'tone', 'style', 'grammar', 'structure', 'writing style',
            'factual correctness', 'safety', 'appropriateness'
        ]
        
        # Try to find category headings/labels
        for keyword in category_keywords:
            try:
                # Look for text containing the keyword (case-insensitive)
                elements = page.locator(f'text=/{keyword}/i').all()
                
                for elem in elements[:1]:  # Take first match
                    try:
                        text = elem.inner_text().strip()
                        # Clean up the text (remove emojis, extra spaces, etc.)
                        clean_text = ' '.join(text.split())
                        
                        # Check if it looks like a category name (not too long)
                        if 5 < len(clean_text) < 60 and clean_text not in [cat['name'] for cat in detected_categories]:
                            detected_categories.append({
                                'name': clean_text,
                                'scale': '1-3'  # Default scale
                            })
                    except:
                        continue
            except:
                continue
        
        # Also try to find common heading patterns
        try:
            headings = page.locator('h1, h2, h3, h4, h5, h6, label, legend, [role="heading"]').all()
            for heading in headings[:20]:  # Check first 20 headings
                try:
                    text = heading.inner_text().strip()
                    clean_text = ' '.join(text.split())
                    
                    # Check if it looks like a category (contains key phrases)
                    if any(word in clean_text.lower() for word in ['rate', 'evaluate', 'assess', 'quality']) and \
                       5 < len(clean_text) < 60 and \
                       clean_text not in [cat['name'] for cat in detected_categories]:
                        detected_categories.append({
                            'name': clean_text,
                            'scale': '1-3'
                        })
                except:
                    continue
        except:
            pass
        
        return detected_categories[:10]  # Return max 10 categories
        
    except Exception as e:
        print(f"⚠ Error auto-detecting: {e}")
        return []

def extract_response_text(page):
    """Extract the model response text from the rating page"""
    print("\n📝 Text Extraction Method:")
    print("1. Auto-detect (try to find response text automatically)")
    print("2. Manual selection (click to select text area)")
    print("3. Copy from clipboard (you copy the text, I'll use it)")
    print("4. Specify CSS selector")
    
    method = input("\nChoice (1/2/3/4): ").strip()
    
    try:
        if method == '2':
            # Manual selection
            print("\n👆 Click on the element containing the response text...")
            print("Waiting for you to click...")
            
            # Wait for user to click an element
            clicked_element = page.wait_for_selector('*:hover', timeout=30000)
            if clicked_element:
                text = clicked_element.inner_text().strip()
                if len(text) > 20:
                    print(f"✓ Extracted {len(text)} characters from clicked element")
                    return text
                else:
                    print("⚠ Element has very little text, trying auto-detect...")
                    method = '1'
        
        elif method == '3':
            # Use clipboard
            clipboard_text = get_clipboard_text()
            if clipboard_text and len(clipboard_text) > 20:
                print(f"✓ Using clipboard text ({len(clipboard_text)} characters)")
                return clipboard_text
            else:
                print("⚠ No valid text in clipboard, trying auto-detect...")
                method = '1'
        
        elif method == '4':
            # Custom CSS selector
            selector = input("Enter CSS selector (e.g., 'div.response-text'): ").strip()
            try:
                element = page.locator(selector).first
                text = element.inner_text().strip()
                if text:
                    print(f"✓ Extracted {len(text)} characters using selector")
                    return text
                else:
                    print("⚠ Selector found no text, trying auto-detect...")
                    method = '1'
            except:
                print("⚠ Selector failed, trying auto-detect...")
                method = '1'
        
        # Method 1 or fallback: Auto-detect
        if method == '1' or True:
            print("\n🔍 Auto-detecting response text...")
            response_texts = []
            
            # Strategy 1: Look for common response containers
            selectors = [
                '[class*="response"]',
                '[class*="model-output"]',
                '[class*="answer"]',
                '[class*="content"]',
                '[role="article"]',
                'div[class*="text"]',
                'pre',
                'code',
                'p'
            ]
            
            for selector in selectors:
                try:
                    elements = page.locator(selector).all()
                    for elem in elements[:10]:  # Check first 10
                        try:
                            text = elem.inner_text().strip()
                            if len(text) > 100:  # Likely a response if longer than 100 chars
                                response_texts.append(text)
                        except:
                            continue
                except:
                    continue
            
            if response_texts:
                # Find the longest unique text
                unique_texts = list(set(response_texts))
                longest_text = max(unique_texts, key=len)
                
                # Show preview and ask for confirmation
                print(f"\n📄 Found text ({len(longest_text)} characters):")
                print("="*60)
                print(longest_text[:300] + "..." if len(longest_text) > 300 else longest_text)
                print("="*60)
                
                confirm = input("\nUse this text? (y/n): ").strip().lower()
                if confirm == 'y':
                    return longest_text
                else:
                    print("Let's try again...")
                    return extract_response_text(page)  # Retry with different method
            
            # Fallback: get all visible text
            print("⚠ Could not auto-detect, extracting all page text...")
            body_text = page.locator('body').inner_text()
            
            if len(body_text) > 100:
                print(f"\n📄 Extracted all page text ({len(body_text)} characters):")
                print("="*60)
                print(body_text[:300] + "..." if len(body_text) > 300 else body_text)
                print("="*60)
                
                confirm = input("\nUse this text? (y/n): ").strip().lower()
                if confirm == 'y':
                    return body_text[:10000]  # Limit to 10k chars
            
            print("✗ Could not extract text")
            return None
        
    except Exception as e:
        print(f"⚠ Error extracting response text: {e}")
        return None

def get_gemini_rating(response_text, category="overall", scale_type="1-3", custom_instructions=""):
    """
    Send response to Gemini for rating evaluation
    Supports different scales: 1-3, 1-5, -2 to +2, etc.
    Accepts custom instructions for specific rating criteria
    """
    if not GEMINI_AVAILABLE:
        print("⚠ Gemini API not available")
        return None
    
    try:
        model = genai.GenerativeModel(user_preferences.get('gemini_model', 'gemini-2.0-flash-exp'))
        
        # Define scale-specific prompts
        scale_configs = {
            "1-3": {
                "scale": "1-3",
                "options": "1 = Major Issues, 2 = Minor Issues, 3 = No Issues",
                "pattern": r'\b([123])\b'
            },
            "1-5": {
                "scale": "1-5",
                "options": "1 = Highly unsatisfying, 2 = Slightly unsatisfying, 3 = Okay, 4 = Slightly satisfying, 5 = Highly satisfying",
                "pattern": r'\b([12345])\b'
            },
            "-2-2": {
                "scale": "-2 to +2",
                "options": "-2 = Too Short (Major Issue), -1 = Just Right (No Issue), 0 = Just Right, +1 = Just Right, +2 = Too Verbose (Major Issue)",
                "pattern": r'\b(-?[012])\b'
            }
        }
        
        config = scale_configs.get(scale_type, scale_configs["1-3"])
        
        # Build custom instructions section
        custom_section = ""
        if custom_instructions:
            custom_section = f"""
CUSTOM RATING INSTRUCTIONS:
{custom_instructions}

Follow these custom instructions carefully when evaluating the response.
"""
        
        # Create rating prompt
        prompt = f"""You are evaluating a model response for quality. 

Category: {category}

Response to evaluate:
\"\"\"
{response_text}
\"\"\"

Rate this response on a scale of {config['scale']}:
{config['options']}
{custom_section}
Standard Evaluation Criteria:
- Localization: Is the language appropriate and natural for the intended audience?
- Instruction Following: Does it follow all requirements in the prompt?
- Truthfulness: Is the information accurate and reliable?
- Overall Quality: Grammar, coherence, helpfulness
- Completeness: Does it fully address the question/task?
- Tone & Style: Is the tone appropriate for the context?

Respond with ONLY the number/value and a brief reason (one sentence).
Format: NUMBER: Reason

Example: 3: Response is well-written, accurate, and follows all instructions perfectly."""

        response = model.generate_content(prompt)
        rating_text = response.text.strip()
        
        # Show Gemini's reasoning
        print(f"  💭 Gemini's reasoning: {rating_text}")
        
        # Extract number from response using pattern
        import re
        match = re.search(config['pattern'], rating_text)
        if match:
            rating_value = match.group(1)
            # Convert to appropriate type
            if scale_type == "-2-2":
                return int(rating_value)
            else:
                return int(rating_value)
        
        print(f"⚠ Could not parse rating from: {rating_text}")
        return None
            
    except Exception as e:
        print(f"✗ Error getting Gemini rating: {e}")
        return None

def auto_rate_with_gemini(page):
    """
    Automatically rate the response using Gemini API
    Supports multiple categories and different rating scales
    """
    print("\n🤖 Gemini Auto-Rating")
    print("="*60)
    
    # Check if Gemini is configured
    if not setup_gemini_api():
        return
    
    # Extract response text
    response_text = extract_response_text(page)
    
    if not response_text:
        print("✗ Could not extract response text")
        print("💡 Tip: Make sure you're on the rating page with the model response visible")
        return
    
    print(f"\n✓ Extracted {len(response_text)} characters")
    
    # Ask for custom rating instructions
    print("\n📋 Custom Rating Instructions (Optional)")
    print("="*60)
    
    # Show saved instructions if any
    saved_instructions = user_preferences.get('gemini_saved_instructions', [])
    last_instructions = user_preferences.get('gemini_custom_instructions', '')
    
    if last_instructions or saved_instructions:
        print("Previously used instructions:")
        if last_instructions:
            print(f"  Last used: {last_instructions[:80]}...")
        
        if saved_instructions:
            print("\nSaved instruction templates:")
            for i, instr in enumerate(saved_instructions[:5], 1):  # Show max 5
                print(f"  {i}. {instr[:80]}...")
        
        print("\nOptions:")
        print("  • Press Enter to use last instructions")
        if saved_instructions:
            print("  • Enter a number (1-{}) to use saved template".format(len(saved_instructions[:5])))
        print("  • Type 'new' to enter new instructions")
        print("  • Type 'none' to skip custom instructions")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == '':
            custom_instructions = last_instructions
            print(f"✓ Using last instructions: {custom_instructions[:100]}...")
        elif choice == 'none':
            custom_instructions = ''
            print("✓ Using default evaluation criteria")
        elif choice == 'new':
            custom_instructions = None  # Will prompt below
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(saved_instructions):
                custom_instructions = saved_instructions[idx]
                print(f"✓ Using saved template: {custom_instructions[:100]}...")
            else:
                custom_instructions = None
        else:
            custom_instructions = None
    else:
        custom_instructions = None
    
    # Prompt for new instructions if needed
    if custom_instructions is None:
        print("\nYou can provide specific criteria for rating.")
        print("Examples:")
        print("  • 'Focus on whether the response is appropriate for a 5-year-old'")
        print("  • 'Check if medical information is accurate and cites sources'")
        print("  • 'Evaluate if the translation sounds natural to native speakers'")
        print("  • 'Rate based on whether it addresses all 5 requirements listed'")
        print("\nLeave blank to use default criteria.")
        print("="*60)
        
        custom_instructions = input("\nEnter custom instructions (or Enter to skip): ").strip()
    
    # Save instructions if provided
    if custom_instructions:
        print(f"✓ Using custom instructions: {custom_instructions[:100]}...")
        
        # Save as last used
        user_preferences['gemini_custom_instructions'] = custom_instructions
        
        # Ask to save as template
        save_template = input("\n💾 Save these instructions as a reusable template? (y/n): ").strip().lower()
        if save_template == 'y':
            saved_list = user_preferences.get('gemini_saved_instructions', [])
            if custom_instructions not in saved_list:
                saved_list.append(custom_instructions)
                user_preferences['gemini_saved_instructions'] = saved_list
                print(f"✓ Saved as template #{len(saved_list)}")
    else:
        print("✓ Using default evaluation criteria")
    
    # Ask for rating configuration
    print("\n📊 Rating Configuration:")
    print("1. Single category (quick)")
    print("2. Multiple categories (batch)")
    
    mode = input("\nChoice (1/2): ").strip()
    
    if mode == '2':
        # Batch mode
        categories = []
        
        # Check if we have saved categories
        last_categories = user_preferences.get('gemini_last_categories', [])
        
        if last_categories:
            print("\n💾 Previously used categories:")
            for i, cat in enumerate(last_categories, 1):
                print(f"  {i}. {cat['name']} (scale: {cat['scale']})")
            
            print("\nOptions:")
            print("  1. Use saved categories")
            print("  2. Auto-detect from page")
            print("  3. Enter manually")
            
            cat_choice = input("\nYour choice (1/2/3): ").strip()
            
            if cat_choice == '1':
                categories = last_categories.copy()
                print(f"✓ Using {len(categories)} saved categories")
            elif cat_choice == '2':
                detected = auto_detect_rating_categories(page)
                if detected:
                    print(f"\n✓ Found {len(detected)} categories:")
                    for i, cat in enumerate(detected, 1):
                        print(f"  {i}. {cat['name']}")
                    
                    use_detected = input("\nUse these categories? (y/n): ").strip().lower()
                    if use_detected == 'y':
                        # Ask for scales
                        for cat in detected:
                            print(f"\nScale for '{cat['name']}':")
                            print("1. 1-3 scale (Major/Minor/No Issues)")
                            print("2. 1-5 scale (Highly unsatisfying to Highly satisfying)")
                            print("3. -2 to +2 scale (Too Short/Just Right/Too Verbose)")
                            scale_choice = input("Choice (1/2/3, or Enter for 1-3): ").strip()
                            
                            scale_map = {"1": "1-3", "2": "1-5", "3": "-2-2"}
                            cat['scale'] = scale_map.get(scale_choice, "1-3")
                        
                        categories = detected
                    else:
                        cat_choice = '3'  # Fall through to manual
                else:
                    print("⚠ No categories detected, please enter manually")
                    cat_choice = '3'
            
            if cat_choice == '3' or not categories:
                # Manual entry
                print("\n📝 Enter categories to rate (one per line, empty line to finish):")
                print("Examples: 'Localization', 'Instruction Following', 'Truthfulness', etc.")
        else:
            # No saved categories - offer auto-detect or manual
            print("\n📝 Category Selection:")
            print("1. Auto-detect from page")
            print("2. Enter manually")
            
            cat_choice = input("\nYour choice (1/2): ").strip()
            
            if cat_choice == '1':
                detected = auto_detect_rating_categories(page)
                if detected:
                    print(f"\n✓ Found {len(detected)} categories:")
                    for i, cat in enumerate(detected, 1):
                        print(f"  {i}. {cat['name']}")
                    
                    use_detected = input("\nUse these categories? (y/n): ").strip().lower()
                    if use_detected == 'y':
                        # Ask for scales
                        for cat in detected:
                            print(f"\nScale for '{cat['name']}':")
                            print("1. 1-3 scale (Major/Minor/No Issues)")
                            print("2. 1-5 scale (Highly unsatisfying to Highly satisfying)")
                            print("3. -2 to +2 scale (Too Short/Just Right/Too Verbose)")
                            scale_choice = input("Choice (1/2/3, or Enter for 1-3): ").strip()
                            
                            scale_map = {"1": "1-3", "2": "1-5", "3": "-2-2"}
                            cat['scale'] = scale_map.get(scale_choice, "1-3")
                        
                        categories = detected
                    else:
                        cat_choice = '2'
                else:
                    print("⚠ No categories detected, please enter manually")
                    cat_choice = '2'
        
        # Manual entry if needed
        if not categories:
            print("\n📝 Enter categories to rate (one per line, empty line to finish):")
            print("Examples: 'Localization', 'Instruction Following', 'Truthfulness', etc.")
            
            while True:
                cat = input(f"Category {len(categories) + 1} (or Enter to finish): ").strip()
                if not cat:
                    break
                
                # Ask for scale type
                print(f"\nScale for '{cat}':")
                print("1. 1-3 scale (Major/Minor/No Issues)")
                print("2. 1-5 scale (Highly unsatisfying to Highly satisfying)")
                print("3. -2 to +2 scale (Too Short/Just Right/Too Verbose)")
                scale_choice = input("Choice (1/2/3): ").strip()
                
                scale_map = {"1": "1-3", "2": "1-5", "3": "-2-2"}
                scale_type = scale_map.get(scale_choice, "1-3")
                
                categories.append({"name": cat, "scale": scale_type})
        
        if not categories:
            print("✗ No categories entered")
            return
        
        # Save categories for next time
        user_preferences['gemini_last_categories'] = categories
        print(f"💾 Saved {len(categories)} categories for next time")
        
        # Rate all categories
        all_ratings = []
        print(f"\n⏳ Getting Gemini ratings for {len(categories)} categories...")
        
        for i, cat_info in enumerate(categories, 1):
            cat_name = cat_info["name"]
            scale_type = cat_info["scale"]
            
            print(f"\n[{i}/{len(categories)}] Rating '{cat_name}' (scale: {scale_type})...")
            rating = get_gemini_rating(response_text, cat_name, scale_type, custom_instructions)
            
            if rating is not None:
                print(f"  ✓ Gemini rated: {rating}")
                all_ratings.append(str(rating))
            else:
                print(f"  ✗ Could not get rating for '{cat_name}'")
                manual = input(f"  Enter manual rating for '{cat_name}' (or 's' to skip): ").strip()
                if manual.lower() != 's':
                    all_ratings.append(manual)
        
        # Display all ratings
        print("\n📊 All Ratings:")
        for i, (cat_info, rating) in enumerate(zip(categories, all_ratings), 1):
            print(f"  {i}. {cat_info['name']}: {rating}")
        
        # Ask about multiple responses
        print(f"\n📝 Multiple Responses:")
        print("Do you have multiple responses to rate (e.g., Response 1 and Response 2)?")
        multiple_responses = input("Enter number of responses (1 or 2+, default: 1): ").strip()
        
        num_responses = 1
        if multiple_responses.isdigit() and int(multiple_responses) > 1:
            num_responses = int(multiple_responses)
            print(f"✓ Will rate {num_responses} responses with the same ratings: {' '.join(all_ratings)}")
        
        # Ask to auto-click all
        total_ratings = len(all_ratings) * num_responses
        print(f"\n🖱️  Click all {total_ratings} rating buttons automatically?")
        if num_responses > 1:
            print(f"({len(all_ratings)} ratings × {num_responses} responses)")
        print(f"Will click in this order: {' '.join(all_ratings)}")
        auto_click = input("Proceed? (y/n): ").strip().lower()
        
        if auto_click == 'y':
            total_clicked = 0
            total_failed = 0
            
            # Process each response
            for response_num in range(1, num_responses + 1):
                if num_responses > 1:
                    print(f"\n{'='*60}")
                    print(f"📝 RESPONSE {response_num} - {len(all_ratings)} ratings")
                    print(f"{'='*60}")
                    
                    # Scroll to find the response section
                    if response_num > 1:
                        print(f"\n🔍 Looking for 'Response {response_num}' section...")
                        try:
                            # Try to find and scroll to Response N heading
                            response_heading = page.locator(f'text=/Response\\s*{response_num}/i').first
                            if response_heading.count() > 0:
                                response_heading.scroll_into_view_if_needed()
                                time.sleep(0.5)
                                print(f"✓ Found and scrolled to Response {response_num}")
                            else:
                                print(f"⚠ Could not find 'Response {response_num}' heading, scrolling down...")
                                page.evaluate(f"window.scrollBy(0, {800 * (response_num - 1)})")
                                time.sleep(0.5)
                        except:
                            print(f"⚠ Scrolling down for Response {response_num}...")
                            page.evaluate(f"window.scrollBy(0, {800 * (response_num - 1)})")
                            time.sleep(0.5)
                else:
                    # Single response - scroll to top
                    print("\n📜 Scrolling to top of page...")
                    try:
                        page.evaluate("window.scrollTo(0, 0)")
                        time.sleep(0.5)
                    except:
                        pass
                
                clicked_count = 0
                clicked_indices = {}  # Track which index of each rating value we've clicked
            
            for i, rating in enumerate(all_ratings, 1):
                try:
                    # Get the index for this rating value
                    current_index = clicked_indices.get(rating, 0)
                    
                    success = False
                    
                    # Get all possible buttons with this rating value
                    all_candidates = []
                    
                    # Method 1: Find all buttons with exact match
                    try:
                        buttons = page.get_by_role("button", name=rating, exact=True).all()
                        all_candidates.extend(buttons)
                    except:
                        pass
                    
                    # Method 2: Find all text elements
                    try:
                        text_elements = page.get_by_text(rating, exact=True).all()
                        all_candidates.extend(text_elements)
                    except:
                        pass
                    
                    # Method 3: Find all button locators
                    try:
                        button_locators = page.locator(f'button:has-text("{rating}")').all()
                        all_candidates.extend(button_locators)
                    except:
                        pass
                    
                    # Remove duplicates and sort by position
                    unique_candidates = []
                    seen_boxes = set()
                    
                    for candidate in all_candidates:
                        try:
                            if candidate.is_visible():
                                box = candidate.bounding_box()
                                if box:
                                    box_id = f"{int(box['x'])},{int(box['y'])},{int(box['width'])},{int(box['height'])}"
                                    if box_id not in seen_boxes:
                                        seen_boxes.add(box_id)
                                        unique_candidates.append((candidate, box))
                        except:
                            continue
                    
                    # Sort by Y position (top to bottom)
                    unique_candidates.sort(key=lambda x: x[1]['y'])
                    
                    # Try to click the button at the current index
                    if current_index < len(unique_candidates):
                        try:
                            candidate, box = unique_candidates[current_index]
                            
                            # Scroll into view
                            candidate.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            
                            # Click it
                            candidate.click(timeout=2000)
                            clicked_indices[rating] = current_index + 1
                            success = True
                            print(f"  [{i}/{len(all_ratings)}] ✓ Clicked rating {rating} (#{current_index + 1} at {int(box['y'])}px)")
                            clicked_count += 1
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"  [{i}/{len(all_ratings)}] ⚠ Click failed: {e}")
                    
                    if not success:
                        print(f"  [{i}/{len(all_ratings)}] ✗ Could not click rating {rating}")
                        print(f"     (Found {len(unique_candidates)} buttons, needed #{current_index + 1})")
                        
                except Exception as e:
                    print(f"  [{i}/{len(all_ratings)}] ✗ Error: {e}")
                
                # Summary for this response
                failed_count = len(all_ratings) - clicked_count
                if num_responses > 1:
                    print(f"\n{'-'*60}")
                    print(f"Response {response_num} Summary:")
                    print(f"  ✓ Successfully clicked: {clicked_count}/{len(all_ratings)}")
                    if failed_count > 0:
                        print(f"  ✗ Failed: {failed_count}/{len(all_ratings)}")
                    print(f"{'-'*60}")
                
                total_clicked += clicked_count
                total_failed += failed_count
            
            # Final summary
            print("\n" + "="*60)
            print(f"📊 Final Rating Summary:")
            print(f"  ✓ Total clicked: {total_clicked}/{total_ratings}")
            if total_failed > 0:
                print(f"  ✗ Total failed: {total_failed}/{total_ratings}")
            if num_responses > 1:
                print(f"  📝 Responses processed: {num_responses}")
            print("="*60)
    
    else:
        # Single category mode (original behavior)
        category = input("Enter category name (e.g., Localization) or press Enter for 'Overall': ").strip()
        if not category:
            category = "Overall"
        
        # Ask for scale type
        print("\nRating Scale:")
        print("1. 1-3 scale (Major/Minor/No Issues)")
        print("2. 1-5 scale (Highly unsatisfying to Highly satisfying)")
        print("3. -2 to +2 scale (Too Short/Just Right/Too Verbose)")
        scale_choice = input("Choice (1/2/3): ").strip()
        
        scale_map = {"1": "1-3", "2": "1-5", "3": "-2-2"}
        scale_type = scale_map.get(scale_choice, "1-3")
        
        print(f"\n⏳ Getting Gemini rating for '{category}'...")
        rating = get_gemini_rating(response_text, category, scale_type, custom_instructions)
        
        if rating is not None:
            print(f"✓ Gemini rated: {rating}")
            
            # Ask to click the button
            auto_click = input(f"\n🖱️  Click rating button '{rating}'? (y/n): ").strip().lower()
            
            if auto_click == 'y':
                try:
                    success = False
                    
                    # Try multiple methods
                    button = page.get_by_role("button", name=str(rating), exact=True).first
                    if button.count() > 0:
                        button.click()
                        success = True
                    else:
                        page.get_by_text(str(rating), exact=True).first.click()
                        success = True
                    
                    if success:
                        print(f"✓ Clicked rating {rating}")
                except Exception as e:
                    print(f"⚠ Could not auto-click: {e}")
                    print(f"💡 Please manually click button '{rating}'")
        else:
            print(f"✗ Could not get rating for '{category}'")
    
    print("\n✅ Auto-rating complete!")

def simple_rating_click(page):
    """
    Simple method: Click multiple rating buttons in sequence
    Supports different rating scales (1-3, 1-5, -2 to +2, etc.)
    """
    print("\n🔢 Simple Batch Rating Click")
    print("="*60)
    print("Enter ratings for multiple categories in one go!")
    print("\nExamples:")
    print("  • For 1-3 scale: Enter '2 3 1' to rate three categories")
    print("  • For 1-5 scale: Enter '4 3 5' to rate three categories")
    print("  • For -2 to +2 scale: Enter '1 0 -1' to rate three categories")
    print("  • Mixed scales: Just enter the numbers in order")
    print("\n💡 Tip: Enter ratings in the order they appear on the page (top to bottom)")
    print("\n🔄 Multiple Responses:")
    print("  • If you have Response 1 and Response 2, enter ratings separated by '|'")
    print("  • Example: '3 2 3 | 3 2 3' = Response 1 gets [3,2,3], Response 2 gets [3,2,3]")
    print("="*60)
    
    ratings_input = input("\nEnter all ratings separated by spaces (use | for multiple responses) or 'c' to cancel: ").strip()
    
    if ratings_input.lower() == 'c':
        print("Cancelled.")
        return
    
    # Check if there are multiple response sections (separated by |)
    if '|' in ratings_input:
        response_groups = [group.strip().split() for group in ratings_input.split('|')]
        print(f"\n📊 Detected {len(response_groups)} response sections:")
        for i, group in enumerate(response_groups, 1):
            print(f"  Response {i}: {len(group)} ratings - {', '.join(group)}")
    else:
        # Single response
        response_groups = [ratings_input.split()]
        print(f"\n📊 Single response with {len(response_groups[0])} rating(s): {', '.join(response_groups[0])}")
    
    confirm = input("\nProceed with clicking these ratings? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Process each response section
    total_clicked = 0
    total_failed = 0
    
    for response_num, ratings in enumerate(response_groups, 1):
        if len(response_groups) > 1:
            print(f"\n{'='*60}")
            print(f"📝 RESPONSE {response_num} - {len(ratings)} ratings")
            print(f"{'='*60}")
            
            # Scroll to find the response section
            if response_num > 1:
                print(f"\n🔍 Looking for 'Response {response_num}' section...")
                try:
                    # Try to find and scroll to Response N heading
                    response_heading = page.locator(f'text=/Response\\s*{response_num}/i').first
                    if response_heading.count() > 0:
                        response_heading.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        print(f"✓ Found and scrolled to Response {response_num}")
                    else:
                        print(f"⚠ Could not find 'Response {response_num}' heading, scrolling down...")
                        page.evaluate(f"window.scrollBy(0, {800 * (response_num - 1)})")
                        time.sleep(0.5)
                except:
                    print(f"⚠ Scrolling down for Response {response_num}...")
                    page.evaluate(f"window.scrollBy(0, {800 * (response_num - 1)})")
                    time.sleep(0.5)
        else:
            # Single response - scroll to top
            print("\n📜 Scrolling to top of page...")
            try:
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)
            except:
                pass
        
        # Click ratings for this response section
        clicked_count = 0
        failed_count = 0
        clicked_indices = {}  # Track which index of each rating value we've clicked
        
        for i, rating in enumerate(ratings, 1):
            print(f"\n[{i}/{len(ratings)}] Clicking rating '{rating}'...")
            
            # Get the index for this rating value (how many times we've clicked this value before)
            current_index = clicked_indices.get(rating, 0)
            
            success = False
            
            # IMPORTANT: Re-query elements each time (page might have changed)
            all_candidates = []
            
            # Method 1: Find all buttons with exact text match
            try:
                buttons = page.get_by_role("button", name=rating, exact=True).all()
                all_candidates.extend(buttons)
            except:
                pass
            
            # Method 2: Find all elements with exact text
            try:
                text_elements = page.get_by_text(rating, exact=True).all()
                all_candidates.extend(text_elements)
            except:
                pass
            
            # Method 3: Find buttons containing this text
            try:
                button_locators = page.locator(f'button:has-text("{rating}")').all()
                all_candidates.extend(button_locators)
            except:
                pass
            
            # Method 4: Find labels (for radio buttons)
            try:
                label_elements = page.locator(f'label:has-text("{rating}")').all()
                all_candidates.extend(label_elements)
            except:
                pass
            
            # Method 5: Find inputs with value
            try:
                input_elements = page.locator(f'input[value="{rating}"]').all()
                all_candidates.extend(input_elements)
            except:
                pass
            
            # Remove duplicates by checking if elements are the same
            unique_candidates = []
            seen_boxes = set()
            
            for candidate in all_candidates:
                try:
                    if candidate.is_visible():
                        box = candidate.bounding_box()
                        if box:
                            box_id = f"{int(box['x'])},{int(box['y'])},{int(box['width'])},{int(box['height'])}"
                            if box_id not in seen_boxes:
                                seen_boxes.add(box_id)
                                unique_candidates.append((candidate, box))
                except:
                    continue
            
            # Sort candidates by Y position (top to bottom)
            unique_candidates.sort(key=lambda x: x[1]['y'])
            
            print(f"  🔍 Found {len(unique_candidates)} buttons with value '{rating}', clicking #{current_index + 1}")
            
            # Try to click the button at the current index
            if current_index < len(unique_candidates):
                try:
                    candidate, box = unique_candidates[current_index]
                    
                    # Scroll into view and wait
                    candidate.scroll_into_view_if_needed()
                    time.sleep(0.4)
                    
                    # Highlight for debugging (optional - can remove later)
                    try:
                        page.evaluate("""(element) => {
                            element.style.outline = '3px solid red';
                            setTimeout(() => element.style.outline = '', 500);
                        }""", candidate)
                    except:
                        pass
                    
                    # Click it
                    candidate.click(timeout=3000, force=False)
                    
                    # Update index for this rating value
                    clicked_indices[rating] = current_index + 1
                    
                    success = True
                    print(f"  ✓ Clicked rating '{rating}' (#{current_index + 1} occurrence)")
                    clicked_count += 1
                    time.sleep(0.6)  # Longer delay to let page settle
                except Exception as e:
                    print(f"  ⚠ Click failed: {e}")
            
            if not success:
                print(f"  ✗ Could not find occurrence #{current_index + 1} of rating '{rating}'")
                print(f"     (Found {len(unique_candidates)} total buttons with this value)")
                
                # Offer to manually click or skip
                print(f"  Options:")
                print(f"    c - Continue anyway (try next available)")
                print(f"    m - Manually click and then press Enter")
                print(f"    s - Skip this rating")
                manual_choice = input(f"  Choice (c/m/s): ").strip().lower()
                
                if manual_choice == 'm':
                    input("  Click the button manually, then press Enter...")
                    clicked_indices[rating] = current_index + 1
                    clicked_count += 1
                elif manual_choice == 'c':
                    # Try to click any available button with this value that we haven't clicked
                    for idx, (candidate, box) in enumerate(unique_candidates):
                        if idx >= current_index:
                            try:
                                candidate.scroll_into_view_if_needed()
                                time.sleep(0.3)
                                candidate.click(timeout=2000)
                                clicked_indices[rating] = idx + 1
                                print(f"  ✓ Clicked rating '{rating}' (#{idx + 1} occurrence at {int(box['y'])}px)")
                                clicked_count += 1
                                time.sleep(0.5)
                                success = True
                                break
                            except:
                                continue
                    if not success:
                        failed_count += 1
                else:
                    failed_count += 1
        
        # Summary for this response
        if len(response_groups) > 1:
            print(f"\n{'-'*60}")
            print(f"Response {response_num} Summary:")
            print(f"  ✓ Successfully clicked: {clicked_count}/{len(ratings)}")
            if failed_count > 0:
                print(f"  ✗ Failed: {failed_count}/{len(ratings)}")
            print(f"{'-'*60}")
        
        total_clicked += clicked_count
        total_failed += failed_count
    
    # Final summary
    print("\n" + "="*60)
    print(f"📊 Final Rating Summary:")
    total_ratings = sum(len(group) for group in response_groups)
    print(f"  ✓ Total clicked: {total_clicked}/{total_ratings}")
    if total_failed > 0:
        print(f"  ✗ Total failed: {total_failed}/{total_ratings}")
    if len(response_groups) > 1:
        print(f"  📝 Responses processed: {len(response_groups)}")
    print("="*60)

def get_session_templates():
    """Get built-in session templates"""
    templates = {
        'login': {
            'name': 'Generic Login Form',
            'description': 'Fill username/email and password, then click login button',
            'variables': ['{{username}}', '{{password}}'],
            'actions': [
                {
                    'type': 'type_by_label',
                    'label': 'email',
                    'value': '{{username}}',
                    'base_delay': 100,
                    'description': 'Enter username/email'
                },
                {
                    'type': 'type_by_label',
                    'label': 'password',
                    'value': '{{password}}',
                    'base_delay': 100,
                    'description': 'Enter password'
                },
                {
                    'type': 'click_by_text',
                    'text': 'login',
                    'element_type': 'button',
                    'description': 'Click login button'
                }
            ]
        },
        'search': {
            'name': 'Search and Select Result',
            'description': 'Enter search query and click first result',
            'variables': ['{{query}}'],
            'actions': [
                {
                    'type': 'type_by_label',
                    'label': 'search',
                    'value': '{{query}}',
                    'base_delay': 100,
                    'description': 'Enter search query'
                },
                {
                    'type': 'click_by_text',
                    'text': 'search',
                    'element_type': 'button',
                    'description': 'Click search button'
                }
            ]
        },
        'form_fill': {
            'name': 'Generic Form Fill',
            'description': 'Auto-detect and fill all form fields',
            'variables': [],
            'actions': [
                {
                    'type': 'auto_fill_form',
                    'description': 'Auto-fill detected form'
                }
            ]
        },
        'contact_form': {
            'name': 'Contact Form',
            'description': 'Fill typical contact form (name, email, message)',
            'variables': ['{{name}}', '{{email}}', '{{message}}'],
            'actions': [
                {
                    'type': 'type_by_label',
                    'label': 'name',
                    'value': '{{name}}',
                    'base_delay': 100,
                    'description': 'Enter name'
                },
                {
                    'type': 'type_by_label',
                    'label': 'email',
                    'value': '{{email}}',
                    'base_delay': 100,
                    'description': 'Enter email'
                },
                {
                    'type': 'type_by_label',
                    'label': 'message',
                    'value': '{{message}}',
                    'base_delay': 100,
                    'description': 'Enter message'
                },
                {
                    'type': 'click_by_text',
                    'text': 'submit',
                    'element_type': 'button',
                    'description': 'Click submit'
                }
            ]
        },
        'gemini_rating': {
            'name': 'Gemini Model Rating',
            'description': 'Click rating buttons (1-3) based on Gemini feedback',
            'variables': ['{{rating}}'],
            'actions': [
                {
                    'type': 'click_by_text',
                    'text': '{{rating}}',
                    'element_type': 'button',
                    'description': 'Click rating button'
                }
            ]
        }
    }
    return templates

def apply_template(page, template_name):
    """Apply a session template with user-provided variables"""
    templates = get_session_templates()
    
    if template_name not in templates:
        print(f"✗ Template '{template_name}' not found")
        return False
    
    template = templates[template_name]
    
    print(f"\n📋 Template: {template['name']}")
    print(f"   {template['description']}")
    
    # Collect variable values
    variables = {}
    if template['variables']:
        print("\n✏️  Enter values for template variables:")
        for var in template['variables']:
            # Check clipboard for smart suggestions
            clipboard_text = get_clipboard_text()
            var_name = var.replace('{{', '').replace('}}', '')
            
            if clipboard_text and user_preferences.get('clipboard_auto_suggest', True):
                use_clipboard = input(f"{var} (📋 '{clipboard_text[:30]}...' or custom): ").strip()
                if not use_clipboard:
                    variables[var] = clipboard_text
                else:
                    variables[var] = use_clipboard
            else:
                variables[var] = input(f"{var}: ").strip()
    
    # Execute template actions
    print(f"\n⚡ Executing {len(template['actions'])} actions...")
    
    for i, action in enumerate(template['actions']):
        print(f"[{i+1}/{len(template['actions'])}] {action['description']}")
        
        # Replace variables in action
        action_copy = action.copy()
        for var, value in variables.items():
            if 'value' in action_copy and isinstance(action_copy['value'], str):
                action_copy['value'] = action_copy['value'].replace(var, value)
            if 'text' in action_copy and isinstance(action_copy['text'], str):
                action_copy['text'] = action_copy['text'].replace(var, value)
            if 'label' in action_copy and isinstance(action_copy['label'], str):
                action_copy['label'] = action_copy['label'].replace(var, value)
        
        # Execute action
        try:
            if action_copy['type'] == 'type_by_label':
                label = action_copy['label']
                value = action_copy['value']
                base_delay = action_copy.get('base_delay', 100)
                
                # Find element by label
                element = None
                try:
                    element = page.get_by_placeholder(label, exact=False).first
                    if element.count() == 0:
                        element = page.get_by_label(label, exact=False).first
                    if element.count() == 0:
                        element = page.locator(f"input[name*='{label}' i], textarea[name*='{label}' i]").first
                except:
                    pass
                
                if element and element.count() > 0:
                    safe_type(element, value, base_delay, f"Type in '{label}'")
                else:
                    print(f"  ⚠ Could not find field: {label}")
            
            elif action_copy['type'] == 'click_by_text':
                text = action_copy['text']
                element_type = action_copy.get('element_type', 'any')
                
                if element_type == 'button':
                    element = page.get_by_role("button", name=text).first
                else:
                    element = page.get_by_text(text, exact=False).first
                
                if element.count() > 0:
                    safe_click(element, f"Click '{text}'")
                else:
                    print(f"  ⚠ Could not find element: {text}")
            
            elif action_copy['type'] == 'auto_fill_form':
                auto_fill_form(page)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue_prompt = input("  Continue with next action? (y/n): ").strip().lower()
            if continue_prompt != 'y':
                return False
    
    print("\n✅ Template execution completed!")
    return True

def list_templates():
    """List all available templates"""
    templates = get_session_templates()
    
    print("\n📚 Available Templates:")
    print("=" * 60)
    
    for i, (key, template) in enumerate(templates.items()):
        print(f"\n[{i}] {template['name']} ('{key}')")
        print(f"    {template['description']}")
        if template['variables']:
            print(f"    Variables: {', '.join(template['variables'])}")
        print(f"    Actions: {len(template['actions'])}")
    
    print("=" * 60)




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

def detect_forms(page):
    """
    Detect all forms on the page and their fields
    Returns a list of form dictionaries with field information
    """
    print("\n🔍 Detecting forms on the page...")
    
    try:
        forms = []
        form_elements = page.locator('form').all()
        
        if not form_elements:
            # Try to detect form-like structures without <form> tag
            print("  ℹ️ No <form> tags found, scanning for individual fields...")
            
            # Create a pseudo-form with all inputs
            all_fields = []
            
            # Collect all input fields
            inputs = page.locator('input[type="text"], input[type="email"], input[type="password"], input[type="tel"], input[type="url"], input[type="number"], input:not([type])').all()
            textareas = page.locator('textarea').all()
            selects = page.locator('select').all()
            
            for inp in inputs:
                try:
                    field_info = {
                        'element': inp,
                        'type': inp.get_attribute('type') or 'text',
                        'name': inp.get_attribute('name') or '',
                        'id': inp.get_attribute('id') or '',
                        'placeholder': inp.get_attribute('placeholder') or '',
                        'label': '',
                        'required': inp.get_attribute('required') is not None
                    }
                    
                    # Try to find associated label
                    try:
                        if field_info['id']:
                            label_elem = page.locator(f'label[for="{field_info["id"]}"]').first
                            if label_elem.count() > 0:
                                field_info['label'] = label_elem.inner_text().strip()
                    except:
                        pass
                    
                    # Try aria-label
                    if not field_info['label']:
                        aria_label = inp.get_attribute('aria-label')
                        if aria_label:
                            field_info['label'] = aria_label
                    
                    all_fields.append(field_info)
                except:
                    continue
            
            for ta in textareas:
                try:
                    field_info = {
                        'element': ta,
                        'type': 'textarea',
                        'name': ta.get_attribute('name') or '',
                        'id': ta.get_attribute('id') or '',
                        'placeholder': ta.get_attribute('placeholder') or '',
                        'label': '',
                        'required': ta.get_attribute('required') is not None
                    }
                    
                    # Try to find associated label
                    try:
                        if field_info['id']:
                            label_elem = page.locator(f'label[for="{field_info["id"]}"]').first
                            if label_elem.count() > 0:
                                field_info['label'] = label_elem.inner_text().strip()
                    except:
                        pass
                    
                    if not field_info['label']:
                        aria_label = ta.get_attribute('aria-label')
                        if aria_label:
                            field_info['label'] = aria_label
                    
                    all_fields.append(field_info)
                except:
                    continue
            
            for sel in selects:
                try:
                    field_info = {
                        'element': sel,
                        'type': 'select',
                        'name': sel.get_attribute('name') or '',
                        'id': sel.get_attribute('id') or '',
                        'placeholder': '',
                        'label': '',
                        'required': sel.get_attribute('required') is not None
                    }
                    
                    # Try to find associated label
                    try:
                        if field_info['id']:
                            label_elem = page.locator(f'label[for="{field_info["id"]}"]').first
                            if label_elem.count() > 0:
                                field_info['label'] = label_elem.inner_text().strip()
                    except:
                        pass
                    
                    if not field_info['label']:
                        aria_label = sel.get_attribute('aria-label')
                        if aria_label:
                            field_info['label'] = aria_label
                    
                    all_fields.append(field_info)
                except:
                    continue
            
            if all_fields:
                forms.append({
                    'index': 0,
                    'name': 'Page Fields',
                    'action': '',
                    'fields': all_fields
                })
        else:
            # Process actual <form> elements
            for i, form in enumerate(form_elements):
                try:
                    form_info = {
                        'index': i,
                        'name': form.get_attribute('name') or form.get_attribute('id') or f'Form {i+1}',
                        'action': form.get_attribute('action') or '',
                        'fields': []
                    }
                    
                    # Get all input fields in this form
                    inputs = form.locator('input[type="text"], input[type="email"], input[type="password"], input[type="tel"], input[type="url"], input[type="number"], input:not([type])').all()
                    textareas = form.locator('textarea').all()
                    selects = form.locator('select').all()
                    
                    # Process each field
                    for inp in inputs:
                        try:
                            field_info = {
                                'element': inp,
                                'type': inp.get_attribute('type') or 'text',
                                'name': inp.get_attribute('name') or '',
                                'id': inp.get_attribute('id') or '',
                                'placeholder': inp.get_attribute('placeholder') or '',
                                'label': '',
                                'required': inp.get_attribute('required') is not None
                            }
                            
                            # Try to find label
                            try:
                                if field_info['id']:
                                    label_elem = page.locator(f'label[for="{field_info["id"]}"]').first
                                    if label_elem.count() > 0:
                                        field_info['label'] = label_elem.inner_text().strip()
                            except:
                                pass
                            
                            if not field_info['label']:
                                aria_label = inp.get_attribute('aria-label')
                                if aria_label:
                                    field_info['label'] = aria_label
                            
                            form_info['fields'].append(field_info)
                        except:
                            continue
                    
                    for ta in textareas:
                        try:
                            field_info = {
                                'element': ta,
                                'type': 'textarea',
                                'name': ta.get_attribute('name') or '',
                                'id': ta.get_attribute('id') or '',
                                'placeholder': ta.get_attribute('placeholder') or '',
                                'label': '',
                                'required': ta.get_attribute('required') is not None
                            }
                            
                            try:
                                if field_info['id']:
                                    label_elem = page.locator(f'label[for="{field_info["id"]}"]').first
                                    if label_elem.count() > 0:
                                        field_info['label'] = label_elem.inner_text().strip()
                            except:
                                pass
                            
                            if not field_info['label']:
                                aria_label = ta.get_attribute('aria-label')
                                if aria_label:
                                    field_info['label'] = aria_label
                            
                            form_info['fields'].append(field_info)
                        except:
                            continue
                    
                    for sel in selects:
                        try:
                            field_info = {
                                'element': sel,
                                'type': 'select',
                                'name': sel.get_attribute('name') or '',
                                'id': sel.get_attribute('id') or '',
                                'placeholder': '',
                                'label': '',
                                'required': sel.get_attribute('required') is not None
                            }
                            
                            try:
                                if field_info['id']:
                                    label_elem = page.locator(f'label[for="{field_info["id"]}"]').first
                                    if label_elem.count() > 0:
                                        field_info['label'] = label_elem.inner_text().strip()
                            except:
                                pass
                            
                            if not field_info['label']:
                                aria_label = sel.get_attribute('aria-label')
                                if aria_label:
                                    field_info['label'] = aria_label
                            
                            form_info['fields'].append(field_info)
                        except:
                            continue
                    
                    if form_info['fields']:
                        forms.append(form_info)
                except:
                    continue
        
        return forms
    except Exception as e:
        print(f"  ✗ Error detecting forms: {e}")
        return []

def auto_fill_form(page):
    """
    Auto-detect and fill forms on the page
    """
    forms = detect_forms(page)
    
    if not forms:
        print("\n⚠ No forms detected on this page!")
        print("💡 Try using the regular interaction options (1-13) instead.")
        return
    
    print(f"\n📋 Found {len(forms)} form(s):")
    for form in forms:
        print(f"\n  [{form['index']}] {form['name']}")
        print(f"      Fields: {len(form['fields'])}")
        if form['action']:
            print(f"      Action: {form['action']}")
    
    # Select form
    if len(forms) == 1:
        selected_form = forms[0]
        print(f"\n✓ Auto-selected: {selected_form['name']}")
    else:
        form_choice = input(f"\nSelect form [0-{len(forms)-1}] (or 'c' to cancel): ").strip()
        if form_choice.lower() == 'c':
            print("Cancelled.")
            return
        try:
            selected_form = forms[int(form_choice)]
        except:
            print("✗ Invalid selection")
            return
    
    # Display fields
    print(f"\n📝 Form: {selected_form['name']}")
    print("=" * 60)
    
    for i, field in enumerate(selected_form['fields']):
        label = field['label'] or field['placeholder'] or field['name'] or field['id'] or 'Unnamed field'
        required = '(required)' if field['required'] else '(optional)'
        print(f"  [{i}] {label} {required}")
        print(f"      Type: {field['type']}")
    
    print("=" * 60)
    
    # Collect values for all fields
    field_values = {}
    
    print("\n✏️  Enter values for each field:")
    print("💡 Type 'p' to paste from clipboard, or Enter to skip\n")
    
    for i, field in enumerate(selected_form['fields']):
        label = field['label'] or field['placeholder'] or field['name'] or field['id'] or f'Field {i}'
        
        if field['type'] == 'select':
            print(f"\n[{i}] {label} (dropdown)")
            value = input(f"    Enter option value: ").strip()
        else:
            # Show field label
            print(f"\n[{i}] {label}")
            user_input = input(f"    Value (p=paste, Enter=skip): ").strip()
            
            if user_input.lower() == 'p':
                # Paste from clipboard instantly
                clipboard_text = get_clipboard_text()
                if clipboard_text:
                    value = clipboard_text
                    print(f"    ✓ Pasted: '{clipboard_text[:60]}...'")
                else:
                    print("    ⚠ Clipboard is empty")
                    value = input(f"    Enter value: ").strip()
            elif user_input == '':
                # Skip this field
                continue
            else:
                # Use the typed value
                value = user_input
        
        if value:
            field_values[i] = value
    
    # Confirm before filling
    print(f"\n📊 Summary: {len(field_values)} fields will be filled")
    confirm = input("Proceed with auto-fill? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Fill the form
    print("\n⌨️  Filling form...")
    base_delay = user_preferences['typing_speed']
    
    for i, value in field_values.items():
        field = selected_form['fields'][i]
        label = field['label'] or field['placeholder'] or field['name'] or f'Field {i}'
        
        try:
            if field['type'] == 'select':
                print(f"  [{i}] {label}: selecting '{value}'...")
                field['element'].select_option(value)
            elif field['type'] == 'textarea':
                print(f"  [{i}] {label}: typing...")
                safe_type(field['element'], value, base_delay, f"Fill {label}")
            else:
                print(f"  [{i}] {label}: typing...")
                safe_type(field['element'], value, base_delay, f"Fill {label}")
            
            time.sleep(0.3)  # Small delay between fields
        except Exception as e:
            print(f"  ⚠ Error filling {label}: {e}")
            continue
    
    print("\n✅ Form auto-fill completed!")
    
    # Now detect and offer to click buttons
    detect_and_click_button(page)

def detect_and_click_button(page):
    """
    Detect common buttons after form fill and offer to click one
    """
    print("\n🔍 Looking for continue buttons...")
    
    # Common button patterns to look for
    common_buttons = ['next', 'continue', 'submit', 'save', 'proceed', 'confirm', 'send', 'finish']
    
    found_buttons = []
    
    try:
        # Find all buttons on the page - expanded detection
        all_buttons = page.locator('button, input[type="button"], input[type="submit"], a.btn, a.button, [role="button"], a[class*="button"], a[class*="btn"]').all()
        
        for idx, btn in enumerate(all_buttons[:20]):  # Increased to 20
            try:
                # Get button text from multiple sources
                text = ''
                try:
                    text = btn.inner_text().strip()
                except:
                    pass
                
                value = btn.get_attribute('value') or ''
                aria_label = btn.get_attribute('aria-label') or ''
                title = btn.get_attribute('title') or ''
                class_name = btn.get_attribute('class') or ''
                
                # Combine all text sources
                btn_text = text or value or aria_label or title or 'Unnamed button'
                
                # Check visibility - include disabled buttons too
                is_visible = False
                try:
                    is_visible = btn.is_visible()
                except:
                    # If visibility check fails, assume it's visible
                    is_visible = True
                
                # Check if disabled
                is_disabled = btn.is_disabled() if hasattr(btn, 'is_disabled') else False
                
                if is_visible:
                    found_buttons.append({
                        'index': idx,
                        'element': btn,
                        'text': btn_text,
                        'is_common': any(keyword in btn_text.lower() for keyword in common_buttons),
                        'is_disabled': is_disabled,
                        'class': class_name[:40] if class_name else ''  # Show class for context
                    })
            except Exception as e:
                continue
        
        if not found_buttons:
            print("  ℹ️  No buttons found")
            print("💡 Review the form before submitting manually!")
            return
        
        # Display found buttons
        print(f"\n🔘 Found {len(found_buttons)} button(s):")
        
        # Show common buttons first
        common_first = sorted(found_buttons, key=lambda x: (not x['is_common'], x['index']))
        
        for btn_info in common_first[:10]:  # Show max 10
            star = "⭐" if btn_info['is_common'] else "  "
            disabled = " [DISABLED]" if btn_info.get('is_disabled') else ""
            class_info = f" ({btn_info['class']})" if btn_info.get('class') else ""
            print(f"  {star} [{btn_info['index']}] {btn_info['text']}{disabled}{class_info}")
        
        if len(found_buttons) > 10:
            print(f"  ... and {len(found_buttons) - 10} more (type 'all' to see all)")
        
        print("\n" + "=" * 60)
        print("Options:")
        print("  • Type button text (e.g., 'Next')")
        print("  • Type number (e.g., '0')")
        print("  • Type 'all' to see all buttons")
        print("  • Press Enter to skip")
        print("=" * 60)
        
        choice = input("\n� Click button: ").strip()
        
        if not choice:
            print("�💡 Review the form before submitting!")
            return
        
        # Try to find button by text or index
        selected_button = None
        
        # Check if it's a number (index)
        try:
            idx = int(choice)
            for btn_info in found_buttons:
                if btn_info['index'] == idx:
                    selected_button = btn_info
                    break
        except ValueError:
            # It's text, search by text
            choice_lower = choice.lower()
            for btn_info in found_buttons:
                if choice_lower in btn_info['text'].lower():
                    selected_button = btn_info
                    break
        
        if not selected_button:
            print(f"✗ Could not find button matching '{choice}'")
            print("💡 Try using Option 11 (Click by Text) or Option 13 (CSS Selector) from the main menu")
            return
        
        # Click the button
        print(f"\n🖱️  Clicking '{selected_button['text']}'...")
        
        success, _, error = safe_click(selected_button['element'], f"Click {selected_button['text']}")
        
        if success:
            print("  ✓ Button clicked!")
            
            # Wait for potential page change
            print("  ⏳ Waiting for page to load...")
            time.sleep(2)  # Give page time to load
            
            # Check if there are new forms
            print("  🔍 Checking for new forms...")
            new_forms = detect_forms(page)
            
            if new_forms:
                print(f"  ✓ Found {len(new_forms)} new form(s)")
                continue_fill = input("\n  Continue filling forms? (y/n): ").strip().lower()
                if continue_fill == 'y':
                    auto_fill_form(page)
            else:
                print("  ℹ️  No new forms detected")
        else:
            print(f"  ✗ Click failed: {error}")
    
    except Exception as e:
        print(f"  ✗ Error detecting buttons: {e}")

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
    Includes human-like typing with typos, variations, and pauses
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
        
        # Get user preferences
        enable_typos = user_preferences.get('enable_typos', True)
        typo_chance = user_preferences.get('typo_chance', 0.05)
        pause_after_punctuation = user_preferences.get('pause_after_punctuation', True)
        thinking_pauses = user_preferences.get('thinking_pauses', True)
        
        # Keyboard nearby keys for typos
        keyboard_nearby = {
            'a': 'sqwz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsd',
            'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'uojk', 'j': 'huikm',
            'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iplk',
            'p': 'ol', 'q': 'wa', 'r': 'etdf', 's': 'awedxz', 't': 'ryfg',
            'u': 'yihj', 'v': 'cfgb', 'w': 'qeas', 'x': 'zsdc', 'y': 'tugh',
            'z': 'asx'
        }
        
        # Type with human-like behavior
        for i, char in enumerate(value):
            # Random typo chance (skip spaces, newlines, and first char)
            if enable_typos and i > 0 and char not in [' ', '\n', '\r', '\t'] and random.random() < typo_chance:
                # Make a typo - type a random nearby key
                typo_char = char
                if char.lower() in keyboard_nearby:
                    nearby_keys = keyboard_nearby[char.lower()]
                    typo_char = random.choice(nearby_keys)
                    if char.isupper():
                        typo_char = typo_char.upper()
                
                # Type the typo
                typo_delay = int(delay * random.uniform(0.8, 1.2))
                element.type(typo_char, delay=typo_delay)
                
                # Pause (noticing the mistake)
                time.sleep(delay * random.uniform(0.3, 0.6) / 1000)
                
                # Delete the typo
                element.press('Backspace')
                time.sleep(delay * 0.5 / 1000)
            
            # Add random variation: ±40% of base speed
            variation = random.uniform(-0.4, 0.4)
            char_delay = int(delay * (1 + variation))
            
            # Longer pauses after punctuation and spaces (more human)
            if pause_after_punctuation:
                if char in '.,!?;:':
                    char_delay = int(char_delay * random.uniform(1.5, 2.5))
                elif char == ' ':
                    char_delay = int(char_delay * random.uniform(1.2, 1.8))
                elif char in ['\n', '\r']:
                    char_delay = int(char_delay * random.uniform(2.0, 3.0))
            
            # Occasional longer "thinking" pauses (2% chance)
            if thinking_pauses and random.random() < 0.02:
                char_delay = int(char_delay * random.uniform(3, 5))
            
            element.type(char, delay=char_delay)
        
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
    
    # Wait a bit for dynamic content to load
    try:
        page.wait_for_timeout(500)
    except:
        pass
    
    element_types = {
        'buttons': 'button, input[type="button"], input[type="submit"]',
        'links': 'a[href]',
        'inputs': 'input[type="text"], input[type="email"], input[type="password"]',
        'textareas': 'textarea, [role="textbox"], [contenteditable="true"]',  # Include contenteditable divs
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
                aria_label = elem.get_attribute('aria-label') or ''
                
                info = f"  [{i}] "
                
                # For textareas, prioritize placeholder over name (more descriptive)
                if element_type == 'textareas':
                    if placeholder:
                        info += f"placeholder='{placeholder[:60]}'"
                    elif aria_label:
                        info += f"aria-label='{aria_label[:60]}'"
                    elif text:
                        info += f"'{text}'"
                    elif name:
                        info += f"name='{name}'"
                    elif id_attr:
                        info += f"id='{id_attr}'"
                    else:
                        info += "(no label)"
                else:
                    # For other elements, keep original priority
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
    print("14. 📋 Auto-fill entire form")
    print("15. Back to main menu")
    
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
                # Track for Watch & Learn
                track_action('click_button', {'index': idx})
                
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
                # Track for Watch & Learn
                track_action('click_link', {'index': idx})
                
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
                if success:
                    # Track for Watch & Learn
                    track_action('click_by_text', {'text': text, 'element_type': element_type})
                    
                    # Wait for any dynamic content to load
                    page.wait_for_timeout(800)
                    
                    # Ask if user wants to rescan
                    rescan = input("\n🔄 Rescan page for new elements? (y/n) [default: y]: ").strip().lower()
                    if rescan != 'n':
                        scan_page_elements(page)
                    
                    if is_recording:
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
                
                if success:
                    # Track for Watch & Learn
                    track_action('type_by_label', {'label': label})
                    
                    if is_recording:
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
        # Auto-fill entire form
        try:
            auto_fill_form(page)
        except Exception as e:
            print(handle_common_errors(e, "form auto-fill"))
    
    elif choice == '15':
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
    
    print("\n⚡ New Features")
    print("-" * 50)
    
    # Enable hotkeys
    hotkey_input = input(f"Enable global hotkeys? (y/n, current: {'yes' if user_preferences.get('enable_hotkeys', False) else 'no'}): ").strip().lower()
    if hotkey_input in ['y', 'n']:
        user_preferences['enable_hotkeys'] = hotkey_input == 'y'
    
    # Clipboard auto-suggest
    clipboard_input = input(f"Enable clipboard auto-suggest? (y/n, current: {'yes' if user_preferences.get('clipboard_auto_suggest', True) else 'no'}): ").strip().lower()
    if clipboard_input in ['y', 'n']:
        user_preferences['clipboard_auto_suggest'] = clipboard_input == 'y'
    
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
        print(f"\n⚡ New Features:")
        print(f"  • Global hotkeys: {'Enabled' if user_preferences.get('enable_hotkeys', False) else 'Disabled'}")
        print(f"  • Clipboard auto-suggest: {'Enabled' if user_preferences.get('clipboard_auto_suggest', True) else 'Disabled'}")
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
    print(f"\n⚡ New Features:")
    print(f"  • Global hotkeys: {'Enabled' if user_preferences.get('enable_hotkeys', False) else 'Disabled'}")
    if user_preferences.get('enable_hotkeys', False):
        print(f"    - Ctrl+Shift+R: Toggle Recording")
        print(f"    - Ctrl+Shift+P: Replay Last Session")
    print(f"  • Clipboard auto-suggest: {'Enabled' if user_preferences.get('clipboard_auto_suggest', True) else 'Disabled'}")
    print(f"  • Page context saved: {'Yes' if user_preferences.get('form_field_cache') else 'No'}")
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
    
    # Offer intelligent enhancements
    enhance = input("\n🧠 Add intelligent error handling and logic? (y/n): ").strip().lower()
    
    actions_to_save = recorded_actions
    if enhance == 'y':
        actions_to_save = suggest_workflow_improvements(recorded_actions)
    
    filepath = f"sessions/{filename}.json"
    
    try:
        # Save with metadata
        session_data = {
            'name': filename,
            'created': datetime.now().isoformat(),
            'actions': actions_to_save,
            'enhanced': enhance == 'y',
            'action_count': len(actions_to_save)
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
        print(f"✓ Session saved to '{filepath}' ({len(actions_to_save)} actions)")
        if enhance == 'y':
            print("  ✓ Enhanced with intelligent error handling")
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
            session_data = json.load(f)
        
        # Handle both old format (list) and new format (dict with metadata)
        if isinstance(session_data, dict) and 'actions' in session_data:
            actions = session_data['actions']
            enhanced = session_data.get('enhanced', False)
            if enhanced:
                print(f"✓ This session has intelligent error handling enabled")
        else:
            actions = session_data
            enhanced = False
        
        print(f"\n🎬 Replaying session '{sessions[idx]}' ({len(actions)} actions)...")
        print("Press Ctrl+C to stop at any time\n")
        
        for i, action in enumerate(actions):
            print(f"[{i+1}/{len(actions)}] {action['type']}: {action.get('description', '')}")
            
            # Apply intelligent error handling if enhanced
            max_retries = action.get('error_handling', {}).get('max_retries', 1) if enhanced else 1
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    if action['type'] == 'navigate':
                        page.goto(action['url'])
                        time.sleep(1)
                        success = True
                    
                    elif action['type'] == 'click_button':
                        # Re-scan to get fresh elements
                        page_elements['buttons'] = page.locator('button, input[type="button"], input[type="submit"]').all()
                        page_elements['buttons'][action['index']].click()
                        time.sleep(0.5)
                        success = True
                    
                    elif action['type'] == 'click_link':
                        page_elements['links'] = page.locator('a[href]').all()
                        page_elements['links'][action['index']].click()
                        time.sleep(0.5)
                        success = True
                    
                    elif action['type'] == 'fill_input':
                        page_elements['inputs'] = page.locator('input[type="text"], input[type="email"], input[type="password"]').all()
                        page_elements['inputs'][action['index']].fill(action['value'])
                        time.sleep(0.3)
                        success = True
                    
                    elif action['type'] == 'type_input':
                        page_elements['inputs'] = page.locator('input[type="text"], input[type="email"], input[type="password"]').all()
                        elem = page_elements['inputs'][action['index']]
                        elem.clear()
                        
                        # Type with human-like behavior
                        for char in action['value']:
                            variation = random.uniform(-0.4, 0.4)
                            delay = int(action.get('base_delay', 100) * (1 + variation))
                            elem.type(char, delay=delay)
                        success = True
                    
                    elif action['type'] == 'select_option':
                        page_elements['selects'] = page.locator('select').all()
                        page_elements['selects'][action['index']].select_option(action['value'])
                        time.sleep(0.3)
                        success = True
                    
                    elif action['type'] == 'check_checkbox':
                        page_elements['checkboxes'] = page.locator('input[type="checkbox"]').all()
                        page_elements['checkboxes'][action['index']].check()
                        time.sleep(0.3)
                        success = True
                
                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"  ⚠ Attempt {retry_count} failed: {e}")
                        retry_delay = action.get('error_handling', {}).get('retry_delay', 1.0) if enhanced else 1.0
                        time.sleep(retry_delay)
                        print(f"  🔄 Retrying ({retry_count + 1}/{max_retries})...")
                    else:
                        print(f"  ✗ Error after {max_retries} attempts: {e}")
                        
                        on_error = action.get('error_handling', {}).get('on_error', 'continue') if enhanced else 'ask'
                        
                        if on_error == 'continue':
                            print("  → Continuing to next action (as per error handling)")
                            break
                        elif on_error == 'stop':
                            print("  → Stopping session (as per error handling)")
                            return
                        else:
                            retry = input("  Continue with next action? (y/n): ").strip().lower()
                            if retry != 'y':
                                return
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
    global is_recording, watch_and_learn_enabled
    
    print("\n" + "="*50)
    print("🌐 WEB AUTOMATION MENU")
    if is_recording:
        print(f"⏺️  RECORDING ({len(recorded_actions)} actions)")
    if watch_and_learn_enabled:
        print(f"👁️  WATCH & LEARN ({len(detected_patterns)} patterns detected)")
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
    print("11. 🔖 Save page context (for resume)")
    print("12. 📚 Use session template")
    print("13. 📄 List available templates")
    print("14. ⌨️  Toggle global hotkeys")
    print("15. 👁️  Toggle Watch & Learn")
    print("16. 📊 View detected patterns")
    print("17. 🧠 Smart Workflow Builder")
    print("18. 🔢 Simple rating click (1/2/3)")
    print("19. 🤖 Auto-rate with Gemini AI")
    print("20. Close browser and exit")
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
                        no_viewport=True,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--start-maximized',
                            '--force-device-scale-factor=1',
                            '--high-dpi-support=1',
                            '--disable-gpu-driver-bug-workarounds'
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
                            '--disable-blink-features=AutomationControlled',
                            '--start-maximized',
                            '--force-device-scale-factor=1',
                            '--high-dpi-support=1',
                            '--disable-gpu-driver-bug-workarounds'
                        ]
                    )
                    context = browser.new_context(no_viewport=True)
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
                        '--disable-blink-features=AutomationControlled',
                        '--start-maximized',
                        '--force-device-scale-factor=1',
                        '--high-dpi-support=1',
                        '--disable-gpu-driver-bug-workarounds'
                    ],
                    ignore_default_args=['--enable-automation']
                )
                context = browser.new_context(no_viewport=True)
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
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized',
                    '--force-device-scale-factor=1',
                    '--high-dpi-support=1',
                    '--disable-gpu-driver-bug-workarounds'
                ]
            )
            context = browser.new_context(no_viewport=True)
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
                    
                    # Restore page context (scroll position and form fields)
                    if user_preferences.get('form_field_cache') or user_preferences.get('last_scroll_position'):
                        restore_context = input("🔄 Restore saved context (scroll position & form fields)? (y/n): ").strip().lower()
                        if restore_context == 'y':
                            restore_page_context(page)
                    
                    # Auto-scan if enabled
                    if user_preferences.get('auto_scan', True):
                        print("\n🔍 Auto-scanning page elements...")
                        time.sleep(0.5)
                        scan_page_elements(page)
                except Exception as e:
                    print(f"⚠ Could not load last URL: {e}")
        
        # Setup hotkeys if enabled
        hotkeys_enabled = False
        if user_preferences.get('enable_hotkeys', False) and HOTKEYS_AVAILABLE:
            setup_hotkeys()
            hotkeys_enabled = True
        
        # Interactive menu loop
        while True:
            # Check for detected patterns and offer automation
            check_for_pattern_prompts()
            
            # Process hotkey actions
            if hotkeys_enabled:
                hotkey_actions = process_hotkey_actions()
                for action in hotkey_actions:
                    if action == 'toggle_record':
                        toggle_recording()
                    elif action == 'replay_last':
                        try:
                            load_session(page)
                        except Exception as e:
                            print(f"✗ Error: {e}")
            
            show_menu()
            choice = input("\nEnter your choice (1-20): ").strip()
            
            if choice == '1':
                url = input("\n🔗 Enter website URL (e.g., google.com): ").strip()
                if not url.startswith('http'):
                    url = 'https://' + url
                try:
                    print(f"Navigating to {url}...")
                    page.goto(url)
                    print(f"✓ Loaded: {page.title()}")
                    
                    # Track for Watch & Learn
                    track_action('navigate', {'url': url})
                    
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
                # Save page context
                try:
                    context_data = save_page_context(page)
                    if context_data:
                        print(f"✓ Page context saved!")
                        print(f"  • URL: {context_data['url']}")
                        print(f"  • Scroll position: {context_data['scroll_position']}px")
                        print(f"  • Form fields cached: {len(context_data['form_fields'])}")
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '12':
                # Use session template
                try:
                    list_templates()
                    template_choice = input("\nEnter template name or number (or 'c' to cancel): ").strip()
                    
                    if template_choice.lower() == 'c':
                        print("Cancelled.")
                        continue
                    
                    # Check if it's a number
                    templates = get_session_templates()
                    template_name = None
                    
                    try:
                        idx = int(template_choice)
                        template_name = list(templates.keys())[idx]
                    except (ValueError, IndexError):
                        # It's a name
                        if template_choice in templates:
                            template_name = template_choice
                    
                    if template_name:
                        apply_template(page, template_name)
                    else:
                        print(f"✗ Invalid template: {template_choice}")
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '13':
                # List templates
                list_templates()
            
            elif choice == '14':
                # Toggle global hotkeys
                if not HOTKEYS_AVAILABLE:
                    print("⚠ pynput not installed. Install with: pip install pynput")
                else:
                    if hotkeys_enabled:
                        stop_hotkeys()
                        hotkeys_enabled = False
                    else:
                        setup_hotkeys()
                        hotkeys_enabled = True
            
            elif choice == '15':
                # Toggle Watch & Learn
                toggle_watch_and_learn()
            
            elif choice == '16':
                # View detected patterns
                view_detected_patterns()
            
            elif choice == '17':
                # Smart Workflow Builder
                workflow_config = smart_workflow_builder()
                print(f"\n✓ Workflow configuration: {workflow_config}")
                print("💡 Now record your actions and they'll be saved with this configuration")
            
            elif choice == '18':
                # Simple rating click
                try:
                    simple_rating_click(page)
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '19':
                # Auto-rate with Gemini
                try:
                    auto_rate_with_gemini(page)
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            elif choice == '20':
                # Close browser and save context
                try:
                    # Auto-save page context before closing
                    if page.url != 'about:blank':
                        save_context = input("\n💾 Save current page context? (y/n): ").strip().lower()
                        if save_context == 'y':
                            save_page_context(page)
                except:
                    pass
                
                print("\n👋 Closing browser...")
                if hotkeys_enabled:
                    stop_hotkeys()
                context.close()
                print("✓ Browser closed. Goodbye!")
                break
            
            else:
                print("⚠ Invalid choice. Please enter 1-20.")

if __name__ == "__main__":
    main()
