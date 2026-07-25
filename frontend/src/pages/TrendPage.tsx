import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Alert, Skeleton, Select, MenuItem, FormControl, InputLabel, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiClient } from '@/services/apiClient';

export default function TrendPage() {
  const [data, setData] = useState<any>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');

  useEffect(() => {
    apiClient.getTrend()
      .then((res) => {
        setData(res.data);
        setWarnings(res.warnings || []);
        if (res.data?.predictions && res.data.predictions.length > 0) {
          setSelectedDistrict(res.data.predictions[0].district_code);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton variant="rounded" height={400} />;

  const isPrediction = data?.is_prediction === true;

  const currentPrediction = data?.predictions?.find((p: any) => p.district_code === selectedDistrict);
  
  // Format data for Recharts, separating historical and predicted lines if needed
  // Alternatively, just one line with different styles or a reference line.
  let chartData: any[] = [];
  if (currentPrediction) {
    chartData = currentPrediction.trend;
  }

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 1 }}>
        District Crime Trend
      </Typography>

      {isPrediction && (
        <Alert severity="success" sx={{ mb: 2 }}>
          ML Forecast Active (Linear Regression). Forecasting horizon: {data.forecast_horizon} years.
        </Alert>
      )}

      {warnings.map((w, i) => <Alert key={i} severity="info" sx={{ mb: 1 }}>{w}</Alert>)}

      {isPrediction && data?.predictions && (
        <Paper sx={{ p: 2.5, mb: 3 }}>
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Select District</InputLabel>
            <Select
              value={selectedDistrict}
              label="Select District"
              onChange={(e) => setSelectedDistrict(e.target.value)}
            >
              {data.predictions.map((p: any) => (
                <MenuItem key={p.district_code} value={p.district_code}>
                  {p.district_name} ({p.district_code})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {currentPrediction && (
            <Box sx={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(label) => `Year: ${label}`}
                    formatter={(value: any, name: any, props: any) => {
                      return [value, props.payload.is_prediction ? 'Predicted Crimes' : 'Actual Crimes'];
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#3fb68a" 
                    activeDot={{ r: 8 }} 
                    name="Crimes"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
                Note: Linear Regression Model Coefficient: {currentPrediction.model_coefficient}
              </Typography>
            </Box>
          )}
        </Paper>
      )}

      {!isPrediction && data?.district_relative_burden && (
        <Paper sx={{ p: 2.5 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>District</TableCell>
                <TableCell align="right">Total IPC Crimes ({data.year_analyzed})</TableCell>
                <TableCell align="right">Relative to State Mean</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.district_relative_burden.map((r: any) => (
                <TableRow key={r.district_code} hover>
                  <TableCell>{r.district_name}</TableCell>
                  <TableCell align="right" sx={{ fontFamily: 'monospace' }}>{r.total_ipc_crimes}</TableCell>
                  <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                    {r.relative_to_state_mean !== null ? `${r.relative_to_state_mean}×` : 'N/A'}
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
