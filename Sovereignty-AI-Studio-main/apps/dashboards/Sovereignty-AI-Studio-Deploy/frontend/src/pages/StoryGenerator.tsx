import React from 'react';
import { BookOpenIcon } from '@heroicons/react/24/outline';

const StoryGenerator: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-4">
          <BookOpenIcon className="h-12 w-12 text-blue-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 font-space-grotesk">
          Story Generator
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Create complete stories with illustrations and narration
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Genre
            </label>
            <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <option>Fantasy</option>
              <option>Science Fiction</option>
              <option>Mystery</option>
              <option>Romance</option>
              <option>Adventure</option>
              <option>Horror</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Theme
            </label>
            <input
              type="text"
              placeholder="e.g., A hero's journey to save the world"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Story Length
            </label>
            <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <option>Short (1-2 pages)</option>
              <option>Medium (3-5 pages)</option>
              <option>Long (6-10 pages)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Style Preferences
            </label>
            <textarea
              placeholder="Describe the tone, style, and any specific elements you want included"
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" />
              <span className="text-sm text-gray-700">Generate illustrations</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" />
              <span className="text-sm text-gray-700">Add narration</span>
            </label>
          </div>

          <button
            type="submit"
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Generate Story
          </button>
        </form>
      </div>
    </div>
  );
};

export default StoryGenerator;