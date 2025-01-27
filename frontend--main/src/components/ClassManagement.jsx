import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/classmanagement.css"
const ClassManagement = () => {
  const [classes, setClasses] = useState([]);
  const [newClassName, setNewClassName] = useState("");
  const [newGradeId, setNewGradeId] = useState("");
  const [error, setError] = useState(null);

  const API_URL = "https://49eca945-a85d-4041-8329-c8ccc69e464c-00-37km72cvzyu68.janeway.replit.dev:5000";

  // Fetch all classes
  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const response = await axios.get(`${API_URL}/classes`);
        setClasses(response.data);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch classes.");
      }
    };

    fetchClasses();
  }, []);

  // Add a new class
  const addClass = async () => {
    if (!newClassName || !newGradeId) {
      setError("Class name and Grade ID are required.");
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/add-class`, {
        name: newClassName,
        grade_id: newGradeId,
      });
      setClasses([...classes, response.data.class]);
      setNewClassName("");
      setNewGradeId("");
      alert("Class added successfully.");
    } catch (err) {
      console.error(err);
      setError("Failed to add class.");
    }
  };

  // Delete a class
  const deleteClass = async (classId) => {
    try {
      await axios.delete(`${API_URL}/delete-class/${classId}`);
      setClasses(classes.filter((cls) => cls.id !== classId));
      alert("Class deleted successfully.");
    } catch (err) {
      console.error(err);
      setError("Failed to delete class.");
    }
  };

  return (
    <div className="class-management">
      <h2>Class Management</h2>
      {error && <p className="error">{error}</p>}

      <div className="add-class-form">
        <input
          type="text"
          placeholder="Class Name"
          value={newClassName}
          onChange={(e) => setNewClassName(e.target.value)}
        />
        <input
          type="number"
          placeholder="Grade ID"
          value={newGradeId}
          onChange={(e) => setNewGradeId(e.target.value)}
        />
        <button onClick={addClass}>Add Class</button>
      </div>

      <div className="class-list">
        {classes.map((cls) => (
          <div key={cls.id} className="class-card">
            <h3>{cls.name}</h3>
            <p>
              <strong>Grade ID:</strong> {cls.grade_id}
            </p>
            <button onClick={() => deleteClass(cls.id)}>Delete Class</button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ClassManagement;
