import React from 'react';
import { MegaphoneIcon } from '@heroicons/react/24/outline';

const SocialCampaign: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-4">
          <MegaphoneIcon className="h-12 w-12 text-green-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 font-space-grotesk">
          Social Media Campaign
        </h1>
        <p className="text-lg text-gray-600 mt-2">
          Create complete campaign packages with posts, images, and copy
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="text-center py-12">
          <MegaphoneIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Social Campaign Generator
          </h3>
          <p className="text-gray-600">
            This feature will be available soon. Stay tuned!
          </p>
        </div>
      </div>
    </div>
  );
};

export default SocialCampaign;