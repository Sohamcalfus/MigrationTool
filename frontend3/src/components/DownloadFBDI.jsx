import React, { useState } from "react";
import { useFBDI } from "./FBDIGenerator3";

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
    <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-3xl font-bold text-indigo-700 mb-2">Generate & Download FBDI</h2>
        <p className="text-gray-600">Generate the complete FBDI package for Oracle Cloud using your configured settings</p>
      </div>

      {/* Show current configuration */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-3">Current Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-blue-700">Raw File:</span>
            <span className="ml-2 text-blue-600">{rawFile ? rawFile.name : "Not selected"}</span>
          </div>
          <div>
            <span className="font-medium text-blue-700">FBDI Type:</span>
            <span className="ml-2 text-blue-600">{selectedTemplate}</span>
          </div>
          <div>
            <span className="font-medium text-blue-700">Project Name:</span>
            <span className="ml-2 text-blue-600">{projectName || "Not set"}</span>
          </div>
          <div>
            <span className="font-medium text-blue-700">Environment:</span>
            <span className="ml-2 text-blue-600">{envType || "Not set"}</span>
          </div>
        </div>
        {mappings.length > 0 && (
          <div className="mt-3 pt-3 border-t border-blue-200">
            <span className="font-medium text-blue-700">Mappings Preview:</span>
            <span className="ml-2 text-blue-600">
              {mappings.filter(m => m.raw_column).length} of {mappings.length} columns mapped
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            Raw File
          </label>
          <input
            type="file"
            accept=".xlsx"
            onChange={(e) => setRawFile(e.target.files[0])}
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          />
          {rawFile && (
            <p className="text-sm text-green-600 mt-1">Selected: {rawFile.name}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            FBDI Type
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          >
            {fbdiTemplates.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            Project Name
          </label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Enter project name"
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          />
        </div>

        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            Environment
          </label>
          <input
            type="text"
            value={envType}
            onChange={(e) => setEnvType(e.target.value)}
            placeholder="Enter environment type"
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          />
        </div>
      </div>

      <div className="flex justify-center pt-4">
        <button
          onClick={handleDownload}
          disabled={loading}
          className={`px-8 py-3 rounded-lg font-semibold shadow-md transition duration-300 transform hover:scale-105 ${
            loading
              ? "bg-gray-400 cursor-not-allowed text-white"
              : "bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
          }`}
        >
          {loading ? "Generating FBDI..." : "Generate & Download FBDI"}
        </button>
      </div>

      {/* Information Section */}
      <div className="bg-green-50 rounded-lg p-6 mt-8">
        <h3 className="text-lg font-semibold text-green-800 mb-3">Package Contents</h3>
        <ul className="space-y-2 text-green-700">
          <li className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
            Complete FBDI template with your data mapped
          </li>
          <li className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
            Data validation and formatting applied
          </li>
          <li className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
            Ready-to-upload ZIP package for Oracle Cloud
          </li>
          <li className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
            Configuration files and documentation
          </li>
        </ul>
      </div>
    </div>
  );
};

export default DownloadFBDI;
