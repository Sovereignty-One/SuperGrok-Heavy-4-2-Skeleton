import React from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpenIcon,
  MegaphoneIcon,
  PresentationChartBarIcon,
  MicrophoneIcon,
  PencilIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const features = [
  {
    name: 'Story Generator',
    description: 'Create complete stories with illustrations and narration',
    icon: BookOpenIcon,
    href: '/story-generator',
    color: 'bg-blue-500',
  },
  {
    name: 'Social Campaign',
    description: 'Generate full social media campaigns with posts and visuals',
    icon: MegaphoneIcon,
    href: '/social-campaign',
    color: 'bg-green-500',
  },
  {
    name: 'Presentation Builder',
    description: 'Build professional presentations with AI-generated content',
    icon: PresentationChartBarIcon,
    href: '/presentation-builder',
    color: 'bg-purple-500',
  },
  {
    name: 'Podcast Generator',
    description: 'Create podcast episodes with scripts and AI voices',
    icon: MicrophoneIcon,
    href: '/podcast-generator',
    color: 'bg-red-500',
  },
  {
    name: 'Writing Assistant',
    description: 'Collaborative writing with AI suggestions and inspiration',
    icon: PencilIcon,
    href: '/writing-assistant',
    color: 'bg-yellow-500',
  },
];

const Dashboard: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto">
      <div className="text-center mb-12">
        <div className="flex justify-center items-center mb-4">
          <SparklesIcon className="h-12 w-12 text-primary-600" />
        </div>
        <h1 className="text-4xl font-bold text-gray-900 font-space-grotesk mb-4">
          Welcome to CreativeFlow AI
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your comprehensive platform for AI-powered content creation. Generate stories, 
          build campaigns, create presentations, and more with cutting-edge AI technology.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature) => (
          <Link
            key={feature.name}
            to={feature.href}
            className="group relative bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200 border border-gray-200 p-6"
          >
            <div className="flex items-center mb-4">
              <div className={`p-3 rounded-lg ${feature.color}`}>
                <feature.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="ml-4 text-lg font-semibold text-gray-900">
                {feature.name}
              </h3>
            </div>
            <p className="text-gray-600 text-sm leading-relaxed">
              {feature.description}
            </p>
            <div className="mt-4 flex items-center text-primary-600 group-hover:text-primary-700 transition-colors">
              <span className="text-sm font-medium">Get started</span>
              <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;