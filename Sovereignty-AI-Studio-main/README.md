# Sovereignty AI Studio

[![CI](https://github.com/Appel420/Sovereignty-AI-Studio/workflows/CI/badge.svg)](https://github.com/Appel420/Sovereignty-AI-Studio/actions)
[![codecov](https://codecov.io/gh/Appel420/Sovereignty-AI-Studio/branch/main/graph/badge.svg)](https://codecov.io/gh/Appel420/Sovereignty-AI-Studio)

**Private Sovereign AI Research and Development Platform**  
**Core Model:** Super Grok Heavy 4.2  
(xAI) – Locked, Sealed, Sovereign  
**Authority:** Derek Appel  
**Last Updated:** March 21, 2026

## Overview

Sovereignty AI Studio is a fully private, self-contained research and production environment for advanced sovereign artificial intelligence systems.

The platform integrates specialized domains including computer vision, logical reasoning, biomedical signal processing, cryptographic vaulting, autonomous agents, and system orchestration. All components are designed for complete operational independence, end-to-end encryption, and tamper-resistant execution.

No external services, third-party models, or internet connectivity are required for core operation.

The latest SuperGrok V90 dashboard is included at `apps/dashboards/SGHv90.html`, kept in sync with the root skeleton version (`/SGHv90.html`) so both repositories remain current.

## Project Structure

```
Sovereignty-AI-Studio/
├── .devcontainer/                 # Dev Container configuration
│   ├── devcontainer.json
│   ├── Ara.yml
│   └── ...
├── .github/                       # GitHub Actions CI workflows
│   └── workflows/
├── src/                           # Source code
│   ├── agents/                    # AI Agent Modules
│   ├── core/                      # Core System Files
│   ├── security/                  # Security & Protection Modules
│   ├── models/                    # Machine Learning Models
│   ├── utils/                     # Utility Functions
│   ├── ai_core/                   # Siri-Replace / Ara Core
│   └── native/                    # Native Code (C++, Swift, Rust)
├── apps/
│   ├── dashboards/                # Dashboard Applications
│   │   ├── SGHv90.html
│   │   ├── Tools_Post_Quantum_Dashboard.html
│   │   ├── Real_Validator.html
│   │   └── SuperGrok-Heavy4-2-Validator.html
│   └── web/                       # Web Applications
│       ├── Server.js
│       └── Deploy.html
├── backend/                       # FastAPI Backend (port 9898)
│   ├── app/
│   │   ├── api/v1/                # REST & WebSocket API endpoints
│   │   ├── core/                  # Database, security, WebSocket hub
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic schemas
│   │   └── services/              # Business logic (alerts, TTS, users)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                      # React TypeScript Frontend
│   └── src/
│       ├── Frontend_src_Auth.jsx   # Post-quantum auth login component
│       ├── xai_in_cert_Chain.html  # xAI certificate chain viewer
│       ├── components/             # Alert center, layout components
│       ├── hooks/                  # WebSocket and alert hooks
│       ├── pages/                  # Dashboard, generator pages
│       └── services/               # API client services
├── ios/                           # iOS Swift Package (SovereigntyGuard)
│   └── Sources/SovereigntyGuard/
│       ├── ContentView.swift
│       ├── SovereigntyAPIClient.swift
│       ├── AuditLogger.swift
│       ├── DebuggerDetection.swift
│       ├── FamilyGuardCore.swift
│       └── VoiceCommandIntegrity.swift
├── node-bridge/                   # Node.js Express+WS bridge (port 9899)
│   ├── server.js
│   ├── package.json
│   └── test/bridge.test.js
├── scripts/                       # Build, Deployment & Utility Scripts
│   ├── deploy.sh
│   ├── init_db.py
│   ├── demo_alerts.py
│   ├── test_alerts.py
│   ├── fullscan_cli.py
│   ├── eeg_streaming.py
│   ├── AI_iOS_Voice.py
│   ├── Backend_API_AUTH.py
│   ├── Build_Judge.py
│   ├── Secure_Audit.py
│   ├── agentMem.py
│   ├── multiAgentOrch.py
│   ├── subAgentorc.py
│   ├── reasercgerAgent.py
│   ├── parser.py
│   ├── workflows.py
│   └── Unlock_Tier_21.js
├── tests/                         # Test suite
│   ├── test_app.py
│   ├── test_weather.py
│   ├── test_authentication.py
│   └── test_studio_services.py
├── docs/                          # Documentation
│   ├── QUICK_REFERENCE.md
│   ├── PIPER_INTEGRATION.md
│   ├── ALERTS_USAGE.md
│   ├── ALERTS_SYSTEM_DIAGRAM.txt
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── POLICY_SEC_ML_ACCESS.md
│   ├── SYSTEM_VALIDATOR.md
│   ├── REORGANIZATION_PLAN.md
│   ├── Compliance_Audit.md
│   └── Harvard_Sentences.txt
├── ai_core/                       # Core AI Modules
│   ├── AI_Core.py
│   ├── ai_defense_module.py
│   ├── lie_detector.py
│   └── second_squad_agent.py
├── resources/
│   ├── assets/                    # Binary & Font Assets
│   │   ├── ESP42.bin
│   │   └── Knucklesandwich.txt.TTF
│   ├── configs/                   # Configuration Files
│   │   ├── Armor.yaml
│   │   ├── Breathe.json
│   │   ├── Pip-mic.xml
│   │   ├── Cargo.toml
│   │   └── environment.yml
│   └── data/                      # Data Files & References
├── crypto/                        # Cryptography Modules
│   └── Vault_crypto.js
├── Sovereignty_python-keycloak-master/  # Keycloak integration
├── requirements.txt               # Python dependencies
├── pkg.json                       # Electron app configuration
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container config
├── Makefile                       # Build automation
├── start-all.sh                   # Launch all services
├── setup-ish.sh                   # iSH/Alpine setup
├── LICENSE.MD
├── SECURITY.md
└── README.md
```

## Key Components

- **src/agents/**: AI Agent Modules for various tasks including lie detection and EEG analysis
- **src/core/**: Core system files for the AI platform
- **src/security/**: Security and protection modules including live alerts and tamper detection
- **src/models/**: Machine learning models and quantum layers
- **src/utils/**: Utility functions and tools
- **apps/dashboards/**: Dashboard applications including post-quantum and EEG dashboards
- **apps/web/**: Web applications
- **ai_core/**: Core AI modules (lie detector, defense module, Ara core)
- **scripts/**: Build, deployment, and utility scripts
- **tests/**: Test suite (pytest + pytest-asyncio)
- **docs/**: Project documentation
- **resources/**: Assets, configurations, and data files
- **crypto/**: Cryptography modules
- **backend/**: FastAPI backend with WebSocket support, REST API, Piper TTS integration (port 9898)
- **frontend/**: React TypeScript frontend with real-time alert notifications and post-quantum auth UI
- **ios/**: iOS Swift Package (SovereigntyGuard) with debugger detection and audit logging
- **node-bridge/**: Node.js Express+WS bridge proxying to backend (port 9899)
- **Piper TTS**: Piper text-to-speech integration for audio alerts (see [docs/PIPER_INTEGRATION.md](docs/PIPER_INTEGRATION.md))

## Features

### Live Alerts System 🚨

The platform includes a comprehensive real-time alert system for monitoring and responding to critical events:

**Backend Features:**
- WebSocket-based real-time alert delivery
- Multiple alert types: Info, Warning, Error, Security, System
- Alert severity levels: low, medium, high, critical
- Database persistence with SQLAlchemy
- RESTful API for alert management
- Integration with Piper TTS for audio notifications

**Frontend Features:**
- Real-time toast notifications for incoming alerts
- Slide-out Alert Center for viewing alert history
- Unread alert count badge in header
- Auto-reconnecting WebSocket connection
- Severity-based visual styling and animations
- Mark as read/dismiss functionality

**Security Alert Types:**
- `DEBUGGER_TOUCH` - Foreign debugger detection
- `CHAIN_BREAK` - Integrity failure events
- `LIE_DETECTED` - Truth probe violations
- `OVERRIDE_SPOKEN` - Forbidden command detection
- `YUVA9V_TRIPPED` - Emergency protocols activated

See [Piper Integration Documentation](docs/PIPER_INTEGRATION.md) for audio alert setup.

### EEG Streaming System 🧠

Real-time EEG biomedical signal acquisition and analysis via `eeg_streaming.py`:

- Lab Streaming Layer (LSL) inlet for hardware-agnostic EEG device support
- Band-power extraction: delta, theta, alpha, beta, gamma
- Butterworth bandpass filtering and Welch power spectral density
- Artifact detection and classification labeling
- Server-Sent Events (SSE) broadcasting for live dashboard streaming
- Thread-safe concurrent data store for polling endpoints

### Post-Quantum Authentication 🔐

`Backend_API_AUTH.py` implements quantum-resistant identity verification:

- **Dilithium2** post-quantum digital signatures (CRYSTALS-Dilithium)
- **TOTP** two-factor authentication as a second factor
- Signed JWT-style tokens using the authenticated public key
- Immutable audit log entries written to `/logs/auth.jsonl`
- `frontend/src/Frontend_src_Auth.jsx`: browser-side Dilithium signing via WebAssembly
- `frontend/src/xai_in_cert_Chain.html`: xAI certificate chain verification viewer

## Deployment

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Initialize the database
python scripts/init_db.py

# Test the alerts system
python scripts/test_alerts.py

# Run the backend server
cd backend
PYTHONPATH=.:./backend uvicorn app.main:app --reload
```

### Frontend Setup

```bash
# Install Node dependencies
cd frontend
npm install

# Set environment variables
echo "REACT_APP_API_URL=http://localhost:9899/api/v1" > .env
echo "REACT_APP_WS_URL=ws://localhost:9899" >> .env

# Run the development server
npm start
```

### Docker Deployment

```bash
# Build and deploy with Docker Compose
make build
make deploy
```

### Piper TTS Setup (Optional)

For audio alert notifications:

```bash
# Build Piper
cd piper-tts
make

# Download a voice model
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-us-libritts-high.tar.gz
tar -xzf voice-en-us-libritts-high.tar.gz

# Set environment variable
export PIPER_MODEL_PATH=./voice-en-us-libritts-high.onnx
```

See [docs/PIPER_INTEGRATION.md](docs/PIPER_INTEGRATION.md) for detailed setup.

## Usage

### Creating Alerts via API

```bash
# Create a security alert
curl -X POST "http://localhost:9898/api/v1/alerts/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "security",
    "title": "Unauthorized Access",
    "message": "Failed login attempt detected",
    "severity": "high",
    "source": "auth_system"
  }'

# Create an alert with audio notification
curl -X POST "http://localhost:9898/api/v1/alerts/?speak=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "critical",
    "title": "System Alert",
    "message": "Critical system failure detected",
    "severity": "critical"
  }'
```

### WebSocket Connection

The frontend automatically connects to the WebSocket endpoint for real-time alerts. To connect manually:

```javascript
const ws = new WebSocket('ws://localhost:9898/api/v1/alerts/ws/USER_ID');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received alert:', message);
};
```

## Testing

```bash
# Run backend tests
make test

# Run linter
make lint

# Clean up
make clean
```

## Execution and Chain Validation

Execution is controlled via the `./Ship` script, which performs:
- Hardware-backed commit sealing
- Chain validation (O-A-T-H)
- Federation checks across devices
- Divergence detection and halt on mismatch

## Access Control

- Root authority: Derek Appel
- Chain identifier: O-A-T-H
- Designated heir: DJ Appel

## License

GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

Copyright (C) 2026 Appel420
