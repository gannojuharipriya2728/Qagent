import React from 'react';
import type { PaperAnalytics } from '../api/client';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts';
import { CheckCircle2, AlertCircle, Award, Target, BookMarked, Layers } from 'lucide-react';

interface CoverageRadarChartProps {
  analytics: PaperAnalytics;
}

const BLOOM_COLORS: Record<string, string> = {
  Remember: '#3b82f6',
  Understand: '#60a5fa',
  Apply: '#10b981',
  Analyze: '#f59e0b',
  Evaluate: '#8b5cf6',
  Create: '#ec4899'
};

const DIFFICULTY_COLORS: Record<string, string> = {
  Easy: '#10b981',
  Medium: '#3b82f6',
  Hard: '#ef4444'
};

export const CoverageRadarChart: React.FC<CoverageRadarChartProps> = ({ analytics }) => {
  // Unit data for bar chart
  const unitData = Object.entries(analytics.unit_coverage || {}).map(([unit, pct]) => ({
    name: `Unit ${unit}`,
    coverage: pct
  }));

  // Bloom data
  const bloomData = Object.entries(analytics.bloom_distribution_actual || {}).map(([bloom, val]) => ({
    name: bloom,
    value: val
  }));

  // Difficulty data
  const diffData = Object.entries(analytics.difficulty_distribution_actual || {}).map(([diff, val]) => ({
    name: diff,
    value: val
  }));

  return (
    <div className="space-y-6">
      
      {/* Top Banner Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift flex items-center space-x-3.5">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl border border-emerald-100 shrink-0">
            <BookMarked className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Syllabus Coverage</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              {analytics.overall_syllabus_coverage}%
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift flex items-center space-x-3.5">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl border border-blue-100 shrink-0">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Marks Sum Check</span>
            <div className="flex items-center space-x-2 mt-0.5">
              <span className="text-2xl font-black text-slate-900">{analytics.total_marks_calculated}M</span>
              {analytics.marks_sum_valid ? (
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Valid
                </span>
              ) : (
                <span className="text-[11px] font-bold text-rose-700 bg-rose-100/80 px-2 py-0.5 rounded-full flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" /> Check
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift flex items-center space-x-3.5">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-2xl border border-purple-100 shrink-0">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Questions</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              {analytics.total_questions} Questions
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-5 shadow-xs hover-card-lift flex items-center space-x-3.5">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-2xl border border-amber-100 shrink-0">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">CO Mapping</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              {Object.keys(analytics.co_distribution || {}).length} COs Mapped
            </div>
          </div>
        </div>

      </div>

      {/* Visual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Unit Syllabus Distribution */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs">
          <h4 className="text-sm font-bold text-slate-900 mb-4 flex items-center justify-between">
            <span>Unit Question Weightage</span>
            <span className="text-xs font-semibold text-slate-400">Coverage %</span>
          </h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={unitData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} 
                  formatter={(value) => [`${value}%`, 'Weightage']} 
                />
                <Bar dataKey="coverage" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bloom's Taxonomy Distribution */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs">
          <h4 className="text-sm font-bold text-slate-900 mb-4 flex items-center justify-between">
            <span>Bloom's Taxonomy Breakdown</span>
            <span className="text-xs font-semibold text-slate-400">Levels</span>
          </h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={bloomData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {bloomData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={BLOOM_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} 
                  formatter={(value) => [`${value}%`, 'Share']} 
                />
                <Legend iconSize={8} wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Difficulty Calibration */}
        <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs">
          <h4 className="text-sm font-bold text-slate-900 mb-4 flex items-center justify-between">
            <span>Difficulty Calibration</span>
            <span className="text-xs font-semibold text-slate-400">Distribution</span>
          </h4>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={diffData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {diffData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={DIFFICULTY_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }} 
                  formatter={(value) => [`${value}%`, 'Share']} 
                />
                <Legend iconSize={8} wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
};
