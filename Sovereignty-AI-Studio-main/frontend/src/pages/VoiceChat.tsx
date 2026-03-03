import React, { useState } from 'react';
import { SpeakerWaveIcon } from '@heroicons/react/24/outline';

const VoiceChat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState<Array<{ role: string; text: string }>>([]);

  const handleSend = () => {
    if (!message.trim()) return;
    setHistory([...history, { role: 'user', text: message }]);
    // Placeholder response - connects to /api/v1/voice/chat
    setHistory((prev) => [
      ...prev,
      { role: 'assistant', text: `Ara acknowledges: ${message}` },
    ]);
    setMessage('');
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-4">
          <SpeakerWaveIcon className="h-12 w-12 text-teal-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 font-space-grotesk">
          Voice Chat
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Talk to Ara — AI voice interaction powered by Piper TTS
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="h-96 overflow-y-auto p-6 space-y-4 bg-gray-50">
          {history.length === 0 && (
            <div className="text-center text-gray-400 mt-20">
              <SpeakerWaveIcon className="h-16 w-16 mx-auto mb-4 opacity-30" />
              <p>Start a conversation with Ara</p>
              <p className="text-sm mt-1">Voice responses powered by Piper TTS (on-device)</p>
            </div>
          )}
          {history.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs md:max-w-md px-4 py-3 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                {msg.role === 'assistant' && (
                  <span className="text-xs font-medium text-teal-600 block mb-1">🔊 Ara</span>
                )}
                <p className="text-sm">{msg.text}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex space-x-3">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type a message or speak..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              onClick={handleSend}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceChat;
