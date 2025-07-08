import React, { useState } from "react";
import FBDIUploader from "./FBDIUploader";
import MappingViewer from "./MappingViewer";

function App() {
  const [activeTab, setActiveTab] = useState("upload");

  return (
    <div className="App">
      <div className="container mt-4">
        <h1 className="text-center mb-4">FBDI Generator Tool</h1>
        
        {/* Navigation Tabs */}
        <ul className="nav nav-tabs mb-4">
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === "upload" ? "active" : ""}`}
              onClick={() => setActiveTab("upload")}
            >
              File Upload
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === "mappings" ? "active" : ""}`}
              onClick={() => setActiveTab("mappings")}
            >
              View Mappings
            </button>
          </li>
        </ul>

        {/* Tab Content */}
        {activeTab === "upload" && <FBDIUploader />}
        {activeTab === "mappings" && <MappingViewer />}
      </div>
    </div>
  );
}

export default App;
