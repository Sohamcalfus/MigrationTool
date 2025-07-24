import React, { useState } from "react";
import { useFBDI } from "./FBDIGenerator3";
import { Download, Package, CheckCircle, AlertCircle, FileText, Settings } from "lucide-react";

const DownloadFBDI = () => {
  const {
    rawFile,
    setRawFile,
    selectedTemplate,
    setSelectedTemplate,
    projectName,
    setProjectName,
    envType,
    setEnvType,
    mappings,
    fbdiTemplates
  } = useFBDI();

  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    if (!rawFile || !selectedTemplate || !projectName || !envType) {
      alert("Please fill all fields before generating FBDI.");
      return;
    }

    const formData = new FormData();
    formData.append("raw_file", rawFile);
    formData.append("fbdi_type", selectedTemplate);
    formData.append("project_name", projectName);
    formData.append("env_type", envType);

    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/generate-fbdi-from-type", {
        method: "POST",
        body: formData,
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${projectName}_${selectedTemplate}_FBDI.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to generate FBDI");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Package className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="ml-4">
            <h2 className="text-2xl font-semibold text-gray-900">Generate FBDI Package</h2>
            <p className="text-gray-600 mt-1">Create a complete FBDI package ready for Oracle Cloud deployment</p>
          </div>
        </div>
      </div>

      {/* Show current configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Settings className="w-5 h-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Configuration Summary</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Raw Data File</span>
              <div className="flex items-center">
                {rawFile ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{rawFile.name}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not selected</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">FBDI Template</span>
              <div className="flex items-center">
                {selectedTemplate ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{selectedTemplate}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not selected</span>
                  </>
                )}
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Project Name</span>
              <div className="flex items-center">
                {projectName ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{projectName}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not set</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Environment</span>
              <div className="flex items-center">
                {envType ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{envType}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not set</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {mappings.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Column Mappings</span>
              <span className="text-sm text-gray-600">
                {mappings.filter(m => m.raw_column).length} of {mappings.length} columns mapped
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Configuration Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Final Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Raw Data File
            </label>
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setRawFile(e.target.files[0])}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              FBDI Template Type
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            >
              {fbdiTemplates.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Project Name
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Enter project identifier"
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Environment Type
            </label>
            <select
              value={envType}
              onChange={(e) => setEnvType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            >
              <option value="">Select Environment</option>
              <option value="DEV">Development</option>
              <option value="TEST">Test</option>
              <option value="UAT">User Acceptance Testing</option>
              <option value="PROD">Production</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-6 border-t border-gray-200 mt-6">
          <button
            onClick={handleDownload}
            disabled={loading || !rawFile || !selectedTemplate || !projectName || !envType}
            className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              loading || !rawFile || !selectedTemplate || !projectName || !envType
                ? "bg-gray-300 cursor-not-allowed text-gray-500"
                : "bg-green-600 hover:bg-green-700 text-white shadow-sm hover:shadow-md"
            }`}
          >
            <Download className="w-5 h-5 mr-2" />
            {loading ? "Generating..." : "Generate FBDI Package"}
          </button>
        </div>
      </div>

      {/* Information Section */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <div className="flex items-center mb-4">
          <Package className="w-5 h-5 text-blue-600 mr-2" />
          <h3 className="text-lg font-medium text-blue-900">Package Contents</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Complete FBDI template with mapped data</span>
            </div>
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Data validation and formatting applied</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Ready-to-upload ZIP package</span>
            </div>
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Configuration files and documentation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
  );
};

export default DownloadFBDI;
