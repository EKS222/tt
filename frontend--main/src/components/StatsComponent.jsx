import React, { useState, useEffect } from "react";
import axios from "axios";
import Chart from "chart.js/auto";
import "./styles/stats.css";

const StatsComponent = () => {
  const [stats, setStats] = useState(null);
  const [view, setView] = useState("school"); // 'school', 'grade', or 'class'

  useEffect(() => {
    axios
      .get("/api/stats")
      .then((response) => {
        setStats(response.data);
        renderCharts(response.data);
      })
      .catch((error) => console.error(error));
  }, []);

  const renderCharts = (data) => {
    // Render charts based on stats
    if (data) {
      const ctx1 = document.getElementById("schoolChart").getContext("2d");
      new Chart(ctx1, {
        type: "doughnut",
        data: {
          labels: ["Collected Fees", "Remaining Fees"],
          datasets: [
            {
              data: [
                data.school.collected_fees,
                data.school.total_fees - data.school.collected_fees,
              ],
              backgroundColor: ["#4CAF50", "#FF5252"],
            },
          ],
        },
      });

      const ctx2 = document.getElementById("gradeChart").getContext("2d");
      new Chart(ctx2, {
        type: "bar",
        data: {
          labels: data.grade_stats.map((grade) => grade.grade_name),
          datasets: [
            {
              label: "Payment Percentage",
              data: data.grade_stats.map((grade) => grade.percentage_collected),
              backgroundColor: "#03A9F4",
            },
          ],
        },
      });
    }
  };

  if (!stats) return <p>Loading stats...</p>;

  return (
    <div className="stats-container">
      <h2>School Statistics</h2>
      <div className="stats-overview">
        <div>
          <h3>Total Revenue: Ksh {stats.school.revenue}</h3>
          <h3>Total Expenses: Ksh {stats.school.expenses}</h3>
        </div>
        <div>
          <h3>Total Fees Collected: Ksh {stats.school.collected_fees}</h3>
          <h3>Collection Percentage: {stats.school.percentage_collected}%</h3>
        </div>
      </div>

      <div className="chart-section">
        <canvas id="schoolChart"></canvas>
        <h3>Grade-wise Fee Collection</h3>
        <canvas id="gradeChart"></canvas>
      </div>

      <div className="toggle-buttons">
        <button onClick={() => setView("school")}>School</button>
        <button onClick={() => setView("grade")}>Grade</button>
        <button onClick={() => setView("class")}>Class</button>
      </div>

      {view === "class" && (
        <div className="class-stats">
          <h3>Class Stats</h3>
          <ul>
            {stats.class_stats.map((cls) => (
              <li key={cls.class_name}>
                {cls.class_name}: {cls.percentage_collected}%
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default StatsComponent;
