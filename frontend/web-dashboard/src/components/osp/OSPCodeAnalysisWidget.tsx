"""
OSP Code Analysis Widget

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Interactive OSP code analysis interface component for analyzing
Jaseci code and generating OSP graphs in real-time.
"""

'use client'

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Paper,
  Tooltip,
  IconButton,
  Divider,
  CircularProgress,
  Fab
} from '@mui/material';
import {
  PlayArrow,
  Timeline,
  Assessment,
  Visibility,
  ExpandMore,
  Code,
  Analytics,
  TrendingUp,
  Security,
  Speed,
  Build,
  FindReplace,
  Refresh,
  Download,
  Upload
} from '@mui/icons-material';
import { Monaco } from '@monaco-editor/react';

interface AnalysisResult {
  analysis_type: string;
  project_id: string;
  results: {
    osp_graph: {
      nodes: Array<{
        id: string;
        node_type: string;
        name: string;
        properties: Record<string, any>;
      }>;
      relationships: Array<{
        from_node: string;
        to_node: string;
        relationship_type: string;
        properties: Record<string, any>;
      }>;
    };
    complexity_metrics: {
      cyclomatic_complexity: number;
      cognitive_complexity: number;
      nesting_depth: number;
      function_count: number;
      class_count: number;
      line_count: number;
      maintainability_index: number;
    };
    element_counts: {
      nodes: number;
      relationships: number;
      node_types: number;
      relationship_types: number;
    };
  };
  metrics: {
    nodes_analyzed: number;
    relationships_analyzed: number;
    code_lines: number;
    parsing_time: number;
  };
  insights: string[];
  recommendations: string[];
  execution_time: number;
}

interface CodeAnalysisWidgetProps {
  onAnalysisComplete?: (result: AnalysisResult) => void;
  defaultCode?: string;
}

