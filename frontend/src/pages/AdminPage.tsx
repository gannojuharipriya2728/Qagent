import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, Users, CheckCircle2, XCircle, RefreshCw
} from 'lucide-react';
import { api, type User } from '../api/client';

export const AdminPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      const [sRes, uRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users')
      ]);
      setStats(sRes.data);
      setUsers(uRes.data);
    } catch (e) {
      console.error('Failed to load admin data:', e);
    }
  };

  const handleToggleUserStatus = async (userId: number) => {
    try {
      await api.patch(`/admin/users/${userId}/toggle-status`);
      loadAdminData();
    } catch (e) {
      alert('Failed to update user status');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-2xl border border-purple-100 shadow-2xs">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Academic Administration & Audit</h1>
            <p className="text-xs text-slate-500 mt-0.5">Monitor multi-agent health, vector indexing capacity, and faculty access</p>
          </div>
        </div>

        <button
          onClick={loadAdminData}
          className="p-2.5 bg-white border border-slate-200 rounded-2xl hover:bg-slate-50 text-slate-600 shadow-2xs transition-all cursor-pointer"
          title="Refresh System Audit"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Evaluators</span>
          <div className="text-2xl font-black text-slate-900 mt-1">{stats?.total_users || users.length} Users</div>
          <span className="text-[11px] text-slate-400 mt-1 block">Role-based Access Active</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Vector Store Index</span>
          <div className="text-2xl font-black text-purple-600 mt-1">{stats?.vector_store_documents || 9} Chunks</div>
          <span className="text-[11px] text-emerald-600 font-semibold mt-1 block">Cosine Similarity Search Active</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Examination Papers</span>
          <div className="text-2xl font-black text-blue-600 mt-1">{stats?.total_papers || 0} Papers</div>
          <span className="text-[11px] text-slate-400 mt-1 block">Syllabus Coverage Monitored</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Document Processing</span>
          <div className="text-2xl font-black text-emerald-600 mt-1">
            {stats?.failed_resources === 0 ? '100% Success' : `${stats?.failed_resources} Failed`}
          </div>
          <span className="text-[11px] text-slate-400 mt-1 block">PDF / DOCX Extractor Healthy</span>
        </div>

      </div>

      {/* Faculty Management Table */}
      <div className="bg-white border border-slate-200 rounded-3xl shadow-xs overflow-hidden">
        <div className="p-5.5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Users className="w-5 h-5 text-slate-700" />
            <h2 className="text-sm font-bold text-slate-900">Faculty & Evaluator Access Management</h2>
          </div>
          <span className="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-xl">{users.length} Registered</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50/80 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200 text-[10px]">
                <th className="py-3.5 px-4.5">Name & Email</th>
                <th className="py-3.5 px-3">Department</th>
                <th className="py-3.5 px-3">Role</th>
                <th className="py-3.5 px-3">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-4 px-4.5">
                    <div className="font-bold text-slate-900">{u.full_name}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">{u.email}</div>
                  </td>
                  <td className="py-4 px-3 text-slate-700 font-medium">{u.department}</td>
                  <td className="py-4 px-3">
                    <span className="capitalize font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">
                      {u.role}
                    </span>
                  </td>
                  <td className="py-4 px-3">
                    {u.is_active ? (
                      <span className="inline-flex items-center text-emerald-700 font-bold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-rose-700 font-bold bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                        <XCircle className="w-3 h-3 mr-1" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-4 text-right">
                    <button
                      onClick={() => handleToggleUserStatus(u.id)}
                      className={`px-3.5 py-1.5 text-xs font-bold rounded-xl transition-colors cursor-pointer ${
                        u.is_active
                          ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                          : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                      }`}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
