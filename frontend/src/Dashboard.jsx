import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, Users, Briefcase, FileText, 
  ArrowUpRight, ArrowDownRight, Calendar, Clock 
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock data for the chart (replace with real API data later)
const chartData = [
  { name: 'Jan', revenue: 40000 },
  { name: 'Feb', revenue: 55000 },
  { name: 'Mar', revenue: 45000 },
  { name: 'Apr', revenue: 70000 },
  { name: 'May', revenue: 65000 },
  { name: 'Jun', revenue: 90000 },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
};

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalRevenue: 1250000,
    activeProjects: 12,
    pendingQuotes: 5,
    totalClients: 48,
    revenueGrowth: 12.5
  });

  useEffect(() => {
    // Simulate API fetch delay for smooth loading experience
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
    
    // TODO: Fetch real data from backend
    // fetch('http://localhost:8000/api/dashboard/summary')...
  }, []);

  const formatCurrency = (val) => `₹${(val / 1000).toFixed(0)}k`;

  if (loading) {
    return (
      <div className="p-8 space-y-6 animate-pulse">
        <div className="h-8 w-64 bg-gray-200 rounded-lg"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-gray-200 rounded-2xl"></div>)}
        </div>
        <div className="h-80 bg-gray-200 rounded-2xl"></div>
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
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome back, here's what's happening with your business today.</p>
        </div>
        <button className="bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-violet-200 flex items-center gap-2">
          <TrendingUp size={18} />
          Generate Report
        </button>
      </motion.div>

      {/* KPI Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard 
          title="Total Revenue" 
          value={formatCurrency(stats.totalRevenue)} 
          icon={TrendingUp} 
          trend={stats.revenueGrowth} 
          color="violet" 
        />
        <KPICard 
          title="Active Projects" 
          value={stats.activeProjects} 
          icon={Briefcase} 
          trend={2} 
          color="blue" 
        />
        <KPICard 
          title="Pending Quotes" 
          value={stats.pendingQuotes} 
          icon={FileText} 
          trend={-1} 
          color="amber" 
        />
        <KPICard 
          title="Total Clients" 
          value={stats.totalClients} 
          icon={Users} 
          trend={8} 
          color="emerald" 
        />
      </motion.div>

      {/* Main Content Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Revenue Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-800">Revenue Overview</h3>
            <select className="text-sm border-gray-200 rounded-lg text-gray-600 bg-gray-50 px-3 py-1.5 outline-none">
              <option>Last 6 Months</option>
              <option>This Year</option>
            </select>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} tickFormatter={formatCurrency} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                  formatter={(value) => [`₹${value.toLocaleString()}`, 'Revenue']}
                />
                <Area type="monotone" dataKey="revenue" stroke="#7c3aed" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Upcoming Deadlines / Activity */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Upcoming Deadlines</h3>
          <div className="space-y-4">
            <DeadlineItem project="E-commerce Website" client="TechCorp" days="3 days" color="bg-red-100 text-red-700" />
            <DeadlineItem project="Brand Identity" client="Nouvo Design" days="5 days" color="bg-amber-100 text-amber-700" />
            <DeadlineItem project="SEO Audit" client="Growth Labs" days="12 days" color="bg-blue-100 text-blue-700" />
            <DeadlineItem project="Mobile App UI" client="StartUp Inc" days="18 days" color="bg-emerald-100 text-emerald-700" />
          </div>
          <button className="w-full mt-6 text-sm text-violet-600 font-medium hover:text-violet-700 transition-colors">
            View all projects →
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// --- Reusable UI Components ---

function KPICard({ title, value, icon: Icon, trend, color }) {
  const isPositive = trend > 0;
  const colorClasses = {
    violet: "bg-violet-50 text-violet-600",
    blue: "bg-blue-50 text-blue-600",
    amber: "bg-amber-50 text-amber-600",
    emerald: "bg-emerald-50 text-emerald-600",
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:-translate-y-1 transition-all duration-300 cursor-default">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <h3 className="text-2xl font-bold text-gray-900 mt-2">{value}</h3>
        </div>
        <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
          <Icon size={22} />
        </div>
      </div>
      <div className="flex items-center gap-1 mt-4">
        {isPositive ? <ArrowUpRight size={16} className="text-emerald-500" /> : <ArrowDownRight size={16} className="text-red-500" />}
        <span className={`text-sm font-medium ${isPositive ? 'text-emerald-600' : 'text-red-600'}`}>
          {Math.abs(trend)}%
        </span>
        <span className="text-sm text-gray-400">vs last month</span>
      </div>
    </div>
  );
}

function DeadlineItem({ project, client, days, color }) {
  return (
    <div className="flex items-center gap-4 p-3 rounded-xl hover:bg-gray-50 transition-colors group">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center group-hover:bg-white group-hover:shadow-sm transition-all">
        <Calendar size={18} className="text-gray-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-gray-900 truncate">{project}</p>
        <p className="text-xs text-gray-500 truncate">{client}</p>
      </div>
      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${color}`}>
        {days}
      </span>
    </div>
  );
}