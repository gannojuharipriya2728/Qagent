import React, { useState } from 'react';
import { 
  BookOpen, Sparkles, FileText, UploadCloud, ShieldCheck, LogOut, GraduationCap, Zap, LogIn, Menu, X, ChevronRight 
} from 'lucide-react';
import { api, type User } from '../api/client';

interface NavbarProps {
  currentPage: string;
  onNavigate: (page: string, params?: any) => void;
  currentUser: User | null;
  onLogout: () => void;
  onQuickLogin?: (token: string, user: User) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPage,
  onNavigate,
  currentUser,
  onLogout,
  onQuickLogin
}) => {
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleInstantDemoLogin = async () => {
    setIsLoggingIn(true);
    try {
      const res = await api.post('/auth/login', {
        email: 'faculty@academic.edu',
        password: 'FacultyPassword123!'
      });
      localStorage.setItem('academic_auth_token', res.data.access_token);
      if (onQuickLogin) {
        onQuickLogin(res.data.access_token, res.data.user);
      } else {
        onNavigate('dashboard');
      }
    } catch (e) {
      console.error('Instant login failed:', e);
      onNavigate('login');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BookOpen },
    { id: 'profile', label: 'Profile', icon: ShieldCheck },
    { id: 'resources', label: 'Syllabus Upload', icon: UploadCloud },
    { id: 'generate', label: 'Generate Paper', icon: Sparkles, highlight: true },
    { id: 'papers', label: 'Generated Papers', icon: FileText },
  ];

  if (currentUser?.role === 'admin') {
    navItems.push({ id: 'admin', label: 'Admin', icon: ShieldCheck });
  }

  const handleMobileNav = (page: string) => {
    onNavigate(page);
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="bg-slate-950/95 backdrop-blur-md border-b border-slate-800/80 text-white sticky top-0 z-50 shadow-lg shadow-black/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo */}
          <div 
            className="flex items-center space-x-3 cursor-pointer group select-none"
            onClick={() => onNavigate(currentUser ? 'dashboard' : 'landing')}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-400 flex items-center justify-center shadow-md shadow-blue-500/25 group-hover:scale-105 transition-transform">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-base tracking-tight text-white font-sans">
                  Q<span className="bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">Agent</span>
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider bg-blue-500/10 text-blue-300 px-1.5 py-0.5 rounded border border-blue-500/20">
                  RAG 2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">Academic Assessment Intelligence</p>
            </div>
          </div>

          {/* Desktop Navigation Menu */}
          {currentUser && (
            <nav className="hidden md:flex items-center space-x-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800/60">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                      isActive
                        ? item.highlight 
                          ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/30' 
                          : 'bg-slate-800 text-white shadow-sm border border-slate-700/60'
                        : item.highlight
                        ? 'text-blue-400 hover:text-blue-300 hover:bg-slate-800/60'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : item.highlight ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          )}

          {/* User Profile & Auth CTAs */}
          <div className="flex items-center space-x-2.5">
            {currentUser ? (
              <div className="flex items-center space-x-3">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-xs font-bold text-slate-100">{currentUser.full_name}</span>
                  <span className="text-[11px] text-slate-400 font-medium capitalize">
                    {currentUser.role} • {currentUser.department.split(' ')[0]}
                  </span>
                </div>
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                  {currentUser.full_name.charAt(0)}
                </div>
                <button
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-2 rounded-lg bg-slate-900 hover:bg-rose-950/50 text-slate-400 hover:text-rose-400 transition-colors border border-slate-800 hover:border-rose-800/40"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                {/* 1-Click Instant Demo Login */}
                <button
                  onClick={handleInstantDemoLogin}
                  disabled={isLoggingIn}
                  className="px-3 py-1.5 text-xs font-bold text-amber-300 bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 rounded-lg transition-all flex items-center space-x-1.5 shadow-sm active:scale-95"
                  title="1-Click Instant Faculty Demo"
                >
                  <Zap className="w-3.5 h-3.5 text-amber-400 fill-amber-400 animate-pulse" />
                  <span>{isLoggingIn ? 'Entering...' : '1-Click Demo'}</span>
                </button>

                <button
                  onClick={() => onNavigate('login')}
                  className="px-3.5 py-1.5 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-900 rounded-lg transition-colors border border-slate-800 flex items-center space-x-1.5"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Sign In</span>
                </button>

                <button
                  onClick={() => onNavigate('register')}
                  className="px-3.5 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors shadow-sm shadow-blue-500/25"
                >
                  Register
                </button>
              </div>
            )}

            {/* Mobile Menu Hamburger */}
            {currentUser && (
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="md:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
                aria-label="Toggle navigation menu"
              >
                {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            )}
          </div>

        </div>
      </div>

      {/* Mobile Drawer Navigation */}
      {isMobileMenuOpen && currentUser && (
        <div className="md:hidden bg-slate-900 border-b border-slate-800 px-4 py-3 space-y-1.5 animate-fadeIn">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleMobileNav(item.id)}
                className={`w-full px-3 py-2.5 rounded-xl text-xs font-semibold transition-all flex items-center justify-between ${
                  isActive 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                <ChevronRight className="w-4 h-4 opacity-50" />
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};
