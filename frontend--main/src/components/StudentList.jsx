import React, { useState, useEffect } from "react";
import axios from "axios";
import "../styles/studentList.css";
import Header from "./Header";
import { useNavigate } from "react-router-dom";

const StudentList = ({ role, onSelectStudent }) => {
  const [students, setStudents] = useState([]);
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [searchQuery, setSearchQuery] = useState(""); // For search input
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Fetch students on component mount
  useEffect(() => {
    const fetchStudents = async () => {
      try {
        let url =
          "https://c70a35f6-0f51-4320-86f4-c560837fc183-00-247oocffqp4w9.worf.replit.dev:5000/students"; // Default for Admin & Bursar

        if (role === "teacher") {
          const staffId = localStorage.getItem("staffId"); // Assuming staffId is stored after login
          url = `https://c70a35f6-0f51-4320-86f4-c560837fc183-00-247oocffqp4w9.worf.replit.dev:5000/staff/${staffId}/students`;
        }

        const response = await axios.get(url);
        setStudents(response.data);
        setFilteredStudents(response.data); // Initialize filtered list
      } catch (err) {
        console.error(err);
        setError("Failed to fetch students. Please try again.");
      }
    };
    fetchStudents();
  }, [role]);

  // Filter students based on the search query
  useEffect(() => {
    const results = students.filter(
      (student) =>
        student.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        student.admission_number?.toString().includes(searchQuery)
    );
    setFilteredStudents(results);
  }, [searchQuery, students]);

  const handleAddStudent = () => {
    navigate("/add-student"); // Navigate to AddStudent page
  };

  return (
    <div className="student-list-container">
      <Header />
      <h2>Student List</h2>
      <button className="add-student-btn" onClick={handleAddStudent}>
        Add Student
      </button>
      {error && <p className="error-message">{error}</p>}

      {/* Search Box */}
      <input
        type="text"
        placeholder="Search by name or admission number"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="search-box"
      />

      {/* Student Cards */}
      <div className="student-list">
        {filteredStudents.length > 0 ? (
          filteredStudents.map((student) => (
            <div
              key={student.id}
              className="student-card"
              onClick={() => onSelectStudent(student)}
            >
              <h3>{student.name}</h3>
                <p>
                <strong>ADM:</strong> {student.admission_number}
              </p>
              <p>
                <strong>Grade:</strong> {student.grade}
              </p>
              <p>
                <strong>Balance:</strong> {student.balance}
              </p>
            </div>
          ))
        ) : (
          <p className="no-results">No students found.</p>
        )}
      </div>
            
    </div>
  );
};

export default StudentList;


