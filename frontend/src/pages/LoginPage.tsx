import React, { useState } from 'react';
import { LogIn, ArrowLeft } from 'lucide-react';
import { api } from '../api/client';

interface LoginPageProps {
  onLoginSuccess: (token: string, user: any) => void;
  onNavigateRegister: () => void;
  onNavigateBack?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ 
  onLoginSuccess, 
  onNavigateRegister,
  onNavigateBack 
}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('academic_auth_token', res.data.access_token);
      onLoginSuccess(res.data.access_token, res.data.user);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async (role: 'faculty' | 'admin') => {
    const creds = role === 'faculty' 
      ? { email: 'faculty@academic.edu', password: 'FacultyPassword123!' }
      : { email: 'admin@academic.edu', password: 'AdminPassword123!' };

    setEmail(creds.email);
    setPassword(creds.password);
    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await api.post('/auth/login', creds);
      localStorage.setItem('academic_auth_token', res.data.access_token);
      onLoginSuccess(res.data.access_token, res.data.user);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-3xl p-8 sm:p-9 shadow-xl relative">
        
        {/* Top Back Navigation Button */}
        {onNavigateBack && (
          <button
            type="button"
            onClick={onNavigateBack}
            className="mb-4 inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back</span>
          </button>
        )}

        {/* Header */}
        <div className="text-center space-y-2 mb-8">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-2 border border-blue-100 shadow-2xs">
            <LogIn className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Faculty Sign In</h2>
          <p className="text-xs text-slate-500">Access Academic RAG & Agentic Question Generator</p>
        </div>

        {/* Demo Quick Logins */}
        <div className="mb-6 p-4 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider">
              ⚡ Instant Demo Sign-In:
            </span>
            <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-bold">
              Viva Ready
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <button
              type="button"
              disabled={isLoading}
              onClick={() => handleQuickLogin('faculty')}
              className="px-3 py-2.5 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all text-center shadow-xs disabled:opacity-50 flex items-center justify-center space-x-1 cursor-pointer"
            >
              <span>⚡ Faculty Login</span>
            </button>
            <button
              type="button"
              disabled={isLoading}
              onClick={() => handleQuickLogin('admin')}
              className="px-3 py-2.5 text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white rounded-xl transition-all text-center shadow-xs disabled:opacity-50 flex items-center justify-center space-x-1 cursor-pointer"
            >
              <span>⚡ Admin Login</span>
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold text-slate-700">Email Address</label>
              <button
                type="button"
                onClick={() => setEmail('faculty@academic.edu')}
                className="text-[10px] text-blue-600 hover:text-blue-700 font-bold hover:underline cursor-pointer"
              >
                Use sample email
              </button>
            </div>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="faculty@academic.edu"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-bold text-slate-700">Password</label>
              <button
                type="button"
                onClick={() => setPassword('FacultyPassword123!')}
                className="text-[10px] text-blue-600 hover:text-blue-700 font-bold hover:underline cursor-pointer"
              >
                Use sample password
              </button>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? 'Signing In...' : 'Sign In to Portal'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500 font-medium">
          New faculty evaluator?{' '}
          <button
            onClick={onNavigateRegister}
            className="font-bold text-blue-600 hover:text-blue-500 hover:underline cursor-pointer"
          >
            Register Account
          </button>
        </div>

      </div>
    </div>
  );
};
