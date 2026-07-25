import { useEffect, useState } from 'react';
import {
  Box, Paper, Typography, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, Skeleton, Alert, ToggleButton, ToggleButtonGroup,
} from '@mui/material';
import { apiClient } from '@/services/apiClient';
import KarnatakaChoroplethMap from '@/components/map/KarnatakaChoroplethMap';
import YearSelector from '@/components/layout/YearSelector';
import type { DistrictRankingItem } from '@/types';

export default function DistrictRankingPage() {
  const [selectedYear, setSelectedYear] = useState<number | undefined>();
  const [ranking, setRanking] = useState<DistrictRankingItem[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [rankingBasis, setRankingBasis] = useState<string>('raw_count');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiClient.getDistrictRanking({ 
      ranking_basis: rankingBasis,
      year: selectedYear 
    })
      .then((res) => {
        if (res.success) {
          setRanking(res.data.district_ranking || []);
          // Use the basis returned by backend or the selected one
        } else {
          setError(res.warnings?.[0] || 'District ranking unavailable.');
        }
        setWarnings(res.warnings || []);
      })
      .catch(() => setError('Failed to load district ranking.'))
      .finally(() => setLoading(false));
  }, [rankingBasis, selectedYear]);

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>
            District Crime Ranking
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Statistical ranking of Karnataka districts by reported IPC crime totals.
            Toggle below to view by raw counts or per-capita rates.
          </Typography>
        </Box>
        <YearSelector selectedYear={selectedYear} onYearChange={setSelectedYear} />
      </Box>

      <Box sx={{ mb: 3 }}>
        <ToggleButtonGroup
          color="primary"
          value={rankingBasis}
          exclusive
          onChange={(e, newBasis) => { if (newBasis) setRankingBasis(newBasis); }}
          aria-label="Ranking Basis"
        >
          <ToggleButton value="raw_count">Raw Count</ToggleButton>
          <ToggleButton value="per_capita_rate">Per Capita Rate (per lakh)</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {warnings.map((w, i) => <Alert key={i} severity="warning" sx={{ mb: 1 }}>{w}</Alert>)}

      <Paper sx={{ height: 460, mb: 3, overflow: 'hidden' }}>
        {loading ? <Skeleton variant="rectangular" height="100%" /> : <KarnatakaChoroplethMap ranking={ranking} />}
      </Paper>

      <Paper sx={{ p: 2.5 }}>
        <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
          Ranking Detail ({ranking.length} districts) — basis: {rankingBasis}
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Rank</TableCell>
              <TableCell>District</TableCell>
              <TableCell align="right">Total IPC Crimes</TableCell>
              <TableCell align="right">Z-score vs State Mean</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {ranking.map((r) => (
              <TableRow key={r.district_code} hover>
                <TableCell>{r.rank}</TableCell>
                <TableCell>{r.district_name}</TableCell>
                <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                  {rankingBasis === 'per_capita_rate' 
                    ? r.crime_rate_per_lakh?.toLocaleString('en-IN', { maximumFractionDigits: 2 })
                    : r.total_ipc_crimes.toLocaleString('en-IN')}
                </TableCell>
                <TableCell align="right" sx={{ fontFamily: 'monospace' }}>{r.z_score_vs_state_mean.toFixed(2)}</TableCell>
                <TableCell>
                  {r.elevated
                    ? <Chip label="ELEVATED" size="small" color="warning" />
                    : <Chip label="Normal range" size="small" variant="outlined" />}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
