import React, { useState } from 'react';
import { UserPlus, ArrowLeft } from 'lucide-react';
import { api } from '../api/client';

interface RegisterPageProps {
  onRegisterSuccess: (token: string, user: any) => void;
  onNavigateLogin: () => void;
  onNavigateBack?: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ 
  onRegisterSuccess, 
  onNavigateLogin,
  onNavigateBack 
}) => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [department, setDepartment] = useState('Computer Science & Engineering');
  const [semester, setSemester] = useState('Semester V');
  const [role, setRole] = useState('faculty');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match. Please verify both password fields.');
      return;
    }

    setIsLoading(true);

    try {
      const res = await api.post('/auth/register', {
        email,
        full_name: fullName,
        department,
        semester,
        role,
        password
      });
      localStorage.setItem('academic_auth_token', res.data.access_token);
      onRegisterSuccess(res.data.access_token, res.data.user);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Registration failed. Please verify details.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAutoFill = () => {
    const randomSuffix = Math.floor(100 + Math.random() * 900);
    setFullName('Prof. Alan Turing');
    setEmail(`aturing${randomSuffix}@academic.edu`);
    setDepartment('Artificial Intelligence & Machine Learning');
    setSemester('Semester VI');
    setRole('faculty');
    setPassword('FacultyPassword123!');
    setConfirmPassword('FacultyPassword123!');
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
        <div className="text-center space-y-2 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-2 border border-indigo-100 shadow-2xs">
            <UserPlus className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Faculty Registration</h2>
          <p className="text-xs text-slate-500">Create your academic evaluator profile</p>
        </div>

        {/* Quick Autofill Helper */}
        <div className="mb-5 flex justify-end">
          <button
            type="button"
            onClick={handleAutoFill}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-3 py-1.5 rounded-xl transition-colors flex items-center space-x-1 cursor-pointer"
          >
            <span>⚡ Auto-Fill Sample Profile</span>
          </button>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Prof. Ada Lovelace"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Academic Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alovelace@university.edu"
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Department</label>
              <input
                type="text"
                required
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="e.g. CSE / AIML"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Semester</label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-semibold cursor-pointer"
              >
                <option value="Semester I">Semester I</option>
                <option value="Semester II">Semester II</option>
                <option value="Semester III">Semester III</option>
                <option value="Semester IV">Semester IV</option>
                <option value="Semester V">Semester V</option>
                <option value="Semester VI">Semester VI</option>
                <option value="Semester VII">Semester VII</option>
                <option value="Semester VIII">Semester VIII</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Confirm Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900 font-medium"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-indigo-500/20 disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? 'Creating Account...' : 'Complete Registration'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-500 font-medium">
          Already registered?{' '}
          <button
            onClick={onNavigateLogin}
            className="font-bold text-indigo-600 hover:text-indigo-500 hover:underline cursor-pointer"
          >
            Sign In Here
          </button>
        </div>

      </div>
    </div>
  );
};
