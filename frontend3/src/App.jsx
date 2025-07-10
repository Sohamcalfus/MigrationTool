// src/App.jsx
import React from "react";
import FBDIGenerator from "./components/FBDIGenerator3";

function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-2xl font-bold mb-6">Calfus</h1>
      <FBDIGenerator />
    </div>
  );
}

export default App;
