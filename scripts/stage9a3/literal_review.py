"""Conservative literal terminal-format recognition, with no answer key."""
import re


def terminal_option(text):
    if re.search(r'\{[^{}]+\}\s*(?:or|and|/)\s*\{[^{}]+\}\s*[.!]?\s*$',text,re.I):return None
    match=re.search(r'\{\s*([A-E])\s*(?::\s*[0-9]+)?\s*\}\s*[.!]?\s*$',text)
    return match.group(1) if match else None
