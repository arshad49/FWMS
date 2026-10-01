import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export default function EditQuote() {
  const { quoteNumber } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/quotes/${quoteNumber}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setFormData(data.quote);
        } else {
          alert('Quote not found');
          navigate('/quotes');
        }
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [quoteNumber]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await fetch(`http://localhost:8000/api/quotes/${quoteNumber}/update`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        alert('✅ Quote updated!');
        navigate('/quotes');
      }
    } catch (err) {
      alert('❌ Error saving');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600"></div></div>;
  if (!formData) return null;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/quotes')} className="text-gray-500 hover:text-gray-700 text-2xl">←</button>
        <h2 className="text-2xl font-bold text-violet-700">Edit Quotation {quoteNumber}</h2>
      </div>

      <form onSubmit={handleSave} className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To Name</label>
            <input type="text" name="to_name" value={formData.to_name || ''} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select name="status" value={formData.status || 'Draft'} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border bg-white">
              <option>Draft</option>
              <option>Sent</option>
              <option>Accepted</option>
              <option>Rejected</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Requirements</label>
          <textarea name="requirements" rows="4" value={formData.requirements || ''} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border"></textarea>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Terms</label>
            <textarea name="terms" rows="4" value={formData.terms || ''} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border"></textarea>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Payment Schedule</label>
            <textarea name="payment_schedule" rows="4" value={formData.payment_schedule || ''} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border"></textarea>
          </div>
        </div>

        <div className="flex gap-4">
          <button type="submit" disabled={saving} className="flex-1 bg-violet-600 text-white font-bold py-3 rounded-lg hover:bg-violet-700 disabled:opacity-50">
            {saving ? 'Saving...' : '💾 Save Changes'}
          </button>
          <button type="button" onClick={() => window.open(`http://localhost:8000/api/quotes/${quoteNumber}/pdf`, '_blank')} className="flex-1 bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700">
            📄 Generate PDF
          </button>
        </div>
      </form>
    </div>
  );
}