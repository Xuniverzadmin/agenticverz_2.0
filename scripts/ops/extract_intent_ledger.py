#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Extract panel information from the INTENT_LEDGER.md file.
# artifact_class: CODE
"""
Extract panel information from the INTENT_LEDGER.md file.

This script parses the Intent Ledger markdown and extracts:
- Panel ID
- Location (Domain, Subdomain, Topic, Slot)
- Class
- State
- Purpose (the question the panel answers)
- Capability binding

Output: CSV file with all panels mapped to their questions

Layer: L8 - Catalyst / Meta
Product: system-wide
"""

import csv
import re
from pathlib import Path
from typing import List, Dict, Optional


def parse_intent_ledger(file_path: Path) -> List[Dict]:
    """Parse the intent ledger markdown and extract panel information."""
    content = file_path.read_text()
    panels = []

    # Split by panel headers
    panel_pattern = r'### Panel: ([A-Z0-9\-]+)'
    panel_sections = re.split(panel_pattern, content)

    # First element is everything before first panel, skip it
    # Then pairs of (panel_id, panel_content)
    for i in range(1, len(panel_sections), 2):
        if i + 1 >= len(panel_sections):
            break

        panel_id = panel_sections[i].strip()
        panel_content = panel_sections[i + 1]

        # Extract location fields
        domain = extract_field(panel_content, r'-\s*Domain:\s*([A-Z_]+)')
        subdomain = extract_field(panel_content, r'-\s*Subdomain:\s*([A-Z_]+)')
        topic = extract_field(panel_content, r'-\s*Topic:\s*([A-Z_]+)')
        slot = extract_field(panel_content, r'-\s*Slot:\s*(\d+)')

        # Extract class
        panel_class = extract_field(panel_content, r'Class:\s*(\w+)')

        # Extract state
        state = extract_field(panel_content, r'State:\s*(\w+)')

        # Extract purpose (the question)
        purpose = extract_purpose(panel_content)

        # Extract capability
        capability = extract_field(panel_content, r'Capability:\s*([a-z0-9_.]+|null)')
        if capability == 'null':
            capability = ''

        panels.append({
            'panel_id': panel_id,
            'domain': domain or '',
            'subdomain': subdomain or '',
            'topic': topic or '',
            'slot': slot or '',
            'class': panel_class or '',
            'state': state or '',
            'question': purpose or '',
            'capability': capability or ''
        })

    return panels


def extract_field(content: str, pattern: str) -> Optional[str]:
    """Extract a single field using regex pattern."""
    match = re.search(pattern, content)
    if match:
        return match.group(1).strip()
    return None


def extract_purpose(content: str) -> str:
    """Extract the Purpose section which contains the question the panel answers."""
    # Find Purpose section - it starts with "Purpose:" and ends at "Capability:" or next section
    purpose_match = re.search(
        r'Purpose:\s*\n(.*?)(?=\nCapability:|\n###|\n---|\Z)',
        content,
        re.DOTALL
    )

    if purpose_match:
        purpose_text = purpose_match.group(1).strip()
        # Clean up the text - remove extra whitespace, normalize
        purpose_text = ' '.join(purpose_text.split())
        # Replace internal quotes for CSV safety
        purpose_text = purpose_text.replace('"', "'")
        # Truncate if too long
        if len(purpose_text) > 500:
            purpose_text = purpose_text[:497] + '...'
        return purpose_text

    return ''


def main():
    """Main function to extract intent ledger panels."""
    ledger_path = Path("/root/agenticverz2.0/design/l2_1/INTENT_LEDGER.md")

    if not ledger_path.exists():
        print("Error: Intent ledger not found:", ledger_path)
        return

    print(f"Parsing intent ledger: {ledger_path}")
    panels = parse_intent_ledger(ledger_path)
    print(f"Found {len(panels)} panels")

    # Write to CSV
    output_path = Path("/root/agenticverz2.0/docs/api/INTENT_LEDGER_PANELS.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'Panel_ID',
            'Domain',
            'Subdomain',
            'Topic',
            'Slot',
            'Class',
            'State',
            'Question',
            'Capability'
        ])

        # Sort by domain, subdomain, topic, slot
        panels.sort(key=lambda x: (x['domain'], x['subdomain'], x['topic'], x['slot']))

        for panel in panels:
            writer.writerow([
                panel['panel_id'],
                panel['domain'],
                panel['subdomain'],
                panel['topic'],
                panel['slot'],
                panel['class'],
                panel['state'],
                panel['question'],
                panel['capability']
            ])

    print(f"\nCSV written to: {output_path}")

    # Print summary by domain
    domains = {}
    for panel in panels:
        domain = panel['domain'] or 'UNKNOWN'
        domains[domain] = domains.get(domain, 0) + 1

    print("\nPanels by domain:")
    for domain, count in sorted(domains.items()):
        print(f"  {domain}: {count}")

    return str(output_path)


if __name__ == "__main__":
    main()
