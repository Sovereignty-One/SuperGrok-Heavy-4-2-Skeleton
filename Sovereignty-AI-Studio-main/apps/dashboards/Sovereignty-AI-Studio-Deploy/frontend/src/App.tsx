import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import StoryGenerator from './pages/StoryGenerator';
import SocialCampaign from './pages/SocialCampaign';
import PresentationBuilder from './pages/PresentationBuilder';
import PodcastGenerator from './pages/PodcastGenerator';
import WritingAssistant from './pages/WritingAssistant';

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
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
