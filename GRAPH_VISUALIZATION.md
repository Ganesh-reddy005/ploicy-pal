# Knowledge Graph Visualization

## Overview

PolicyPal now includes an interactive knowledge graph visualization that shows how your policy document is structured in Neo4j. This helps you understand the relationships between different policy components.

## Features

### 🎨 Visual Elements

**Nodes** represent policy entities:
- **Policy**: Main policy document (Blue)
- **Section**: Major sections like "Coverage", "Exclusions" (Green)
- **Clause**: Specific clauses within sections (Purple)
- **Condition**: Conditions that must be met (Orange)
- **Exclusion**: Specific exclusions (Red)
- **WaitingPeriod**: Waiting periods (Pink)
- **Benefit**: Benefits provided (Cyan)
- **Definition**: Defined terms (Indigo)

**Edges** represent relationships:
- `CONTAINS`: Section contains Clause
- `HAS_CONDITION`: Clause has Condition
- `HAS_EXCLUSION`: Clause has Exclusion
- `HAS_WAITING_PERIOD`: Clause has Waiting Period
- `PROVIDES_BENEFIT`: Clause provides Benefit
- `DEFINES`: Section defines Definition
- `HAS_SECTION`: Policy has Section

### 🎯 Interactive Features

1. **Click on Nodes**: View detailed properties
2. **Hover**: See node labels
3. **Sidebar**: Shows selected node details
4. **Legend**: Color-coded node types
5. **Stats**: Node and relationship counts

## How to Access

1. Upload and process your policy document
2. Wait for processing to complete (100%)
3. In the chat interface, click the **"Graph"** button in the header
4. View the knowledge graph visualization
5. Click nodes to see details
6. Click **"← Back"** to return to chat

## API Endpoint

### GET /api/graph/{document_id}

Returns graph data for visualization:

```json
{
  "nodes": [
    {
      "id": "unique_id",
      "label": "Node Name",
      "type": "Section",
      "properties": {
        "name": "Coverage",
        "document_id": "...",
        ...
      }
    }
  ],
  "edges": [
    {
      "source": "source_node_id",
      "target": "target_node_id",
      "type": "CONTAINS",
      "properties": {}
    }
  ],
  "stats": {
    "node_count": 45,
    "edge_count": 67,
    "node_types": ["Policy", "Section", "Clause", ...]
  }
}
```

## Technical Details

### Backend Implementation

**Graph Service Method:**
```python
def get_graph_for_visualization(self, document_id: str) -> dict:
    """
    Get graph data formatted for visualization.
    Returns nodes and edges in a format suitable for visualization libraries.
    """
```

**Query Logic:**
1. Fetch all nodes for document
2. Extract node properties and labels
3. Fetch all relationships between nodes
4. Calculate statistics
5. Return structured JSON

### Frontend Implementation

**Components:**
- `GraphView.tsx`: Main visualization component
- Canvas-based rendering for performance
- Force-directed layout (circular)
- Click handling for node selection

**Rendering:**
- HTML5 Canvas for high performance
- Responsive sizing
- Color-coded nodes by type
- Edge labels showing relationship types

## Layout Algorithm

Currently uses a **circular layout** for simplicity:
- Nodes arranged in a circle
- Equal spacing between nodes
- Center of canvas as origin
- Radius based on canvas size

**Future improvements could include:**
- Force-directed layout (D3.js style)
- Hierarchical layout
- Clustering by node type
- Zoom and pan controls

## Example Graph Structure

```
                    [Policy]
                       |
          ┌────────────┼────────────┐
          |            |            |
      [Section 1]  [Section 2]  [Section 3]
          |            |            |
    ┌─────┴─────┐      |      ┌─────┴─────┐
    |           |      |      |           |
[Clause 1.1] [Clause 1.2] [Clause 2.1] [Clause 3.1]
    |           |              |
[Condition] [Exclusion]   [Benefit]
```

## Color Scheme

| Node Type | Color | Hex |
|-----------|-------|-----|
| Policy | Blue | #3b82f6 |
| Section | Green | #10b981 |
| Clause | Purple | #8b5cf6 |
| Condition | Orange | #f59e0b |
| Exclusion | Red | #ef4444 |
| WaitingPeriod | Pink | #ec4899 |
| Benefit | Cyan | #06b6d4 |
| Definition | Indigo | #6366f1 |
| Unknown | Gray | #9ca3af |

## Use Cases

### 1. Understanding Policy Structure
See how sections are organized and which clauses belong to which section.

### 2. Finding Related Information
Identify which exclusions or conditions are associated with specific clauses.

### 3. Coverage Analysis
Visualize all benefits and their relationships to policy sections.

### 4. Compliance Checking
Verify that all required sections and clauses are present.

### 5. Debugging Document Processing
Check if entity extraction worked correctly.

## Limitations

### Current Version
- ✅ Simple circular layout
- ✅ Click to select nodes
- ✅ View node properties
- ⚠️ No zoom/pan controls
- ⚠️ No force-directed layout
- ⚠️ No edge filtering
- ⚠️ No search functionality

### Performance
- Works well up to ~200 nodes
- May become crowded with larger graphs
- Canvas rendering is efficient

## Future Enhancements

### Planned Features
- [ ] Zoom and pan controls
- [ ] Force-directed layout (like D3.js)
- [ ] Node search and filtering
- [ ] Edge filtering by type
- [ ] Export as image (PNG/SVG)
- [ ] 3D visualization option
- [ ] Minimap for navigation
- [ ] Node clustering
- [ ] Path finding between nodes
- [ ] Compare multiple documents

### Advanced Features
- [ ] Interactive editing (add/remove nodes)
- [ ] Animation for layout changes
- [ ] Timeline view (show how graph evolved)
- [ ] Integration with chat (click node → ask about it)
- [ ] Graph statistics dashboard
- [ ] Community detection algorithms

## Integration with Chat

You can toggle between:
- **Chat View**: Q&A interface with citations
- **Graph View**: Visual knowledge graph

Both views show the same document but different perspectives:
- Chat: Text-based question answering
- Graph: Visual structure exploration

## Troubleshooting

### Graph Shows No Nodes
**Possible causes:**
- Entity extraction failed during processing
- Neo4j connection issues
- Document not fully processed

**Solution:**
1. Check backend logs for errors
2. Verify Neo4j is running
3. Try re-uploading the document

### Canvas is Blank
**Possible causes:**
- Browser compatibility issues
- Canvas rendering failed
- No graph data returned

**Solution:**
1. Check browser console for errors
2. Try a different browser
3. Check API response in Network tab

### Nodes Overlap
**Current limitation:**
- Simple circular layout can cause overlap
- More nodes = more crowded

**Workaround:**
- Wait for force-directed layout update
- Or use Neo4j Browser directly

## Alternative: Neo4j Browser

For advanced graph exploration, you can also use Neo4j Browser:

1. Open http://localhost:7474 (local Neo4j)
2. Or open your Neo4j AuraDB console
3. Run Cypher query:
   ```cypher
   MATCH (n {document_id: "your_document_id"})
   OPTIONAL MATCH (n)-[r]->(m {document_id: "your_document_id"})
   RETURN n, r, m
   ```
4. Get full Neo4j visualization features

## Summary

The Knowledge Graph Visualization provides:
- ✅ Interactive visual representation
- ✅ Easy-to-understand structure
- ✅ Click-to-inspect functionality
- ✅ Color-coded node types
- ✅ Relationship visualization
- ✅ Quick toggle with chat view

It's a powerful tool for understanding how PolicyPal structures and analyzes your policy documents!
