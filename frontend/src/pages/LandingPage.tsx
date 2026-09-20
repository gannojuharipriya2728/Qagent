import React, { useState } from 'react';
import { 
  Sparkles, ArrowRight, Zap, Cpu, Layers, FileDown, RefreshCw
} from 'lucide-react';
import { api, type User } from '../api/client';

interface LandingPageProps {
  onGetStarted: () => void;
  onExploreDemo: () => void;
  onQuickLogin?: (token: string, user: User) => void;
}

const SAMPLES = [
  {
    course: 'CS301 • Data Structures',
    question: 'Demonstrate LL and LR rotations on an AVL Tree and compute search complexity.',
    bloom: 'L4 Analyze',
    co: 'CO3',
    marks: '10M'
  },
  {
    course: 'CS401 • DBMS',
    question: 'Compare Tuple and Domain Relational Calculus with query transformations.',
    bloom: 'L5 Evaluate',
    co: 'CO2',
    marks: '10M'
  },
  {
    course: 'CS301 • Data Structures',
    question: 'Formulate an in-place array reversal algorithm with circular linked lists.',
    bloom: 'L3 Apply',
    co: 'CO1',
    marks: '5M'
  }
];

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onExploreDemo, onQuickLogin }) => {
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  const [qIndex, setQIndex] = useState(0);

  const handleInstantDemo = async () => {
    setIsDemoLoading(true);
    try {
      const res = await api.post('/auth/login', {
        email: 'faculty@academic.edu',
        password: 'FacultyPassword123!'
      });
      localStorage.setItem('academic_auth_token', res.data.access_token);
      if (onQuickLogin) {
        onQuickLogin(res.data.access_token, res.data.user);
      } else {
        onExploreDemo();
      }
    } catch (e) {
      onExploreDemo();
    } finally {
      setIsDemoLoading(false);
    }
  };

  const current = SAMPLES[qIndex];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-12">
      
      {/* Sleek Creative Hero */}
      <section className="relative overflow-hidden rounded-3xl bg-slate-900 border border-slate-800 text-white p-8 sm:p-14 text-center shadow-2xl">
        
        {/* Glow Effects */}
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-blue-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 right-1/4 w-80 h-80 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl mx-auto space-y-6">
          
          {/* Creative Pill */}
          <div className="inline-flex items-center space-x-2 bg-blue-500/10 border border-blue-400/30 px-3.5 py-1.5 rounded-full text-xs font-semibold text-blue-300 backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>QAgent • Autonomous Multi-Agent RAG</span>
          </div>

          {/* Minimalist Headline */}
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
            Generate Exam Papers with <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">Autonomous AI</span>
          </h1>

          {/* 1-Line Punch */}
          <p className="text-slate-300 text-sm sm:text-base font-medium">
            Syllabus Grounded • Bloom's Taxonomy • Print-Ready University PDF
          </p>

          {/* Bold CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
            <button
              onClick={handleInstantDemo}
              disabled={isDemoLoading}
              className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 text-slate-950 font-black text-sm shadow-lg shadow-amber-500/25 flex items-center space-x-2 transition-transform hover:scale-105 cursor-pointer"
            >
              <Zap className="w-4 h-4 fill-slate-950 text-slate-950" />
              <span>{isDemoLoading ? 'Entering...' : '⚡ 1-Click Demo'}</span>
            </button>

            <button
              onClick={onGetStarted}
              className="px-6 py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-lg shadow-blue-500/25 flex items-center space-x-2 transition-transform hover:scale-105 cursor-pointer"
            >
              <span>Launch Paper Wizard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

        </div>

        {/* Live Interactive Sample Preview Inside Hero */}
        <div className="relative z-10 max-w-xl mx-auto mt-10 bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 shadow-2xl backdrop-blur-md text-left space-y-3.5">
          <div className="flex items-center justify-between text-xs border-b border-slate-700/60 pb-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-mono text-slate-300 text-[11px] font-semibold">{current.course}</span>
            </div>
            <button
              onClick={() => setQIndex((qIndex + 1) % SAMPLES.length)}
              className="text-[11px] font-bold text-slate-300 hover:text-white flex items-center space-x-1 bg-slate-700/60 hover:bg-slate-700 px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Next Sample</span>
            </button>
          </div>

          <p className="text-sm font-semibold text-slate-100 leading-relaxed">
            "{current.question}"
          </p>

          <div className="flex items-center gap-2 pt-1 text-[10px] font-bold">
            <span className="bg-purple-500/20 text-purple-300 border border-purple-500/40 px-2 py-0.5 rounded">
              {current.bloom}
            </span>
            <span className="bg-blue-500/20 text-blue-300 border border-blue-500/40 px-2 py-0.5 rounded">
              {current.co}
            </span>
            <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
              {current.marks}
            </span>
            <span className="ml-auto text-emerald-400 text-[10px] font-bold">
              ✓ Validated by Agent 4
            </span>
          </div>
        </div>

      </section>

      {/* 3 Creative Minimal Cards */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <div className="bg-white border border-slate-200 rounded-3xl p-6.5 shadow-xs hover-card-lift text-center group">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3.5 group-hover:scale-110 transition-transform">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">5-Agent RAG Pipeline</h3>
          <p className="text-xs text-slate-500 mt-1">Autonomous retrieval, curriculum grounding & duplicate prevention</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-6.5 shadow-xs hover-card-lift text-center group">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3.5 group-hover:scale-110 transition-transform">
            <Layers className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Bloom & CO Verification</h3>
          <p className="text-xs text-slate-500 mt-1">Accredited L1–L6 cognitive mapping with course outcome matrices</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-3xl p-6.5 shadow-xs hover-card-lift text-center group">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3.5 group-hover:scale-110 transition-transform">
            <FileDown className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">University-Grade PDF</h3>
          <p className="text-xs text-slate-500 mt-1">Print-ready official examination sheets with institution headers</p>
        </div>

      </section>

    </div>
  );
};
