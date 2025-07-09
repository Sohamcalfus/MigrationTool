import React, { useState } from 'react';

const fbdiOptions = ['AR', 'AP', 'GL']; // For now only AR will work, but you can list others for UI

const FBDIGenerator3 = () => {
  const [rawFile, setRawFile] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('AR');
  const [selectedProject, setSelectedProject] = useState('Project A');
  const [selectedEnv, setSelectedEnv] = useState('DEV');

  const handleRawFileChange = (e) => {
    setRawFile(e.target.files[0]);
  };

  const handleGenerateFBDI = () => {
    alert(`Generating FBDI for template: ${selectedTemplate}, project: ${selectedProject}, env: ${selectedEnv}`);
    // Add fetch call here later
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 p-6">
      {/* Left: Raw File Upload */}
      <div className="flex-1 card border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4">Attach Raw File</h3>
        <input
          type="file"
          accept=".xlsx"
          onChange={handleRawFileChange}
          className="block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {rawFile && <p className="mt-2 text-sm text-green-600">Selected: {rawFile.name}</p>}
      </div>

      {/* Middle: Drag-Drop Styled FBDI Options */}
      <div className="flex-1 card border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4">Choose FBDI Template Type</h3>
        <div className="grid grid-cols-2 gap-4 overflow-y-auto max-h-64">
          {fbdiOptions.map((option) => (
            <div
              key={option}
              onClick={() => setSelectedTemplate(option)}
              className={`cursor-pointer p-4 rounded border-2 text-center transition-all ${
                selectedTemplate === option
                  ? 'border-blue-500 bg-blue-50 font-semibold'
                  : 'border-gray-200 hover:border-blue-300'
              }`}
            >
              {option}
            </div>
          ))}
        </div>
      </div>

      {/* Right: Project + ENV + Button */}
      <div className="flex-1 card border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
          <select
            className="w-full border-gray-300 rounded-md shadow-sm"
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
          >
            <option>Project A</option>
            <option>Project B</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Environment</label>
          <select
            className="w-full border-gray-300 rounded-md shadow-sm"
            value={selectedEnv}
            onChange={(e) => setSelectedEnv(e.target.value)}
          >
            <option>DEV</option>
            <option>UAT</option>
            <option>PROD</option>
          </select>
        </div>

        <button
          onClick={handleGenerateFBDI}
          className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-semibold shadow"
        >
          Generate FBDI
        </button>
      </div>
    </div>
  );
};

export default FBDIGenerator3;
