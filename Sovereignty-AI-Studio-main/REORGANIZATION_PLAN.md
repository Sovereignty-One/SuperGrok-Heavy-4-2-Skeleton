# Repository Reorganization Plan

This document outlines the reorganization of the Sovereignty-AI-Studio repository for better maintainability and structure.

## New Folder Structure

### `/src/agents/` - AI Agent Modules
- AI-Lie-Detector.py
- AI-Self-Lie-Detection.py
- Coach_agent.py
- Second_Squad_Agent.py
- Pieces_Agent.py
- eeg_agent.py
- eeg_agent_qresist.py
- eyes_agent.py
- XAI-Judge.py

### `/src/core/` - Core System Files
- Sovereignty_core.py
- sovereign_mind.py
- main.py
- __init__.py
- enable.py
- root.py

### `/src/security/` - Security & Protection Modules
- Scar-Keep.py
- Scar-Memory.py
- Scar-keep-tamper.py
- scar-keep.py
- scarExact.py
- Syntax-Guard.py
- Voice_Guard.py
- echo_guard.py
- SecureApp.py
- Fortress-Protocol-7.887.Rust
- Alerts.Rust

### `/src/models/` - Machine Learning Models
- ML_Board.py
- model_Definitions.py
- quantum_layer.py

### `/src/utils/` - Utility Functions
- argparser.py
- subtools.py
- cli.py
- pickers.py
- cardexport.py
- sources.py
- constance.py
- validator.py
- Verifier.py
- Code_Clean.py
- Remove-word.py
- remove-Word.py
- Bug.py
- Reasoning.py
- Mapping.py
- xView.py
- system_File_Log.py
- fonttools.py

### `/apps/dashboards/` - Dashboard Applications
- weather_dashboard.py
- Tools_Post_Quantum_Dashboard.html
- Real_Validator.html
- SuperGrok-Heavy4-2-Validator.html

### `/apps/web/` - Web Applications
- Server.js
- Deploy.html

### `/src/native/` - Native Code (C++, Swift, Rust)
- main_v1_7_sovereign.cpp
- Arc.swift
- Main.swift
- Honey.swift
- build.rs

### `/resources/assets/` - Binary & Font Assets
- ESP42.bin
- Knucklesandwich.txt.TTF
- Sovereignty_python-keycloak-master.zip

### `/resources/configs/` - Configuration Files
- Armor.yaml
- Breathe.json
- Pip-mic.xml
- Cargo.toml
- docker-compose.yml
- environment.yml

### `/resources/data/` - Data Files & Documentation
- AI Reading Accuracy
- AI-LLM-Model-Choosing
- AI_Error_Handling
- AI_Eyes_Medical
- AI_Reading_Rules
- Ai-self-code-With-TamperLock
- Airplane_blueprint.py
- Animals-Ai-Humans-Resonance_bridge
- Animals-Ai-Humans.txt
- Bulletproof-AI-Code-Fix
- HIPAA.txt
- MidasV2.0
- Ship
- Sovereignty_Truth_Wire
- UNC-AI-2026
- Scar-tamper.txt
- Scary_Truth.py
- SuperGrok-Heavy-4-2.py

### `/scripts/` - Build & Deployment Scripts
- deploy.sh

### `/crypto/` - Cryptography Modules
- Vault_crypto.js

### Keep at Root Level
- README.md
- LICENSE.MD
- SECURITY.md
- POLICY_SEC_ML_ACCESS.md
- sovereignty_structure.md
- requirements.txt
- Dockerfile
- .gitignore
- .github/
- .devcontainer/
- docs/
- FamilyGuard/
- ai_core/
- backend/
- frontend/
- src/ (already exists, will be reorganized)

## Implementation Steps

1. Create new directory structure
2. Move files to appropriate directories
3. Update import statements in Python files
4. Update configuration file paths
5. Update documentation
6. Test the reorganized structure

## Benefits

- **Better Organization**: Files grouped by functionality
- **Easier Navigation**: Clear separation of concerns
- **Scalability**: Easy to add new modules
- **Maintainability**: Logical structure for contributors
- **Professional**: Industry-standard project layout

## Notes

- All file movements preserve git history
- Import paths will need to be updated
- CI/CD configurations may need path updates
- Documentation should be updated to reflect new structure