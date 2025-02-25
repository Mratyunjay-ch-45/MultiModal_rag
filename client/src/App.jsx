import { useState } from 'react'
import SignIn from "./components/UserAuth/SignIn";
import SignUp from "./components/UserAuth/SignUp";
import UserDashboard from "./components/Dashboard/UserDashboard";
import AdminDashboard from "./components/Dashboard/AdminDashboard";
import MainPdf from './components/Pdf/MainPdf';


import {BrowserRouter as Router, Route,Routes} from 'react-router-dom'
function App() {
  
  return (
    <>
    <Router>
      <Routes>
        <Route path="/" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/user/dashboard" element={<UserDashboard />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path='pdf' element={<MainPdf />} />
      </Routes>
    </Router>
    </>
  )
}

export default App;
