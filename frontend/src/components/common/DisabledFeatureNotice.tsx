import { Box, Typography, Chip } from '@mui/material';
import { InfoOutlined } from '@mui/icons-material';

interface DisabledFeatureNoticeProps {
  featureName: string;
  reason: string;
}

/**
 * Renders wherever a feature (Network Analysis, Repeat Offender
 * Tracking, Anomaly Detection) is disabled due to insufficient public
 * data. This component exists specifically so the platform NEVER
 * shows an empty/blank section without explanation, and NEVER shows
 * fabricated content in its place.
 */
export default function DisabledFeatureNotice({ featureName, reason }: DisabledFeatureNoticeProps) {
  return (
    <Box
      sx={{
        border: '1px dashed #4B5563',
        borderRadius: 2,
        p: 3,
        textAlign: 'center',
        bgcolor: 'rgba(75,85,99,0.08)',
      }}
    >
      <InfoOutlined sx={{ color: '#9CA3AF', fontSize: 32, mb: 1 }} />
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        {featureName}
      </Typography>
      <Chip label="Awaiting live police data integration" size="small"
            sx={{ mb: 1.5, bgcolor: 'rgba(217,119,6,0.15)', color: '#D97706' }} />
      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 480, mx: 'auto' }}>
        {reason}
      </Typography>
    </Box>
  );
}
