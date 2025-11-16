"""
OSP Graph Visualization Component

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Interactive OSP (Object-Subject-Predicate) graph visualization component
for the Jaseci Learning Companion frontend dashboard.
"""

'use client'

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Toolbar,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Button,
  Switch,
  FormControlLabel,
  Tooltip,
  Chip,
  Alert,
  CircularProgress,
  Fab,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Grid
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  Settings,
  Download,
  Upload,
  Refresh,
  Timeline,
  TrendingUp,
  Search,
  FilterList,
  ViewModule,
  ViewList
} from '@mui/icons-material';
import * as d3 from 'd3';
import { io, Socket } from 'socket.io-client';

interface OSPNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
  size: number;
  color: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface OSPEdge {
  from: string;
  to: string;
  label: string;
  properties: Record<string, any>;
  width: number;
  color: string;
  source?: OSPNode;
  target?: OSPNode;
}

interface GraphVisualizationData {
  nodes: OSPNode[];
  edges: OSPEdge[];
  layout: string;
  statistics: {
    total_nodes: number;
    total_edges: number;
    node_types: string[];
    relationship_types: string[];
  };
}

interface FilterOptions {
  nodeTypes: string[];
  relationshipTypes: string[];
  showLabels: boolean;
  showProperties: boolean;
  minNodeSize: number;
  maxNodeSize: number;
  edgeOpacity: number;
}

