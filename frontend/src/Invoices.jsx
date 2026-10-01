import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [generatingPDF, setGeneratingPDF] = useState(null);
  
  // Modal States
  const [showPaidModal, setShowPaidModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Payment Form State
  const [paymentForm, setPaymentForm] = useState({
    amount: 0,
    payment_method: 'Bank Transfer',
    payment_date: new Date().toISOString().split('T')[0] // Default to today
  });

  // Status Update State
  const [updatingStatus, setUpdatingStatus] = useState(null);
  const [statusUpdateSuccess, setStatusUpdateSuccess] = useState(null);

  useEffect(() => {
    fetchInvoices();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/invoices/list');
      const data = await response.json();
      if (data.status === 'success') {
        setInvoices(data.invoices);
      }
    } catch (error) {
      console.error('Error fetching invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async (invoiceNumber) => {
    setGeneratingPDF(invoiceNumber);
    try {
      window.open(`http://localhost:8000/api/invoices/${invoiceNumber}/pdf`, '_blank');
    } catch (error) {
      alert('❌ Failed to generate PDF');
    } finally {
      setGeneratingPDF(null);
    }
  };

  const handleStatusChange = async (invoiceNumber, newStatus) => {
    if (newStatus === 'Paid') {
      const invoice = invoices.find(i => i.invoice_number === invoiceNumber);
      setSelectedInvoice(invoice);
      setPaymentForm({
        amount: invoice.total_amount,
        payment_method: 'Bank Transfer',
        payment_date: new Date().toISOString().split('T')[0]
      });
      setShowPaidModal(true);
      return;
    }
    
    setUpdatingStatus(invoiceNumber);
    setStatusUpdateSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/invoices/${invoiceNumber}/status?status=${newStatus}`, { method: 'PUT' });
      const data = await response.json();
      if (data.status === 'success') {
        setInvoices(invoices.map(i => i.invoice_number === invoiceNumber ? { ...i, status: newStatus } : i));
        setStatusUpdateSuccess(invoiceNumber);
        setTimeout(() => setStatusUpdateSuccess(null), 2000);
      } else { alert(`❌ ${data.message}`); }
    } catch (error) {
      alert('❌ Failed to update status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    setIsProcessing(true);
    try {
      const params = new URLSearchParams({
        amount: paymentForm.amount,
        payment_method: paymentForm.payment_method,
        payment_date: paymentForm.payment_date
      });
      
      const response = await fetch(`http://localhost:8000/api/invoices/${selectedInvoice.invoice_number}/record-payment?${params}`, {
        method: 'POST',
      });
      const data = await response.json();

      if (data.status === 'success') {
        setShowPaidModal(false);
        setSelectedInvoice(null);
        fetchInvoices(); // Refresh to show updated paid amount and status
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('❌ Failed to record payment');
    } finally {
      setIsProcessing(false);
    }
  };

  const filteredInvoices = invoices.filter(i =>
    i.invoice_number.toLowerCase().includes(search.toLowerCase()) ||
    (i.client_name && i.client_name.toLowerCase().includes(search.toLowerCase())) ||
    (i.project_name && i.project_name.toLowerCase().includes(search.toLowerCase()))
  );

  const totalAmount = invoices.reduce((sum, i) => sum + (i.total_amount || 0), 0);
  const paidAmount = invoices.filter(i => i.status === 'Paid').reduce((sum, i) => sum + (i.total_amount || 0), 0);
  const pendingAmount = totalAmount - paidAmount;

  const getStatusColor = (status) => {
    switch (status) {
      case 'Draft': return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'Sent': return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'Unpaid': return 'bg-amber-100 text-amber-700 border-amber-300';
      case 'Paid': return 'bg-emerald-100 text-emerald-700 border-emerald-300';
      case 'Overdue': return 'bg-red-100 text-red-700 border-red-300';
      case 'Cancelled': return 'bg-gray-200 text-gray-500 border-gray-400';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Invoices</h1>
          <p className="text-sm text-gray-500 mt-1">{invoices.length} total invoices</p>
        </div>
        <Link to="/invoices/new" className="bg-violet-600 text-white px-4 py-2.5 rounded-lg hover:bg-violet-700 transition font-medium flex items-center gap-2 shadow-sm">
          <span className="text-lg">+</span> Create New Invoice
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-xs text-gray-500 uppercase font-semibold">Total Invoiced</p>
          <p className="text-2xl font-bold text-gray-800 mt-1">₹{totalAmount.toLocaleString('en-IN')}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-emerald-200 p-4">
          <p className="text-xs text-emerald-600 uppercase font-semibold">Paid</p>
          <p className="text-2xl font-bold text-emerald-700 mt-1">₹{paidAmount.toLocaleString('en-IN')}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-amber-200 p-4">
          <p className="text-xs text-amber-600 uppercase font-semibold">Pending</p>
          <p className="text-2xl font-bold text-amber-700 mt-1">₹{pendingAmount.toLocaleString('en-IN')}</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by invoice number, client, or project..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full md:w-96 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none shadow-sm"
        />
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          {/* ✨ FIXED: Clean Table Header with Balance Column */}
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Invoice #</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Client</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Project</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Amount</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Balance</th> {/* ✨ NEW */}
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Date</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Due Date</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredInvoices.length === 0 ? (
              <tr>
                {/* ✨ FIXED: Changed colSpan from 8 to 9 */}
                <td colSpan="9" className="text-center py-12 text-gray-400">
                  <p className="text-lg">No invoices found</p>
                  <p className="text-sm mt-1">Create your first invoice to get started</p>
                </td>
              </tr>
            ) : (
              filteredInvoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50 transition">
                  <td className="px-6 py-4 font-semibold text-violet-600">{invoice.invoice_number}</td>
                  <td className="px-6 py-4 text-gray-800">{invoice.client_name || '—'}</td>
                  <td className="px-6 py-4">
                    {invoice.project_name ? (
                      <Link to={`/projects/${invoice.project_id}`} className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1">
                        <span className="text-xs">📁</span> {invoice.project_name}
                      </Link>
                    ) : <span className="text-gray-400 text-sm italic">No project</span>}
                  </td>
                  <td className="px-6 py-4 font-semibold text-gray-800">₹{parseFloat(invoice.total_amount || 0).toLocaleString('en-IN')}</td>
                  
                  {/* ✨ NEW: Balance Column Cell */}
                  <td className="px-6 py-4 font-semibold">
                    {parseFloat(invoice.balance || 0) <= 0 ? (
                      <span className="text-emerald-600 flex items-center gap-1 text-sm">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                        Paid
                      </span>
                    ) : (
                      <span className="text-amber-600 text-sm">
                        ₹{parseFloat(invoice.balance || 0).toLocaleString('en-IN')}
                      </span>
                    )}
                  </td>

                  <td className="px-6 py-4 text-gray-500 text-sm">{invoice.created_at ? new Date(invoice.created_at).toLocaleDateString() : '—'}</td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{invoice.due_date || '—'}</td>
                  
                  <td className="px-6 py-4">
                    <div className="relative flex items-center gap-2">
                      <select
                        value={invoice.status}
                        onChange={(e) => handleStatusChange(invoice.invoice_number, e.target.value)}
                        disabled={updatingStatus === invoice.invoice_number}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border cursor-pointer focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all ${getStatusColor(invoice.status)}`}
                      >
                        <option value="Draft">📝 Draft</option>
                        <option value="Sent">📤 Sent</option>
                        <option value="Unpaid">⏳ Unpaid</option>
                        <option value="Paid">💰 Paid</option>
                        <option value="Overdue">⚠️ Overdue</option>
                        <option value="Cancelled">🚫 Cancelled</option>
                      </select>
                      
                      {updatingStatus === invoice.invoice_number && (
                        <svg className="animate-spin h-4 w-4 text-violet-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                      
                      {statusUpdateSuccess === invoice.invoice_number && (
                        <svg className="h-4 w-4 text-emerald-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                      )}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="flex gap-3 flex-wrap items-center">
                      <Link to={`/invoices/edit/${invoice.invoice_number}`} className="text-blue-600 hover:text-blue-800 text-sm font-medium">Edit</Link>
                      
                      <button onClick={() => handleGeneratePDF(invoice.invoice_number)} disabled={generatingPDF === invoice.invoice_number} className="text-violet-600 hover:text-violet-800 text-sm font-medium disabled:opacity-50">
                        {generatingPDF === invoice.invoice_number ? '⏳' : '📄 PDF'}
                      </button>
                      
                      {(invoice.status === 'Draft' || invoice.status === 'Sent' || invoice.status === 'Unpaid' || invoice.status === 'Overdue') && (
                        <button
                          onClick={() => {
                            setSelectedInvoice(invoice);
                            setPaymentForm({
                              amount: invoice.total_amount,
                              payment_method: 'Bank Transfer',
                              payment_date: new Date().toISOString().split('T')[0]
                            });
                            setShowPaidModal(true);
                          }}
                          className="text-emerald-600 hover:text-emerald-800 hover:bg-emerald-50 px-3 py-1 rounded-md text-sm font-medium transition-all flex items-center gap-1"
                        >
                          💰 Record Payment
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Record Payment Modal */}
      {showPaidModal && selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100">
            <div className="bg-emerald-50 px-6 py-4 border-b border-emerald-100 flex items-center gap-3">
              <div className="bg-emerald-100 p-2 rounded-full">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Record Payment</h3>
                <p className="text-sm text-gray-600">For Invoice {selectedInvoice.invoice_number}</p>
              </div>
            </div>

            <form onSubmit={handleRecordPayment} className="p-6 space-y-4">
              <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm mb-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Client:</span>
                  <span className="font-semibold text-gray-900">{selectedInvoice.client_name || '—'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total Amount:</span>
                  <span className="font-semibold text-emerald-600">₹{parseFloat(selectedInvoice.total_amount || 0).toLocaleString('en-IN')}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase mb-1.5">Payment Amount (₹)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({...paymentForm, amount: e.target.value})}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none text-sm font-semibold"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1.5">Payment Method</label>
                  <select
                    value={paymentForm.payment_method}
                    onChange={(e) => setPaymentForm({...paymentForm, payment_method: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm bg-white"
                  >
                    <option value="Bank Transfer">Bank Transfer</option>
                    <option value="UPI">UPI</option>
                    <option value="Cash">Cash</option>
                    <option value="Cheque">Cheque</option>
                    <option value="Credit Card">Credit Card</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase mb-1.5">Payment Date</label>
                  <input
                    type="date"
                    required
                    value={paymentForm.payment_date}
                    onChange={(e) => setPaymentForm({...paymentForm, payment_date: e.target.value})}
                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => { setShowPaidModal(false); setSelectedInvoice(null); }}
                  disabled={isProcessing}
                  className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isProcessing}
                  className="px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-sm"
                >
                  {isProcessing ? (
                    <>
                      <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Processing...
                    </>
                  ) : (
                    <>💰 Confirm Payment</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}