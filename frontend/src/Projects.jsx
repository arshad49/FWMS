import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  
  // Edit Modal State
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', status: '', total_cost: '', deadline: '', notes: '', requirements: [], description: '' });
  const [isSaving, setIsSaving] = useState(false);

  // Create Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', client_name: '', total_cost: 0, deadline: '', requirements: [], description: '' });
  const [isCreating, setIsCreating] = useState(false);

  // ✨ Assignee Modal State
    // ✨ Assignee Modal State (Expanded)
  const [showAssigneeModal, setShowAssigneeModal] = useState(false);
  const [modalProject, setModalProject] = useState(null);
  const [newAssigneeName, setNewAssigneeName] = useState(''); 
  const [newAssigneeTask, setNewAssigneeTask] = useState(''); 
  const [newAssigneeCost, setNewAssigneeCost] = useState(0); 
  const [isAddingAssignee, setIsAddingAssignee] = useState(false);
  useEffect(() => { fetchProjects(); }, []);

  const fetchProjects = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/projects/list');
      const data = await response.json();
      if (data.status === 'success') setProjects(data.projects);
    } catch (error) { console.error('Error fetching projects:', error); } 
    finally { setLoading(false); }
  };

  const parseRequirements = (reqString) => {
    if (!reqString) return [];
    if (Array.isArray(reqString)) return reqString;
    try {
      const parsed = JSON.parse(reqString);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch { return reqString ? [reqString] : []; }
  };

  const handleCreateProject = async () => {
    if (!createForm.name.trim()) return alert('Project name is required');
    setIsCreating(true);
    try {
      const params = new URLSearchParams({
        name: createForm.name, client_name: createForm.client_name, total_cost: createForm.total_cost,
        deadline: createForm.deadline, requirements: JSON.stringify(createForm.requirements), description: createForm.description
      });
      const response = await fetch(`http://localhost:8000/api/projects?${params}`, { method: 'POST' });
      const data = await response.json();
      if (data.status === 'success') {
        setShowCreateModal(false);
        setCreateForm({ name: '', client_name: '', total_cost: 0, deadline: '', requirements: [], description: '' });
        fetchProjects();
      } else { alert(`❌ ${data.message}`); }
    } catch (error) { alert('❌ Failed to create project'); } 
    finally { setIsCreating(false); }
  };

  const handleDeleteProject = async (project) => {
    if (!window.confirm(`Are you sure you want to delete "${project.name}"?`)) return;
    try {
      const response = await fetch(`http://localhost:8000/api/projects/${project.id}`, { method: 'DELETE' });
      const data = await response.json();
      if (data.status === 'success') setProjects(projects.filter(p => p.id !== project.id));
      else { alert(`❌ ${data.message}`); }
    } catch (error) { alert('❌ Failed to delete project'); }
  };

  const openEditModal = (project) => {
    setSelectedProject(project);
    setEditForm({ 
      name: project.name || '', status: project.status || 'Pending', total_cost: project.total_cost || 0, 
      deadline: project.deadline || '', notes: project.notes || '', 
      requirements: parseRequirements(project.requirements), description: project.description || '' 
    });
    setShowEditModal(true);
  };

  const handleSaveProject = async () => {
    if (!selectedProject) return;
    setIsSaving(true);
    try {
      const params = new URLSearchParams({ 
        name: editForm.name, status: editForm.status, total_cost: editForm.total_cost, 
        deadline: editForm.deadline, notes: editForm.notes,
        requirements: JSON.stringify(editForm.requirements), description: editForm.description
      });
      const response = await fetch(`http://localhost:8000/api/projects/${selectedProject.id}?${params}`, { method: 'PUT' });
      const data = await response.json();
      if (data.status === 'success') {
        setProjects(projects.map(p => p.id === selectedProject.id ? { ...p, ...editForm, total_cost: parseFloat(editForm.total_cost) } : p));
        setShowEditModal(false);
      } else { alert(`❌ ${data.message}`); }
    } catch (error) { alert('❌ Failed to update project'); } 
    finally { setIsSaving(false); }
  };

  const handleStatusChange = async (projectId, newStatus) => {
    try {
      await fetch(`http://localhost:8000/api/projects/${projectId}/status?status=${newStatus}`, { method: 'PUT' });
      setProjects(projects.map(p => p.id === projectId ? { ...p, status: newStatus } : p));
    } catch (error) { console.error('Error updating status:', error); }
  };

    const openAssigneeModal = (project) => {
    setModalProject(project);
    // Reset inputs when opening
    setNewAssigneeName('');
    setNewAssigneeTask('');
    setNewAssigneeCost(0);
    setShowAssigneeModal(true);
  };

  //  Add Person to Project with Task & Amount
  const handleAddAssignee = async (e) => {
    if (e) e.preventDefault();
    if (!newAssigneeName.trim() || !modalProject) return;
    
    setIsAddingAssignee(true);
    try {
      const params = new URLSearchParams({
        name: newAssigneeName.trim(),
        task_title: newAssigneeTask.trim(),
        task_cost: newAssigneeCost
      });
      
      const res = await fetch(`http://localhost:8000/api/projects/${modalProject.id}/assignees?${params}`, { method: 'POST' });
      const data = await res.json();
      
      if (data.status === 'success') {
        const updatedAssignees = [...(modalProject.assignees || []), newAssigneeName.trim()];
        const updatedProject = { ...modalProject, assignees: updatedAssignees };
        
        setModalProject(updatedProject);
        setProjects(projects.map(p => p.id === updatedProject.id ? updatedProject : p));
        
        // Clear inputs
        setNewAssigneeName('');
        setNewAssigneeTask('');
        setNewAssigneeCost(0);
      } else { alert(`❌ ${data.message}`); }
    } catch (error) { alert('❌ Failed to add assignee'); } 
    finally { setIsAddingAssignee(false); }
  };

  // ✨ Remove Person from Project
  const handleRemoveAssignee = async (name) => {
    if (!window.confirm(`Remove ${name} from this project?`)) return;
    
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${modalProject.id}/assignees/${encodeURIComponent(name)}`, { method: 'DELETE' });
      const data = await res.json();
      
      if (data.status === 'success') {
        const updatedAssignees = modalProject.assignees.filter(a => a !== name);
        const updatedProject = { ...modalProject, assignees: updatedAssignees };
        
        setModalProject(updatedProject);
        setProjects(projects.map(p => p.id === updatedProject.id ? updatedProject : p));
      } else { alert(`❌ ${data.message}`); }
    } catch (error) { alert('❌ Failed to remove assignee'); }
  };

  const getDueStatus = (deadline) => {
    if (!deadline) return null;
    const today = new Date(); today.setHours(0,0,0,0);
    const due = new Date(deadline); due.setHours(0,0,0,0);
    const diffTime = due - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { text: `Overdue by ${Math.abs(diffDays)} days`, color: 'text-red-600 bg-red-50 border-red-100' };
    if (diffDays <= 3) return { text: `Due in ${diffDays} day${diffDays !== 1 ? 's' : ''}`, color: 'text-amber-600 bg-amber-50 border-amber-100' };
    return { text: `Due in ${diffDays} days`, color: 'text-gray-500' };
  };

  const filteredProjects = projects.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || (p.client_name && p.client_name.toLowerCase().includes(search.toLowerCase()));
    const matchesStatus = filterStatus === 'all' || p.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status) => {
    switch (status) {
      case 'Pending': return 'text-gray-600 bg-gray-100';
      case 'In Progress': return 'text-blue-600 bg-blue-50';
      case 'Completed': return 'text-green-600 bg-green-50';
      case 'On Hold': return 'text-amber-600 bg-amber-50';
      case 'Cancelled': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div></div>;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Top Header Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Projects</h1>
          <p className="text-sm text-gray-500">{projects.length} total records</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            <input type="text" placeholder="Search projects..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none bg-white text-sm" />
          </div>
          <button onClick={() => setShowCreateModal(true)} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors whitespace-nowrap">
            <span className="text-lg leading-none">+</span> Create New Project
          </button>
        </div>
      </div>

      {/* Filter & Action Bar */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3 w-full md:w-auto">
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="px-3 py-1.5 border border-gray-300 rounded-md text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white">
            <option value="all">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="On Hold">On Hold</option>
          </select>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex border border-gray-300 rounded-md overflow-hidden">
            <button onClick={() => setViewMode('grid')} className={`p-1.5 ${viewMode === 'grid' ? 'bg-gray-100 text-violet-600' : 'text-gray-500 hover:bg-gray-50'}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
            </button>
            <button onClick={() => setViewMode('list')} className={`p-1.5 ${viewMode === 'list' ? 'bg-gray-100 text-violet-600' : 'text-gray-500 hover:bg-gray-50'}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </button>
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      {filteredProjects.length === 0 ? (
        <div className="text-center py-20 text-gray-500">No projects found.</div>
      ) : (
        <div className={`grid gap-6 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
          {filteredProjects.map((project) => {
            const dueStatus = getDueStatus(project.deadline);
            return (
              <div key={project.id} className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 flex flex-col">
                <div className="p-5 border-b border-gray-100 flex justify-between items-start">
                  <h3 className="font-bold text-gray-800 text-lg leading-tight pr-4 line-clamp-2">{project.name}</h3>
                </div>
                <div className="p-5 flex-1">
                  <div className="grid grid-cols-2 gap-y-4 gap-x-4">
                    <div>
                      <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Client</p>
                      <p className="text-sm font-medium text-gray-800 truncate">{project.client_name || '—'}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Status</p>
                      <select value={project.status} onChange={(e) => handleStatusChange(project.id, e.target.value)} className={`text-xs font-semibold px-2 py-1 rounded-md border-0 focus:ring-2 focus:ring-violet-500 cursor-pointer ${getStatusColor(project.status)}`}>
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                        <option value="On Hold">On Hold</option>
                        <option value="Cancelled">Cancelled</option>
                      </select>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Budget</p>
                      <p className="text-sm font-medium text-gray-800">₹{(project.total_cost || 0).toLocaleString('en-IN')}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 uppercase font-semibold mb-1">Deadline</p>
                      {dueStatus ? (
                        <span className={`text-xs font-medium px-2 py-1 rounded-md border ${dueStatus.color}`}>{dueStatus.text}</span>
                      ) : <p className="text-sm font-medium text-gray-400">—</p>}
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
                    <div>
                      <p className="text-xs text-gray-400 uppercase font-semibold">Created</p>
                      <p className="text-xs text-gray-600 mt-0.5">{project.created_at ? new Date(project.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}</p>
                    </div>
                    {project.source === 'quote' && <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-violet-100 text-violet-800"> Quote</span>}
                  </div>
                </div>
                
                {/* Card Footer */}
                <div className="p-3 border-t border-gray-100 flex justify-center gap-3 bg-gray-50/50 rounded-b-lg">
                  <Link to={`/projects/${project.id}`} className="w-9 h-9 rounded-full border border-gray-200 bg-white text-gray-500 hover:text-violet-600 hover:border-violet-300 hover:bg-violet-50 flex items-center justify-center transition-all shadow-sm" title="View Project">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                  </Link>

                  {/* ✨ ALWAYS VISIBLE: Clickable People Icon */}
                  <button 
                    onClick={() => openAssigneeModal(project)}
                    className="w-9 h-9 rounded-full border border-gray-200 bg-white flex items-center justify-center shadow-sm transition-all hover:border-violet-300 hover:bg-violet-50 relative group"
                    title="Manage Team"
                  >
                    {project.assignees && project.assignees.length > 0 ? (
                      <>
                        {project.assignees.length === 1 ? (
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                        ) : (
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                        )}
                        {project.assignees.length > 1 && (
                          <span className="absolute -top-1 -right-1 bg-violet-600 text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full border border-white shadow-sm">
                            {project.assignees.length}
                          </span>
                        )}
                      </>
                    ) : (
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                    )}
                  </button>

                  <button onClick={() => openEditModal(project)} className="w-9 h-9 rounded-full border border-gray-200 bg-white text-gray-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 flex items-center justify-center transition-all shadow-sm" title="Edit Project">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                  </button>

                  <button onClick={() => handleDeleteProject(project)} className="w-9 h-9 rounded-full border border-gray-200 bg-white text-gray-500 hover:text-red-600 hover:border-red-300 hover:bg-red-50 flex items-center justify-center transition-all shadow-sm" title="Delete Project">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ✨ INTERACTIVE ASSIGNEE MODAL */}
      {showAssigneeModal && modalProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-bold text-gray-800">Manage Team</h3>
              <button onClick={() => setShowAssigneeModal(false)} className="text-gray-400 hover:text-gray-600 transition">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            
            <div className="p-6">
              <p className="text-sm text-gray-600 mb-4">
                Project: <span className="font-semibold text-gray-800">{modalProject.name}</span>
              </p>
              
              {/* List of Assigned People */}
              <div className="space-y-2 mb-6 max-h-60 overflow-y-auto">
                {modalProject.assignees && modalProject.assignees.length > 0 ? (
                  modalProject.assignees.map((person, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-violet-50 rounded-lg border border-violet-100">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-violet-200 text-violet-700 flex items-center justify-center font-bold text-sm">
                          {person.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-800">{person}</span>
                      </div>
                      <button onClick={() => handleRemoveAssignee(person)} className="text-red-400 hover:text-red-600 hover:bg-red-100 p-1.5 rounded-full transition-colors" title="Remove">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-gray-500">
                    <p className="text-sm">No team members assigned yet.</p>
                  </div>
                )}
              </div>
              
              {/* Add New Person Input */}
                            {/* Add New Person Form */}
              <form onSubmit={handleAddAssignee} className="space-y-3 pt-2 border-t border-gray-100">
                <p className="text-xs font-semibold text-gray-500 uppercase">Add New Team Member</p>
                
                {/* Name Input */}
                <input 
                  type="text" 
                  value={newAssigneeName} 
                  onChange={(e) => setNewAssigneeName(e.target.value)}
                  placeholder="Person Name (e.g. John)" 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm"
                  required
                />
                
                {/* Task & Cost Row */}
                <div className="grid grid-cols-2 gap-2">
                  <input 
                    type="text" 
                    value={newAssigneeTask} 
                    onChange={(e) => setNewAssigneeTask(e.target.value)}
                    placeholder="Task / Requirement" 
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm"
                  />
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">₹</span>
                    <input 
                      type="number" 
                      value={newAssigneeCost} 
                      onChange={(e) => setNewAssigneeCost(e.target.value)}
                      placeholder="Amount" 
                      className="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm"
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <button 
                  type="submit" 
                  disabled={isAddingAssignee || !newAssigneeName.trim()}
                  className="w-full bg-violet-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-violet-700 transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isAddingAssignee ? (
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                      Add to Project
                    </>
                  )}
                </button>
              </form>

              <div className="pt-4 mt-4 border-t border-gray-100">
                <Link 
                  to={`/projects/${modalProject.id}`} 
                  onClick={() => setShowAssigneeModal(false)}
                  className="w-full block text-center text-violet-600 hover:text-violet-800 py-2 text-sm font-medium transition"
                >
                  View Full Project Details & Tasks →
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CREATE PROJECT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
              <h3 className="text-lg font-bold text-gray-800">Create New Project</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Project Name <span className="text-red-500">*</span></label>
                  <input type="text" value={createForm.name} onChange={(e) => setCreateForm({...createForm, name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" placeholder="e.g. Website Redesign" />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Client Name (Optional)</label>
                  <input type="text" value={createForm.client_name} onChange={(e) => setCreateForm({...createForm, client_name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" placeholder="e.g. KD Companies" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Budget (₹)</label>
                  <input type="number" value={createForm.total_cost} onChange={(e) => setCreateForm({...createForm, total_cost: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Deadline</label>
                  <input type="date" value={createForm.deadline} onChange={(e) => setCreateForm({...createForm, deadline: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Requirements (Point by Point)</label>
                <div className="space-y-2">
                  {createForm.requirements.map((req, index) => (
                    <div key={index} className="flex gap-2">
                      <span className="flex items-center text-gray-400 font-bold text-sm w-6">{index + 1}.</span>
                      <input type="text" value={req} onChange={(e) => {
                        const newReqs = [...createForm.requirements];
                        newReqs[index] = e.target.value;
                        setCreateForm({...createForm, requirements: newReqs});
                      }} className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" placeholder={`Requirement ${index + 1}`} />
                      <button onClick={() => setCreateForm({...createForm, requirements: createForm.requirements.filter((_, i) => i !== index)})} className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Remove">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                      </button>
                    </div>
                  ))}
                  <button onClick={() => setCreateForm({...createForm, requirements: [...createForm.requirements, '']})} className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm font-medium text-gray-500 hover:border-violet-400 hover:text-violet-600 transition-colors flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                    Add Requirement
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Description</label>
                <textarea value={createForm.description} onChange={(e) => setCreateForm({...createForm, description: e.target.value})} rows="2" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm resize-none" placeholder="Brief project description..."></textarea>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3 flex-shrink-0">
              <button onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
              <button onClick={handleCreateProject} disabled={isCreating} className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50">
                {isCreating ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* EDIT PROJECT MODAL */}
      {showEditModal && selectedProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
              <h3 className="text-lg font-bold text-gray-800">Edit Project</h3>
              <button onClick={() => setShowEditModal(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Project Name</label>
                <input type="text" value={editForm.name} onChange={(e) => setEditForm({...editForm, name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Status</label>
                  <select value={editForm.status} onChange={(e) => setEditForm({...editForm, status: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm bg-white">
                    <option value="Pending">Pending</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Completed">Completed</option>
                    <option value="On Hold">On Hold</option>
                    <option value="Cancelled">Cancelled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Budget (₹)</label>
                  <input type="number" value={editForm.total_cost} onChange={(e) => setEditForm({...editForm, total_cost: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Deadline</label>
                <input type="date" value={editForm.deadline} onChange={(e) => setEditForm({...editForm, deadline: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-2">Requirements (Point by Point)</label>
                <div className="space-y-2">
                  {editForm.requirements.map((req, index) => (
                    <div key={index} className="flex gap-2">
                      <span className="flex items-center text-gray-400 font-bold text-sm w-6">{index + 1}.</span>
                      <input type="text" value={req} onChange={(e) => {
                        const newReqs = [...editForm.requirements];
                        newReqs[index] = e.target.value;
                        setEditForm({...editForm, requirements: newReqs});
                      }} className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm" placeholder={`Requirement ${index + 1}`} />
                      <button onClick={() => setEditForm({...editForm, requirements: editForm.requirements.filter((_, i) => i !== index)})} className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Remove">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                      </button>
                    </div>
                  ))}
                  <button onClick={() => setEditForm({...editForm, requirements: [...editForm.requirements, '']})} className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm font-medium text-gray-500 hover:border-violet-400 hover:text-violet-600 transition-colors flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                    Add Requirement
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Description</label>
                <textarea value={editForm.description} onChange={(e) => setEditForm({...editForm, description: e.target.value})} rows="2" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm resize-none" placeholder="Brief project description..."></textarea>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1">Internal Notes</label>
                <textarea value={editForm.notes} onChange={(e) => setEditForm({...editForm, notes: e.target.value})} rows="2" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 outline-none text-sm resize-none" placeholder="Private notes..."></textarea>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-end gap-3 flex-shrink-0">
              <button onClick={() => setShowEditModal(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
              <button onClick={handleSaveProject} disabled={isSaving} className="px-4 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50">
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}