import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, Search, Plus, Mail, Phone, Building2, 
  Briefcase, TrendingUp, MoreVertical, Filter
} from 'lucide-react';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
};

// Generate gradient colors based on name
const getGradient = (name) => {
  const gradients = [
    'from-violet-500 to-purple-600',
    'from-blue-500 to-cyan-600',
    'from-emerald-500 to-teal-600',
    'from-amber-500 to-orange-600',
    'from-pink-500 to-rose-600',
    'from-indigo-500 to-blue-600',
  ];
  const index = name ? name.charCodeAt(0) % gradients.length : 0;
  return gradients[index];
};

// Get initials from name
const getInitials = (name) => {
  if (!name) return '?';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
};

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all'); // all, has-projects, no-projects

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/clients');
      const data = await response.json();
      // Handle both array and object responses
      const clientList = Array.isArray(data) ? data : (data.clients || []);
      setClients(clientList);
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setTimeout(() => setLoading(false), 500);
    }
  };

  // Filter clients based on search and filter
  const filteredClients = clients.filter(client => {
    const matchesSearch = 
      client.name?.toLowerCase().includes(search.toLowerCase()) ||
      client.company?.toLowerCase().includes(search.toLowerCase()) ||
      client.email?.toLowerCase().includes(search.toLowerCase());
    
    if (filter === 'has-projects') return matchesSearch && (client.project_count || 0) > 0;
    if (filter === 'no-projects') return matchesSearch && (client.project_count || 0) === 0;
    return matchesSearch;
  });

  const stats = {
    total: clients.length,
    withProjects: clients.filter(c => (c.project_count || 0) > 0).length,
    totalRevenue: clients.reduce((sum, c) => sum + (c.total_value || 0), 0)
  };

  if (loading) {
    return (
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 w-48 bg-gray-200 rounded-lg"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => <div key={i} className="h-28 bg-gray-200 rounded-2xl"></div>)}
        </div>
        <div className="h-14 bg-gray-200 rounded-xl"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => <div key={i} className="h-56 bg-gray-200 rounded-2xl"></div>)}
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      className="p-6 md:p-8 max-w-7xl mx-auto space-y-8"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clients</h1>
          <p className="text-gray-500 mt-1">Manage and track all your client relationships</p>
        </div>
        <Link 
          to="/clients/new"
          className="bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-violet-200 flex items-center gap-2 w-fit"
        >
          <Plus size={18} />
          Add New Client
        </Link>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          icon={Users} 
          label="Total Clients" 
          value={stats.total} 
          color="violet" 
        />
        <StatCard 
          icon={Briefcase} 
          label="Active Clients" 
          value={stats.withProjects} 
          color="blue" 
        />
        <StatCard 
          icon={TrendingUp} 
          label="Total Revenue" 
          value={`₹${(stats.totalRevenue / 1000).toFixed(0)}k`} 
          color="emerald" 
        />
      </motion.div>

      {/* Search & Filter Bar */}
      <motion.div variants={itemVariants} className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, company, or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
            />
          </div>
          
          {/* Filter Buttons */}
          <div className="flex gap-2">
            <FilterButton active={filter === 'all'} onClick={() => setFilter('all')}>
              All ({clients.length})
            </FilterButton>
            <FilterButton active={filter === 'has-projects'} onClick={() => setFilter('has-projects')}>
              Active ({stats.withProjects})
            </FilterButton>
            <FilterButton active={filter === 'no-projects'} onClick={() => setFilter('no-projects')}>
              Inactive ({clients.length - stats.withProjects})
            </FilterButton>
          </div>
        </div>
      </motion.div>

      {/* Client Grid */}
      {filteredClients.length === 0 ? (
        <motion.div variants={itemVariants} className="bg-white rounded-2xl p-12 text-center border border-gray-100">
          <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Users size={28} className="text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {search ? 'No clients found' : 'No clients yet'}
          </h3>
          <p className="text-gray-500 text-sm">
            {search ? 'Try a different search term' : 'Add your first client to get started'}
          </p>
        </motion.div>
      ) : (
        <motion.div 
          variants={containerVariants}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          <AnimatePresence>
            {filteredClients.map(client => (
              <ClientCard key={client.id} client={client} />
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </motion.div>
  );
}

// --- Reusable Components ---

function StatCard({ icon: Icon, label, value, color }) {
  const colorClasses = {
    violet: "bg-violet-50 text-violet-600",
    blue: "bg-blue-50 text-blue-600",
    emerald: "bg-emerald-50 text-emerald-600",
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
          <Icon size={22} />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <h3 className="text-2xl font-bold text-gray-900 mt-0.5">{value}</h3>
        </div>
      </div>
    </div>
  );
}

function FilterButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${
        active 
          ? 'bg-violet-600 text-white shadow-md shadow-violet-200' 
          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
      }`}
    >
      {children}
    </button>
  );
}

function ClientCard({ client }) {
  const gradient = getGradient(client.name);
  const initials = getInitials(client.name);

  return (
    <motion.div
      variants={itemVariants}
      layout
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <Link to={`/clients/${client.id}`} className="block">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg hover:border-violet-200 transition-all group h-full">
          {/* Header with Avatar */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-bold text-lg shadow-md`}>
                {initials}
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-gray-900 truncate group-hover:text-violet-600 transition-colors">
                  {client.name}
                </h3>
                {client.company && (
                  <p className="text-sm text-gray-500 truncate flex items-center gap-1">
                    <Building2 size={12} />
                    {client.company}
                  </p>
                )}
              </div>
            </div>
            <button 
              onClick={(e) => e.preventDefault()}
              className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-all"
            >
              <MoreVertical size={16} />
            </button>
          </div>

          {/* Contact Info */}
          <div className="space-y-2 mb-4">
            {client.email && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Mail size={14} className="text-gray-400 flex-shrink-0" />
                <span className="truncate">{client.email}</span>
              </div>
            )}
            {client.phone && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Phone size={14} className="text-gray-400 flex-shrink-0" />
                <span>{client.phone}</span>
              </div>
            )}
          </div>

          {/* Stats Footer */}
          <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Briefcase size={14} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-700">
                {client.project_count || 0} projects
              </span>
            </div>
            {client.total_value > 0 && (
              <div className="text-sm font-semibold text-violet-600">
                ₹{(client.total_value / 1000).toFixed(0)}k
              </div>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  );
}