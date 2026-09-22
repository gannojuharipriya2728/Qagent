import React, { useState, useEffect } from 'react';
import { api, type User } from './api/client';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { FacultyProfilePage } from './pages/FacultyProfilePage';
import { AcademicAnalysisPage } from './pages/AcademicAnalysisPage';
import { DashboardPage } from './pages/DashboardPage';
import { ResourceManagementPage } from './pages/ResourceManagementPage';
import { GeneratePaperWizard } from './pages/GeneratePaperWizard';
import { PaperViewPage } from './pages/PaperViewPage';
import { PapersArchivePage } from './pages/PapersArchivePage';
import { AdminPage } from './pages/AdminPage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<string>('landing');
  const [pageParams, setPageParams] = useState<any>({});
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    checkCurrentUser();
  }, []);

  const checkCurrentUser = async () => {
    const token = localStorage.getItem('academic_auth_token');
    if (!token) return;
    try {
      const res = await api.get('/auth/me');
      setCurrentUser(res.data);
      if (currentPage === 'landing' || currentPage === 'login' || currentPage === 'register') {
        setCurrentPage('profile');
      }
    } catch (e) {
      localStorage.removeItem('academic_auth_token');
      setCurrentUser(null);
    }
  };

  const handleNavigate = (page: string, params: any = {}) => {
    setCurrentPage(page);
    setPageParams(params);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLoginSuccess = (_token: string, user: User) => {
    setCurrentUser(user);
    handleNavigate('profile');
  };

  const handleLogout = () => {
    localStorage.removeItem('academic_auth_token');
    setCurrentUser(null);
    handleNavigate('landing');
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      
      {/* Global Navbar */}
      <Navbar
        currentPage={currentPage}
        onNavigate={handleNavigate}
        currentUser={currentUser}
        onLogout={handleLogout}
        onQuickLogin={handleLoginSuccess}
      />

      {/* Main Routed Page Area */}
      <main className="flex-1">
        {currentPage === 'landing' && (
          <LandingPage
            onGetStarted={() => handleNavigate(currentUser ? 'profile' : 'login')}
            onExploreDemo={() => handleNavigate(currentUser ? 'profile' : 'login')}
            onQuickLogin={handleLoginSuccess}
          />
        )}

        {currentPage === 'login' && (
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onNavigateRegister={() => handleNavigate('register')}
            onNavigateBack={() => handleNavigate('landing')}
          />
        )}

        {currentPage === 'register' && (
          <RegisterPage
            onRegisterSuccess={handleLoginSuccess}
            onNavigateLogin={() => handleNavigate('login')}
            onNavigateBack={() => handleNavigate('landing')}
          />
        )}

        {currentPage === 'profile' && (
          <FacultyProfilePage
            onContinue={(courseId) => {
              if (courseId) {
                handleNavigate('dashboard', { prefillCourseId: courseId });
              } else {
                handleNavigate('dashboard');
              }
            }}
          />
        )}

        {currentPage === 'dashboard' && (
          <DashboardPage 
            onNavigate={handleNavigate}
          />
        )}

        {currentPage === 'analysis' && (
          <AcademicAnalysisPage
            courseId={pageParams.courseId || 1}
            onNavigateExam={() => handleNavigate('generate', { prefillCourseId: pageParams.courseId })}
            onNavigateBack={() => handleNavigate('dashboard')}
          />
        )}

        {currentPage === 'resources' && (
          <ResourceManagementPage 
            onNavigateAnalysis={(cId) => handleNavigate('analysis', { courseId: cId })}
          />
        )}

        {currentPage === 'generate' && (
          <GeneratePaperWizard
            prefillCourseId={pageParams.prefillCourseId}
            onGenerationComplete={(paperId) => handleNavigate('paper_view', { paperId })}
          />
        )}

        {currentPage === 'paper_view' && (
          <PaperViewPage
            paperId={pageParams.paperId}
            onNavigateBack={() => handleNavigate('papers')}
          />
        )}

        {currentPage === 'papers' && (
          <PapersArchivePage
            onSelectPaper={(paperId) => handleNavigate('paper_view', { paperId })}
            onNavigateGenerate={() => handleNavigate('generate')}
          />
        )}

        {currentPage === 'admin' && (
          <AdminPage />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 py-6 text-xs text-center no-print">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>QAgent — Agentic Question Generator Using RAG • 2026</span>
          <span className="text-slate-500">Autonomous Agents • Bloom's Taxonomy • Course Outcome Mapping</span>
        </div>
      </footer>

    </div>
  );
};

export default App;
