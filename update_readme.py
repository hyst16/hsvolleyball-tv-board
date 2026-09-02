#!/usr/bin/env python3
"""
Generate README.md office mappings from teams.json
Run this before committing teams.json changes to keep README in sync.
"""

import json
from pathlib import Path

REPO_OWNER = "hyst16"
REPO_NAME = "hsvolleyball-tv-board"
TEAMS_FILE = Path("teams.json")
README_FILE = Path("README.md")

def generate_office_section(teams_data):
    """Generate the office mappings section for README."""
    if not teams_data:
        return "<!-- offices-start -->\n\nNo office mappings found.\n\n<!-- offices-end -->"
    
    lines = ["<!-- offices-start -->\n", "## Office URL mappings\n", "Use the links to open each office directly:\n"]
    
    for office_key in sorted(teams_data.keys()):
        teams = teams_data[office_key]
        lines.append(f"\n- [{office_key}](https://{REPO_OWNER}.github.io/{REPO_NAME}/?office={office_key})\n")
        for team in teams:
            lines.append(f"  - {team}\n")
    
    lines.append("\n<!-- offices-end -->")
    return "".join(lines)

def update_readme():
    """Update README.md with office section from teams.json."""
    if not TEAMS_FILE.exists():
        print(f"Error: {TEAMS_FILE} not found")
        return False
    
    with open(TEAMS_FILE) as f:
        teams_data = json.load(f)
    
    readme_content = README_FILE.read_text()
    
    # Find and replace the offices section
    import re
    pattern = r"<!-- offices-start -->.*?<!-- offices-end -->"
    new_section = generate_office_section(teams_data)
    
    updated_content = re.sub(pattern, new_section, readme_content, flags=re.DOTALL)
    
    if updated_content != readme_content:
        README_FILE.write_text(updated_content)
        print(f"Updated {README_FILE}")
        return True
    else:
        print(f"No changes needed in {README_FILE}")
        return False

if __name__ == "__main__":
    update_readme()
