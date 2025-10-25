"""
Test script for AI-powered plugin selector
Run with: python3 test_plugin_selector.py
"""

import asyncio
import os
from plugin_selector import PluginSelector


async def test_plugin_selection():
    """Test various queries to verify AI plugin selection"""
    
    # Get API key from environment or use placeholder
    api_key = os.environ.get("GEMINI_API_KEY", "")
    
    if not api_key:
        print("⚠️  No GEMINI_API_KEY found. Set it with:")
        print("   export GEMINI_API_KEY='your-key-here'")
        return
    
    print("🧪 Testing AI-Powered Plugin Selection\n")
    print("=" * 60)
    
    # Initialize selector
    selector = PluginSelector(api_key, model="gemini-1.5-flash")
    
    # Test cases: (query, context, expected_plugin)
    test_cases = [
        # Chat plugin tests
        ("help me come up with a witty reply", {"selected_text": "Hey! How are you?"}, "chat"),
        ("what should I respond with", {"selected_text": "Want to hang out?"}, "chat"),
        ("be my wingman", {"selected_text": "You're cute"}, "chat"),
        
        # Calendar plugin tests
        ("schedule a meeting for tomorrow at 3pm", {}, "calendar"),
        ("add this to my calendar", {"selected_text": "Team sync Monday 10am"}, "calendar"),
        ("remind me about this", {}, "calendar"),
        
        # Terminal plugin tests
        ("find all python files", {}, "terminal"),
        ("what's the command to list processes", {}, "terminal"),
        ("grep for TODO in all files", {}, "terminal"),
        
        # Email plugin tests
        ("send an email to john", {}, "email"),
        ("compose a professional message", {}, "email"),
        ("draft email about project update", {}, "email"),
        
        # Code plugin tests
        ("fix this error", {"selected_text": "TypeError: undefined"}, "code"),
        ("debug this code", {"selected_text": "def func():"}, "code"),
        ("explain what's wrong", {"selected_text": "syntax error"}, "code"),
        
        # Screenshot plugin tests
        ("what's in this image", {"has_screenshot": True}, "screenshot"),
        ("explain this screenshot", {"has_screenshot": True}, "screenshot"),
        
        # Notes plugin tests
        ("save this to notion", {"selected_text": "Important meeting notes"}, "notes"),
        ("add to my notes", {}, "notes"),
    ]
    
    results = {
        "correct": 0,
        "incorrect": 0,
        "errors": 0
    }
    
    for i, (query, context, expected) in enumerate(test_cases, 1):
        try:
            print(f"\n{i}. Query: '{query}'")
            if context:
                print(f"   Context: {context}")
            
            selected = await selector.select_plugin(query, context)
            
            if selected == expected:
                print(f"   ✅ Correct: {selected}")
                results["correct"] += 1
            else:
                print(f"   ❌ Wrong: got '{selected}', expected '{expected}'")
                results["incorrect"] += 1
                
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            results["errors"] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    total = results["correct"] + results["incorrect"] + results["errors"]
    print(f"✅ Correct: {results['correct']}/{total} ({results['correct']/total*100:.1f}%)")
    print(f"❌ Incorrect: {results['incorrect']}/{total}")
    print(f"⚠️  Errors: {results['errors']}/{total}")
    
    if results["correct"] / total >= 0.8:
        print("\n🎉 Great! AI plugin selection is working well!")
    elif results["correct"] / total >= 0.6:
        print("\n⚠️  Decent performance, but could be improved")
    else:
        print("\n❌ Poor performance, needs attention")


if __name__ == "__main__":
    asyncio.run(test_plugin_selection())
