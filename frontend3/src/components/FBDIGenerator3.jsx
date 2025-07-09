import React, { useState } from 'react';

const FBDIGenerator3 = () => {
  const [rawFile, setRawFile] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState("AR");
  const [projectName, setProjectName] = useState("");
  const [selectedEnv, setSelectedEnv] = useState("DEV");
  const [loading, setLoading] = useState(false);

  const fbdiTemplates = [
    "AP", "AR", "GL", "FA", "CM", "EX", "TX", "INV", "PO", "OM",
    "PIM", "MF", "CST", "WMS", "HR", "PY", "WFM", "TM", "CMP"
  ];

  const envOptions = ["DEV", "TEST", "UAT", "PROD"];

  const handleGenerate = async () => {
    if (!rawFile || !selectedTemplate) {
      alert("Please select a raw file and FBDI type.");
      return;
    }

    const formData = new FormData();
    formData.append("raw_file", rawFile);
    formData.append("fbdi_type", selectedTemplate);
    formData.append("project_name", projectName);
    formData.append("env_type", selectedEnv);

    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/generate-fbdi-from-type", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Failed to generate");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "fbdi_output.zip";
      a.click();
      window.URL.revokeObjectURL(url);

      alert("✓ FBDI downloaded");
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-bold mb-4">FBDI Generator</h2>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Side */}
        <div className="flex-1 space-y-4">
          {/* Raw File Upload */}
          <div>
            <label className="block font-medium mb-2">Upload Raw File (.xlsx)</label>
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setRawFile(e.target.files[0])}
              className="block w-full border rounded px-3 py-2"
            />
          </div>

          {/* FBDI Type Dropdown */}
          <div>
            <label className="block font-medium mb-2">Select FBDI Type</label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              {fbdiTemplates.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Right Side */}
        <div className="w-full lg:w-1/3 space-y-4">
          {/* Project Name Input */}
          <div>
            <label className="block font-medium mb-2">Project Name</label>
            <input
              type="text"
              placeholder="Enter project name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          {/* ENV Dropdown */}
          <div>
            <label className="block font-medium mb-2">Select ENV</label>
            <select
              value={selectedEnv}
              onChange={(e) => setSelectedEnv(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              {envOptions.map((env) => (
                <option key={env} value={env}>
                  {env}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Generate Button */}
      <div className="pt-4">
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate FBDI"}
        </button>
      </div>
    </div>
  );
};

export default FBDIGenerator3;
