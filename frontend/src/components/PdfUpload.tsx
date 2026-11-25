"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Upload, FileText, X, AlertCircle, Loader2 } from "lucide-react";

interface DocumentStatus {
  document_id: string;
  status: string;
  message: string;
  progress: number;
}

interface PdfUploadProps {
  onUploadComplete: (status: DocumentStatus) => void;
}

export default function PdfUpload({ onUploadComplete }: PdfUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const validateFile = (selectedFile: File): boolean => {
    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are allowed");
      return false;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError("File size must be less than 50MB");
      return false;
    }
    return true;
  };

  const handleFileSelect = useCallback((selectedFile: File) => {
    setError(null);
    if (validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const pollStatus = useCallback((documentId: string) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/status/${documentId}`
        );
        
        if (!res.ok) {
          throw new Error("Failed to get status");
        }
        
        const statusData: DocumentStatus = await res.json();

        setProgress(statusData.progress || 0);
        setStatusMessage(statusData.message);

        if (statusData.status === "completed" || statusData.status === "failed") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
          setUploading(false);
          
          if (statusData.status === "failed") {
            setError(statusData.message);
          } else {
            onUploadComplete(statusData);
          }
        }
      } catch (err) {
        console.error("Status poll error:", err);
      }
    }, 1500);

    // Cleanup after 5 minutes
    setTimeout(() => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        setUploading(false);
        setError("Processing timeout. Please try again.");
      }
    }, 5 * 60 * 1000);
  }, [onUploadComplete]);

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setError(null);
    setStatusMessage("Uploading document...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      // Start polling for status
      pollStatus(data.document_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      {/* Drop Zone */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-all ${
          isDragging
            ? "border-gray-900 bg-gray-50"
            : "border-gray-200 hover:border-gray-300"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleInputChange}
          className="hidden"
          id="pdf-upload"
        />

        {!file ? (
          <>
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Upload className="w-5 h-5 text-gray-400" />
            </div>
            <h3 className="text-base font-medium text-gray-900 mb-1">
              Drop your policy PDF here
            </h3>
            <p className="text-sm text-gray-400 mb-4">
              or click to browse files
            </p>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-800 transition-colors"
            >
              <FileText className="w-4 h-4" />
              Choose File
            </button>
            <p className="text-xs text-gray-300 mt-4">Max 50MB • PDF only</p>
          </>
        ) : (
          /* File Selected Preview */
          <div className="text-left max-w-sm mx-auto">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center flex-shrink-0">
                  <FileText className="w-4 h-4 text-gray-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate max-w-[180px]">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                disabled={uploading}
                className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-100 rounded-lg flex items-center gap-2 text-red-600">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {uploading && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 text-gray-600 animate-spin" />
                    <span className="text-xs text-gray-600 font-medium">{statusMessage}</span>
                  </div>
                  <span className="text-xs text-gray-400">{progress}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="bg-gray-900 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {!uploading && (
              <button
                onClick={handleUpload}
                className="mt-4 w-full py-2.5 px-4 bg-gray-900 text-white text-sm rounded-lg font-medium hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Upload & Process
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}