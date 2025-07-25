import React, { useState, useEffect } from 'react';
import { FBDIProvider, useFBDI } from './components/FBDIGenerator3';
import PreviewMappings from './components/PreviewMappings';
import DownloadFBDI from './components/DownloadFBDI';
import FBDIOperations from './components/FBDIOperations';
import JobStatus from './components/JobStatus';
import { FileText, Download, Settings, BarChart3, Menu, X, Book, Home } from 'lucide-react';
import ReconReport from './components/ReconReport';
import HomePage from './components/Home';

// Create a wrapper component that can access the FBDI context
const AppContent = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Access workflow step from context
  const { workflowStep } = useFBDI();

  // Auto-switch tabs based on workflow step - but skip initial 'generate' state
  useEffect(() => {
    switch (workflowStep) {
      case 'process':
        setActiveTab('operations');
        break;
      case 'reconcile':
        setActiveTab('report');
        break;
      case 'complete':
        setActiveTab('report');
        break;
      // Removed the 'generate' case so it doesn't auto-switch on initial load
      default:
        // Don't change tab for other cases
        break;
    }
  }, [workflowStep]);

  const tabs = [
    { id: 'home', label: 'Home', icon: Home, component: (props) => <HomePage {...props} setActiveTab={setActiveTab} /> },
    { id: 'preview', label: 'Column Mapping', icon: FileText, component: PreviewMappings },
    { id: 'download', label: 'Generate FBDI', icon: Download, component: DownloadFBDI },
    { id: 'operations', label: 'Process FBDI', icon: Settings, component: FBDIOperations },
    { id: 'status', label: 'Job Status', icon: BarChart3, component: JobStatus },
    { id: 'report', label: 'Recon Report', icon: Book, component: ReconReport },
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
              <div className="flex items-center ml-4 lg:ml-0">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-teal-500 rounded-lg flex items-center justify-center">
                    <FileText className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div className="ml-4">
                  <h1 className="text-xl font-semibold text-gray-900">TransforMate</h1>
                  <p className="text-sm text-gray-500">Calfus FBDI Management Suite</p>
                </div>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Calfus Inc.
              </div>
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-gray-700">C</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white shadow-lg lg:shadow-none border-r border-gray-200 transition-transform duration-300 ease-in-out`}>
          <div className="flex flex-col h-full pt-16 lg:pt-0">
            <nav className="flex-1 px-4 py-6 space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                // Add workflow indicator
                const getWorkflowIndicator = () => {
                  if (workflowStep === 'generate' && tab.id === 'download') return '';
                  if (workflowStep === 'process' && tab.id === 'operations') return '🔄';
                  if (workflowStep === 'reconcile' && tab.id === 'report') return '📊';
                  if (workflowStep === 'complete' && tab.id === 'report') return '✅';
                  return '';
                };

                return (
                  <button
                    key={tab.id}
                    onClick={() => {
                      setActiveTab(tab.id);
                      setSidebarOpen(false);
                    }}
                    className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className={`w-5 h-5 mr-3 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                    <span className="flex-1">{tab.label}</span>
                    <span className="text-sm">{getWorkflowIndicator()}</span>
                  </button>
                );
              })}
            </nav>
            
            {/* Footer */}
            <div className="px-4 py-4 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                <p className="font-medium">Version 2.1.0</p>
                <p>© 2025 Calfus Solutions</p>
              </div>
            </div>
          </div>
        </div>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div 
            className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-50"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Content */}
        <div className="flex-1 lg:ml-0">
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Breadcrumb */}
            <div className="mb-6">
              <nav className="flex" aria-label="Breadcrumb">
                <ol className="flex items-center space-x-2">
                  <li>
                    <span className="text-gray-500 text-sm">FBDI Suite</span>
                  </li>
                  <li>
                    <span className="text-gray-400 mx-2">/</span>
                    <span className="text-blue-600 text-sm font-medium">
                      {tabs.find(tab => tab.id === activeTab)?.label}
                    </span>
                  </li>
                  {/* Workflow step indicator */}
                  {workflowStep !== 'generate' && activeTab !== 'home' && (
                    <li>
                      <span className="text-gray-400 mx-2">•</span>
                      <span className="text-orange-600 text-sm font-medium">
                        Step {workflowStep === 'generate' ? '1' : workflowStep === 'process' ? '2' : workflowStep === 'reconcile' ? '3' : workflowStep === 'complete' ? '4' : '1'} of 4
                      </span>
                    </li>
                  )}
                </ol>
              </nav>
            </div>

            {/* Content */}
            <div className="transition-all duration-300 ease-in-out">
              {ActiveComponent && <ActiveComponent />}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <FBDIProvider>
      <AppContent />
    </FBDIProvider>
  );
}

export default App;
