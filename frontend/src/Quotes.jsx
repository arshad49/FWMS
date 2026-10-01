import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function Quotes() {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [generatingPDF, setGeneratingPDF] = useState(null);
  
  // Modal & Conversion States
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionSuccess, setConversionSuccess] = useState(null); // ✨ Success Modal State
  
  // Status Update State
  const [updatingStatus, setUpdatingStatus] = useState(null);
  const [statusUpdateSuccess, setStatusUpdateSuccess] = useState(null);

  useEffect(() => {
    fetchQuotes();
  }, []);

  const fetchQuotes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/quotes/list');
      const data = await response.json();
      if (data.status === 'success') {
        setQuotes(data.quotes);
      }
    } catch (error) {
      console.error('Error fetching quotes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePDF = async (quoteNumber) => {
    setGeneratingPDF(quoteNumber);
    try {
      window.open(`http://localhost:8000/api/quotes/${quoteNumber}/pdf`, '_blank');
    } catch (error) {
      alert('❌ Failed to generate PDF');
    } finally {
      setGeneratingPDF(null);
    }
  };

  const handleStatusChange = async (quoteNumber, newStatus) => {
    setUpdatingStatus(quoteNumber);
    setStatusUpdateSuccess(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/quotes/${quoteNumber}/status?status=${newStatus}`, {
        method: 'PUT',
      });
      const data = await response.json();

      if (data.status === 'success') {
        setQuotes(quotes.map(q => 
          q.quote_number === quoteNumber ? { ...q, status: newStatus } : q
        ));
        setStatusUpdateSuccess(quoteNumber);
        setTimeout(() => setStatusUpdateSuccess(null), 2000);
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      console.error('Error updating status:', error);
      alert('❌ Failed to update status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  const openConvertModal = (quote) => {
    setSelectedQuote(quote);
    setShowConvertModal(true);
  };

  // ✨ UPDATED: Replaced alert() with setConversionSuccess()
  const handleConfirmConvert = async () => {
    if (!selectedQuote) return;
    
    setIsConverting(true);
    try {
      const response = await fetch(`http://localhost:8000/api/quotes/${selectedQuote.quote_number}/convert-to-project`, {
        method: 'POST',
      });
      const data = await response.json();

      if (data.status === 'success') {
        setShowConvertModal(false);
        setSelectedQuote(null);
        setConversionSuccess(data); // ✨ Triggers the Success Modal
        fetchQuotes();
      } else {
        alert(`❌ ${data.message}`);
      }
    } catch (error) {
      console.error('Error converting quote:', error);
      alert('❌ Failed to convert. Please try again.');
    } finally {
      setIsConverting(false);
    }
  };

  const filteredQuotes = quotes.filter(q =>
    q.quote_number.toLowerCase().includes(search.toLowerCase()) ||
    q.client_name.toLowerCase().includes(search.toLowerCase()) ||
    q.to_name.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'Draft': return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'Sent': return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'Accepted': return 'bg-green-100 text-green-700 border-green-300';
      case 'Rejected': return 'bg-red-100 text-red-700 border-red-300';
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
          <h1 className="text-2xl font-bold text-gray-800">Quotations</h1>
          <p className="text-sm text-gray-500 mt-1">{quotes.length} total quotations</p>
        </div>
        <Link
          to="/quotes/new"
          className="bg-violet-600 text-white px-4 py-2.5 rounded-lg hover:bg-violet-700 transition font-medium flex items-center gap-2 shadow-sm"
        >
          <span className="text-lg">+</span> Create New Quote
        </Link>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by quote number, client name, or company..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full md:w-96 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none shadow-sm"
        />
      </div>

      {/* Quotes Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Quote #</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Client</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">To</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Amount</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Date</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Valid Until</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredQuotes.length === 0 ? (
              <tr>
                <td colSpan="8" className="text-center py-12 text-gray-400">
                  <p className="text-lg">No quotations found</p>
                  <p className="text-sm mt-1">Create your first quote to get started</p>
                </td>
              </tr>
            ) : (
              filteredQuotes.map((quote) => (
                <tr key={quote.id} className="hover:bg-gray-50 transition">
                  <td className="px-6 py-4 font-semibold text-violet-600">{quote.quote_number}</td>
                  <td className="px-6 py-4 text-gray-800">{quote.client_name}</td>
                  <td className="px-6 py-4 text-gray-600">{quote.to_name}</td>
                  <td className="px-6 py-4 font-semibold text-gray-800">₹{parseFloat(quote.total_amount || 0).toLocaleString('en-IN')}</td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{quote.quotation_date}</td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{quote.valid_until}</td>
                  
                  <td className="px-6 py-4">
                    <div className="relative flex items-center gap-2">
                      <select
                        value={quote.status}
                        onChange={(e) => handleStatusChange(quote.quote_number, e.target.value)}
                        disabled={updatingStatus === quote.quote_number || quote.status === 'Accepted'}
                        className={`px-3 py-1.5 rounded-full text-xs font-medium border cursor-pointer focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all ${getStatusColor(quote.status)} ${quote.status === 'Accepted' ? 'opacity-75 cursor-not-allowed' : ''}`}
                      >
                        <option value="Draft"> Draft</option>
                        <option value="Sent"> Sent</option>
                        <option value="Accepted">Accepted</option>
                        <option value="Rejected">Rejected</option>
                      </select>
                      
                      {updatingStatus === quote.quote_number && (
                        <svg className="animate-spin h-4 w-4 text-violet-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                      
                      {statusUpdateSuccess === quote.quote_number && (
                        <svg className="h-4 w-4 text-green-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                      )}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4">
                    <div className="flex gap-3 flex-wrap items-center">
                      <Link to={`/quotes/edit/${quote.quote_number}`} className="text-blue-600 hover:text-blue-800 text-sm font-medium">Edit</Link>
                      
                      <button onClick={() => handleGeneratePDF(quote.quote_number)} disabled={generatingPDF === quote.quote_number} className="text-violet-600 hover:text-violet-800 text-sm font-medium disabled:opacity-50">
                        {generatingPDF === quote.quote_number ? '⏳' : ' PDF'}
                      </button>
                      
                      {(quote.status === 'Draft' || quote.status === 'Sent') && (
                        <button
                          onClick={() => openConvertModal(quote)}
                          className="text-green-600 hover:text-green-800 hover:bg-green-50 px-3 py-1 rounded-md text-sm font-medium transition-all flex items-center gap-1"
                        >
                          ✅ Accept & Invoice
                        </button>
                      )}
                      
                      {quote.status === 'Accepted' && (
                        <span className="text-green-700 text-xs font-semibold flex items-center gap-1 bg-green-50 border border-green-200 px-3 py-1.5 rounded-full">
                          🚀 Project & Invoice Created
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Confirmation Modal */}
      {showConvertModal && selectedQuote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-opacity">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100">
            <div className="bg-violet-50 px-6 py-4 border-b border-violet-100 flex items-center gap-3">
              <div className="bg-violet-100 p-2 rounded-full">
                <svg className="w-6 h-6 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">Accept Quotation</h3>
                <p className="text-sm text-gray-600">Review the actions below before confirming</p>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div className="bg-gray-50 rounded-lg p-4 space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Quote:</span>
                  <span className="font-semibold text-gray-900">{selectedQuote.quote_number}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Client:</span>
                  <span className="font-semibold text-gray-900">{selectedQuote.client_name}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Amount:</span>
                  <span className="font-semibold text-violet-600">₹{parseFloat(selectedQuote.total_amount || 0).toLocaleString('en-IN')}</span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">This will automatically:</p>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Mark this quote as <strong>Accepted</strong></span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Create project <strong>"Project - {selectedQuote.quote_number}"</strong></span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">✓</span>
                    <span>Generate invoice <strong>"INV-{selectedQuote.quote_number.replace('Q-', '')}"</strong> (Unpaid)</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3 border-t border-gray-200">
              <button
                onClick={() => { setShowConvertModal(false); setSelectedQuote(null); }}
                disabled={isConverting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmConvert}
                disabled={isConverting}
                className="px-4 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed shadow-sm"
              >
                {isConverting ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Processing...
                  </>
                ) : (
                  <>Confirm & Create</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ✨ NEW: Professional Success Modal (Direct to Invoice) */}
      {conversionSuccess && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden transform transition-all scale-100">
            <div className="p-8 text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-900">Quote Accepted!</h3>
              <p className="text-sm text-gray-500 mt-2 px-4">
                Project <strong className="text-gray-800">{conversionSuccess.project?.name || 'Created'}</strong> and Invoice <strong className="text-violet-600">{conversionSuccess.invoice?.invoice_number || 'Generated'}</strong> have been created successfully.
              </p>
              
              <div className="mt-8 flex flex-col gap-3">
                <Link 
                  to="/invoices" 
                  onClick={() => setConversionSuccess(null)}
                  className="w-full bg-violet-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-violet-700 transition shadow-sm flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                  Go to Invoices & Send PDF
                </Link>
                <button 
                  onClick={() => setConversionSuccess(null)} 
                  className="w-full px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Stay on Quotes Page
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}