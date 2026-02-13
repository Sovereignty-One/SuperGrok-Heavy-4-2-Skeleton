import React from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <SparklesIcon className="h-8 w-8 text-primary-600" />
            <h1 className="ml-2 text-2xl font-bold text-gray-900 font-space-grotesk">
              CreativeFlow AI
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
              Sign In
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;