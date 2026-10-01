import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from './api';
import toast from 'react-hot-toast';
import { ArrowLeft, IndianRupee, Wallet, Receipt, FolderKanban, FileText, Calendar, Mail, Phone, Clock } from 'lucide-react';

export default function ClientDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('projects');

  useEffect(() => { fetchClientDetails(); }, [id]);

  const fetchClientDetails = async () => {
    try {
      const res = await api.get(`/clients/${id}/details`);
      setData(res.data);
    } catch (error) { toast.error("Failed to load client details"); } 
    finally { setLoading(false); }
  };

  if (loading) return <div className="p-8"><div className="animate-pulse space-y-6"><div className="h-40 bg-gray-100 rounded-2xl"></div><div className="h-96 bg-gray-100 rounded-2xl"></div></div></div>;
  if (!data) return <div className="p-8 text-center text-red-500">Client not found.</div>;

  const { client, projects, quotes, invoices, total_invoiced, total_paid, balance_due } = data;

  const getStatusColor = (status) => {
    const colors = {
      'Completed': 'border-blue-900 text-blue-900 bg-blue-50',
      'In Progress': 'border-slate-400 text-slate-700 bg-white',
      'On Hold': 'border-gray-300 text-gray-500 bg-gray-50',
      'Pending': 'border-gray-200 text-gray-400 bg-white',
      'Paid': 'border-blue-900 text-blue-900 bg-blue-50',
      'Partial': 'border-slate-400 text-slate-700 bg-white',
      'Unpaid': 'border-gray-300 text-gray-500 bg-gray-50',
      'Accepted': 'border-blue-900 text-blue-900 bg-blue-50',
      'Sent': 'border-slate-400 text-slate-700 bg-white',
      'Draft': 'border-gray-200 text-gray-400 bg-white',
    };
    return colors[status] || colors['Pending'];
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  return (
    <div className="p-8 max-w-7xl mx-auto bg-gray-50 min-h-screen space-y-6">
      {/* Back Button */}
      <Link to="/clients" className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-blue-900 transition-colors group">
        <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" /> Back to Contacts
      </Link>

      {/* 1. Premium Profile Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <div className="flex flex-col md:flex-row gap-8 items-start">
          {/* Avatar */}
          <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-blue-900 to-slate-800 flex items-center justify-center text-white text-4xl font-bold shadow-md flex-shrink-0">
            {client.name.charAt(0).toUpperCase()}
          </div>
          
          {/* Info */}
          <div className="flex-1">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-slate-900">{client.name}</h1>
                {client.company && (
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-3 py-1 bg-blue-50 text-blue-900 rounded-md text-sm font-semibold border border-blue-100 flex items-center gap-1.5">
                      {client.company}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Contact Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
              {client.email && (
                <a href={`mailto:${client.email}`} className="flex items-center gap-3 text-gray-600 hover:text-blue-900 transition group">
                  <div className="w-9 h-9 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-blue-50 transition border border-gray-100 group-hover:border-blue-100">
                    <Mail size={18} className="text-gray-500 group-hover:text-blue-900" />
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Email</p>
                    <p className="text-sm font-medium text-slate-700">{client.email}</p>
                  </div>
                </a>
              )}
              {client.phone && (
                <a href={`tel:${client.phone}`} className="flex items-center gap-3 text-gray-600 hover:text-blue-900 transition group">
                  <div className="w-9 h-9 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-blue-50 transition border border-gray-100 group-hover:border-blue-100">
                    <Phone size={18} className="text-gray-500 group-hover:text-blue-900" />
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Phone</p>
                    <p className="text-sm font-medium text-slate-700">{client.phone}</p>
                  </div>
                </a>
              )}
              {client.created_at && (
                <div className="flex items-center gap-3 text-gray-600">
                  <div className="w-9 h-9 rounded-lg bg-gray-50 flex items-center justify-center border border-gray-100">
                    <Clock size={18} className="text-gray-500" />
                  </div>
                  <div>
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Client Since</p>
                    <p className="text-sm font-medium text-slate-700">{formatDate(client.created_at)}</p>
                  </div>
                </div>
              )}
            </div>
            
            {client.notes && (
              <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-xl">
                <p className="text-sm text-slate-600 italic">"{client.notes}"</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 2. Financial Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Total Invoiced" value={`₹${total_invoiced.toLocaleString('en-IN')}`} icon={<Receipt size={20} />} color="bg-blue-900" />
        <StatCard title="Total Received" value={`₹${total_paid.toLocaleString('en-IN')}`} icon={<IndianRupee size={20} />} color="bg-slate-700" />
        <StatCard title="Outstanding Balance" value={`₹${balance_due.toLocaleString('en-IN')}`} icon={<Wallet size={20} />} color="bg-slate-600" isWarning={balance_due > 0} />
      </div>

      {/* 3. Tabs & Content */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Segmented Tab Navigation */}
        <div className="p-2 bg-gray-50 border-b border-gray-200 flex gap-2">
          {[
            { id: 'projects', label: 'Projects', count: projects.length, icon: FolderKanban },
            { id: 'quotes', label: 'Quotes', count: quotes.length, icon: FileText },
            { id: 'invoices', label: 'Invoices', count: invoices.length, icon: Receipt },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-white text-blue-900 shadow-sm border border-gray-200'
                    : 'text-gray-500 hover:text-slate-700 hover:bg-gray-100'
                }`}
              >
                <Icon size={16} />
                {tab.label}
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${isActive ? 'bg-blue-50 text-blue-900' : 'bg-gray-200 text-gray-600'}`}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Area */}
        <div className="p-6">
          {activeTab === 'projects' && (
            projects.length > 0 ? (
              <TableLayout headers={['Project Name', 'Total Cost', 'Status', 'Deadline']}>
                {projects.map((proj) => (
                  <tr key={proj.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-4 py-4"><div className="font-semibold text-slate-900">{proj.name}</div>{proj.notes && <div className="text-xs text-gray-500 mt-1 truncate max-w-xs">{proj.notes}</div>}</td>
                    <td className="px-4 py-4"><div className="flex items-center gap-1.5 font-semibold text-slate-900"><IndianRupee size={14} className="text-gray-400" />{proj.total_cost.toLocaleString('en-IN')}</div></td>
                    <td className="px-4 py-4"><span className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-lg border ${getStatusColor(proj.status)}`}>{proj.status}</span></td>
                    <td className="px-4 py-4 text-sm text-gray-600 flex items-center gap-2"><Calendar size={14} className="text-gray-400" />{formatDate(proj.deadline)}</td>
                  </tr>
                ))}
              </TableLayout>
            ) : <EmptyState icon={FolderKanban} title="No projects yet" description="This client doesn't have any active or past projects." />
          )}

          {activeTab === 'quotes' && (
            quotes.length > 0 ? (
              <TableLayout headers={['Quote Number', 'Total Amount', 'Status', 'Created Date']}>
                {quotes.map((quote) => (
                  <tr key={quote.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-4 py-4 font-semibold text-blue-900">{quote.quote_number}</td>
                    <td className="px-4 py-4"><div className="flex items-center gap-1.5 font-semibold text-slate-900"><IndianRupee size={14} className="text-gray-400" />{quote.total_amount.toLocaleString('en-IN')}</div></td>
                    <td className="px-4 py-4"><span className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-lg border ${getStatusColor(quote.status)}`}>{quote.status}</span></td>
                    <td className="px-4 py-4 text-sm text-gray-600">{formatDate(quote.created_at)}</td>
                  </tr>
                ))}
              </TableLayout>
            ) : <EmptyState icon={FileText} title="No quotes yet" description="You haven't sent any quotes to this client." />
          )}

          {activeTab === 'invoices' && (
            invoices.length > 0 ? (
              <TableLayout headers={['Invoice Number', 'Total', 'Paid', 'Balance', 'Status']}>
                {invoices.map((inv) => {
                  const balance = inv.total_amount - inv.amount_paid;
                  return (
                    <tr key={inv.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-4 font-semibold text-blue-900">{inv.invoice_number}</td>
                      <td className="px-4 py-4 font-semibold text-slate-900">₹{inv.total_amount.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-4 font-semibold text-slate-700">₹{inv.amount_paid.toLocaleString('en-IN')}</td>
                      <td className={`px-4 py-4 font-bold ${balance > 0 ? 'text-slate-900' : 'text-gray-400'}`}>₹{balance.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-4"><span className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-lg border ${getStatusColor(inv.status)}`}>{inv.status}</span></td>
                    </tr>
                  );
                })}
              </TableLayout>
            ) : <EmptyState icon={Receipt} title="No invoices yet" description="No invoices have been generated for this client." />
          )}
        </div>
      </div>
    </div>
  );
}

// Reusable Components for Clean Code
function StatCard({ title, value, icon, color, isWarning = false }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between hover:shadow-md transition-shadow">
      <div>
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{title}</p>
        <p className={`text-2xl font-bold mt-1 ${isWarning ? 'text-slate-900' : 'text-slate-900'}`}>{value}</p>
      </div>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color} bg-opacity-10`}>
        <div className={`${color.replace('bg-', 'text-')}`}>{icon}</div>
      </div>
    </div>
  );
}

function TableLayout({ headers, children }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200">
            {headers.map((h, i) => (
              <th key={i} className="px-4 py-3 text-left text-[11px] font-bold text-gray-400 uppercase tracking-wider">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">{children}</tbody>
      </table>
    </div>
  );
}

function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center mb-4">
        <Icon size={32} className="text-gray-300" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm">{description}</p>
    </div>
  );
}