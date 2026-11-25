"use client";

import { useEffect, useRef, useState } from "react";
import { Network, ArrowLeft, Loader2, AlertCircle, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

interface Node {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

interface Edge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
  stats: {
    node_count: number;
    edge_count: number;
    node_types: string[];
  };
}

interface GraphViewProps {
  documentId: string;
  onBack: () => void;
}

export default function GraphView({ documentId, onBack }: GraphViewProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchGraphData();
  }, [documentId]);

  const fetchGraphData = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/graph/${documentId}`
      );
      
      if (!res.ok) {
        throw new Error("Failed to fetch graph data");
      }
      
      const data = await res.json();
      setGraphData(data);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load graph");
      setLoading(false);
    }
  };

  useEffect(() => {
    if (graphData && canvasRef.current) {
      drawGraph();
    }
  }, [graphData, scale, offset]);

  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Apply transformations
    ctx.save();
    ctx.translate(canvas.width / 2 + offset.x, canvas.height / 2 + offset.y);
    ctx.scale(scale, scale);

    // Calculate positions using force-directed layout simulation (simple version)
    const nodes = graphData.nodes.map((node, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      const radius = Math.min(canvas.width, canvas.height) * 0.25;
      return {
        ...node,
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
      };
    });

    // Color mapping for node types
    const colors: Record<string, string> = {
      Policy: "#3b82f6",
      Section: "#10b981",
      Clause: "#8b5cf6",
      Condition: "#f59e0b",
      Exclusion: "#ef4444",
      WaitingPeriod: "#ec4899",
      Benefit: "#06b6d4",
      Definition: "#6366f1",
    };

    // Draw edges
    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = 1.5 / scale; // Adjust line width based on scale
    graphData.edges.forEach((edge) => {
      const source = nodes.find((n) => n.id === edge.source);
      const target = nodes.find((n) => n.id === edge.target);
      
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
        
        // Draw edge label (only if zoomed in)
        if (scale > 0.7) {
          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          ctx.fillStyle = "#6b7280";
          ctx.font = `${10 / scale}px sans-serif`;
          ctx.textAlign = "center";
          ctx.fillText(edge.type, midX, midY);
        }
      }
    });

    // Draw nodes
    nodes.forEach((node) => {
      const color = colors[node.type] || "#9ca3af";
      const radius = 30 / scale; // Adjust radius based on scale
      
      // Node circle
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fill();
      
      // Node border
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2 / scale;
      ctx.stroke();
      
      // Node label
      ctx.fillStyle = "#ffffff";
      ctx.font = `bold ${10 / scale}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      
      // Truncate label if too long
      let label = node.label;
      if (label.length > 15) {
        label = label.substring(0, 12) + "...";
      }
      ctx.fillText(label, node.x, node.y);
    });

    ctx.restore();
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev * 1.2, 5));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev / 1.2, 0.3));
  };

  const handleResetView = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale((prev) => Math.max(0.3, Math.min(5, prev * delta)));
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    // Only handle click if not dragging
    if (isDragging) return;
    
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    
    // Get click position relative to canvas
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    // Transform click position to graph coordinates
    const graphX = (clickX - canvas.width / 2 - offset.x) / scale;
    const graphY = (clickY - canvas.height / 2 - offset.y) / scale;

    // Calculate node positions
    const nodes = graphData.nodes.map((node, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      const radius = Math.min(canvas.width, canvas.height) * 0.25;
      return {
        ...node,
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
      };
    });

    // Find clicked node
    const clickedNode = nodes.find((node) => {
      const distance = Math.sqrt((node.x - graphX) ** 2 + (node.y - graphY) ** 2);
      return distance <= 30 / scale;
    });

    setSelectedNode(clickedNode || null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-gray-600">{error}</p>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
            <Network className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-medium text-gray-900">Knowledge Graph</h2>
            <p className="text-xs text-gray-400">
              {graphData?.stats.node_count} nodes • {graphData?.stats.edge_count} relationships
            </p>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4 text-gray-600" />
          </button>
          <span className="text-xs text-gray-500 min-w-[50px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={handleResetView}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-2"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Graph Visualization */}
      <div className="flex">
        <div className="flex-1 p-4">
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            onWheel={handleWheel}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className={`w-full h-[600px] border border-gray-200 rounded-lg ${
              isDragging ? "cursor-grabbing" : "cursor-grab"
            }`}
          />
          
          {/* Instructions */}
          <div className="mt-3 text-xs text-gray-400 text-center">
            Scroll to zoom • Drag to pan • Click nodes for details
          </div>
          
          {/* Legend */}
          <div className="mt-4 flex flex-wrap gap-2">
            {graphData?.stats.node_types.map((type) => (
              <div key={type} className="flex items-center gap-2 px-3 py-1 bg-gray-50 rounded-full text-xs">
                <div className="w-3 h-3 rounded-full bg-gray-400" />
                <span className="text-gray-600">{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Node Details Sidebar */}
        {selectedNode && (
          <div className="w-80 border-l border-gray-100 p-4 bg-gray-50/50 overflow-y-auto">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Node Details</h3>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-400">Type</p>
                <p className="text-sm text-gray-900 font-medium">{selectedNode.type}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Label</p>
                <p className="text-sm text-gray-900">{selectedNode.label}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Properties</p>
                <div className="mt-1 space-y-1">
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="text-gray-500">{key}:</span>{" "}
                      <span className="text-gray-900">
                        {typeof value === "object" ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
