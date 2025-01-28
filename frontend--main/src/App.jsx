import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import Home from './components/Home';
import LoginForm from './components/LoginForm';
import AdminDashboard from './components/AdminDashboard';
import BursarDashboard from './components/BursarDashboard';
import DirectorDashboard from './components/DirectorDashboard';
import TeacherDashboard from './components/TeacherDashboard';
import StudentDashboard from './components/StudentDashboard';
import { AuthProvider } from './auth/AuthProvider';
import PrivateRoute from './auth/PrivateRoute';
import RoleBasedRoute from './auth/RoleBasedRoute';
import StaffList from './components/StaffList';
import AddStudent from './components/AddStudent';
import StudentList from './components/StudentList';
import PaymentTable from './components/PaymentTable';
import ClassManagement from './components/ClassManagement';


const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/Payments" element={<PaymentTable />} />
          <Route path="/students" element={<StudentList />} />
          <Route path="/staff" element={<StaffList />} />
          <Route path="/classes" element={<ClassManagement />} />
          <Route path="/student" element={<StudentDashboard />} />
          {/* <Route path="/payments" element={<StudentPaymentsByTerm />} />
          */}

          {/* Role-Based Private Routes */}
          <Route path="/admin" element={<PrivateRoute><RoleBasedRoute role="admin"><AdminDashboard /></RoleBasedRoute></PrivateRoute>} />
          
          <Route 
  path="/add-student" 
  element={
    <PrivateRoute>
      <RoleBasedRoute role="admin">
        <AddStudent />
      </RoleBasedRoute>
    </PrivateRoute>
  } 
/>
3. Update
          <Route path="/bursar" element={<PrivateRoute><RoleBasedRoute role="bursar"><BursarDashboard /></RoleBasedRoute></PrivateRoute>} />
          <Route path="/director" element={<PrivateRoute><RoleBasedRoute role="director"><DirectorDashboard /></RoleBasedRoute></PrivateRoute>} />
          <Route path="/teacher" element={<PrivateRoute><RoleBasedRoute role="teacher"><TeacherDashboard /></RoleBasedRoute></PrivateRoute>} />
          

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
