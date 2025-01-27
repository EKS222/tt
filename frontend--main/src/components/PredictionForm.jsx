import React, { useState } from "react";
import axios from "axios";
import "./styles/prediction.css";

const PredictionForm = () => {
  const [dailyExpenses, setDailyExpenses] = useState("");
  const [inKindPayments, setInKindPayments] = useState("");
  const [prediction, setPrediction] = useState(null);

  const handlePredict = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post("/api/prediction", {
        daily_expenses: parseFloat(dailyExpenses),
        in_kind_payments: parseFloat(inKindPayments)
      });
      setPrediction(response.data);
    } catch (error) {
      console.error("Error predicting operational days:", error);
    }
  };

  return (
    <div className="prediction-container">
      <h2>Predict Operational Days</h2>
      <form onSubmit={handlePredict} className="prediction-form">
        <div>
          <label>Average Daily Expenses (Ksh):</label>
          <input
            type="number"
            value={dailyExpenses}
            onChange={(e) => setDailyExpenses(e.target.value)}
            required
          />
        </div>
        <div>
          <label>In-kind Payments Value (Ksh):</label>
          <input
            type="number"
            value={inKindPayments}
            onChange={(e) => setInKindPayments(e.target.value)}
          />
        </div>
        <button type="submit">Predict</button>
      </form>

      {prediction && (
        <div className="prediction-result">
          <h3>Prediction Results</h3>
          <p>Total Revenue: Ksh {prediction.total_revenue}</p>
          <p>Daily Expenses: Ksh {prediction.daily_expenses}</p>
          <p>Estimated Operational Days: {prediction.operational_days} days</p>
        </div>
      )}
    </div>
  );
};

export default PredictionForm;
