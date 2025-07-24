import React from "react";
 
 
const features = [
  {
    title: "Upload Data",
    desc: "Start by uploading your raw data file in CSV or Excel format.",
    icon: "⬆️",
  },
  {
    title: "AI-Powered Mapping",
    desc: "Our AI suggests mappings between your source and Oracle FBDI target columns.",
    icon: "🤖",
  },
  {
    title: "Automated Import",
    desc: "Calfus handles the complex process of loading data into Oracle Fusion.",
    icon: "🚀",
  },
  {
    title: "Reconciliation",
    desc: "Generate a detailed report to verify the import process was successful.",
    icon: "✅",
  },
];
 
const HomePage = ({ setActiveTab }) => {
  return (
    <div className="bg-[#f6fafd] min-h-screen">
      {/* Hero Section */}
      <section className="text-center py-20 px-6">
        <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-4">
          Automate Your Oracle FBDI Data Imports
        </h1>
        <p className="max-w-2xl mx-auto text-gray-600 text-lg">
          Calfus uses AI to streamline the entire File-Based Data Import (FBDI) process — from data mapping to reconciliation — saving time and reducing errors.
        </p>
        <div className="mt-8">
          <button
            onClick={() => setActiveTab('download')}
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold px-6 py-3 rounded-lg shadow transition-all"
          >
            Get Started →
          </button>
        </div>
      </section>
 
      {/* How It Works Section */}
      <section className="bg-white py-12 px-6">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-10">
          How It Works
        </h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
          {features.map((f, idx) => (
            <div
              key={idx}
              className="bg-[#f9fafa] rounded-2xl p-6 shadow hover:shadow-md transition-all text-center"
            >
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="font-semibold text-lg text-gray-800 mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
 
export default HomePage;