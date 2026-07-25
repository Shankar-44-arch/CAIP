import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from '@/pages/LoginPage';
import SignupPage from '@/pages/SignupPage';
import AppLayout from '@/components/layout/AppLayout';
import ExecutiveDashboard from '@/pages/ExecutiveDashboard';
import DistrictRankingPage from '@/pages/DistrictRankingPage';
import TrendPage from '@/pages/TrendPage';
import NetworkAnalysisPage from '@/pages/NetworkAnalysisPage';
import RepeatOffendersPage from '@/pages/RepeatOffendersPage';
import AnomalyAlertsPage from '@/pages/AnomalyAlertsPage';
import DataUploadPage from '@/pages/DataUploadPage';
import ProfilePage from '@/pages/ProfilePage';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('caip_access_token'));

  useEffect(() => {
    const handleAuth = () => setIsAuthenticated(!!localStorage.getItem('caip_access_token'));
    window.addEventListener('auth_change', handleAuth);
    return () => window.removeEventListener('auth_change', handleAuth);
  }, []);

  // BUG FIX: previously there was no /login route defined at all — an
  // unauthenticated user was redirected to a path with no matching
  // <Route>, producing a blank white screen. /login is now always
  // routable, regardless of auth state.
  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<ExecutiveDashboard />} />
        <Route path="/district-ranking" element={<DistrictRankingPage />} />
        <Route path="/trend" element={<TrendPage />} />
        <Route path="/network" element={<NetworkAnalysisPage />} />
        <Route path="/offenders" element={<RepeatOffendersPage />} />
        <Route path="/anomalies" element={<AnomalyAlertsPage />} />
        <Route path="/upload" element={<DataUploadPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/signup" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}

