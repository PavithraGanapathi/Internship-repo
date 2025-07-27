// src/pages/SegmentPage.jsx
import React, { useState } from "react";
import axios from "axios";

const SegmentPage = () => {
  const [filename, setFilename] = useState("");
  const [message, setMessage] = useState("");

  const handleSegment = async () => {
    if (!filename) return alert("Enter filename (e.g., se_302.pdf)");
    try {
      const res = await axios.post(
        `http://127.0.0.1:8000/api/segment/?filename=${filename}&offset=0&limit=5`
      );
      setMessage(res.data.message);
    } catch (error) {
      setMessage("Error during segmentation!");
    }
  };

  return (
    <div className="max-w-xl mx-auto bg-white shadow-lg p-6 rounded-xl">
      <h2 className="text-2xl font-bold mb-4">Segment Lines</h2>
      <input
        type="text"
        placeholder="Enter filename (e.g., se_302.pdf)"
        value={filename}
        onChange={(e) => setFilename(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4"
      />
      <button
        onClick={handleSegment}
        className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
      >
        Segment
      </button>
      {message && <p className="mt-4 text-green-600">{message}</p>}
    </div>
  );
};

export default SegmentPage;
