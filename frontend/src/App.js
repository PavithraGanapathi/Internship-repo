import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import SegmentPage from "./pages/SegmentPage";
import LabelPage from "./pages/LabelPage";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 flex flex-col">
        {/* NAVBAR */}
        <nav className="bg-white shadow-md p-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-indigo-600">OCR Labeling Tool</h1>
          <div className="space-x-6">
            <Link
              to="/"
              className="text-gray-700 hover:text-indigo-600 transition"
            >
              Upload
            </Link>
            <Link
              to="/segment"
              className="text-gray-700 hover:text-indigo-600 transition"
            >
              Segment
            </Link>
            <Link
              to="/label"
              className="text-gray-700 hover:text-indigo-600 transition"
            >
              Label
            </Link>
          </div>
        </nav>

        {/* MAIN CONTENT */}
        <main className="flex-grow p-6">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/segment" element={<SegmentPage />} />
            <Route path="/label" element={<LabelPage />} />
          </Routes>
        </main>

        {/* FOOTER */}
        <footer className="bg-white text-center py-4 shadow-inner text-sm text-gray-500">
          © {new Date().getFullYear()} OCR Labeling Tool
        </footer>
      </div>
    </Router>
  );
}

export default App;
