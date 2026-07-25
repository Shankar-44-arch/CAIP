import { useEffect, useState, useRef, useCallback } from 'react';
import { Box, Typography, Paper, Alert, Skeleton } from '@mui/material';
import ForceGraph2D from 'react-force-graph-2d';
import { apiClient } from '@/services/apiClient';
import { caipPalette } from '@/theme/theme';

export default function NetworkAnalysisPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    apiClient.getNetworkData()
      .then((res) => {
        if (res.success) {
          setData(res.data);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: 600
      });
    }
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: 600
        });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [loading, data]);

  const fgRef = useRef<any>(null);

  useEffect(() => {
    if (fgRef.current) {
      // Increase repulsion to spread out the nodes
      fgRef.current.d3Force('charge').strength(-400);
      fgRef.current.d3Force('link').distance(60);
    }
  }, [data]);

  const getNodeColor = (node: any) => {
    if (node.risk_level === 'High') return caipPalette.riskCritical;
    if (node.risk_level === 'Medium') return caipPalette.riskHigh;
    return caipPalette.riskLow;
  };

  const drawNodeCanvas = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.name || node.label || `Node ${node.id}`;
    const fontSize = 12/globalScale;
    ctx.font = `${fontSize}px Sans-Serif`;
    const textWidth = ctx.measureText(label).width;
    const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = getNodeColor(node);
    ctx.fillText(label, node.x, node.y);

    node.__bckgDimensions = bckgDimensions;
  }, []);

  if (loading) return <Skeleton variant="rounded" height={600} />;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2.5 }}>Criminal Network Analysis</Typography>

      {!data || !data.nodes || data.nodes.length === 0 ? (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No intelligence data available. Please upload a Police Dossier PDF to generate networks and offender profiles.
        </Alert>
      ) : (
        <Paper sx={{ p: 3, minHeight: 650 }} ref={containerRef}>
          <Typography variant="h6" gutterBottom>Network Visualization</Typography>
          <Box sx={{ border: `1px solid ${caipPalette.hairline}`, borderRadius: 2, overflow: 'hidden' }}>
            <ForceGraph2D
              ref={fgRef}
              width={dimensions.width - 48} // Padding adjustments
              height={dimensions.height}
              graphData={data}
              nodeLabel={(n: any) => n.name || n.label || n.id}
              nodeColor={getNodeColor}
              nodeCanvasObject={drawNodeCanvas}
              linkColor={() => caipPalette.hairline}
              linkWidth={2}
              backgroundColor={caipPalette.bgDeep}
            />
          </Box>
        </Paper>
      )}
    </Box>
  );
}
