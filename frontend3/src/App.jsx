// src/App.jsx
import React from "react";
import FBDIGenerator from "./components/FBDIGenerator";

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-2xl font-bold mb-6">FBDI Generator (Testing UI)</h1>
      <FBDIGenerator />
    </div>
  );
}

export default App;
