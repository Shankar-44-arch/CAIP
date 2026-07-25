import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Button, Avatar, Skeleton, Alert } from '@mui/material';
import { Person, Email, Badge, Logout } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '@/services/apiClient';
import { caipPalette } from '@/theme/theme';

export default function ProfilePage() {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.getMe()
      .then(setUser)
      .catch((err) => setError(err.message || 'Failed to load profile'))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('caip_access_token');
    window.dispatchEvent(new Event('auth_change'));
    navigate('/login');
  };

  if (loading) return <Skeleton variant="rounded" height={300} sx={{ maxWidth: 600, mx: 'auto', mt: 4 }} />;

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 3 }}>User Profile</Typography>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {user && (
        <Paper sx={{ p: 4, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 4 }}>
            <Avatar sx={{ width: 80, height: 80, bgcolor: caipPalette.signalCyan, color: '#000', fontSize: 32 }}>
              {user.full_name ? user.full_name[0].toUpperCase() : user.username[0].toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="h5" fontWeight={600}>{user.full_name || user.username}</Typography>
              <Typography variant="body1" color="text.secondary">@{user.username}</Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Email color="action" />
              <Typography variant="body1">{user.email}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Badge color="action" />
              <Typography variant="body1" sx={{ textTransform: 'capitalize' }}>
                Role: {user.role}
              </Typography>
            </Box>
          </Box>

          <Button
            variant="outlined"
            color="error"
            startIcon={<Logout />}
            onClick={handleLogout}
            fullWidth
          >
            Sign Out
          </Button>
        </Paper>
      )}
    </Box>
  );
}
