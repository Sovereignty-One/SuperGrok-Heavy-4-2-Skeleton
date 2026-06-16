#!/usr/bin/env python3
import re

# Read the HTML file
with open('SGHv119.html', 'r', encoding='utf-8') as f:
    content = f.read()

# FIX 1: Remove the bridge check that calls Claude API
pattern1 = r'var bridgeOk = \(typeof PiperTTS.*?\n\}[\s\n]*\/\* Offline fallback'
replacement1 = '/* Local lint — no bridge, no API, no cost */\n/* Offline fallback'
content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# FIX 2: Remove duplicate at line ~20710
pattern2 = r'var bridgeOk = \(typeof PiperTTS.*?\n\}[\s\n]*\/\* Offline fallback'
replacement2 = '/* Local lint — no bridge, no API, no cost */\n/* Offline fallback'
content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)

# Write fixed file
with open('SGHv119.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ CodeMaster AI FIX patched — local lint only, zero API calls")