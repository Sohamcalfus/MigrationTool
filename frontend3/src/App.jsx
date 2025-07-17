import React, { useState } from "react";
import { FBDIProvider } from "./components/FBDIGenerator3";
import PreviewMappings from "./components/PreviewMappings";
import DownloadFBDI from "./components/DownloadFBDI";
import FBDIOperations from "./components/FBDIOperations";
import JobStatus from "./components/JobStatus";

const App = () => {
  const [activeTab, setActiveTab] = useState("preview");

  const tabs = [
    { id: "preview", label: "Preview Mappings", icon: "🔍" },
    { id: "download", label: "Download FBDI", icon: "📥" },
    { id: "operations", label: "FBDI Operations", icon: "⚙️" },
    { id: "status", label: "Job Status", icon: "📊" }
  ];

  return (
    <FBDIProvider>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <div className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              Calfus
            </h1>
            <p className="text-gray-600 mt-1">Enterprise FBDI Management System</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="bg-white rounded-lg shadow-sm p-2 mb-6">
            <nav className="flex space-x-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                    activeTab === tab.id
                      ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md transform scale-105"
                      : "text-gray-600 hover:bg-gray-100 hover:text-indigo-600"
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="transition-all duration-300">
            {activeTab === "preview" && <PreviewMappings />}
            {activeTab === "download" && <DownloadFBDI />}
            {activeTab === "operations" && <FBDIOperations />}
            {activeTab === "status" && <JobStatus />}
          </div>
        </div>
      </div>
    </FBDIProvider>
  );
};

export default App;
