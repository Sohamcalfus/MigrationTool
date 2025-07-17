import React, { useState } from "react";

const JobStatus = () => {
  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const checkStatus = async () => {
    if (!jobId) {
      alert("Please enter a job ID");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/fbdi/check-job-status/${jobId}`);
      const data = await response.json();
      setJobStatus(data);
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-3xl font-bold text-indigo-700 mb-2">Check Job Status</h2>
        <p className="text-gray-600">Monitor the status of your submitted Oracle Cloud jobs</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block font-medium text-gray-700 mb-2">Job ID</label>
          <input
            type="text"
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            placeholder="Enter job ID"
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <button
          onClick={checkStatus}
          disabled={loading}
          className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
            loading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-indigo-500 hover:bg-indigo-600 text-white"
          }`}
        >
          {loading ? "Checking..." : "Check Status"}
        </button>
      </div>

      {jobStatus && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Job Status Result</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium">Job ID:</span>
              <span>{jobStatus.job_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-medium">Status:</span>
              <span className={`px-2 py-1 rounded text-sm ${
                jobStatus.job_status === 'SUCCEEDED' ? 'bg-green-100 text-green-800' :
                jobStatus.job_status === 'FAILED' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {jobStatus.job_status}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobStatus;
