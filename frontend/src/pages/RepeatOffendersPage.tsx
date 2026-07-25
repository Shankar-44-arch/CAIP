import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Alert, Skeleton, Table, TableHead, TableRow, TableCell, TableBody, Chip } from '@mui/material';
import { apiClient } from '@/services/apiClient';

export default function RepeatOffendersPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.getOffendersData()
      .then((res) => {
        if (res.success) {
          setData(res.data);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton variant="rounded" height={400} />;

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2.5 }}>Repeat Offenders</Typography>

      {!data || data.length === 0 ? (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No intelligence data available. Please upload a Police Dossier PDF to generate networks and offender profiles.
        </Alert>
      ) : (
      <Paper sx={{ p: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Offender ID</TableCell>
              <TableCell>Name / Alias</TableCell>
              <TableCell align="right">Total Crimes</TableCell>
              <TableCell>Risk Level</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.id}</TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell align="right">{row.crimes_count}</TableCell>
                <TableCell>
                  <Chip 
                    label={row.risk_level} 
                    color={row.risk_level === 'High' ? 'error' : row.risk_level === 'Medium' ? 'warning' : 'success'} 
                    size="small" 
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
      )}
    </Box>
  );
}
