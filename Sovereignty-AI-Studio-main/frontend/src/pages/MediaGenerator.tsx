import React, { useState } from 'react';
import {
  PhotoIcon,
  FilmIcon,
  MusicalNoteIcon,
  SpeakerWaveIcon,
} from '@heroicons/react/24/outline';

const mediaTypes = [
  { id: 'image', name: 'Image', icon: PhotoIcon, color: 'bg-indigo-500' },
  { id: 'video', name: 'Video', icon: FilmIcon, color: 'bg-pink-500' },
  { id: 'audio', name: 'Audio', icon: SpeakerWaveIcon, color: 'bg-green-500' },
  { id: 'music', name: 'Music', icon: MusicalNoteIcon, color: 'bg-purple-500' },
];

const MediaGenerator: React.FC = () => {
  const [selectedType, setSelectedType] = useState('image');
  const [prompt, setPrompt] = useState('');

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-4">
          <PhotoIcon className="h-12 w-12 text-indigo-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 font-space-grotesk">
          Media Generator
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Generate images, videos, audio, and music with AI
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {mediaTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setSelectedType(type.id)}
            className={`p-4 rounded-xl border-2 transition-all ${
              selectedType === type.id
                ? 'border-primary-500 bg-primary-50 shadow-md'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <div className={`p-2 rounded-lg ${type.color} inline-block mb-2`}>
              <type.icon className="h-6 w-6 text-white" />
            </div>
            <p className="text-sm font-medium text-gray-900">{type.name}</p>
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe what you want to create
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={`Describe your ${selectedType} in detail...`}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {selectedType === 'music' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Genre</label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  <option>Ambient</option>
                  <option>Electronic</option>
                  <option>Classical</option>
                  <option>Lo-Fi</option>
                  <option>Cinematic</option>
                  <option>Focus</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Duration</label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  <option>30 seconds</option>
                  <option>1 minute</option>
                  <option>2 minutes</option>
                  <option>5 minutes</option>
                </select>
              </div>
            </div>
          )}

          {selectedType === 'audio' && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm text-green-800">
                🔊 Audio generation powered by <strong>Piper TTS</strong> — fully on-device, no cloud required.
              </p>
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Generate {selectedType.charAt(0).toUpperCase() + selectedType.slice(1)}
          </button>
        </form>
      </div>
    </div>
  );
};

export default MediaGenerator;
