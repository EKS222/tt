import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/stafflist.css";

const StaffList = () => {
  const [staffList, setStaffList] = useState([]);
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [error, setError] = useState(null);

  const API_URL = "https://49eca945-a85d-4041-8329-c8ccc69e464c-00-37km72cvzyu68.janeway.replit.dev:5000";

  // Fetch staff list
  useEffect(() => {
    const fetchStaff = async () => {
      try {
        const response = await axios.get(`${API_URL}/staff`);
        setStaffList(response.data);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch staff list.");
      }
    };

    const fetchClasses = async () => {
      try {
        const response = await axios.get(`${API_URL}/classes`);
        setClasses(response.data);
      } catch (err) {
        console.error(err);
        setError("Failed to fetch classes.");
      }
    };

    fetchStaff();
    fetchClasses();
  }, []);

  // Delete a staff
  const deleteStaff = async (staffId) => {
    try {
      await axios.delete(`${API_URL}/staff/${staffId}`);
      setStaffList(staffList.filter((staff) => staff.id !== staffId));
    } catch (err) {
      console.error(err);
      setError("Failed to delete staff.");
    }
  };

  // Assign a class to a staff
  const assignToClass = async (staffId) => {
    if (!selectedClass) {
      setError("Please select a class first.");
      return;
    }

    try {
      await axios.post(`${API_URL}/assign-class`, {
        staff_id: staffId,
        class_id: selectedClass,
      });
      alert("Staff assigned to class successfully.");
    } catch (err) {
      console.error(err);
      setError("Failed to assign staff to class.");
    }
  };

  // Add staff (Navigate to Add Staff page or Modal)
  const addStaff = () => {
    alert("Navigate to Add Staff page here.");
  };

  return (
    <div className="staff-list-container">
      <h2>Staff List</h2>
      <button className="add-staff-btn" onClick={addStaff}>
        Add Staff
      </button>
      {error && <p className="error-message">{error}</p>}
      <div className="staff-list">
        {staffList.map((staff) => (
          <div key={staff.id} className="staff-card">
            <h3>{staff.name}</h3>
            <p>
              <strong>Phone:</strong> {staff.phone}
            </p>
            <p>
              <strong>Role:</strong> {staff.role}
            </p>
            <div className="actions">
              <select
                onChange={(e) => setSelectedClass(e.target.value)}
                className="class-select"
              >
                <option value="">Select Class</option>
                {classes.map((cls) => (
                  <option key={cls.id} value={cls.id}>
                    {cls.name}
                  </option>
                ))}
              </select>
              <button onClick={() => assignToClass(staff.id)}>Assign</button>
              <button onClick={() => deleteStaff(staff.id)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StaffList;
