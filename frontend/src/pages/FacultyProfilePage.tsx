import React, { useState, useEffect } from 'react';
import { api, type FacultyProfile, type FacultyProfileUpdate } from '../api/client';
import { 
  UserCheck, 
  BookOpen, 
  Building, 
  Mail, 
  ArrowRight, 
  Edit3, 
  CheckCircle2, 
  ShieldCheck, 
  Sparkles,
  Award,
  Layers
} from 'lucide-react';

interface FacultyProfilePageProps {
  onContinue: (courseId?: number) => void;
  onNavigateCourseCreate?: () => void;
}

export const FacultyProfilePage: React.FC<FacultyProfilePageProps> = ({ onContinue }) => {
  const [profile, setProfile] = useState<FacultyProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editForm, setEditForm] = useState<FacultyProfileUpdate>({
    full_name: '',
    department: '',
  });
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await api.get('/faculty/profile');
      setProfile(res.data);
      setEditForm({
        full_name: res.data.full_name,
        department: res.data.department || '',
      });
      setError(null);
    } catch (err: any) {
      console.error('Error fetching faculty profile:', err);
      setError(err.response?.data?.detail || 'Failed to load faculty profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.put('/faculty/profile', editForm);
      setProfile(res.data);
      setIsEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      console.error('Failed to update profile:', err);
      alert(err.response?.data?.detail || 'Failed to save profile changes');
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-600 font-medium text-sm">Loading Faculty & Academic Profile...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-6 rounded-2xl flex flex-col items-center text-center">
          <p className="font-semibold mb-2">Error Loading Profile</p>
          <p className="text-sm text-rose-600 mb-4">{error || 'Faculty profile not found.'}</p>
          <button 
            onClick={fetchProfile}
            className="px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 text-white p-8 rounded-3xl shadow-xl relative overflow-hidden mb-8">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-8 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/30 border border-indigo-400/30 text-indigo-200 text-xs font-medium mb-4">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Verified Faculty Profile
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
            Faculty & Academic Profile
          </h1>
          <p className="text-indigo-200 text-sm max-w-xl">
            Please verify your academic profile and assigned courses below before proceeding to the Course Workspace.
          </p>
        </div>
      </div>

      {saveSuccess && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl flex items-center gap-3 animate-fade-in text-sm font-medium">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          Faculty profile updated successfully!
        </div>
      )}

      {/* Profile Details Card */}
      <div className="bg-white border border-slate-200/80 rounded-3xl shadow-sm p-6 sm:p-8 mb-8 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white text-xl font-bold shadow-md shadow-indigo-200">
              {profile.full_name?.charAt(0) || 'F'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">{profile.full_name}</h2>
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-md mt-1">
                <Award className="w-3.5 h-3.5" />
                {profile.role || 'Faculty'}
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="inline-flex items-center gap-2 px-4 py-2 border border-slate-300 hover:border-indigo-400 text-slate-700 hover:text-indigo-700 rounded-xl text-sm font-medium transition-colors"
          >
            <Edit3 className="w-4 h-4" />
            {isEditing ? 'Cancel Edit' : 'Edit Profile'}
          </button>
        </div>

        {isEditing ? (
          <form onSubmit={handleUpdate} className="py-6 space-y-4 max-w-lg">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                required
                value={editForm.full_name}
                onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-slate-900"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Department
              </label>
              <input
                type="text"
                required
                value={editForm.department}
                onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm text-slate-900"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-200 transition-colors"
              >
                Save Changes
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 py-6">
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Building className="w-3.5 h-3.5" /> Department
              </span>
              <p className="text-sm font-medium text-slate-800">{profile.department || 'Not Assigned'}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" /> Email Address
              </span>
              <p className="text-sm font-medium text-slate-800">{profile.email}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <UserCheck className="w-3.5 h-3.5" /> Faculty ID
              </span>
              <p className="text-sm font-medium text-slate-800">{profile.faculty_id || `FAC-${profile.id.toString().padStart(4, '0')}`}</p>
            </div>
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" /> Academic Role
              </span>
              <p className="text-sm font-medium text-slate-800">{profile.role || 'Faculty Member'}</p>
            </div>
          </div>
        )}

        {/* Assigned Courses Section */}
        <div className="pt-6 border-t border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-600" />
              Courses Assigned ({profile.courses_assigned?.length || 0})
            </h3>
          </div>

          {profile.courses_assigned && profile.courses_assigned.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {profile.courses_assigned.map((course) => (
                <div
                  key={course.id}
                  onClick={() => onContinue(course.id)}
                  className="p-4 rounded-2xl border border-slate-200/80 hover:border-indigo-300 bg-slate-50/50 hover:bg-indigo-50/30 transition-all cursor-pointer group flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-mono font-bold text-indigo-600">{course.code}</span>
                    <h4 className="text-sm font-semibold text-slate-900 group-hover:text-indigo-900 transition-colors">
                      {course.name}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Sem: {course.semester} • AY: {course.academic_year}
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-1 transition-all flex-shrink-0" />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 px-4 bg-slate-50/60 rounded-2xl border border-dashed border-slate-200">
              <p className="text-sm text-slate-500 mb-2">No courses assigned yet.</p>
              <p className="text-xs text-slate-400">You can create a new course in the Course Workspace.</p>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm">
        <div className="flex items-center gap-2 text-slate-600 text-xs">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span>Profile verified? Proceed to your active course workspace to manage resources & generate papers.</span>
        </div>
        <button
          onClick={() => onContinue()}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-sm font-semibold shadow-lg shadow-indigo-200 transition-all transform hover:-translate-y-0.5"
        >
          <span>Continue to Course Workspace</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