const OSPCodeAnalysisWidget: React.FC<CodeAnalysisWidgetProps> = ({
  onAnalysisComplete,
  defaultCode = `walker main {
  # Initialize variables
  can print, std.out;
  
  # Define a function
  can calculate_sum(a, b) {
    return a + b;
  }
  
  # Main execution
  print("Starting Jaseci program");
  
  # Call the function
  result = calculate_sum(10, 20);
  print("Sum is: " + result);
  
  # Conditional logic
  if (result > 15) {
    print("Result is greater than 15");
  } else {
    print("Result is not greater than 15");
  }
  
  # Report the result
  report result;
}`
}) => {
  // State management
  const [code, setCode] = useState(defaultCode);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisStage, setAnalysisStage] = useState('');
  const [selectedInsight, setSelectedInsight] = useState<string | null>(null);

  // Analysis stages
  const analysisStages = [
    { stage: 'Parsing Jaseci Code', progress: 20 },
    { stage: 'Generating AST', progress: 40 },
    { stage: 'Creating OSP Nodes', progress: 60 },
    { stage: 'Building Relationships', progress: 80 },
    { stage: 'Analyzing Complexity', progress: 100 }
  ];

  // Handle code analysis
  const handleAnalyze = async () => {
    if (!code.trim()) {
      setError('Please enter some Jaseci code to analyze');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysisProgress(0);
    setAnalysisStage('Starting analysis...');
    setAnalysisResult(null);

    try {
      // Simulate progressive analysis stages
      for (const { stage, progress } of analysisStages) {
        setAnalysisStage(stage);
        setAnalysisProgress(progress);
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // Make API call to OSP Graph Service
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_OSP_GRAPH_SERVICE_URL}/analyze/jaseci`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code: code,
            filename: 'analysis.jac',
            project_id: 'default'
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        setAnalysisResult(data.analysis);
        onAnalysisComplete?.(data.analysis);
      } else {
        throw new Error(data.message || 'Analysis failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setAnalyzing(false);
      setAnalysisProgress(0);
      setAnalysisStage('');
    }
  };

  // Handle code example loading
  const loadExample = (exampleType: string) => {
    const examples: Record<string, string> = {
      simple: `walker simple_walker {
  can print;
  
  print("Hello from Jaseci!");
  report "Analysis complete";
}`,

      complex: `node Person {
    can talk, walk;
    has name, age;
    
    can greet(other_person) {
        print("Hello " + other_person.name);
    }
}

walker social_network {
    can visit, spawn;
    
    # Create a simple social network
    p1 = spawn node Person;
    p1.name = "Alice";
    p1.age = 25;
    
    p2 = spawn node Person;
    p2.name = "Bob";
    p2.age = 30;
    
    # Visit and interact
    visit(p1);
    p1.greet(p2);
    
    report "Network created";
}`,

      graph: `walker graph_traversal {
    can visit, spawn, take;
    
    has current_node;
    has visited_nodes;
    
    # Create a graph structure
    node1 = spawn node {};
    node2 = spawn node {};
    node3 = spawn node {};
    
    # Connect nodes
    spawn edge {from: node1, to: node2};
    spawn edge {from: node2, to: node3};
    
    # Traverse the graph
    visit(node1);
    
    # DFS traversal
    for (edge in node1.out) {
        if (!(edge.to in visited_nodes)) {
            visited_nodes.add(edge.to);
            visit(edge.to);
        }
    }
    
    report visited_nodes;
}`
    };

    setCode(examples[exampleType] || examples.simple);
  };

  // Load sample code on component mount
  useEffect(() => {
    if (defaultCode && !code) {
      setCode(defaultCode);
    }
  }, [defaultCode]);

  // Get complexity color
  const getComplexityColor = (complexity: number): 'success' | 'warning' | 'error' => {
    if (complexity < 5) return 'success';
    if (complexity < 10) return 'warning';
    return 'error';
  };

  // Get complexity label
  const getComplexityLabel = (complexity: number): string => {
    if (complexity < 5) return 'Low';
    if (complexity < 10) return 'Medium';
    return 'High';
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Code Input Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6" gutterBottom>
                  Jaseci Code Editor
                </Typography>
                <Box>
                  <Tooltip title="Load Simple Example">
                    <IconButton
                      size="small"
                      onClick={() => loadExample('simple')}
                      sx={{ mr: 1 }}
                    >
                      <Code />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Load Complex Example">
                    <IconButton
                      size="small"
                      onClick={() => loadExample('complex')}
                      sx={{ mr: 1 }}
                    >
                      <Analytics />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Load Graph Example">
                    <IconButton
                      size="small"
                      onClick={() => loadExample('graph')}
                    >
                      <Timeline />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              <TextField
                fullWidth
                multiline
                rows={20}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Enter your Jaseci code here..."
                variant="outlined"
                sx={{ mb: 2 }}
              />

              {/* Analysis Controls */}
              <Box display="flex" gap={2} alignItems="center">
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={handleAnalyze}
                  disabled={analyzing || !code.trim()}
                  size="large"
                >
                  {analyzing ? 'Analyzing...' : 'Analyze Code'}
                </Button>

                <Button
                  variant="outlined"
                  onClick={() => setCode('')}
                  disabled={analyzing}
                >
                  Clear
                </Button>
              </Box>

              {/* Analysis Progress */}
              {analyzing && (
                <Box mt={3}>
                  <Typography variant="body2" gutterBottom>
                    {analysisStage}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={analysisProgress}
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    {analysisProgress}% complete
                  </Typography>
                </Box>
              )}

              {/* Error Display */}
              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Results Section */}
        <Grid item xs={12} md={6}>
          {analysisResult && (
            <Box>
              {/* Summary Card */}
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Analysis Summary
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {analysisResult.results.element_counts.nodes}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          OSP Nodes
                        </Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="secondary">
                          {analysisResult.results.element_counts.relationships}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Relationships
                        </Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={12}>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        Analysis completed in {analysisResult.execution_time.toFixed(2)}s
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Complexity Metrics */}
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Complexity Metrics
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          Cyclomatic Complexity
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="h6">
                            {analysisResult.results.complexity_metrics.cyclomatic_complexity.toFixed(1)}
                          </Typography>
                          <Chip
                            label={getComplexityLabel(analysisResult.results.complexity_metrics.cyclomatic_complexity)}
                            color={getComplexityColor(analysisResult.results.complexity_metrics.cyclomatic_complexity)}
                            size="small"
                          />
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(analysisResult.results.complexity_metrics.cyclomatic_complexity * 10, 100)}
                          color={getComplexityColor(analysisResult.results.complexity_metrics.cyclomatic_complexity)}
                          sx={{ mt: 1 }}
                        />
                      </Box>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          Cognitive Complexity
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="h6">
                            {analysisResult.results.complexity_metrics.cognitive_complexity.toFixed(1)}
                          </Typography>
                          <Chip
                            label={getComplexityLabel(analysisResult.results.complexity_metrics.cognitive_complexity)}
                            color={getComplexityColor(analysisResult.results.complexity_metrics.cognitive_complexity)}
                            size="small"
                          />
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(analysisResult.results.complexity_metrics.cognitive_complexity * 10, 100)}
                          color={getComplexityColor(analysisResult.results.complexity_metrics.cognitive_complexity)}
                          sx={{ mt: 1 }}
                        />
                      </Box>
                    </Grid>

                    <Grid item xs={12}>
                      <Divider sx={{ my: 2 }} />
                    </Grid>

                    <Grid item xs={12}>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Nesting Depth
                          </Typography>
                          <Typography variant="h6">
                            {analysisResult.results.complexity_metrics.nesting_depth}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Maintainability Index
                          </Typography>
                          <Typography variant="h6">
                            {analysisResult.results.complexity_metrics.maintainability_index.toFixed(1)}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Insights */}
              {analysisResult.insights.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Insights
                    </Typography>
                    <List dense>
                      {analysisResult.insights.map((insight, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <TrendingUp color="primary" />
                          </ListItemIcon>
                          <ListItemText
                            primary={insight}
                            onClick={() => setSelectedInsight(
                              selectedInsight === insight ? null : insight
                            )}
                            sx={{ cursor: 'pointer' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Recommendations */}
              {analysisResult.recommendations.length > 0 && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Recommendations
                    </Typography>
                    <List dense>
                      {analysisResult.recommendations.map((recommendation, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <Build color="secondary" />
                          </ListItemIcon>
                          <ListItemText primary={recommendation} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}

              {/* Detailed Analysis */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">
                    Detailed Analysis
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" paragraph>
                    <strong>Nodes by Type:</strong>
                  </Typography>
                  <List dense>
                    {Object.entries(
                      analysisResult.results.osp_graph.nodes.reduce((acc, node) => {
                        acc[node.node_type] = (acc[node.node_type] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([type, count]) => (
                      <ListItem key={type}>
                        <ListItemText
                          primary={`${type}: ${count} nodes`}
                        />
                      </ListItem>
                    ))}
                  </List>

                  <Typography variant="body2" paragraph sx={{ mt: 2 }}>
                    <strong>Relationships by Type:</strong>
                  </Typography>
                  <List dense>
                    {Object.entries(
                      analysisResult.results.osp_graph.relationships.reduce((acc, rel) => {
                        acc[rel.relationship_type] = (acc[rel.relationship_type] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([type, count]) => (
                      <ListItem key={type}>
                        <ListItemText
                          primary={`${type}: ${count} relationships`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>

              {/* Action Buttons */}
              <Box mt={2} display="flex" gap={2}>
                <Button
                  variant="outlined"
                  startIcon={<Visibility />}
                  onClick={() => {
                    // Open graph visualization
                    window.open('/dashboard/osp-graph', '_blank');
                  }}
                >
                  View Graph
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => {
                    const dataStr = JSON.stringify(analysisResult, null, 2);
                    const dataBlob = new Blob([dataStr], { type: 'application/json' });
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = 'osp-analysis-result.json';
                    link.click();
                  }}
                >
                  Export Results
                </Button>
              </Box>
            </Box>
          )}

          {/* Empty State */}
          {!analysisResult && !analyzing && (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <Analytics sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Ready for Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Enter your Jaseci code and click "Analyze Code" to generate an OSP graph
                  and get detailed code analysis insights.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default OSPCodeAnalysisWidget;