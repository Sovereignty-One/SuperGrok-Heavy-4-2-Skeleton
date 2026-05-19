// xAI Voice Agent — Node.js
// npm install ws  ·  export XAI_API_KEY="xai-..."

import WebSocket from 'ws';

const ws = new WebSocket('wss://api.x.ai/v1/realtime', {
  headers: { Authorization: `Bearer ${process.env.XAI_API_KEY}` },
});

ws.on('open', () => {
  ws.send(JSON.stringify({
    type: 'session.update',
    session: {
      voice: 'Ara',
      instructions: AGENT_PROMPT, // see Agent Prompt tab
      turn_detection: { type: 'server_vad' },
      tools: [{ type: 'web_search' }, { type: 'x_search' }],
      input_audio_transcription: { model: 'grok-2-audio' },
    },
  }));

  // Trigger agent to speak first
  ws.send(JSON.stringify({ type: 'response.create' }));
});

ws.on('message', (raw) => {
  const event = JSON.parse(raw.toString());

  switch (event.type) {
    case 'session.created':
      console.log('Session:', event.session.id);
      break;
    case 'input_audio_buffer.speech_started':
      ws.send(JSON.stringify({ type: 'response.cancel' }));
      break;
    case 'response.output_audio.delta':
      // Base64 PCM audio → decode and play
      playAudio(Buffer.from(event.delta, 'base64'));
      break;
    case 'response.output_audio_transcript.delta':
      process.stdout.write(event.delta);
      break;
    case 'response.done':
      console.log('\nTokens:', event.usage?.total_tokens);
      break;
  }
});

// Stream mic: ws.send({ type: 'input_audio_buffer.append', audio: '<base64>' })