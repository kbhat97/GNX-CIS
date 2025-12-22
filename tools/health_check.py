"""
Codebase Health Check Script
Checks for:
- Duplicate functions
- Duplicate routes
- Sensitive data exposure
- Import errors
- Syntax errors
"""
import re
import os
from collections import Counter

def check_main_py():
    """Check main.py for issues."""
    print("=" * 60)
    print("CODEBASE HEALTH CHECK")
    print("=" * 60)
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Check for duplicate functions
    print("\n[1] Checking for duplicate functions...")
    funcs = re.findall(r'^(?:async )?def (\w+)\(', content, re.MULTILINE)
    func_counts = Counter(funcs)
    dupes = [(f, c) for f, c in func_counts.items() if c > 1]
    if dupes:
        print(f"   ⚠️  WARNING: Duplicate functions: {dupes}")
    else:
        print("   ✅ No duplicate functions")
    
    # 2. Check for duplicate routes (same method + path)
    print("\n[2] Checking for duplicate routes...")
    # Find method + route pairs
    routes = re.findall(r'@app\.(\w+)\(["\']([^"\']+)["\']', content)
    route_counts = Counter(routes)  # (method, path) pairs
    dupe_routes = [(f"{method.upper()} {path}", c) for (method, path), c in route_counts.items() if c > 1]
    if dupe_routes:
        print(f"   ⚠️  WARNING: Duplicate routes: {dupe_routes}")
    else:
        print("   ✅ No duplicate routes")
    
    # 3. Check for sensitive data exposure
    print("\n[3] Checking for sensitive data exposure...")
    sensitive_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
        (r'sk_live_\w+', 'Stripe live key'),
        (r'sk_test_\w+', 'Stripe test key'),
        (r'Bearer\s+[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', 'JWT token'),
    ]
    found_sensitive = []
    for pattern, desc in sensitive_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found_sensitive.append(desc)
    if found_sensitive:
        print(f"   ⚠️  WARNING: Potential sensitive data: {found_sensitive}")
    else:
        print("   ✅ No obvious sensitive data exposure")
    
    # 4. Check for TODO/FIXME
    print("\n[4] Checking for TODOs/FIXMEs...")
    todos = re.findall(r'#\s*(TODO|FIXME)[^\n]*', content, re.IGNORECASE)
    if todos:
        print(f"   📝 Found {len(todos)} TODOs/FIXMEs")
    else:
        print("   ✅ No TODOs/FIXMEs")
    
    # 5. Import main to verify all imports work
    print("\n[5] Verifying all imports...")
    try:
        import main
        print(f"   ✅ All imports OK - {len(main.app.routes)} routes loaded")
    except Exception as e:
        print(f"   ❌ Import error: {e}")

def check_app_html():
    """Check dashboard/app.html for issues."""
    print("\n" + "=" * 60)
    print("FRONTEND CHECK (app.html)")
    print("=" * 60)
    
    html_path = os.path.join('dashboard', 'app.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Check for duplicate function names
    print("\n[1] Checking for duplicate JS functions...")
    funcs = re.findall(r'(?:async\s+)?function\s+(\w+)\s*\(', content)
    func_counts = Counter(funcs)
    dupes = [(f, c) for f, c in func_counts.items() if c > 1]
    if dupes:
        print(f"   ⚠️  WARNING: Duplicate functions: {dupes}")
    else:
        print("   ✅ No duplicate JS functions")
    
    # 2. Check for emojis in Voice Profile section
    print("\n[2] Checking Voice Profile for emojis (should use SVGs)...")
    # Find voice profile section
    vp_match = re.search(r'id="voice-profile-section".*?</div>\s*</div>\s*</div>', content, re.DOTALL)
    if vp_match:
        vp_section = vp_match.group()
        emojis = ['🏢', '🎯', '✍️', '📌', '👤', '✨']
        found_emojis = [e for e in emojis if e in vp_section]
        if found_emojis:
            print(f"   ⚠️  WARNING: Emojis still in Voice Profile: {found_emojis}")
        else:
            print("   ✅ No emojis in Voice Profile (using SVGs)")
    else:
        print("   ⚠️  Voice Profile section not found")
    
    # 3. Check for autoSyncSubscription function
    print("\n[3] Checking for auto-sync subscription...")
    if 'autoSyncSubscription' in content:
        print("   ✅ autoSyncSubscription function exists")
    else:
        print("   ❌ autoSyncSubscription function NOT found")
    
    # 4. Check for session timeout using showNotification
    print("\n[4] Checking session timeout notification...")
    if 'showNotification' in content and 'Session expired' in content:
        print("   ✅ Session timeout uses showNotification")
    else:
        print("   ⚠️  Session timeout may still use alert()")
    
    # 5. Check for sensitive data
    print("\n[5] Checking for hardcoded sensitive data...")
    sensitive = []
    if re.search(r'sk_live_\w+', content):
        sensitive.append('Stripe live key')
    if re.search(r'pk_live_\w+', content):
        sensitive.append('Stripe publishable live key')
    if sensitive:
        print(f"   ⚠️  WARNING: Sensitive data found: {sensitive}")
    else:
        print("   ✅ No hardcoded sensitive keys")

def main():
    """Run all checks."""
    check_main_py()
    check_app_html()
    print("\n" + "=" * 60)
    print("HEALTH CHECK COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
