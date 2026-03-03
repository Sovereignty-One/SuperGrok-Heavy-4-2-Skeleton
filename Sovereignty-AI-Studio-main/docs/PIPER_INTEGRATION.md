# Piper TTS Integration for Alerts

This integration provides text-to-speech capabilities for the live alerts system using the Piper TTS engine.

## Overview

Piper is a fast, local neural text-to-speech system that provides high-quality voice synthesis. This integration allows alerts to be spoken aloud, which is particularly useful for:

- Security alerts that require immediate attention
- Critical system notifications
- Accessibility features for visually impaired users
- Hands-free alert monitoring

## Setup

### 1. Install Piper

The Piper repository has been cloned to `piper-tts/` directory. To build and install Piper:

```bash
cd piper-tts
make
```

This will build the Piper executable. For detailed instructions, see the [Piper documentation](https://github.com/rhasspy/piper).

### 2. Download Voice Model

Download a Piper voice model (ONNX format) from the [Piper voices repository](https://github.com/rhasspy/piper/releases).

Example:
```bash
# Download a high-quality English voice
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-us-libritts-high.tar.gz
tar -xzf voice-en-us-libritts-high.tar.gz
```

### 3. Configure the Backend

Set the environment variable for the Piper model:

```bash
export PIPER_MODEL_PATH=/path/to/voice-model.onnx
```

Or configure it in your `.env` file:

```
PIPER_MODEL_PATH=/path/to/voice-model.onnx
PIPER_DIR=/path/to/piper-tts
```

## Usage

### Via API

When creating an alert via the API, add the `speak=true` query parameter:

```bash
curl -X POST "http://localhost:9898/api/v1/alerts/?speak=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "security",
    "title": "Security Alert",
    "message": "Unauthorized access detected",
    "severity": "high"
  }'
```

### Programmatically

```python
from app.services.piper_tts_service import piper_service

# Speak an alert
success = piper_service.speak_alert(
    alert_title="System Alert",
    alert_message="Database connection lost",
    severity="high"
)
```

## Alert Types and Voice Customization

The TTS service automatically adjusts the spoken text based on alert severity:

- **Critical/High**: Prefixed with "Alert!" for urgency
- **Medium/Low**: Normal tone without prefix

## Supported Platforms

- **Linux**: Uses `aplay` for audio playback
- **macOS**: Uses `afplay` for audio playback
- **Windows**: Uses PowerShell Media.SoundPlayer

## Troubleshooting

### Piper not found

If the Piper executable is not found:
1. Ensure Piper is built: `cd piper-tts && make`
2. Add Piper to your PATH: `export PATH=$PATH:/path/to/piper-tts/build`
3. Set `PIPER_DIR` environment variable

### No audio output

If TTS generates audio but doesn't play:
1. Check audio system is working: `speaker-test -t sine -f 440 -c 2`
2. Install required audio player:
   - Linux: `sudo apt-get install alsa-utils`
   - macOS: Built-in (afplay)
   - Windows: Built-in (PowerShell)

### Model not found

Download a compatible voice model from the Piper releases and set `PIPER_MODEL_PATH`.

## Integration with Security Modules

The Piper TTS integration works seamlessly with the security alerts from:

- `src/security/Alerts.Rust` - Visual security alerts
- `src/agents/AI-Lie-Detector.py` - Truth verification
- `src/security/Voice_Guard.py` - Voice command integrity
- `src/agents/eeg_agent.py` - EEG monitoring alerts

When these modules trigger alerts through the API, they can optionally enable TTS for critical notifications.

## Performance

- **Latency**: ~200-500ms for short alerts
- **Quality**: Neural TTS with natural-sounding voices
- **Offline**: Fully local, no internet required
- **Resources**: Low CPU usage, minimal memory footprint

## Future Enhancements

- [ ] Support for multiple voice models/languages
- [ ] Voice selection based on alert type
- [ ] Adjustable speech rate and pitch
- [ ] Background queue for multiple simultaneous alerts
- [ ] Integration with hardware speakers/PA systems
