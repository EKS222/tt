import React, { useState, useEffect } from 'react';

const PaymentForm = ({ studentId, onPaymentSuccess }) => {
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('cash');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [termId, setTermId] = useState('');
  const [description, setDescription] = useState('');
  const [terms, setTerms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchTerms = async () => {
      try {
        const response = await fetch(
          'https://c70a35f6-0f51-4320-86f4-c560837fc183-00-247oocffqp4w9.worf.replit.dev:5000/terms'
        );
        if (!response.ok) throw new Error('Failed to fetch terms.');

        const data = await response.json();
        console.log('Fetched terms:', data); // Debugging: Check fetched terms
        setTerms(data);

        // Set the default term to the active term or the first term in the list
        const activeTerm = data.find((term) => term.is_active);
        if (activeTerm) {
          setTermId(activeTerm.id);
        } else if (data.length > 0) {
          setTermId(data[0].id);
        }
      } catch (err) {
        console.error('Error fetching terms:', err);
        setError(err.message || 'Failed to load terms.');
      }
    };

    fetchTerms();
  }, []);

  const handlePayment = async () => {
    setError('');
    setSuccess('');

    // Validate input
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
      setError('Please enter a valid payment amount.');
      return;
    }

    if (!termId) {
      setError('Please select a valid term.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(
        'https://c70a35f6-0f51-4320-86f4-c560837fc183-00-247oocffqp4w9.worf.replit.dev:5000/payments',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: studentId,
            amount: parseFloat(amount),
            method,
            description,
            date,
            term_id: termId,
          }),
        }
      );

      // Check if response is successful
      if (!response.ok) {
        const text = await response.text(); // Get response text first
        const errorData = text ? JSON.parse(text) : { error: 'Failed to process payment.' }; // Try to parse as JSON
        throw new Error(errorData.error || 'Failed to process payment.');
      }

      // Payment successful
      setSuccess('Payment successfully added!');
      onPaymentSuccess();
      setAmount('');
      setDescription('');
    } catch (err) {
      console.error('Error adding payment:', err);
      setError(err.message || 'Failed to add payment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h4>Make Payment</h4>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}
      <div>
        <label htmlFor="amount">Amount:</label>
        <input
          id="amount"
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Enter amount"
        />
      </div>
      <div>
        <label htmlFor="method">Method:</label>
        <select
          id="method"
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          <option value="cash">Cash</option>
          <option value="mpesa">In-Kind</option>
          <option value="paybill">Paybill</option>
        </select>
      </div>
      <div>
        <label htmlFor="date">Date:</label>
        <input
          id="date"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="description">Description:</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description"
        />
      </div>
      <div>
        <label htmlFor="term">Term:</label>
        <select
          id="term"
          value={termId}
          onChange={(e) => setTermId(e.target.value)}
        >
          <option value="">Select Term</option>
          {terms.map((term) => (
            <option key={term.id} value={term.id}>
              {term.name} {term.is_active ? '(Active)' : ''}
            </option>
          ))}
        </select>
      </div>
      <button onClick={handlePayment} disabled={loading}>
        {loading ? 'Processing...' : 'Add Payment'}
      </button>
    </div>
  );
};

export default PaymentForm;





