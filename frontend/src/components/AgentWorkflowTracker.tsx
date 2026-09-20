import React from 'react';
import { 
  CheckCircle2, CircleDashed, RefreshCw, BrainCircuit, Search, Sparkles, ShieldCheck, Layers, FileSpreadsheet, Terminal
} from 'lucide-react';
import type { AgentStepLog } from '../api/client';

interface AgentWorkflowTrackerProps {
  stepsLog: AgentStepLog[];
  isGenerating: boolean;
  totalDuration?: number;
}

const AGENT_STAGES = [
  { id: 'req', name: 'Requirement Analysis', icon: FileSpreadsheet, agent: 'Agent 1', desc: 'Blueprint Matrix' },
  { id: 'rag', name: 'Knowledge Retrieval', icon: Search, agent: 'Agent 2', desc: 'Vector Context' },
  { id: 'gen', name: 'Question Generation', icon: Sparkles, agent: 'Agent 3', desc: 'Pedagogical Synthesis' },
  { id: 'val', name: 'Bloom & CO Alignment', icon: ShieldCheck, agent: 'Agent 4', desc: 'Taxonomy Audit' },
  { id: 'dup', name: 'Duplicate Check', icon: Layers, agent: 'Agent 4', desc: 'Cosine Uniqueness' },
  { id: 'final', name: 'Paper Synthesis', icon: BrainCircuit, agent: 'Orchestrator', desc: 'Whole Paper Review' }
];

export const AgentWorkflowTracker: React.FC<AgentWorkflowTrackerProps> = ({
  stepsLog,
  isGenerating,
  totalDuration
}) => {
  return (
    <div className="relative overflow-hidden bg-slate-950 border border-slate-800/90 rounded-3xl p-6 sm:p-8 text-white shadow-2xl space-y-6">
      <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5 relative z-10">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-gradient-to-tr from-blue-600 to-indigo-500 text-white rounded-2xl shadow-md shadow-blue-500/25">
            <BrainCircuit className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-extrabold text-white">5-Agent Autonomous Academic Workflow</h3>
              <span className="text-[10px] uppercase font-bold tracking-wider bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30">
                Nemotron AI
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium mt-0.5">RAG context retrieval, cognitive synthesis, and automated validation</p>
          </div>
        </div>

        <div className="self-start sm:self-auto">
          {isGenerating ? (
            <div className="flex items-center space-x-2 bg-blue-500/15 text-blue-300 border border-blue-500/30 px-3.5 py-1.5 rounded-full text-xs font-bold shadow-xs">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
              <span>Agents Formulating Paper...</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 px-3.5 py-1.5 rounded-full text-xs font-bold shadow-xs">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Paper Synthesized {totalDuration ? `in ${totalDuration}s` : ''}</span>
            </div>
          )}
        </div>
      </div>

      {/* Stage Flow Indicator */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 relative z-10">
        {AGENT_STAGES.map((st, i) => {
          const Icon = st.icon;
          const isDone = !isGenerating || stepsLog.length > (i * 2 + 1);
          const isCurrent = isGenerating && stepsLog.length <= (i * 2 + 1) && stepsLog.length >= (i * 2);

          return (
            <div 
              key={st.id}
              className={`p-3.5 rounded-2xl border transition-all ${
                isDone 
                  ? 'bg-slate-900/90 border-blue-500/30 text-white shadow-xs' 
                  : isCurrent 
                  ? 'bg-blue-950/70 border-blue-500 text-blue-200 ring-2 ring-blue-500/30 shadow-md shadow-blue-500/20' 
                  : 'bg-slate-900/40 border-slate-800/80 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] uppercase font-bold tracking-wider ${isCurrent ? 'text-blue-300' : isDone ? 'text-slate-300' : 'text-slate-600'}`}>
                  {st.agent}
                </span>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
                ) : (
                  <CircleDashed className="w-4 h-4 opacity-30" />
                )}
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center space-x-1.5">
                  <Icon className={`w-3.5 h-3.5 ${isDone ? 'text-blue-400' : isCurrent ? 'text-blue-300' : 'opacity-40'}`} />
                  <span className="text-xs font-bold truncate">{st.name}</span>
                </div>
                <span className="text-[10px] text-slate-400 block truncate">{st.desc}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Live Telemetry Console */}
      <div className="bg-slate-950/90 border border-slate-800/90 rounded-2xl p-4.5 max-h-64 overflow-y-auto font-mono text-xs space-y-2 relative z-10 shadow-inner">
        <div className="flex items-center justify-between text-[11px] text-slate-500 border-b border-slate-800/60 pb-2 mb-2 font-sans font-semibold">
          <div className="flex items-center space-x-1.5">
            <Terminal className="w-3.5 h-3.5 text-blue-400" />
            <span>Multi-Agent Live Execution Telemetry</span>
          </div>
          <span>{stepsLog.length} events logged</span>
        </div>

        {stepsLog.length === 0 ? (
          <div className="text-slate-500 py-6 text-center italic font-sans text-xs">
            Initiating autonomous agent handshake and RAG context vector query...
          </div>
        ) : (
          stepsLog.map((log, idx) => (
            <div key={idx} className="flex items-start space-x-2.5 py-1 border-b border-slate-900/60 last:border-0">
              <span className="text-slate-500 shrink-0 text-[10px]">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              
              {log.status === 'completed' && (
                <span className="text-emerald-400 shrink-0 font-bold">[✓ OK]</span>
              )}
              {log.status === 'started' && (
                <span className="text-blue-400 shrink-0 font-bold">[▶ EXEC]</span>
              )}
              {log.status === 'retrying' && (
                <span className="text-amber-400 shrink-0 font-bold">[⟲ REVISE]</span>
              )}
              {log.status === 'failed' && (
                <span className="text-rose-400 shrink-0 font-bold">[✗ FAIL]</span>
              )}

              <div className="flex-1 min-w-0 font-mono text-[11px] leading-relaxed">
                <span className="text-blue-400 font-semibold mr-2">{log.agent_name}:</span>
                <span className="text-slate-300">{log.message}</span>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
};
