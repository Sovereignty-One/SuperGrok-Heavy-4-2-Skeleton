import React, { useState } from 'react';
import { UserCircleIcon } from '@heroicons/react/24/outline';

const styles = [
  { id: 'robot', emoji: '🤖', name: 'Robot' },
  { id: 'wizard', emoji: '🧙', name: 'Wizard' },
  { id: 'fox', emoji: '🦊', name: 'Fox' },
  { id: 'panda', emoji: '🐼', name: 'Panda' },
  { id: 'astronaut', emoji: '🚀', name: 'Astronaut' },
  { id: 'lion', emoji: '🦁', name: 'Lion' },
];

const moods = ['neutral', 'happy', 'focused', 'alert', 'calm'];

const AvatarCompanion: React.FC = () => {
  const [selectedStyle, setSelectedStyle] = useState('robot');
  const [mood, setMood] = useState('neutral');
  const [eegLinked, setEegLinked] = useState(false);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-4">
          <UserCircleIcon className="h-12 w-12 text-violet-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 font-space-grotesk">
          Avatar Companion
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Customize your AI companion — Ara
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Avatar Preview */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
          <div className="text-8xl mb-4">
            {styles.find((s) => s.id === selectedStyle)?.emoji || '🤖'}
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Ara</h2>
          <p className="text-sm text-gray-500 mt-1">
            Mood: <span className="capitalize font-medium">{mood}</span>
          </p>
          {eegLinked && (
            <p className="text-xs text-teal-600 mt-2">
              🧬 EEG Linked — mood adapts to your brainwaves
            </p>
          )}
        </div>

        {/* Settings */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Style</h3>
            <div className="grid grid-cols-3 gap-3">
              {styles.map((style) => (
                <button
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`p-3 rounded-lg border-2 text-center transition-all ${
                    selectedStyle === style.id
                      ? 'border-violet-500 bg-violet-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-2xl block">{style.emoji}</span>
                  <span className="text-xs text-gray-600">{style.name}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Mood</h3>
            <div className="flex flex-wrap gap-2">
              {moods.map((m) => (
                <button
                  key={m}
                  onClick={() => setMood(m)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    mood === m
                      ? 'bg-violet-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <label className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-700">EEG Link</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Connect avatar mood to BLE EEG headset
                </p>
              </div>
              <button
                onClick={() => setEegLinked(!eegLinked)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  eegLinked ? 'bg-teal-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    eegLinked ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AvatarCompanion;