const OSPGraphVisualization: React.FC = () => {
  // State management
  const [graphData, setGraphData] = useState<GraphVisualizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [selectedLayout, setSelectedLayout] = useState('force-directed');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState<OSPNode | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    nodeTypes: [],
    relationshipTypes: [],
    showLabels: true,
    showProperties: false,
    minNodeSize: 5,
    maxNodeSize: 20,
    edgeOpacity: 0.6
  });

  // Refs
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<OSPNode, OSPEdge> | null>(null);

  // Layout options
  const layoutOptions = [
    { value: 'force-directed', label: 'Force Directed' },
    { value: 'hierarchical', label: 'Hierarchical' },
    { value: 'circular', label: 'Circular' },
    { value: 'grid', label: 'Grid' }
  ];

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io(process.env.NEXT_PUBLIC_OSP_GRAPH_SERVICE_URL || 'http://localhost:8001', {
      transports: ['websocket'],
      upgrade: false
    });

    newSocket.on('connect', () => {
      console.log('Connected to OSP Graph Service');
    });

    newSocket.on('graph_updated', (data: GraphVisualizationData) => {
      setGraphData(data);
      setLoading(false);
    });

    newSocket.on('node_selected', (nodeData: OSPNode) => {
      setSelectedNode(nodeData);
    });

    newSocket.on('error', (error: string) => {
      setError(error);
      setLoading(false);
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  // Initialize D3 visualization
  useEffect(() => {
    if (!graphData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const container = svg.node()?.parentElement;
    if (!container) return;

    const width = container.clientWidth;
    const height = 600;

    svg.attr('width', width).attr('height', height);

    // Create main group for zoom/pan
    const g = svg.append('g');

    // Create arrow markers for edges
    const defs = svg.append('defs');
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('xoverflow', 'visible')
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
      .attr('fill', '#666')
      .style('stroke', 'none');

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Apply filters
    const filteredData = applyFilters(graphData);

    // Create simulation based on layout
    let simulation: d3.Simulation<OSPNode, OSPEdge>;

    switch (selectedLayout) {
      case 'force-directed':
        simulation = d3.forceSimulation<OSPNode>(filteredData.nodes)
          .force('link', d3.forceLink<OSPNode, OSPEdge>(filteredData.edges)
            .id(d => d.id)
            .distance(100)
            .strength(0.1))
          .force('charge', d3.forceManyBody().strength(-300))
          .force('center', d3.forceCenter(width / 2, height / 2))
          .force('collision', d3.forceCollide().radius(d => d.size + 5));
        break;

      case 'hierarchical':
        // Simple hierarchical layout
        const levels = d3.group(filteredData.nodes, d => d.type);
        let yOffset = 0;
        simulation = d3.forceSimulation<OSPNode>(filteredData.nodes)
          .force('x', d3.forceX(width / 2).strength(0.1))
          .force('y', d3.forceY((d) => {
            const levelIndex = Array.from(levels.keys()).indexOf(d.type);
            return 100 + levelIndex * 150;
          }).strength(0.1))
          .force('collision', d3.forceCollide().radius(d => d.size + 5));
        break;

      case 'circular':
        const radius = Math.min(width, height) * 0.4;
        simulation = d3.forceSimulation<OSPNode>(filteredData.nodes)
          .force('x', d3.forceX((d, i) => width / 2 + radius * Math.cos((2 * Math.PI * i) / filteredData.nodes.length)).strength(0.1))
          .force('y', d3.forceY((d, i) => height / 2 + radius * Math.sin((2 * Math.PI * i) / filteredData.nodes.length)).strength(0.1))
          .force('collision', d3.forceCollide().radius(d => d.size + 5));
        break;

      default:
        simulation = d3.forceSimulation<OSPNode>(filteredData.nodes)
          .force('center', d3.forceCenter(width / 2, height / 2))
          .force('collision', d3.forceCollide().radius(d => d.size + 5));
    }

    simulationRef.current = simulation;

    // Create links
    const link = g.selectAll('.link')
      .data(filteredData.edges)
      .enter().append('line')
      .attr('class', 'link')
      .attr('stroke', d => d.color)
      .attr('stroke-opacity', filters.edgeOpacity)
      .attr('stroke-width', d => d.width)
      .attr('marker-end', 'url(#arrowhead)');

    // Create nodes
    const node = g.selectAll('.node')
      .data(filteredData.nodes)
      .enter().append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(d3.drag<SVGGElement, OSPNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    // Add circles for nodes
    node.append('circle')
      .attr('r', d => d.size)
      .attr('fill', d => d.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => handleNodeClick(d))
      .on('mouseover', (event, d) => showTooltip(event, d))
      .on('mouseout', hideTooltip);

    // Add labels if enabled
    if (filters.showLabels) {
      node.append('text')
        .attr('dy', d => d.size + 15)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', '#333')
        .text(d => d.label);
    }

    // Simulation update
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as OSPNode).x!)
        .attr('y1', d => (d.source as OSPNode).y!)
        .attr('x2', d => (d.target as OSPNode).x!)
        .attr('y2', d => (d.target as OSPNode).y!);

      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, OSPNode, OSPNode>, d: OSPNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, OSPNode, OSPNode>, d: OSPNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, OSPNode, OSPNode>, d: OSPNode) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Tooltip functions
    function showTooltip(event: MouseEvent, d: OSPNode) {
      const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('padding', '10px')
        .style('border-radius', '5px')
        .style('pointer-events', 'none')
        .style('font-size', '12px')
        .style('z-index', '1000');

      let content = `<strong>${d.label}</strong><br/>Type: ${d.type}<br/>Size: ${d.size}`;
      
      if (filters.showProperties && d.properties) {
        content += `<br/><br/>Properties:<br/>`;
        Object.entries(d.properties).forEach(([key, value]) => {
          content += `${key}: ${value}<br/>`;
        });
      }

      tooltip.html(content)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px');
    }

    function hideTooltip() {
      d3.selectAll('.tooltip').remove();
    }

  }, [graphData, selectedLayout, filters]);

  // Apply filters to graph data
  const applyFilters = useCallback((data: GraphVisualizationData): GraphVisualizationData => {
    let filteredNodes = data.nodes;
    let filteredEdges = data.edges;

    // Filter by node types
    if (filters.nodeTypes.length > 0) {
      filteredNodes = filteredNodes.filter(node => filters.nodeTypes.includes(node.type));
    }

    // Filter by relationship types
    if (filters.relationshipTypes.length > 0) {
      filteredEdges = filteredEdges.filter(edge => filters.relationshipTypes.includes(edge.label));
    }

    // Filter by node size
    filteredNodes = filteredNodes.filter(node => 
      node.size >= filters.minNodeSize && node.size <= filters.maxNodeSize
    );

    // Filter edges to only include those between visible nodes
    const visibleNodeIds = new Set(filteredNodes.map(node => node.id));
    filteredEdges = filteredEdges.filter(edge => 
      visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)
    );

    return {
      ...data,
      nodes: filteredNodes,
      edges: filteredEdges
    };
  }, [filters]);

  // Handle node click
  const handleNodeClick = (node: OSPNode) => {
    setSelectedNode(node);
    setSidebarOpen(true);
    
    // Notify backend about node selection
    if (socket) {
      socket.emit('select_node', { nodeId: node.id, projectId: 'default' });
    }
  };

  // Search functionality
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    if (!graphData) return;

    // Highlight matching nodes
    const svg = d3.select(svgRef.current);
    svg.selectAll('.node')
      .style('opacity', d => 
        term === '' || d.label.toLowerCase().includes(term.toLowerCase()) ? 1 : 0.3
      );
    
    svg.selectAll('.link')
      .style('opacity', d => 
        term === '' || 
        d.source.label.toLowerCase().includes(term.toLowerCase()) ||
        d.target.label.toLowerCase().includes(term.toLowerCase()) ? 
        filters.edgeOpacity : 0.1
      );
  }, [graphData, filters.edgeOpacity]);

  // Export graph as image
  const exportAsImage = () => {
    const svg = svgRef.current;
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    canvas.width = svg.clientWidth;
    canvas.height = svg.clientHeight;

    img.onload = () => {
      if (ctx) {
        ctx.drawImage(img, 0, 0);
        const link = document.createElement('a');
        link.download = 'osp-graph.png';
        link.href = canvas.toDataURL();
        link.click();
      }
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  // Center graph view
  const centerGraph = () => {
    const svg = d3.select(svgRef.current);
    const g = svg.select('g');
    
    const bounds = g.node()?.getBBox();
    if (!bounds) return;

    const fullWidth = svg.node()?.clientWidth || 800;
    const fullHeight = svg.node()?.clientHeight || 600;
    const width = bounds.width;
    const height = bounds.height;
    const midX = bounds.x + width / 2;
    const midY = bounds.y + height / 2;

    const scale = Math.min(fullWidth / width, fullHeight / height) * 0.9;
    const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];

    svg.transition()
      .duration(750)
      .call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
      );
  };

  // Load graph data
  const loadGraphData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_OSP_GRAPH_SERVICE_URL}/graph/visualization/default?layout=${selectedLayout}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to load graph data: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setGraphData(data.visualization_data);
      } else {
        throw new Error(data.message || 'Failed to load graph data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Initialize graph on component mount
  useEffect(() => {
    loadGraphData();
  }, []);

  if (loading && !graphData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="600px">
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading OSP Graph...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        <Typography variant="h6">Error Loading Graph</Typography>
        <Typography variant="body2">{error}</Typography>
        <Button variant="contained" onClick={loadGraphData} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      {/* Main toolbar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Layout</InputLabel>
              <Select
                value={selectedLayout}
                onChange={(e) => setSelectedLayout(e.target.value)}
                label="Layout"
              >
                {layoutOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={2}>
            <Tooltip title="Refresh Graph">
              <IconButton onClick={loadGraphData}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Grid>
          
          <Grid item xs={12} sm={6} md={2}>
            <Tooltip title="Center Graph">
              <IconButton onClick={centerGraph}>
                <CenterFocusStrong />
              </IconButton>
            </Tooltip>
          </Grid>
          
          <Grid item xs={12} sm={6} md={2}>
            <Tooltip title="Export as Image">
              <IconButton onClick={exportAsImage}>
                <Download />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>
      </Paper>

      {/* Graph statistics */}
      {graphData && (
        <Box sx={{ mb: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" color="primary">
                    {graphData.statistics.total_nodes}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Nodes
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" color="secondary">
                    {graphData.statistics.total_edges}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Edges
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" color="success.main">
                    {graphData.statistics.node_types.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Node Types
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" color="warning.main">
                    {graphData.statistics.relationship_types.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Edge Types
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {/* Main graph container */}
      <Card>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ position: 'relative' }}>
            <svg ref={svgRef} style={{ width: '100%', height: '600px' }} />
            
            {/* Node type legend */}
            {graphData && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 10,
                  right: 10,
                  background: 'rgba(255, 255, 255, 0.9)',
                  padding: 2,
                  borderRadius: 1,
                  maxWidth: 200
                }}
              >
                <Typography variant="subtitle2" gutterBottom>
                  Node Types
                </Typography>
                {graphData.statistics.node_types.slice(0, 5).map((type) => (
                  <Chip
                    key={type}
                    label={type}
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                    onClick={() => {
                      setFilters(prev => ({
                        ...prev,
                        nodeTypes: prev.nodeTypes.includes(type)
                          ? prev.nodeTypes.filter(t => t !== type)
                          : [...prev.nodeTypes, type]
                      }));
                    }}
                    color={filters.nodeTypes.includes(type) ? 'primary' : 'default'}
                  />
                ))}
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Properties sidebar */}
      <Drawer
        anchor="right"
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      >
        <Box sx={{ width: 300, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Node Properties
          </Typography>
          
          {selectedNode ? (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                {selectedNode.label}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Type: {selectedNode.type}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Size: {selectedNode.size}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle2" gutterBottom>
                Properties
              </Typography>
              
              {Object.entries(selectedNode.properties || {}).map(([key, value]) => (
                <Box key={key} sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {key}:
                  </Typography>
                  <Typography variant="body2">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </Typography>
                </Box>
              ))}
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Select a node to view its properties
            </Typography>
          )}
        </Box>
      </Drawer>
    </Box>
  );
};

export default OSPGraphVisualization;