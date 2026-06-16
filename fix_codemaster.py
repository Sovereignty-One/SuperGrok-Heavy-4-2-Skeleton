#!/usr/bin/env python3
import re

# Read the HTML file
with open('SGHv119.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all occurrences of the bridge check that calls Claude API
pattern = r'var bridgeOk = \(typeof PiperTTS.*?\n\}[\s\n]*\/\* Offline fallback'
replacement = '/* Local lint — no bridge, no API, no cost */\n/* Offline fallback'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write fixed file
with open('SGHv119.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ CodeMaster AI FIX patched — local lint only, zero API calls")