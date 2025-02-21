import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const SignIn = () => {
  const [userData, setUserData] = useState({
    email: "",
    password: ""
  });
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({ ...userData, [name]: value });
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    try {
    
      const response = await axios.post("http://localhost:5000/api/signin", userData, { withCredentials: true });
      
      if (response && response.data) {
       
        localStorage.setItem("token", response.data.token);
        localStorage.setItem("role", response.data.role);
        
        
        if (response.data.role === "admin") {
          navigate("/admin/dashboard");
        } else {
          navigate("/user/dashboard");
        }
      }
    } catch (error) {
      console.error("Sign in error:", error.response?.data?.message || error.message);
      setMessage(error.response?.data?.message || "Sign in failed. Please try again.");
    }
  };

  return (
    <div>
      <h1>Sign In</h1>
      <form onSubmit={handleSignIn}>
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={userData.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={userData.password}
          onChange={handleChange}
          required
        />
        <button type="submit">Sign In</button>
      </form>
      {message && <h3>{message}</h3>}
    </div>
  );
};

export default SignIn;
