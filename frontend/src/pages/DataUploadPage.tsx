import { useState, ChangeEvent, FormEvent } from 'react';
import { Box, Typography, Button, Paper, Alert, CircularProgress, List, ListItem, ListItemText, Grid } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { apiClient } from '@/services/apiClient';

export default function DataUploadPage() {
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [uploadingCsv, setUploadingCsv] = useState(false);
  const [csvResult, setCsvResult] = useState<any>(null);
  const [csvError, setCsvError] = useState<string | null>(null);

  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [pdfResult, setPdfResult] = useState<any>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const handleCsvChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setCsvFile(e.target.files[0]);
      setCsvError(null);
      setCsvResult(null);
    }
  };

  const handlePdfChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setPdfFile(e.target.files[0]);
      setPdfError(null);
      setPdfResult(null);
    }
  };

  const handleUploadCsv = async (e: FormEvent) => {
    e.preventDefault();
    if (!csvFile) return;
    setUploadingCsv(true);
    setCsvError(null);
    setCsvResult(null);
    const formData = new FormData();
    formData.append('file', csvFile);
    try {
      const response = await apiClient.uploadCSV(formData);
      setCsvResult(response.data);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      setCsvError(errorMsg && errorMsg !== '"{}"' && errorMsg !== 'undefined' ? errorMsg : err.message || 'An error occurred during upload.');
    } finally {
      setUploadingCsv(false);
    }
  };

  const handleUploadPdf = async (e: FormEvent) => {
    e.preventDefault();
    if (!pdfFile) return;
    setUploadingPdf(true);
    setPdfError(null);
    setPdfResult(null);
    const formData = new FormData();
    formData.append('file', pdfFile);
    try {
      const response = await apiClient.uploadPDF(formData);
      setPdfResult(response.data);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      setPdfError(errorMsg && errorMsg !== '"{}"' && errorMsg !== 'undefined' ? errorMsg : err.message || 'An error occurred during PDF upload.');
    } finally {
      setUploadingPdf(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 4 }}>
        Data Management
      </Typography>

      <Grid container spacing={4}>
        {/* CSV Upload */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 4, textAlign: 'center', height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Upload District Crime CSV
            </Typography>
            <Box component="form" onSubmit={handleUploadCsv} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
              <Button variant="outlined" component="label" startIcon={<CloudUploadIcon />} sx={{ px: 4, py: 2, borderStyle: 'dashed' }}>
                {csvFile ? csvFile.name : 'Select CSV File'}
                <input type="file" hidden accept=".csv" onChange={handleCsvChange} />
              </Button>
              <Button type="submit" variant="contained" disabled={!csvFile || uploadingCsv} sx={{ minWidth: 200 }}>
                {uploadingCsv ? <CircularProgress size={24} /> : 'Process CSV'}
              </Button>
            </Box>
            {csvError && <Alert severity="error" sx={{ mt: 3, textAlign: 'left' }}>{csvError}</Alert>}
            {csvResult && csvResult.success && (
              <Alert severity="success" sx={{ mt: 3, textAlign: 'left' }}>
                {csvResult.message}
                <List dense sx={{ mt: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <ListItem><ListItemText primary="Rows Read" secondary={csvResult.stats.rows_read} /></ListItem>
                  <ListItem><ListItemText primary="Rows Imported" secondary={csvResult.stats.rows_imported} /></ListItem>
                  <ListItem><ListItemText primary="Rows Skipped" secondary={csvResult.stats.rows_skipped} /></ListItem>
                  <ListItem><ListItemText primary="Districts Seen" secondary={csvResult.stats.districts_seen} /></ListItem>
                </List>
              </Alert>
            )}
          </Paper>
        </Grid>

        {/* PDF Upload */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 4, textAlign: 'center', height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Upload Intelligence PDF
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Extracts offenders and associates for Network Analysis.
            </Typography>
            <Box component="form" onSubmit={handleUploadPdf} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
              <Button variant="outlined" color="secondary" component="label" startIcon={<PictureAsPdfIcon />} sx={{ px: 4, py: 2, borderStyle: 'dashed' }}>
                {pdfFile ? pdfFile.name : 'Select PDF File'}
                <input type="file" hidden accept=".pdf" onChange={handlePdfChange} />
              </Button>
              <Button type="submit" variant="contained" color="secondary" disabled={!pdfFile || uploadingPdf} sx={{ minWidth: 200 }}>
                {uploadingPdf ? <CircularProgress size={24} /> : 'Extract Intelligence'}
              </Button>
            </Box>
            {pdfError && <Alert severity="error" sx={{ mt: 3, textAlign: 'left' }}>{pdfError}</Alert>}
            {pdfResult && pdfResult.success && (
              <Alert severity="success" sx={{ mt: 3, textAlign: 'left' }}>
                {pdfResult.message}
                <List dense sx={{ mt: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <ListItem><ListItemText primary="Offenders Found" secondary={pdfResult.data.offenders.length} /></ListItem>
                  <ListItem><ListItemText primary="Associates Found" secondary={pdfResult.data.associates.length} /></ListItem>
                </List>
                {pdfResult.data.offenders.length === 0 && (
                  <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
                    <strong>Note:</strong> OGD statistical reports do not contain individual names. Please upload CCTNS/Police Charge Sheet PDFs or rely on sample intelligence dossiers.
                  </Typography>
                )}
              </Alert>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
