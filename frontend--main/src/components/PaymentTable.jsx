import React, { useEffect, useState } from 'react';

const PaymentTable = ({ studentId }) => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentTerm, setCurrentTerm] = useState(null);

  useEffect(() => {
    const fetchPayments = async () => {
      try {
        setLoading(true);
        const response = await fetch(`https://c70a35f6-0f51-4320-86f4-c560837fc183-00-247oocffqp4w9.worf.replit.dev:5000/payments/student/${studentId}`);
        const termResponse = await fetch(`https://c70a35f6-0f51-4320-86f4-c560837fc183-00-247oocffqp4w9.worf.replit.dev:5000/terms/active`);
        if (!response.ok || !termResponse.ok) throw new Error("Failed to fetch payments or term.");

        const paymentData = await response.json();
        const termData = await termResponse.json();
        setPayments(paymentData);
        setCurrentTerm(termData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (studentId) fetchPayments();
  }, [studentId]);

  if (loading) return <p>Loading payments...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;

  const groupedPayments = payments.reduce((acc, payment) => {
    const term = `Term ${payment.term_id}`;
    if (!acc[term]) acc[term] = [];
    acc[term].push(payment);
    return acc;
  }, {});

  return (
    <div>
      <h4>Payment History</h4>
      {Object.keys(groupedPayments).sort().map((term) => (
        <div key={term}>
          <h5>{term}</h5>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Amount</th>
                <th>Remaining Balance</th>
                <th>Payment Method</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {groupedPayments[term].map((payment) => (
                <tr key={payment.id}>
                  <td>{new Date(payment.date).toLocaleDateString()}</td>
                  <td>{payment.amount.toFixed(2)}</td>
                  <td>{payment.balance_after_payment.toFixed(2)}</td>
                  <td>{payment.method}</td>
                  <td>{payment.description || "N/A"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      <div>
        <h5>Arrears/Prepayments</h5>
        <p>{/* Fetch and display arrears or prepayments here */}</p>
      </div>
      <div>
        <h5>Current Term Fee</h5>
        <p>{currentTerm?.name}: {/* Calculate and display balance */}</p>
      </div>
    </div>
  );
};

export default PaymentTable;
