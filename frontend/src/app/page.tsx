"use client";

import { useState, useEffect } from "react";
import { CheckCircle, AlertCircle, Loader2, Sparkles } from "lucide-react";
import PdfUpload from "@/components/PdfUpload";
import ChatSection from "@/components/ChatSection";
import GraphView from "@/components/GraphView";

interface HealthStatus {
  status: string;
  version: string;
  services: {
    qdrant: string;
    neo4j: string;
  };
}

interface DocumentStatus {
  document_id: string;
  status: string;
  message: string;
  progress: number;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [document, setDocument] = useState<DocumentStatus | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/health`);
      const data = await res.json();
      setHealth(data);
      setIsCheckingHealth(false);
    } catch {
      setHealth({ 
        status: "error", 
        version: "1.0.0",
        services: { qdrant: "disconnected", neo4j: "disconnected" }
      });
      setIsCheckingHealth(false);
    }
  };

  const handleUploadComplete = (doc: DocumentStatus) => {
    setDocument(doc);
    if (doc.status === "completed") {
      setShowChat(true);
    }
  };

  const handleNewDocument = () => {
    setDocument(null);
    setShowChat(false);
    setShowGraph(false);
  };

  const handleViewGraph = () => {
    setShowGraph(true);
    setShowChat(false);
  };

  const handleBackToChat = () => {
    setShowGraph(false);
    setShowChat(true);
  };

  const getStatusIcon = (connected: boolean) =>
    connected ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : (
      <AlertCircle className="w-4 h-4 text-red-500" />
    );
  
  const isConnected = (service: string) => service === "connected";

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  PolicyPal
                </h1>
                <p className="text-xs text-gray-400">
                  Intelligent Policy Explainer
                </p>
              </div>
            </div>

            {/* Health Status Badge */}
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full transition-colors ${
                health && isConnected(health.services.qdrant) ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                <span className="text-xs font-medium">Qdrant</span>
                {getStatusIcon(health ? isConnected(health.services.qdrant) : false)}
              </div>
              <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full transition-colors ${
                health && isConnected(health.services.neo4j) ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
              }`}>
                <span className="text-xs font-medium">Neo4j</span>
                {getStatusIcon(health ? isConnected(health.services.neo4j) : false)}
              </div>
              {isCheckingHealth && (
                <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-12">
        {!document ? (
          /* Upload State */
          <div className="max-w-lg mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Upload Your Policy
              </h2>
              <p className="text-gray-500">
                Upload an insurance policy PDF to get started
              </p>
            </div>
            <PdfUpload onUploadComplete={handleUploadComplete} />
          </div>
        ) : document.status !== "completed" ? (
          /* Processing State */
          <div className="max-w-lg mx-auto text-center">
            <div className="bg-white rounded-xl border border-gray-100 p-8">
              <div className="flex justify-center mb-6">
                <div className="relative">
                  <Loader2 className="w-12 h-12 text-gray-900 animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-medium text-gray-600">
                      {document.progress}%
                    </span>
                  </div>
                </div>
              </div>
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                Processing Your Policy
              </h2>
              <p className="text-gray-500 text-sm mb-6">
                {document.message}
              </p>
              
              {/* Progress Steps */}
              <div className="space-y-3 mb-6">
                <ProcessingStep 
                  label="Extracting text from PDF" 
                  isActive={document.progress >= 10}
                  isComplete={document.progress > 10}
                />
                <ProcessingStep 
                  label="Building knowledge graph" 
                  isActive={document.progress >= 40}
                  isComplete={document.progress > 40}
                />
                <ProcessingStep 
                  label="Indexing embeddings" 
                  isActive={document.progress >= 70}
                  isComplete={document.progress > 70}
                />
                <ProcessingStep 
                  label="Ready to answer questions" 
                  isActive={document.progress >= 100}
                  isComplete={document.progress >= 100}
                />
              </div>
              
              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="bg-gray-900 h-1.5 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${document.progress}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
          /* Chat/Graph State */
          <div className="max-w-4xl mx-auto">
            {showGraph ? (
              <GraphView documentId={document.document_id} onBack={handleBackToChat} />
            ) : (
              <ChatSection
                documentId={document.document_id}
                onNewDocument={handleNewDocument}
                onViewGraph={handleViewGraph}
              />
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 py-6">
        <div className="max-w-5xl mx-auto px-6 text-center text-xs text-gray-400">
          Powered by GraphRAG • Neo4j • Qdrant
        </div>
      </footer>
    </div>
  );
}

function ProcessingStep({ 
  label, 
  isActive, 
  isComplete 
}: { 
  label: string; 
  isActive: boolean; 
  isComplete: boolean;
}) {
  return (
    <div className={`flex items-center gap-3 text-sm transition-all ${
      isActive ? 'text-gray-900' : 'text-gray-300'
    }`}>
      <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-all ${
        isComplete 
          ? 'bg-green-500 text-white' 
          : isActive 
          ? 'bg-gray-900 text-white' 
          : 'bg-gray-100 text-gray-400'
      }`}>
        {isComplete ? (
          <CheckCircle className="w-3 h-3" />
        ) : isActive ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : (
          <span className="w-2 h-2 bg-gray-300 rounded-full" />
        )}
      </div>
      <span className={isActive ? 'font-medium' : ''}>{label}</span>
    </div>
  );
}