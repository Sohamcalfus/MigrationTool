import React, { useState } from "react";
import { Search, CheckCircle, XCircle, Clock, AlertCircle } from "lucide-react";

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
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Search className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <div className="ml-4">
            <h2 className="text-2xl font-semibold text-gray-900">Job Status Monitor</h2>
            <p className="text-gray-600 mt-1">Track the status of your Oracle Cloud job submissions</p>
          </div>
        </div>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Job Lookup</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job ID
            </label>
            <div className="relative">
              <input
                type="text"
                value={jobId}
                onChange={(e) => setJobId(e.target.value)}
                placeholder="Enter Oracle Cloud job ID"
                className="w-full border border-gray-300 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              />
              <Search className="absolute right-3 top-3 w-5 h-5 text-gray-400" />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={checkStatus}
              disabled={loading || !jobId.trim()}
              className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                loading || !jobId.trim()
                  ? "bg-gray-300 cursor-not-allowed text-gray-500"
                  : "bg-orange-600 hover:bg-orange-700 text-white shadow-sm hover:shadow-md"
              }`}
            >
              <Search className="w-5 h-5 mr-2" />
              {loading ? "Checking..." : "Check Status"}
            </button>
          </div>
        </div>
      </div>

      {/* Job Status Result */}
      {jobStatus && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-6">
            {jobStatus.job_status === 'SUCCEEDED' ? (
              <CheckCircle className="w-6 h-6 text-green-500 mr-3" />
            ) : jobStatus.job_status === 'FAILED' ? (
              <XCircle className="w-6 h-6 text-red-500 mr-3" />
            ) : jobStatus.job_status === 'RUNNING' ? (
              <Clock className="w-6 h-6 text-blue-500 mr-3" />
            ) : (
              <AlertCircle className="w-6 h-6 text-yellow-500 mr-3" />
            )}
            <h3 className="text-lg font-medium text-gray-900">Job Status Details</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Job ID</span>
                <span className="text-sm text-gray-900 font-mono">{jobStatus.job_id}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Status</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  jobStatus.job_status === 'SUCCEEDED' 
                    ? 'bg-green-100 text-green-800' 
                    : jobStatus.job_status === 'FAILED' 
                    ? 'bg-red-100 text-red-800'
                    : jobStatus.job_status === 'RUNNING'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {jobStatus.job_status === 'SUCCEEDED' && <CheckCircle className="w-3 h-3 mr-1" />}
                  {jobStatus.job_status === 'FAILED' && <XCircle className="w-3 h-3 mr-1" />}
                  {jobStatus.job_status === 'RUNNING' && <Clock className="w-3 h-3 mr-1" />}
                  {!['SUCCEEDED', 'FAILED', 'RUNNING'].includes(jobStatus.job_status) && <AlertCircle className="w-3 h-3 mr-1" />}
                  {jobStatus.job_status}
                </span>
              </div>
            </div>
            
            <div className="space-y-4">
              {jobStatus.start_time && (
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Started</span>
                  <span className="text-sm text-gray-900">{new Date(jobStatus.start_time).toLocaleString()}</span>
                </div>
              )}
              
              {jobStatus.end_time && (
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Completed</span>
                  <span className="text-sm text-gray-900">{new Date(jobStatus.end_time).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
          
          {jobStatus.error_message && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="text-sm font-medium text-red-800 mb-2">Error Details</h4>
              <p className="text-sm text-red-700">{jobStatus.error_message}</p>
            </div>
          )}
        </div>
      )}
    </div>
    
  );
};

export default JobStatus;
