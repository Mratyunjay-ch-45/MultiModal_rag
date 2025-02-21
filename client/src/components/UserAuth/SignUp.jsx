import React, { useState } from "react";
import axios from "axios";

const SignUp = () => {
  const [userData, setUserData] = useState({
    name: '',
    email: '',
    password: ''
  });
  
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({ ...userData, [name]: value });
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("http://localhost:5000/api/register", userData);
      if (response.status === 201) {
        setMessage("User created successfully");
      }
    } catch (error) {
      console.error("Registration error:", error.response?.data?.message || error.message);
      setMessage(error.response?.data?.message || "Registration failed");
    }
  };

  return (
    <div>
      <h1>Sign Up</h1>
      <form onSubmit={handleSignUp}>
        <input 
          type="text"
          name="name"
          placeholder="Name"
          value={userData.name}
          onChange={handleChange}
          required
        />
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
        <button type="submit">Sign Up</button>
      </form>
      {message && <h3>{message}</h3>}
    </div>
  );
};

export default SignUp;
