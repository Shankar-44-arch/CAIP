import { useEffect, useState } from 'react';
import { Select, MenuItem, FormControl, InputLabel, CircularProgress, SelectChangeEvent } from '@mui/material';
import { apiClient } from '@/services/apiClient';

interface YearSelectorProps {
  selectedYear: number | undefined;
  onYearChange: (year: number) => void;
}

export default function YearSelector({ selectedYear, onYearChange }: YearSelectorProps) {
  const [years, setYears] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.listAvailableYears().then((res) => {
      const available = res.years_available.sort((a, b) => b - a);
      setYears(available);
      if (available.length > 0 && !selectedYear) {
        onYearChange(available[0]);
      }
      setLoading(false);
    }).catch(console.error);
  }, []);

  const handleChange = (event: SelectChangeEvent<number>) => {
    onYearChange(Number(event.target.value));
  };

  if (loading) return <CircularProgress size={24} />;
  
  if (years.length === 0) return null;

  return (
    <FormControl size="small" sx={{ minWidth: 120 }}>
      <InputLabel id="year-select-label">Year</InputLabel>
      <Select
        labelId="year-select-label"
        value={selectedYear || ''}
        label="Year"
        onChange={handleChange}
      >
        {years.map((y) => (
          <MenuItem key={y} value={y}>{y}</MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
