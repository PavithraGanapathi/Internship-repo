// src/components/Navbar.jsx
import React from "react";
import { Link } from "react-router-dom";

const Navbar = () => {
  return (
    <nav className="bg-gray-900 text-white p-4 flex justify-between items-center shadow-lg">
      <h1 className="text-xl font-bold">OCR Labeling Tool</h1>
      <div className="space-x-6">
        <Link to="/upload" className="hover:text-blue-400">Upload</Link>
        <Link to="/segment" className="hover:text-blue-400">Segment</Link>
        <Link to="/label" className="hover:text-blue-400">Label</Link>
      </div>
    </nav>
  );
};

export default Navbar;
