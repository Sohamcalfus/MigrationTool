import React, { useState } from 'react';
import { FileText, Database, Upload, Download } from 'lucide-react';
import FBDIUploader from './components/FBDIUploader';
import MappingViewer from './components/MappingViewer';
 
function App() {
  const [activeTab, setActiveTab] = useState('upload');
 
  const tabs = [
    { id: 'upload', label: 'File Processing', icon: Upload },
    { id: 'mappings', label: 'View Mappings', icon: Database },
  ];
 
  return (
<div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
<div className="container mx-auto px-4 py-8">
        {/* Header */}
<div className="text-center mb-8">
<div className="flex items-center justify-center mb-4">
<FileText className="h-12 w-12 text-primary-600 mr-3" />
<h1 className="text-4xl font-bold text-gray-900">FBDI Generator Tool</h1>
</div>
<p className="text-gray-600 text-lg">
            Generate FBDI files with intelligent column mapping
</p>
</div>
 
        {/* Navigation Tabs */}
<div className="flex justify-center mb-8">
<div className="bg-white rounded-xl p-1 shadow-lg">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
<button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-primary-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
>
<Icon className="h-5 w-5 mr-2" />
                  {tab.label}
</button>
              );
            })}
</div>
</div>
 
        {/* Tab Content */}
<div className="max-w-7xl mx-auto">
          {activeTab === 'upload' && <FBDIUploader />}
          {activeTab === 'mappings' && <MappingViewer />}
</div>
</div>
</div>
  );
}
 
export default App;