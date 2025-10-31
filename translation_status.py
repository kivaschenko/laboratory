#!/usr/bin/env python3
"""
Script to identify remaining Ukrainian text in templates that needs translation
"""

import os
import re
import glob


def find_ukrainian_text_in_templates():
    """Find Ukrainian text in template files."""
    template_dir = "laboratory/templates/"
    ukrainian_pattern = r"[А-Яа-яІіЇїЄєʼ\']+[^<]*[А-Яа-яІіЇїЄєʼ\']+"

    templates_with_ukrainian = {}

    for template_file in glob.glob(f"{template_dir}*.jinja2"):
        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

            ukrainian_lines = []
            for line_num, line in enumerate(lines, 1):
                # Skip lines that already have translation functions
                if "_(" in line and ")" in line:
                    continue

                matches = re.findall(ukrainian_pattern, line)
                if matches:
                    ukrainian_lines.append((line_num, line.strip(), matches))

            if ukrainian_lines:
                templates_with_ukrainian[os.path.basename(template_file)] = (
                    ukrainian_lines
                )

    return templates_with_ukrainian


def main():
    print("🔍 Scanning for remaining Ukrainian text in templates...\n")

    templates = find_ukrainian_text_in_templates()

    if not templates:
        print("✅ All templates have been internationalized!")
        return

    print(f"📋 Found {len(templates)} templates with untranslated Ukrainian text:\n")

    total_lines = 0
    for template_name, ukrainian_lines in templates.items():
        print(f"📄 {template_name}:")
        for line_num, line, matches in ukrainian_lines:
            print(f"   Line {line_num}: {line}")
            total_lines += 1
        print()

    print(
        f"📊 Summary: {total_lines} lines across {len(templates)} templates need translation."
    )

    # Priority templates for completion
    priority_templates = [
        "solutions.jinja2",
        "normatives_list.jinja2",
        "recipes.jinja2",
        "analysis_done.jinja2",
        "statistic_form.jinja2",
        "new_normative.jinja2",
    ]

    priority_found = [t for t in templates.keys() if t in priority_templates]
    if priority_found:
        print(f"\n🎯 Priority templates to translate: {', '.join(priority_found)}")


if __name__ == "__main__":
    main()
