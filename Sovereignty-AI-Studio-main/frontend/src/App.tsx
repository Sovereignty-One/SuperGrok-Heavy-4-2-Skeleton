import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import StoryGenerator from './pages/StoryGenerator';
import SocialCampaign from './pages/SocialCampaign';
import PresentationBuilder from './pages/PresentationBuilder';
import PodcastGenerator from './pages/PodcastGenerator';
import WritingAssistant from './pages/WritingAssistant';
import MediaGenerator from './pages/MediaGenerator';
import VoiceChat from './pages/VoiceChat';
import AvatarCompanion from './pages/AvatarCompanion';
import GameBuilder from './pages/GameBuilder';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/story-generator" element={<StoryGenerator />} />
          <Route path="/social-campaign" element={<SocialCampaign />} />
          <Route path="/presentation-builder" element={<PresentationBuilder />} />
          <Route path="/podcast-generator" element={<PodcastGenerator />} />
          <Route path="/writing-assistant" element={<WritingAssistant />} />
          <Route path="/media-generator" element={<MediaGenerator />} />
          <Route path="/voice-chat" element={<VoiceChat />} />
          <Route path="/avatar-companion" element={<AvatarCompanion />} />
          <Route path="/game-builder" element={<GameBuilder />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
