import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Task Form State
  const [memberName, setMemberName] = useState('');
  const [taskTitle, setTaskTitle] = useState(''); // Now holds the selected requirement
  const [taskCost, setTaskCost] = useState(0);
  const [isCreatingTask, setIsCreatingTask] = useState(false);

  useEffect(() => {
    fetchProjectDetails();
    fetchTasks();
    fetchInvoices();
  }, [id]);

  const fetchProjectDetails = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${id}`);
      const data = await res.json();
      if (data.status === 'success') setProject(data.project);
    } catch (error) { console.error('Error fetching project:', error); } 
    finally { setLoading(false); }
  };

  const fetchTasks = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${id}/tasks`);
      const data = await res.json();
      if (data.status === 'success') setTasks(data.tasks);
    } catch (error) { console.error('Error fetching tasks:', error); }
  };

  const fetchInvoices = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${id}/invoices`);
      const data = await res.json();
      if (data.status === 'success') setInvoices(data.invoices);
    } catch (error) { console.error('Error fetching invoices:', error); }
  };

  const toggleRequirement = async (index) => {
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${id}/toggle-requirement?index=${index}`, { method: 'PUT' });
      const data = await res.json();
      if (data.status === 'success') {
        setProject({ ...project, requirements: data.requirements });
      }
    } catch (error) { console.error('Error toggling requirement:', error); }
  };

  const getRequirements = () => {
    if (!project?.requirements) return [];
    if (Array.isArray(project.requirements)) {
      return project.requirements.map(r => typeof r === 'string' ? { text: r, completed: false } : r);
    }
    try {
      const parsed = JSON.parse(project.requirements);
      return Array.isArray(parsed) ? parsed.map(r => typeof r === 'string' ? { text: r, completed: false } : r) : [];
    } catch { return []; }
  };

  const handleAddTask = async () => {
    if (!memberName.trim() || !taskTitle.trim()) return alert('Member name and a Requirement are required');
    
    setIsCreatingTask(true);
    try {
      const params = new URLSearchParams({
        title: taskTitle, 
        assigned_to: memberName.trim(), 
        task_cost: taskCost
      });
      const res = await fetch(`http://localhost:8000/api/projects/${id}/tasks?${params}`, { method: 'POST' });
      const data = await res.json();
      
      if (data.status === 'success') {
        const currentTeam = project.assignees || [];
        if (!currentTeam.includes(memberName.trim())) {
          setProject({ ...project, assignees: [...currentTeam, memberName.trim()] });
        }
        
        setMemberName(''); setTaskTitle(''); setTaskCost(0);
        fetchTasks();
      } else { alert(`❌ ${data.message}`); }
    } catch (error) { alert('❌ Failed to add task'); } 
    finally { setIsCreatingTask(false); }
  };

  const getStatusColor = (status) => {
    const colors = {
      'Draft': 'bg-slate-100 text-slate-600', 'Sent': 'bg-blue-50 text-blue-600',
      'Paid': 'bg-emerald-50 text-emerald-600', 'Overdue': 'bg-red-50 text-red-600',
      'pending': 'bg-slate-100 text-slate-600', 'in_progress': 'bg-blue-50 text-blue-600',
      'completed': 'bg-emerald-50 text-emerald-600'
    };
    return colors[status] || colors['Draft'];
  };

  if (loading) return <div className="flex items-center justify-center h-screen bg-slate-50"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div></div>;
  if (!project) return <div className="text-center py-20 text-slate-500 bg-slate-50 min-h-screen">Project not found.</div>;

  const requirements = getRequirements();
  const completedReqs = requirements.filter(r => r.completed).length;
  const progressPercent = requirements.length > 0 ? (completedReqs / requirements.length) * 100 : 0;
  const teamMembers = project.assignees || [];

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <button onClick={() => navigate(-1)} className="text-sm text-slate-500 hover:text-violet-600 mb-4 flex items-center gap-1.5 transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
          Back to Projects
        </button>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">{project.name}</h1>
            <p className="text-slate-500 mt-1 flex items-center gap-2">
              <span className="font-medium text-slate-700">{project.client_name}</span>
              {project.company && <><span className="text-slate-300">•</span><span>{project.company}</span></>}
            </p>
          </div>
          <div className="flex gap-2">
            <span className={`px-3 py-1.5 rounded-full text-xs font-semibold capitalize ${getStatusColor(project.status)}`}>
              {project.status.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-400 uppercase font-semibold tracking-wider">Budget</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">₹{(project.total_cost || 0).toLocaleString('en-IN')}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-400 uppercase font-semibold tracking-wider">Deadline</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{project.deadline ? new Date(project.deadline).toLocaleDateString('en-IN', {day:'2-digit', month:'short'}) : '—'}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-400 uppercase font-semibold tracking-wider">Team</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{teamMembers.length} <span className="text-sm font-normal text-slate-400">members</span></p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-400 uppercase font-semibold tracking-wider">Tasks</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{tasks.length} <span className="text-sm font-normal text-slate-400">total</span></p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: Checklist, Description, Notes */}
        <div className="lg:col-span-1 space-y-6">
          {/* Interactive Requirements Checklist */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Requirements</h3>
              <span className="text-xs font-semibold text-violet-600">{completedReqs}/{requirements.length}</span>
            </div>
            
            <div className="w-full bg-slate-100 rounded-full h-1.5 mb-5">
              <div className="bg-violet-600 h-1.5 rounded-full transition-all duration-500" style={{ width: `${progressPercent}%` }}></div>
            </div>

            <div className="space-y-3">
              {requirements.length === 0 ? (
                <p className="text-sm text-slate-400 italic text-center py-4">No requirements added yet.</p>
              ) : (
                requirements.map((req, index) => (
                  <button key={index} onClick={() => toggleRequirement(index)} className="w-full flex items-start gap-3 text-left group p-2 rounded-lg hover:bg-slate-50 transition-colors">
                    <div className={`mt-0.5 w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all ${req.completed ? 'bg-violet-600 border-violet-600' : 'border-slate-300 group-hover:border-violet-400'}`}>
                      {req.completed && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>}
                    </div>
                    <span className={`text-sm transition-all ${req.completed ? 'text-slate-400 line-through' : 'text-slate-700'}`}>{req.text}</span>
                  </button>
                ))
              )}
            </div>
          </div>

          {project.description && (
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3">Description</h3>
              <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{project.description}</p>
            </div>
          )}

          {project.notes && (
            <div className="bg-amber-50/50 p-6 rounded-xl border border-amber-100 shadow-sm">
              <h3 className="text-sm font-bold text-amber-800 uppercase tracking-wider mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                Internal Notes
              </h3>
              <p className="text-sm text-amber-900/80 leading-relaxed whitespace-pre-wrap">{project.notes}</p>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Tasks, Team, Invoices */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* ✨ Add Task Form with Requirements Dropdown */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
              <svg className="w-4 h-4 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
              Assign Requirement to Member
            </h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 1. Member Name */}
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Team Member Name *</label>
                  <input 
                    type="text" 
                    value={memberName} 
                    onChange={(e) => setMemberName(e.target.value)} 
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none text-sm transition-all" 
                    placeholder="e.g., John Doe" 
                  />
                </div>

                {/*  2. Requirements Dropdown */}
                <div className="md:col-span-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Select Requirement *</label>
                  <select 
                    value={taskTitle} 
                    onChange={(e) => setTaskTitle(e.target.value)}
                    disabled={requirements.length === 0}
                    className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm transition-all bg-white ${requirements.length === 0 ? 'border-slate-200 text-slate-400 cursor-not-allowed' : 'border-slate-200 text-slate-800'}`}
                  >
                    <option value="">
                      {requirements.length === 0 ? "Add requirements first..." : "Choose a requirement..."}
                    </option>
                    {requirements.map((req, index) => (
                      <option 
                        key={index} 
                        value={req.text} 
                        disabled={req.completed}
                      >
                        {req.text} {req.completed ? '(Completed)' : ''}
                      </option>
                    ))}
                  </select>
                  {requirements.length === 0 && (
                    <p className="text-xs text-amber-600 mt-1.5 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                      Add requirements in the checklist first.
                    </p>
                  )}
                </div>

                {/* 3. Amount */}
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1.5">Amount (₹)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></span>
                    <input 
                      type="number" 
                      value={taskCost} 
                      onChange={(e) => setTaskCost(e.target.value)} 
                      className="w-full pl-7 pr-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" 
                      placeholder="0" 
                    />
                  </div>
                </div>
              </div>

              <button 
                onClick={handleAddTask} 
                disabled={isCreatingTask || !memberName.trim() || !taskTitle.trim()} 
                className="w-full bg-slate-900 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isCreatingTask ? (
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                    Assign Requirement
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Tasks List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Assigned Tasks</h3>
              <span className="text-xs text-slate-500">{tasks.length} total</span>
            </div>
            {tasks.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">No tasks assigned to the team yet.</div>
            ) : (
              <div className="divide-y divide-slate-100">
                {tasks.map((task) => (
                  <div key={task.id} className="p-5 hover:bg-slate-50/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-800 text-sm mb-1.5">{task.title}</h4>
                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                        {task.task_cost > 0 && <div className="flex items-center gap-1.5"><svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg><span>₹{task.task_cost.toLocaleString('en-IN')}</span></div>}
                      </div>
                    </div>
                    
                    {/* Team Member Badge */}
                    <div className="flex items-center justify-between sm:justify-end gap-3 w-full sm:w-auto">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(task.status)}`}>{task.status.replace('_', ' ')}</span>
                      {task.assigned_to && (
                        <div className="flex items-center gap-2 bg-violet-50 px-3 py-1.5 rounded-full border border-violet-100">
                          <div className="w-5 h-5 rounded-full bg-violet-200 text-violet-700 flex items-center justify-center text-[10px] font-bold">
                            {task.assigned_to.charAt(0).toUpperCase()}
                          </div>
                          <span className="text-xs font-semibold text-violet-700">{task.assigned_to}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Linked Invoices */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Linked Invoices</h3>
              <span className="text-xs text-slate-500">{invoices.length} total</span>
            </div>
            {invoices.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm">No invoices linked to this project yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 uppercase bg-slate-50/50 border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Invoice #</th>
                      <th className="px-6 py-3 font-semibold">Amount</th>
                      <th className="px-6 py-3 font-semibold">Status</th>
                      <th className="px-6 py-3 font-semibold">Due Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {invoices.map((inv) => (
                      <tr key={inv.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 font-medium text-violet-600">{inv.invoice_number}</td>
                        <td className="px-6 py-4 font-semibold text-slate-800">{inv.total_amount.toLocaleString('en-IN')}</td>
                        <td className="px-6 py-4"><span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(inv.status)}`}>{inv.status}</span></td>
                        <td className="px-6 py-4 text-slate-500">{inv.due_date ? new Date(inv.due_date).toLocaleDateString('en-IN', {day:'2-digit', month:'short'}) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}