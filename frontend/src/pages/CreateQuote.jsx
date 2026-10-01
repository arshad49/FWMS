import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CreateQuote() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);
  const [formData, setFormData] = useState({
    client_name: '',
    quote_number: '',
    to_name: '',
    requirements: '',
    terms: '1. Project advance 50% on total work amount, and 50% final project submitting.\n2. Any additional features requested beyond the agreed scope will be quoted separately.\n3. Revisions: Up to 2 revisions included.\n4. Domain and Hosting are not included.\n5. Third-party premium plugins or licenses, if required, will be charged separately.',
    payment_schedule: 'Project advance 50% on total work amount, and 50% final project submitting',
    tax_rate: 0,
    discount: 0,
    valid_days: 30,
    notes: '',
    items: [{ description: '', note: '', quantity: 1, amount: 0 }],
    timeline: [{ process: '', note: '', delivery: '' }]
  });

  // Fetch clients for dropdown
  useEffect(() => {
    fetch('http://localhost:8000/api/clients')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setClients(data);
      })
      .catch(err => console.error('Error fetching clients:', err));
  }, []);

  // Auto-fill client details when selected
  const handleClientSelect = (clientName) => {
    setFormData(prev => ({ ...prev, client_name: clientName, to_name: clientName }));
    const selectedClient = clients.find(c => c.name === clientName);
    if (selectedClient && selectedClient.company) {
      setFormData(prev => ({ ...prev, to_name: selectedClient.company }));
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = field === 'quantity' || field === 'amount' ? parseFloat(value) || 0 : value;
    setFormData(prev => ({ ...prev, items: newItems }));
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { description: '', note: '', quantity: 1, amount: 0 }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length <= 1) return;
    setFormData(prev => ({ ...prev, items: prev.items.filter((_, i) => i !== index) }));
  };

  const handleTimelineChange = (index, field, value) => {
    const newTimeline = [...formData.timeline];
    newTimeline[index][field] = value;
    setFormData(prev => ({ ...prev, timeline: newTimeline }));
  };

  const addTimeline = () => {
    setFormData(prev => ({
      ...prev,
      timeline: [...prev.timeline, { process: '', note: '', delivery: '' }]
    }));
  };

  const removeTimeline = (index) => {
    if (formData.timeline.length <= 1) return;
    setFormData(prev => ({ ...prev, timeline: prev.timeline.filter((_, i) => i !== index) }));
  };

  // Calculate totals live
  const subtotal = formData.items.reduce((sum, item) => sum + (item.amount || 0), 0);
  const taxAmount = (subtotal * formData.tax_rate) / 100;
  const total = subtotal + taxAmount - formData.discount;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/quotes/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        alert('✅ Quotation created successfully!');
        window.open(`http://localhost:8000/api/quotes/${formData.quote_number}/pdf`, '_blank');
        navigate('/quotes');
      } else {
        alert('❌ Error: ' + (data.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('❌ Failed to connect to the server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/quotes')} className="text-gray-500 hover:text-gray-700 text-2xl">←</button>
        <h2 className="text-2xl font-bold text-violet-700">Create New Quotation</h2>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 space-y-8">

        {/* Section 1: Basic Info */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-100">📋 Quotation Info</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Quote Number *</label>
              <input type="text" name="quote_number" required value={formData.quote_number} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border focus:ring-2 focus:ring-violet-500 outline-none" placeholder="e.g., Q-1001" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Client *</label>
              <select value={formData.client_name} onChange={(e) => handleClientSelect(e.target.value)} required className="w-full rounded-lg border-gray-300 p-2.5 border focus:ring-2 focus:ring-violet-500 outline-none bg-white">
                <option value="">-- Choose a client --</option>
                {clients.map(c => (
                  <option key={c.id} value={c.name}>{c.name} {c.company ? `(${c.company})` : ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">To Name (Company) *</label>
              <input type="text" name="to_name" required value={formData.to_name} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border focus:ring-2 focus:ring-violet-500 outline-none" placeholder="Auto-filled from client" />
            </div>
          </div>
        </div>

        {/* Section 2: Requirements */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-100">📝 Client Requirements</h3>
          <textarea name="requirements" rows="4" value={formData.requirements} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border focus:ring-2 focus:ring-violet-500 outline-none" placeholder="Modern website&#10;5 pages&#10;WordPress CMS&#10;SEO Friendly&#10;Responsive development"></textarea>
        </div>

        {/* Section 3: Services */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-100">💰 Services & Pricing</h3>
          <div className="space-y-2">
            <div className="grid grid-cols-12 gap-2 text-xs font-semibold text-gray-500 uppercase px-1">
              <div className="col-span-5">Description</div>
              <div className="col-span-2">Note</div>
              <div className="col-span-1">Qty</div>
              <div className="col-span-2">Amount (₹)</div>
              <div className="col-span-2"></div>
            </div>
            {formData.items.map((item, index) => (
              <div key={index} className="grid grid-cols-12 gap-2 items-center">
                <input type="text" placeholder="e.g., Web UI Design" value={item.description} onChange={(e) => handleItemChange(index, 'description', e.target.value)} className="col-span-5 rounded-lg border-gray-300 p-2.5 border" required />
                <input type="text" placeholder="e.g., 6 pages" value={item.note} onChange={(e) => handleItemChange(index, 'note', e.target.value)} className="col-span-2 rounded-lg border-gray-300 p-2.5 border" />
                <input type="number" value={item.quantity} onChange={(e) => handleItemChange(index, 'quantity', e.target.value)} className="col-span-1 rounded-lg border-gray-300 p-2.5 border" />
                <input type="number" placeholder="15000" value={item.amount} onChange={(e) => handleItemChange(index, 'amount', e.target.value)} className="col-span-2 rounded-lg border-gray-300 p-2.5 border" required />
                <div className="col-span-2 flex justify-end">
                  {formData.items.length > 1 && (
                    <button type="button" onClick={() => removeItem(index)} className="text-red-400 hover:text-red-600 p-2">✕</button>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button type="button" onClick={addItem} className="mt-3 text-sm text-violet-600 hover:text-violet-800 font-medium border border-dashed border-violet-300 px-4 py-2 rounded-lg w-full hover:bg-violet-50 transition">+ Add Service</button>
        </div>

        {/* Section 4: Timeline */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-100">📅 Project Timeline</h3>
          <div className="space-y-2">
            {formData.timeline.map((tl, index) => (
              <div key={index} className="grid grid-cols-12 gap-2 items-center">
                <input type="text" placeholder="Process (e.g., UI Design)" value={tl.process} onChange={(e) => handleTimelineChange(index, 'process', e.target.value)} className="col-span-5 rounded-lg border-gray-300 p-2.5 border" />
                <input type="text" placeholder="Note (e.g., 5 pages)" value={tl.note} onChange={(e) => handleTimelineChange(index, 'note', e.target.value)} className="col-span-3 rounded-lg border-gray-300 p-2.5 border" />
                <input type="text" placeholder="Delivery (e.g., 18-20 Days)" value={tl.delivery} onChange={(e) => handleTimelineChange(index, 'delivery', e.target.value)} className="col-span-3 rounded-lg border-gray-300 p-2.5 border" />
                <div className="col-span-1 flex justify-end">
                  {formData.timeline.length > 1 && (
                    <button type="button" onClick={() => removeTimeline(index)} className="text-red-400 hover:text-red-600 p-2">✕</button>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button type="button" onClick={addTimeline} className="mt-3 text-sm text-violet-600 hover:text-violet-800 font-medium border border-dashed border-violet-300 px-4 py-2 rounded-lg w-full hover:bg-violet-50 transition">+ Add Timeline Phase</button>
        </div>

        {/* Section 5: Financials */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-100">🧮 Financial Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tax Rate (%)</label>
              <input type="number" name="tax_rate" step="0.01" value={formData.tax_rate} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Discount (₹)</label>
              <input type="number" name="discount" step="0.01" value={formData.discount} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Valid For (Days)</label>
              <input type="number" name="valid_days" value={formData.valid_days} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border" />
            </div>
          </div>
          {/* Live Total Preview */}
          <div className="bg-violet-50 rounded-lg p-4 border border-violet-200">
            <div className="flex justify-between text-sm text-gray-600 mb-1"><span>Subtotal</span><span>₹{subtotal.toLocaleString('en-IN')}</span></div>
            {formData.tax_rate > 0 && <div className="flex justify-between text-sm text-gray-600 mb-1"><span>Tax ({formData.tax_rate}%)</span><span>₹{taxAmount.toLocaleString('en-IN')}</span></div>}
            {formData.discount > 0 && <div className="flex justify-between text-sm text-gray-600 mb-1"><span>Discount</span><span>- ₹{formData.discount.toLocaleString('en-IN')}</span></div>}
            <div className="flex justify-between text-lg font-bold text-violet-700 pt-2 border-t border-violet-200 mt-2"><span>Total</span><span>₹{total.toLocaleString('en-IN')}</span></div>
          </div>
        </div>

        {/* Section 6: Terms & Payment */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4 pb-2 border-b border-gray-100">📜 Terms & Payment</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Additional Terms (one per line)</label>
              <textarea name="terms" rows="5" value={formData.terms} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border"></textarea>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Payment Schedule</label>
              <textarea name="payment_schedule" rows="5" value={formData.payment_schedule} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border"></textarea>
            </div>
          </div>
        </div>

        {/* Section 7: Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Additional Notes</label>
          <textarea name="notes" rows="2" value={formData.notes} onChange={handleChange} className="w-full rounded-lg border-gray-300 p-2.5 border" placeholder="Any special instructions..."></textarea>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-violet-600 text-white font-bold py-3.5 px-4 rounded-lg hover:bg-violet-700 transition duration-200 disabled:opacity-50 text-lg"
        >
          {loading ? '⏳ Creating Quotation & Generating PDF...' : '✅ Create Quotation & Generate PDF'}
        </button>
      </form>
    </div>
  );
}