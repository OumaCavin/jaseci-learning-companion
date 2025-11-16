"""
OSP Graph Widget for Dashboard

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Main OSP Graph widget component for the dashboard that provides
overview and quick access to OSP graph functionality.
"""

'use client'

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  Skeleton,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Timeline,
  Analytics,
  TrendingUp,
  Visibility,
  PlayArrow,
  Assessment,
  Psychology,
  Speed,
  Security,
  Build,
  ExpandMore,
  Refresh,
  AutoAwesome,
  Hub
} from '@mui/icons-material';
import { useRouter } from 'next/navigation';

interface OSPMetrics {
  total_nodes: number;
  total_relationships: number;
  graph_density: number;
  node_distribution: Record<string, number>;
  relationship_distribution: Record<string, number>;
  most_connected_nodes: Array<{
    id: string;
    name: string;
    node_type: string;
    connections: number;
  }>;
  analysis_timestamp: string;
}

interface ComplexityAnalysis {
  topology: {
    node_count: number;
    edge_count: number;
    density: number;
    average_degree: number;
    connected_components: number;
  };
  complexity: {
    high_complexity_count: number;
    avg_fan_out: number;
    complexity_distribution: {
      low: number;
      medium: number;
      high: number;
    };
  };
  insights: string[];
  recommendations: string[];
}

interface OSPWidgetProps {
  projectId?: string;
  compact?: boolean;
}

const OSPGraphWidget: React.FC<OSPWidgetProps> = ({
  projectId = 'default',
  compact = false
}) => {
  const router = useRouter();
  
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<OSPMetrics | null>(null);
  const [complexityAnalysis, setComplexityAnalysis] = useState<ComplexityAnalysis | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Load OSP metrics
  const loadMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_OSP_GRAPH_SERVICE_URL}/analytics/metrics/${projectId}`
      );

      if (!response.ok) {
        throw new Error(`Failed to load metrics: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        setMetrics(data.metrics);
        setLastUpdated(new Date());
      } else {
        throw new Error(data.message || 'Failed to load metrics');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Load complexity analysis
  const loadComplexityAnalysis = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_OSP_GRAPH_SERVICE_URL}/analyze/complexity`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ project_id: projectId }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setComplexityAnalysis(data.analysis);
        }
      }
    } catch (err) {
      console.warn('Failed to load complexity analysis:', err);
    }
  };

  // Initialize data on mount
  useEffect(() => {
    loadMetrics();
    loadComplexityAnalysis();
  }, [projectId]);

  // Get complexity color
  const getComplexityColor = (density: number): 'success' | 'warning' | 'error' => {
    if (density < 0.3) return 'success';
    if (density < 0.7) return 'warning';
    return 'error';
  };

  // Get complexity label
  const getComplexityLabel = (density: number): string => {
    if (density < 0.3) return 'Loose';
    if (density < 0.7) return 'Moderate';
    return 'Tight';
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading && !metrics) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            OSP Graph Analysis
          </Typography>
          <Box>
            <Skeleton variant="rectangular" height={100} sx={{ mb: 1 }} />
            <Skeleton variant="text" />
            <Skeleton variant="text" />
            <Skeleton variant="text" />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error && !metrics) {
    return (
      <Card>
        <CardContent>
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={loadMetrics}>
                Retry
              </Button>
            }
          >
            Failed to load OSP metrics: {error}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Timeline color="primary" />
            <Typography variant="h6">
              OSP Graph Analysis
            </Typography>
          </Box>
          
          <Tooltip title="Refresh Data">
            <IconButton size="small" onClick={loadMetrics}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>

        {metrics ? (
          <Box>
            {/* Overview Metrics */}
            <Grid container spacing={2} mb={3}>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {metrics.total_nodes}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Nodes
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="secondary">
                    {metrics.total_relationships}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Edges
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                    <Typography variant="h4" color={getComplexityColor(metrics.graph_density)}>
                      {(metrics.graph_density * 100).toFixed(0)}%
                    </Typography>
                    <Chip
                      label={getComplexityLabel(metrics.graph_density)}
                      color={getComplexityColor(metrics.graph_density)}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Density
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {metrics.connected_components || 1}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Components
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            {/* Node Type Distribution */}
            <Accordion defaultExpanded={!compact}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">
                  Node Distribution
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={1}>
                  {Object.entries(metrics.node_distribution || {}).map(([type, count]) => (
                    <Grid item xs={6} sm={4} key={type}>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {type}
                        </Typography>
                        <Chip
                          label={count}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(count / metrics.total_nodes) * 100}
                        sx={{ mt: 0.5, height: 4 }}
                      />
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>

            {/* Most Connected Nodes */}
            {metrics.most_connected_nodes && metrics.most_connected_nodes.length > 0 && (
              <Accordion defaultExpanded={!compact}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle1">
                    Most Connected Nodes
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {metrics.most_connected_nodes.slice(0, 5).map((node, index) => (
                      <ListItem key={node.id}>
                        <ListItemIcon>
                          <Hub color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={node.name}
                          secondary={`${node.node_type} • ${node.connections} connections`}
                        />
                        <Chip
                          label={`#${index + 1}`}
                          size="small"
                          color="secondary"
                        />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            )}

            {/* Complexity Analysis */}
            {complexityAnalysis && (
              <Accordion defaultExpanded={!compact}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="subtitle1">
                    Complexity Insights
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          Average Degree
                        </Typography>
                        <Typography variant="h6">
                          {complexityAnalysis.topology.average_degree.toFixed(1)}
                        </Typography>
                      </Box>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          High Complexity Nodes
                        </Typography>
                        <Typography variant="h6" color="error">
                          {complexityAnalysis.complexity.high_complexity_count}
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  {complexityAnalysis.insights.length > 0 && (
                    <Box mt={2}>
                      <Typography variant="subtitle2" gutterBottom>
                        Key Insights
                      </Typography>
                      <List dense>
                        {complexityAnalysis.insights.slice(0, 3).map((insight, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <AutoAwesome color="primary" />
                            </ListItemIcon>
                            <ListItemText primary={insight} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            )}

            {/* Actions */}
            <Box mt={3} display="flex" gap={1} flexWrap="wrap">
              <Button
                variant="contained"
                size="small"
                startIcon={<Visibility />}
                onClick={() => router.push('/dashboard/osp-graph')}
              >
                View Graph
              </Button>

              <Button
                variant="outlined"
                size="small"
                startIcon={<Assessment />}
                onClick={() => router.push('/dashboard/code-analysis')}
              >
                Analyze Code
              </Button>

              <Button
                variant="outlined"
                size="small"
                startIcon={<Psychology />}
                onClick={() => loadComplexityAnalysis()}
              >
                Reanalyze
              </Button>
            </Box>

            {/* Last Updated */}
            {lastUpdated && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Last updated: {lastUpdated.toLocaleString()}
              </Typography>
            )}
          </Box>
        ) : (
          <Box textAlign="center" py={4}>
            <Timeline sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No OSP Data Available
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Start by analyzing some Jaseci code to generate OSP graphs
            </Typography>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => router.push('/dashboard/code-analysis')}
            >
              Analyze Code
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default OSPGraphWidget;