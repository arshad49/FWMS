import { useState, useEffect, Fragment } from 'react';
import toast from 'react-hot-toast';
import { Dialog, Transition } from '@headlessui/react';
import { Plus, Edit2, Trash2, X, IndianRupee, ListTodo, Search, TrendingUp, AlertCircle, Wallet, CreditCard, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  
  const [editingTask, setEditingTask] = useState(null);
  const [filterProjectId, setFilterProjectId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [modalProjectDetails, setModalProjectDetails] = useState(null);
  
  const [formData, setFormData] = useState({
    project_id: '', title: '', description: '', status: 'To Do', deadline: '', assigned_to: '', task_cost: 0, notes: ''
  });

  useEffect(() => { fetchInitialData(); }, []);
  useEffect(() => { fetchTasks(); }, [filterProjectId]);

  const fetchInitialData = async () => {
    try {
      const taskRes = await fetch('http://localhost:8000/api/tasks');
      const projRes = await fetch('http://localhost:8000/api/projects/list');
      const taskData = await taskRes.json();
      const projData = await projRes.json();
      setTasks(taskData.tasks || taskData || []); 
      setProjects(projData.projects || projData || []);
    } catch (error) { toast.error("Failed to load data"); } finally { setLoading(false); }
  };

  const fetchTasks = async () => {
    try {
      const url = filterProjectId ? `/tasks?project_id=${filterProjectId}` : '/tasks';
      const res = await fetch(`http://localhost:8000/api${url}`); 
      const data = await res.json();
      setTasks(data.tasks || data || []);
    } catch (error) { toast.error("Failed to load tasks"); }
  };

  const handleProjectSelect = async (projectId) => {
    setFormData((prev) => ({ ...prev, project_id: projectId, title: '' }));
    setModalProjectDetails(null);
    if (projectId) {
      try {
        const res = await fetch(`http://localhost:8000/api/projects/${projectId}`);
        const data = await res.json();
        setModalProjectDetails(data.project || data);
      } catch (error) { console.error("Failed to load project details", error); }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.project_id || !formData.title) return toast.error("Project and Requirement are required!");
    try {
      const method = editingTask ? 'PUT' : 'POST';
      const url = editingTask ? `http://localhost:8000/api/tasks/${editingTask.id}` : 'http://localhost:8000/api/tasks';
      await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(formData) });
      toast.success(editingTask ? "Task updated!" : "Task allocated!");
      closeModal(); fetchTasks();
    } catch (error) { toast.error("Failed to save task"); }
  };

  const openModal = (task = null) => {
    if (task) {
      setEditingTask(task);
      setFormData({ project_id: task.project_id, title: task.title, description: task.description || '', status: task.status, deadline: task.deadline || '', assigned_to: task.assigned_to || '', task_cost: task.task_cost || 0, notes: task.notes || '' });
      if (task.project_id) handleProjectSelect(task.project_id);
    } else {
      setEditingTask(null);
      setFormData({ project_id: filterProjectId || '', title: '', description: '', status: 'To Do', deadline: '', assigned_to: '', task_cost: 0, notes: '' });
      setModalProjectDetails(null);
      if (filterProjectId) handleProjectSelect(filterProjectId);
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingTask(null); setModalProjectDetails(null); };

  const handleStatusChange = async (taskId, newStatus) => {
    try { 
      await fetch(`http://localhost:8000/api/tasks/${taskId}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ status: newStatus }) }); 
      toast.success("Status updated"); fetchTasks(); 
    } catch (error) { toast.error("Failed to update status"); }
  };

  const handleDelete = async (id, title) => {
    if (window.confirm(`Delete task "${title}"?`)) {
      try { await fetch(`http://localhost:8000/api/tasks/${id}`, { method: 'DELETE' }); toast.success("Task deleted"); fetchTasks(); } 
      catch (error) { toast.error("Failed to delete"); }
    }
  };

  // ✨ Handle Task Payment
  const handlePayTask = async () => {
    if (!selectedTask) return;
    try {
      const res = await fetch(`http://localhost:8000/api/tasks/${selectedTask.id}/pay`, { method: 'PUT' });
      const data = await res.json();
      if (data.status === 'success') {
        toast.success("Task marked as paid!");
        setIsPayModalOpen(false);
        fetchTasks();
      } else {
        toast.error(data.message);
      }
    } catch (error) { toast.error("Failed to pay task"); }
  };

  const filteredTasks = tasks.filter(task =>
    task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.assigned_to?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    task.project_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch(status) {
      case 'Done': return 'border-blue-900 text-blue-900 bg-blue-50';
      case 'In Progress': return 'border-slate-400 text-slate-700 bg-white';
      default: return 'border-gray-200 text-gray-400 bg-white';
    }
  };

  // --- Calculations ---
  const totalAllocated = filteredTasks.reduce((sum, t) => sum + (t.task_cost || 0), 0);
  const totalPaid = filteredTasks.filter(t => t.is_paid).reduce((sum, t) => sum + (t.task_cost || 0), 0);
  const selectedProject = projects.find(p => p.id === filterProjectId);
  const projectBudget = selectedProject?.total_cost || 0;
  const balanceAllocated = projectBudget - totalAllocated;

  if (loading) return <div className="p-8"><div className="animate-pulse h-64 bg-gray-100 rounded"></div></div>;

  return (
    <div className="p-8 max-w-7xl mx-auto bg-gray-50 min-h-screen">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Task Allocation & Management</h1>
        <p className="text-sm text-gray-500 mt-1">Allocate tasks, track budgets, and manage assignee payments</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <input type="text" placeholder="Search tasks..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition" />
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        </div>
        <div className="flex gap-2">
          <select className="px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition min-w-[200px]" value={filterProjectId} onChange={(e) => setFilterProjectId(e.target.value)}>
            <option value="">All Projects</option>
            {projects.map(p => (<option key={p.id} value={p.id}>{p.name}</option>))}
          </select>
          <button onClick={() => openModal()} className="flex items-center gap-2 bg-blue-900 text-white px-6 py-2.5 rounded-lg hover:bg-blue-800 transition shadow-sm font-medium">
            <Plus size={18} /> Allocate Task
          </button>
        </div>
      </div>

      {/* ✨ Summary Cards (Cleaned up: Removed Invoice card) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-br from-blue-900 to-blue-800 text-white p-5 rounded-xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-200">Total Allocated</p>
              <p className="text-2xl font-bold mt-1">₹{totalAllocated.toLocaleString('en-IN')}</p>
              <p className="text-xs text-blue-300 mt-1">{filteredTasks.length} tasks</p>
            </div>
            <IndianRupee size={32} className="text-blue-300" />
          </div>
        </div>

        {filterProjectId && selectedProject && (
          <div className={`p-5 rounded-xl shadow-sm border ${balanceAllocated >= 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-xs uppercase font-semibold ${balanceAllocated >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>Balance Allocated</p>
                <p className={`text-2xl font-bold mt-1 ${balanceAllocated >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>₹{Math.abs(balanceAllocated).toLocaleString('en-IN')}</p>
                <p className="text-xs text-gray-500 mt-1">Budget: ₹{projectBudget.toLocaleString('en-IN')}</p>
              </div>
              {balanceAllocated < 0 ? <AlertCircle size={24} className="text-red-500" /> : <TrendingUp size={24} className="text-emerald-500" />}
            </div>
          </div>
        )}

        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 uppercase font-semibold">Paid to Team</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">₹{totalPaid.toLocaleString('en-IN')}</p>
              <p className="text-xs text-gray-400 mt-1">{filteredTasks.filter(t => t.is_paid).length} tasks paid</p>
            </div>
            <CreditCard size={24} className="text-gray-400" />
          </div>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {filteredTasks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Task</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Assigned</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Cost</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Payment Status</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <AnimatePresence>
                  {filteredTasks.map((task) => (
                    <motion.tr key={task.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-3">
                          <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-900 flex-shrink-0"><ListTodo size={20} /></div>
                          <div>
                            <div className="font-semibold text-slate-900">{task.title}</div>
                            <div className="text-xs text-gray-400 mt-0.5">{task.project_name || '-'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {task.assigned_to ? (
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-900">{task.assigned_to.charAt(0).toUpperCase()}</div>
                            <span className="text-sm font-medium text-gray-700">{task.assigned_to}</span>
                          </div>
                        ) : <span className="text-gray-400 text-sm">-</span>}
                      </td>
                      <td className="px-6 py-4 font-semibold text-slate-900">₹{(task.task_cost || 0).toLocaleString('en-IN')}</td>
                      <td className="px-6 py-4">
                        <select className={`text-xs font-semibold rounded-full px-3 py-1.5 border cursor-pointer focus:ring-1 focus:ring-blue-900 outline-none ${getStatusColor(task.status)}`} value={task.status} onChange={(e) => handleStatusChange(task.id, e.target.value)}>
                          <option>To Do</option><option>In Progress</option><option>Done</option>
                        </select>
                      </td>
                      
                      {/* ✨ Simplified Payment Column (No Invoice) */}
                      <td className="px-6 py-4">
                        {task.is_paid ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 size={12} /> Paid
                          </span>
                        ) : (
                          <button onClick={() => { setSelectedTask(task); setIsPayModalOpen(true); }} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-50 text-gray-600 border border-gray-200 hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-200 transition">
                            <CreditCard size={12} /> Pay Assignee
                          </button>
                        )}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button onClick={() => openModal(task)} className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition"><Edit2 size={16} /></button>
                          <button onClick={() => handleDelete(task.id, task.title)} className="p-2 text-gray-500 hover:bg-red-50 hover:text-red-600 rounded-lg transition"><Trash2 size={16} /></button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-16 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4"><ListTodo size={32} className="text-gray-300" /></div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">No tasks found</h3>
            <p className="text-gray-500 mb-4">Allocate your first task to get started</p>
          </div>
        )}
      </div>

      {/* ✨ Simple Pay Task Modal */}
      <Transition appear show={isPayModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={() => setIsPayModalOpen(false)}>
          <Transition.Child as={Fragment} enter="ease-out duration-300" enterFrom="opacity-0" enterTo="opacity-100" leave="ease-in duration-200" leaveFrom="opacity-100" leaveTo="opacity-0">
            <div className="fixed inset-0 bg-black bg-opacity-25 backdrop-blur-sm" />
          </Transition.Child>
          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child as={Fragment} enter="ease-out duration-300" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100" leave="ease-in duration-200" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95">
                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <Dialog.Title as="h3" className="text-lg font-bold text-slate-900 flex items-center gap-2">
                      <CreditCard className="text-emerald-600" /> Record Task Payment
                    </Dialog.Title>
                    <button onClick={() => setIsPayModalOpen(false)} className="p-2 text-gray-400 hover:text-slate-900 hover:bg-gray-100 rounded-lg transition"><X size={20} /></button>
                  </div>
                  
                  {selectedTask && (
                    <div className="space-y-4">
                      <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                        <p className="text-sm text-gray-500">Task</p>
                        <p className="font-semibold text-slate-900">{selectedTask.title}</p>
                        <p className="text-xs text-gray-400 mt-1">Assigned to: {selectedTask.assigned_to || 'Unassigned'}</p>
                      </div>
                      
                      <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-lg border border-emerald-100">
                        <span className="text-sm font-medium text-emerald-900">Amount to Pay:</span>
                        <span className="text-xl font-bold text-emerald-900">₹{(selectedTask.task_cost || 0).toLocaleString('en-IN')}</span>
                      </div>

                      <p className="text-xs text-gray-500">
                        This will mark the task as paid to the assignee and update the "Paid to Team" total.
                      </p>

                      <div className="flex gap-3 pt-2">
                        <button onClick={() => setIsPayModalOpen(false)} className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium">Cancel</button>
                        <button onClick={handlePayTask} className="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition font-medium shadow-sm flex items-center justify-center gap-2">
                          <CreditCard size={16} /> Confirm Payment
                        </button>
                      </div>
                    </div>
                  )}
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>

      {/* Allocation Modal (Existing) */}
      <Transition appear show={isModalOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50" onClose={closeModal}>
          <Transition.Child as={Fragment} enter="ease-out duration-300" enterFrom="opacity-0" enterTo="opacity-100" leave="ease-in duration-200" leaveFrom="opacity-100" leaveTo="opacity-0">
            <div className="fixed inset-0 bg-black bg-opacity-25 backdrop-blur-sm" />
          </Transition.Child>
          <div className="fixed inset-0 overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <Transition.Child as={Fragment} enter="ease-out duration-300" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100" leave="ease-in duration-200" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95">
                <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-6">
                    <Dialog.Title as="h3" className="text-xl font-bold text-slate-900">{editingTask ? 'Edit Task' : 'Allocate New Task'}</Dialog.Title>
                    <button onClick={closeModal} className="p-2 text-gray-400 hover:text-slate-900 hover:bg-gray-100 rounded-lg transition"><X size={20} /></button>
                  </div>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">Project <span className="text-gray-400">*</span></label>
                      <select required className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition" value={formData.project_id} onChange={(e) => handleProjectSelect(e.target.value)}>
                        <option value="">Select a project</option>{projects.map(p => (<option key={p.id} value={p.id}>{p.name}</option>))}
                      </select>
                    </div>
                    {modalProjectDetails && (
                      <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2"><Wallet size={16} className="text-blue-600" /><span className="text-gray-600">Project Budget:</span><span className="font-bold text-blue-900">₹{(modalProjectDetails.total_cost || 0).toLocaleString('en-IN')}</span></div>
                      </div>
                    )}
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">Select Requirement <span className="text-gray-400">*</span></label>
                      <select required disabled={!modalProjectDetails} className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition disabled:bg-gray-100" value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})}>
                        <option value="">{modalProjectDetails ? "Choose a requirement..." : "Select a project first"}</option>
                        {modalProjectDetails && (Array.isArray(modalProjectDetails.requirements) ? modalProjectDetails.requirements : []).map((req, index) => (
                          <option key={index} value={typeof req === 'string' ? req : req.text} disabled={typeof req !== 'string' && req.completed}>
                            {typeof req === 'string' ? req : req.text} {typeof req !== 'string' && req.completed ? '(Completed)' : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">Assigned To</label>
                        <input type="text" className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition" value={formData.assigned_to} onChange={(e) => setFormData({...formData, assigned_to: e.target.value})} />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">Task Cost (₹)</label>
                        <input type="number" min="0" step="0.01" className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition" value={formData.task_cost} onChange={(e) => setFormData({...formData, task_cost: parseFloat(e.target.value) || 0})} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">Status</label>
                        <select className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition" value={formData.status} onChange={(e) => setFormData({...formData, status: e.target.value})}>
                          <option>To Do</option><option>In Progress</option><option>Done</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5 uppercase tracking-wider">Deadline</label>
                        <input type="date" className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-1 focus:ring-blue-900 focus:border-blue-900 outline-none transition" value={formData.deadline} onChange={(e) => setFormData({...formData, deadline: e.target.value})} />
                      </div>
                    </div>
                    <div className="flex gap-3 pt-4 border-t border-gray-100">
                      <button type="button" onClick={closeModal} className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium">Cancel</button>
                      <button type="submit" className="flex-1 px-4 py-2.5 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition font-medium shadow-sm">{editingTask ? 'Update' : 'Allocate'} Task</button>
                    </div>
                  </form>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </Dialog>
      </Transition>
    </div>
  );
}