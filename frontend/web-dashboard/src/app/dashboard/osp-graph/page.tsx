"""
OSP Graph Visualization Page

Author: Cavin Otieno
Contact: cavin.otieno012@gmail.com | +254708101604
LinkedIn: https://www.linkedin.com/in/cavin-otieno-9a841260/

Dedicated page for OSP graph visualization and analysis
in the Jaseci Learning Companion frontend.
"""

'use client'

import React from 'react';
import {
  Box,
  Container,
  Typography,
  Breadcrumbs,
  Link,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert
} from '@mui/material';
import {
  Timeline,
  Home,
  Dashboard,
  Code,
  Analytics
} from '@mui/icons-material';
import OSPGraphVisualization from '@/components/osp/OSPGraphVisualization';
import OSPCodeAnalysisWidget from '@/components/osp/OSPCodeAnalysisWidget';
import { useSearchParams } from 'next/navigation';

const OSPGraphPage: React.FC = () => {
  const searchParams = useSearchParams();
  const initialCode = searchParams.get('code') || undefined;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header Section */}
      <Box mb={4}>
        {/* Breadcrumbs */}
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            href="/dashboard"
            color="inherit"
            sx={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}
          >
            <Home sx={{ mr: 0.5 }} fontSize="inherit" />
            Dashboard
          </Link>
          <Link
            href="/dashboard"
            color="inherit"
            sx={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}
          >
            <Dashboard sx={{ mr: 0.5 }} fontSize="inherit" />
            Learning Platform
          </Link>
          <Typography
            color="text.primary"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <Timeline sx={{ mr: 0.5 }} fontSize="inherit" />
            OSP Graph Analysis
          </Typography>
        </Breadcrumbs>

        {/* Page Title */}
        <Paper sx={{ p: 3, background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)', color: 'white' }}>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Timeline sx={{ fontSize: 32 }} />
            <Typography variant="h4" component="h1" fontWeight="bold">
              OSP Graph Visualization
            </Typography>
          </Box>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            Interactive Object-Subject-Predicate graph analysis for Jaseci code
          </Typography>
        </Paper>
      </Box>

      {/* Features Overview */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Code sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Code Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Parse Jaseci code into OSP graph structures automatically
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Timeline sx={{ fontSize: 48, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Graph Visualization
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Interactive force-directed, hierarchical, and circular layouts
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Analytics sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Complexity Metrics
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cyclomatic, cognitive complexity, and maintainability analysis
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 3 }}>
              <Timeline sx={{ fontSize: 48, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Pattern Detection
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Identify design patterns and anti-patterns in your code
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Code Analysis Widget */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 3, height: 'fit-content' }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <Code color="primary" />
              <Typography variant="h6">
                Jaseci Code Analysis
              </Typography>
              <Chip label="Interactive" color="primary" size="small" />
            </Box>
            <OSPCodeAnalysisWidget 
              defaultCode={initialCode}
              onAnalysisComplete={(result) => {
                console.log('Analysis completed:', result);
                // Could trigger graph refresh here
              }}
            />
          </Paper>
        </Grid>

        {/* Graph Visualization */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <Timeline color="secondary" />
              <Typography variant="h6">
                Interactive Graph Visualization
              </Typography>
              <Chip label="Real-time" color="secondary" size="small" />
            </Box>
            <OSPGraphVisualization />
          </Paper>
        </Grid>
      </Grid>

      {/* Information Section */}
      <Box mt={6}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  What is OSP Graph Analysis?
                </Typography>
                <Typography variant="body2" paragraph>
                  OSP (Object-Subject-Predicate) graph analysis transforms Jaseci code 
                  into a graph structure where:
                </Typography>
                <Box component="ul" sx={{ pl: 2 }}>
                  <li><strong>Objects</strong> represent code elements (functions, classes, variables)</li>
                  <li><strong>Subjects</strong> are the entities performing actions</li>
                  <li><strong>Predicates</strong> describe relationships between objects</li>
                </Box>
                <Typography variant="body2" paragraph sx={{ mt: 2 }}>
                  This approach enables advanced code analysis, pattern detection, 
                  and complexity assessment that traditional static analysis cannot provide.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Analysis Features
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Alert severity="info" sx={{ mb: 1 }}>
                      <strong>Cyclomatic Complexity:</strong> Measures decision points in code
                    </Alert>
                  </Grid>
                  <Grid item xs={12}>
                    <Alert severity="success" sx={{ mb: 1 }}>
                      <strong>Cognitive Complexity:</strong> Evaluates code understandability
                    </Alert>
                  </Grid>
                  <Grid item xs={12}>
                    <Alert severity="warning" sx={{ mb: 1 }}>
                      <strong>Graph Density:</strong> Indicates code coupling level
                    </Alert>
                  </Grid>
                  <Grid item xs={12}>
                    <Alert severity="error">
                      <strong>Pattern Detection:</strong> Identifies anti-patterns and smells
                    </Alert>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Quick Start Guide */}
      <Paper sx={{ p: 3, mt: 4, backgroundColor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>
          Quick Start Guide
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="flex-start" gap={2}>
              <Chip label="1" color="primary" />
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Enter Jaseci Code
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Type or paste your Jaseci code in the analysis widget on the left
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="flex-start" gap={2}>
              <Chip label="2" color="primary" />
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Run Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Click "Analyze Code" to parse and generate the OSP graph
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="flex-start" gap={2}>
              <Chip label="3" color="primary" />
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Explore Results
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  View the interactive graph and analyze the insights and recommendations
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default OSPGraphPage;