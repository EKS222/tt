import React, { useState } from "react";

import "../styles/studentDetails.css";
import PaymentTable from "./PaymentTable";


const StudentDetails = ({ student, showAddPayment, onAddPayment }) => {
  const [showPayments, setShowPayments] = useState(false);
  if (!student) return <p>Select a student to view details.</p>;

  return (
    <div className="student-details-container">
      <h2>Details for {student.name}</h2>
      <div className="student-info">
        <p>
          <strong>Grade:</strong> {student.grade}
        </p>
        <p>
          <strong>Admission Number:</strong> {student.admission_number}
        </p>
        <p>
          <strong>Balance:</strong> {student.balance}
        </p>
        <p>
          <strong>Arrears:</strong> {student.arrears}
        </p>
        <p>
          <strong>Term Fee:</strong> {student.term_fee}
        </p>
        <p>
          <strong>Uses Bus Service:</strong> {student.use_bus ? "Yes" : "No"}
        </p>
        <p>
          <strong>Bus Balance:</strong> {student.bus_balance}
        </p>
      </div>

      {showAddPayment && (
        <button className="add-payment-btn" onClick={onAddPayment}>
          Add Payment
        </button>
      )}
      <button
        className="view-payments-btn"
        onClick={() => setShowPayments(!showPayments)}
      >
        {showPayments ? "Hide Payments" : "View Payments"}
      </button>
      {showPayments && <PaymentTable studentId={student.id} />}
    </div>
  );
};

export default StudentDetails;
