import { useEffect, useState } from 'react';
import {
  Box, Grid, Paper, Typography, Skeleton, Alert, Chip, Divider,
} from '@mui/material';
import { WarningAmber, TrendingUp, Public } from '@mui/icons-material';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { apiClient } from '@/services/apiClient';
import KarnatakaChoroplethMap from '@/components/map/KarnatakaChoroplethMap';
import DisabledFeatureNotice from '@/components/common/DisabledFeatureNotice';
import YearSelector from '@/components/layout/YearSelector';
import type { KarnatakaCrimeReport } from '@/types';

export default function ExecutiveDashboard() {
  const [selectedYear, setSelectedYear] = useState<number | undefined>();
  const [report, setReport] = useState<KarnatakaCrimeReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiClient.getFullReport(selectedYear ? { year: selectedYear } : undefined)
      .then(setReport)
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load report.'))
      .finally(() => setLoading(false));
  }, [selectedYear]);

  if (error) return <Alert severity="error">{error}</Alert>;

  if (loading || !report) {
    return (
      <Grid container spacing={2.5}>
        {[1, 2, 3].map((i) => <Grid item xs={12} md={4} key={i}><Skeleton variant="rounded" height={110} /></Grid>)}
        <Grid item xs={12}><Skeleton variant="rounded" height={420} /></Grid>
      </Grid>
    );
  }

  const { executive_summary: summary } = report;
  const categoryData = (report.crime_category_breakdown.group_breakdown || []).slice(0, 8);

  return (
    <Box>

      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>{summary.headline}</Typography>
          <Typography variant="body2" color="text.secondary">Period: {summary.period}</Typography>
        </Box>
        <YearSelector selectedYear={selectedYear} onYearChange={setSelectedYear} />
      </Box>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="overline" color="text.secondary">Total IPC Crimes (Statewide)</Typography>
            <Typography variant="h4" fontWeight={700} sx={{ fontFamily: 'monospace' }}>
              {summary.total_ipc_crimes_statewide.toLocaleString('en-IN')}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="overline" color="text.secondary">Districts Analyzed</Typography>
            <Typography variant="h4" fontWeight={700} sx={{ fontFamily: 'monospace' }}>
              {summary.districts_analyzed}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="overline" color="text.secondary">Data Year</Typography>
            <Typography variant="h4" fontWeight={700} sx={{ fontFamily: 'monospace' }}>
              {summary.data_year ?? 'N/A'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ height: 420, p: 1 }}>
            <KarnatakaChoroplethMap ranking={report.district_ranking} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2.5, height: 420, overflow: 'auto' }}>
            <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 1.5 }}>Key Findings</Typography>
            {report.key_findings.map((f, i) => (
              <Typography key={i} variant="body2" sx={{ mb: 1 }}>• {f}</Typography>
            ))}
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>Recommendations</Typography>
            {report.recommendations.length > 0 ? (
              report.recommendations.map((r, i) => (
                <Chip key={i} label={r} size="small" variant="outlined"
                      sx={{ mb: 1, mr: 1, height: 'auto', py: 0.5, '& .MuiChip-label': { whiteSpace: 'normal', display: 'block' } }} />
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">No recommendations available. Please upload data.</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2.5, mb: 3, height: 340 }}>
        <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
          Crime Category Breakdown ({report.crime_category_breakdown.year})
        </Typography>
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={categoryData} layout="vertical" margin={{ left: 16 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" />
            <YAxis dataKey="crime_group" type="category" width={180} fontSize={12} />
            <Tooltip />
            <Bar dataKey="count" fill="#3FD6D0" radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Paper>

    </Box>
  );
}
