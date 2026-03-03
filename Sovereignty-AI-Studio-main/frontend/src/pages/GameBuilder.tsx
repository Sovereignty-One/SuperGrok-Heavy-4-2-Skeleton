import React, { useState } from 'react';
import { CommandLineIcon } from '@heroicons/react/24/outline';

const GameBuilder: React.FC = () => {
  const [projectName, setProjectName] = useState('');
  const [projectType, setProjectType] = useState('game');
  const [description, setDescription] = useState('');

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-4">
          <CommandLineIcon className="h-12 w-12 text-orange-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 font-space-grotesk">
          AI Project Builder
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Build games, apps, and projects with AI assistance
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Project Name
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="My Awesome Game"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type
            </label>
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="game">🎮 Game</option>
              <option value="webapp">🌐 Web App</option>
              <option value="dashboard">📊 Dashboard</option>
              <option value="automation">🤖 Automation</option>
              <option value="data-viz">📈 Data Visualization</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what you want to build..."
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <option>SuperGrok Heavy 4.20</option>
              <option>Sovereign Mind</option>
              <option>Ara Core</option>
            </select>
          </div>

          <button
            type="submit"
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Build Project
          </button>
        </form>

        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">📄 Output</h3>
          <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-green-400 min-h-[120px]">
            <span className="text-gray-500">// Your project code will appear here…</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameBuilder;
