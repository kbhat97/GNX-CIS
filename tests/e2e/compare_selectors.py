"""Compare selectors.py with actual HTML IDs."""
from pathlib import Path

# Load actual IDs from HTML
actual_ids = Path('tests/e2e/actual_ids.txt').read_text().strip().split('\n')
actual_ids = [line.strip().replace('id="', '').replace('"', '') for line in actual_ids if line.strip()]

# Load selectors from selectors.py
selectors_content = Path('tests/e2e/selectors.py').read_text()

# Extract IDs from selectors (simple regex)
import re
selector_ids = re.findall(r'#([\w-]+)', selectors_content)

print("=" * 60)
print("SELECTOR ALIGNMENT ANALYSIS")
print("=" * 60)

print(f"\n📊 Stats:")
print(f"  Actual IDs in HTML: {len(actual_ids)}")
print(f"  IDs in selectors.py: {len(set(selector_ids))}")

# Check which selectors DON'T exist in actual HTML
print(f"\n❌ Selectors NOT in actual HTML (will cause test failures):")
missing_in_html = []
for sel_id in set(selector_ids):
    if sel_id not in actual_ids:
        missing_in_html.append(sel_id)
        print(f"  - #{sel_id}")

if not missing_in_html:
    print("  ✓ All selectors exist in HTML!")

# Check which IDs exist in HTML but NOT in selectors (potential coverage gaps)
print(f"\n⚠️  IDs in HTML NOT in selectors.py (unused):")
missing_in_selectors = []
for html_id in actual_ids:
    if html_id not in selector_ids:
        missing_in_selectors.append(html_id)
        print(f"  - #{html_id}")

print(f"\n" + "=" * 60)
print(f"SUMMARY:")
print(f"  Missing in HTML: {len(missing_in_html)} (FIX THESE)")
print(f"  Missing in selectors: {len(missing_in_selectors)} (optional)")
print("=" * 60)

# Create a fixes recommendation
if missing_in_html:
    print(f"\n🔧 RECOMMENDED FIXES:")
    print(f"   Option 1: Update selectors.py to match actual IDs")
    print(f"   Option 2: Add missing IDs to app.html (if they're required)")
    print(f"   Option 3: Mark tests as xfail if features don't exist yet")
