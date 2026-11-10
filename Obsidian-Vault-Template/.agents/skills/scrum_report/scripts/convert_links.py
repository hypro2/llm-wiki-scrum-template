#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_links.py - Convert absolute file:/// links of plans and chats to relative markdown links
"""

import os
import sys
import re

# Set UTF-8 encoding for console output on Windows
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

script_dir = os.path.dirname(os.path.abspath(__file__))
scrum_dir = os.path.abspath(os.path.join(script_dir, ".."))

print(f"Scrum directory detected: {scrum_dir}")

subdirs = ["daily", "monthly", "total"]

# Regex patterns for plans and chats (matches any absolute file URL ending in plans/... or chats/...)
plan_pattern = re.compile(
    r"file:///[^\s)]+?/plans/([^)]+?\.md)",
    re.IGNORECASE
)

chat_md_pattern = re.compile(
    r"file:///[^\s)]+?/chats/md/([^)]+?\.md)",
    re.IGNORECASE
)

chat_root_pattern = re.compile(
    r"file:///[^\s)]+?/chats/(?!md/)([^)]+?\.md)",
    re.IGNORECASE
)

count_plans = 0
count_chats = 0

def read_file_safe(fpath):
    try:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), "utf-8"
    except Exception:
        with open(fpath, "r", encoding="cp949", errors="replace") as f:
            return f.read(), "cp949"

for subdir in subdirs:
    target_dir = os.path.join(scrum_dir, subdir)
    if not os.path.exists(target_dir):
        continue
    for fname in os.listdir(target_dir):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(target_dir, fname)
        try:
            content, encoding = read_file_safe(fpath)
        except Exception as e:
            print(f"Skipped {subdir}/{fname} due to read error: {e}")
            continue
        
        plan_matches = plan_pattern.findall(content)
        chat_md_matches = chat_md_pattern.findall(content)
        chat_root_matches = chat_root_pattern.findall(content)

        if plan_matches or chat_md_matches or chat_root_matches:
            new_content = plan_pattern.sub(r"../plans/\1", content)
            new_content = chat_md_pattern.sub(r"../chats/md/\1", new_content)
            new_content = chat_root_pattern.sub(r"../chats/md/\1", new_content)
            
            with open(fpath, "w", encoding=encoding, errors="replace") as f:
                f.write(new_content)
            
            p_len = len(plan_matches)
            c_len = len(chat_md_matches) + len(chat_root_matches)
            print(f"Updated {subdir}/{fname}: replaced {p_len} plan links, {c_len} chat links.")
            count_plans += p_len
            count_chats += c_len

print(f"\nFinished conversion:")
print(f"- Total replaced plan links: {count_plans}")
print(f"- Total replaced chat links: {count_chats}")
