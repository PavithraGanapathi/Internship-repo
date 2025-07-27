// src/pages/LabelPage.jsx
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

const LabelPage = () => {
  const [filename, setFilename] = useState("");
  const [lines, setLines] = useState([]);
  const [offset, setOffset] = useState(0);

  // Fetch lines with useCallback to avoid eslint warnings
  const fetchLines = useCallback(async () => {
    if (!filename) return;
    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/api/lines/?filename=${filename}&offset=${offset}`
      );
      setLines(res.data.lines || []);
    } catch (error) {
      console.error(error);
      alert("Failed to load lines!");
    }
  }, [filename, offset]);

  // Fetch lines whenever offset changes
  useEffect(() => {
    if (filename) fetchLines();
  }, [fetchLines, filename]);

  const handleNext = () => {
    setOffset((prev) => prev + 5);
  };

  const handlePrev = () => {
    setOffset((prev) => (prev >= 5 ? prev - 5 : 0));
  };

  return (
    <div className="max-w-4xl mx-auto bg-white shadow-lg p-6 rounded-xl">
      <h2 className="text-2xl font-bold mb-4">Label OCR Lines</h2>

      <div className="flex mb-4 gap-2">
        <input
          type="text"
          placeholder="Enter filename (e.g., se_302.pdf)"
          value={filename}
          onChange={(e) => setFilename(e.target.value)}
          className="flex-grow border border-gray-300 rounded-lg px-3 py-2"
        />
        <button
          onClick={() => {
            setOffset(0);
            fetchLines();
          }}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          Load Lines
        </button>
      </div>

      {lines.length === 0 && filename && (
        <p className="text-gray-500">No lines found for {filename}.</p>
      )}

      {lines.map((line) => (
        <div
          key={line.line_id}
          className="mb-4 p-4 bg-gray-100 rounded-lg shadow-sm"
        >
          <p className="text-sm font-semibold text-gray-600 mb-2">
            {line.line_id}
          </p>
          <img
            src={`data:image/png;base64,${line.image_base64}`}
            alt="Line"
            className="mb-2 rounded border"
          />
          <textarea
            className="w-full border border-gray-300 rounded-lg p-2"
            defaultValue={line.ocr_text}
          />
        </div>
      ))}

      {lines.length > 0 && (
        <div className="flex justify-between mt-4">
          <button
            onClick={handlePrev}
            disabled={offset === 0}
            className={`px-4 py-2 rounded-lg ${
              offset === 0
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : "bg-gray-300 hover:bg-gray-400 text-gray-800"
            }`}
          >
            Previous
          </button>
          <button
            onClick={handleNext}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default LabelPage;
