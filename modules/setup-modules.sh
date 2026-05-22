#!/bin/sh
# Initialize all Sovereignty platform integration submodules.
set -e
git submodule update --init --recursive modules/familyguard
git submodule update --init --recursive modules/every-cloud-for-everyone
echo "Modules initialized:"
echo "  modules/familyguard              -- FamilyGuard iOS/macOS safety companion"
echo "  modules/every-cloud-for-everyone -- Universal cloud encryption library"
