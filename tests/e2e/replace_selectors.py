"""Script to batch-replace hard-coded selectors with imports."""
from pathlib import Path

# Selector mappings
REPLACEMENTS = {
    # Dashboard
    '"#dashboard-page"': 'Dashboard.PAGE',
    '"#section-dashboard"': 'Dashboard.SECTION_DASHBOARD',
    '"#section-generate"': 'Dashboard.SECTION_GENERATE',
    '"#section-history"': 'Dashboard.SECTION_HISTORY',
    '"#section-settings"': 'Dashboard.SECTION_SETTINGS',
    '"#history-grid"': 'Dashboard.HISTORY_GRID',
    '".post-row"': 'Dashboard.POST_ROW',
    '"#style-filter"': 'Dashboard.STYLE_FILTER',
    '"#search-input"': 'Dashboard.SEARCH_INPUT',
    '"#nav-dashboard"': 'Dashboard.NAV_DASHBOARD',
    '"#nav-generate"': 'Dashboard.NAV_GENERATE',
    '"#nav-history"': 'Dashboard.NAV_HISTORY',
    '"#nav-settings"': 'Dashboard.NAV_SETTINGS',
    
    # Generate
    '"#topic-input"': 'Generate.TOPIC_INPUT',
    '"#generate-btn"': 'Generate.BUTTON',
    '"#result-content"': 'Generate.RESULT_CONTENT',
    '"#result-empty"': 'Generate.RESULT_EMPTY',
    '"#virality-score"': 'Generate.VIRALITY_SCORE',
    '"#agent-progress"': 'Generate.AGENT_PROGRESS',
    '"#generate-loading"': 'Generate.LOADING_SPINNER',
    '"#style-select"': 'Generate.STYLE_SELECT',
    
    # Persona/Admin
    '"#admin-persona-section"': 'Persona.ADMIN_SECTION',
    '"#persona-toggle"': 'Persona.TOGGLE',
    '"#admin-linkedin-actions"': 'Persona.LINKEDIN_ACTIONS',
    '"#regular-persona-section"': 'Persona.REGULAR_SECTION',
    '"#admin-settings-section"': 'Persona.SETTINGS_SECTION',
    '"#persona-mode-label"': 'Persona.MODE_LABEL',
    '"#persona-details"': 'Persona.DETAILS',
}

def add_imports(content: str, file_name: str) -> str:
    """Add necessary imports if not present."""
    imports_needed = set()
    
    # Check which imports are needed based on replacements
    if 'Dashboard.' in content or 'dashboard' in file_name.lower():
        imports_needed.add('DashboardSelectors as Dashboard')
    if 'Generate.' in content or 'generate' in file_name.lower():
        imports_needed.add('GenerateSelectors as Generate')
    if 'Persona.' in content or 'role' in file_name.lower():
        imports_needed.add('PersonaSelectors as Persona')
    
    if not imports_needed:
        return content
    
    # Build import line
    import_line = f"from tests.e2e.selectors import {', '.join(sorted(imports_needed))}"
    
    # Add after existing imports if not already present
    if import_line not in content:
        lines = content.split('\n')
        # Find last import line
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                last_import_idx = i
        
        # Insert after last import
        lines.insert(last_import_idx + 1, import_line)
        content = '\n'.join(lines)
    
    return content

def process_file(file_path: Path):
    """Process a single test file."""
    print(f"Processing {file_path.name}...")
    content = file_path.read_text(encoding='utf-8')
    
    # Apply replacements
    original = content
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)
    
    # Add imports if changes were made
    if content != original:
        content = add_imports(content, file_path.name)
        file_path.write_text(content, encoding='utf-8')
        changes = sum(1 for o, n in REPLACEMENTS.items() if o in original)
        print(f"  ✓ Replaced {changes} selectors")
    else:
        print(f"  - No changes needed")

# Process all test files
test_dir = Path('tests/e2e')
test_files = [
    'test_generate.py',
    'test_dashboard_workflows.py',
    'test_roles.py',
    'test_responsive.py',
    'test_accessibility.py',
    'test_security_ui.py',
]

for file_name in test_files:
    file_path = test_dir / file_name
    if file_path.exists():
        process_file(file_path)

print("\n✅ Selector replacement complete!")
