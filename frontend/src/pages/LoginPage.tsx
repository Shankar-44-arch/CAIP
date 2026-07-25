import { useState } from 'react';
import { Box, Paper, TextField, Button, Typography, Alert } from '@mui/material';
import { Shield } from '@mui/icons-material';
import { useNavigate, useLocation, Link as RouterLink } from 'react-router-dom';
import { caipPalette } from '@/theme/theme';

// BUG FIX: Use the full backend URL including port, not a relative path.
// A relative fetch('/api/v1/auth/login') would hit the Vite dev server
// (port 5173) instead of FastAPI (port 8000), causing a silent 404/CORS
// failure. VITE_API_BASE_URL is injected at build/run time via
// docker-compose environment; falls back to localhost:8000 for local
// `npm run dev` outside Docker.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(location.state?.message || null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Login failed (HTTP ${response.status})`);
      }

      const data = await response.json();
      localStorage.setItem('caip_access_token', data.access_token);
      window.dispatchEvent(new Event('auth_change'));
      navigate('/');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not reach the backend. Is it running on port 8000?'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `radial-gradient(circle at 30% 20%, rgba(63,214,208,0.08), transparent 50%), ${caipPalette.bgDeep}`,
      }}
    >
      <Paper sx={{ p: 4, width: 380, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
          <Shield sx={{ color: caipPalette.signalCyan, fontSize: 32 }} />
          <Box>
            <Typography variant="h6" fontWeight={700}>CAIP</Typography>
            <Typography variant="caption" color="text.secondary">
              Karnataka Crime Intelligence Platform
            </Typography>
          </Box>
        </Box>

        <form onSubmit={handleSubmit}>
          <TextField
            label="Username"
            fullWidth
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
          <Button type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 3 }}>
            {loading ? 'Signing in…' : 'Sign In'}
          </Button>
        </form>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
          No account?{' '}
          <RouterLink to="/signup" style={{ color: caipPalette.signalCyan, textDecoration: 'none' }}>
            Sign Up
          </RouterLink>
        </Typography>
      </Paper>
    </Box>
  );
}
