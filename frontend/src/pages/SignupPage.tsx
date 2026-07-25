import { useState, FormEvent } from 'react';
import { Box, Button, TextField, Typography, Paper, Alert, Link } from '@mui/material';
import { Shield } from '@mui/icons-material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { apiClient } from '@/services/apiClient';
import { caipPalette } from '@/theme/theme';

export default function SignupPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSignup = async (e: FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setError(null);
    setLoading(true);

    try {
      await apiClient.signup({
        full_name: formData.fullName,
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      // Redirect to login upon successful signup
      navigate('/login', { state: { message: "Account created successfully. Please sign in." } });
    } catch (err: any) {
      setError(
        err.response?.data?.detail || err.message || 'An error occurred during signup.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default', p: 3 }}>
      <Paper elevation={0} sx={{ p: { xs: 4, md: 6 }, width: '100%', maxWidth: 480, border: `1px solid ${caipPalette.hairline}`, borderRadius: 2 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Shield sx={{ color: caipPalette.signalCyan, fontSize: 48, mb: 1 }} />
          <Typography variant="h4" fontWeight={700} sx={{ mb: 1 }}>Create Account</Typography>
          <Typography variant="body2" color="text.secondary">
            Sign up for CAIP-Karnataka Intelligence
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        <Box component="form" onSubmit={handleSignup} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          <TextField
            name="fullName"
            label="Full Name"
            variant="outlined"
            fullWidth
            required
            value={formData.fullName}
            onChange={handleChange}
          />
          <TextField
            name="username"
            label="Username"
            variant="outlined"
            fullWidth
            required
            value={formData.username}
            onChange={handleChange}
          />
          <TextField
            name="email"
            label="Email Address"
            type="email"
            variant="outlined"
            fullWidth
            required
            value={formData.email}
            onChange={handleChange}
          />
          <TextField
            name="password"
            label="Password"
            type="password"
            variant="outlined"
            fullWidth
            required
            value={formData.password}
            onChange={handleChange}
          />
          <TextField
            name="confirmPassword"
            label="Confirm Password"
            type="password"
            variant="outlined"
            fullWidth
            required
            value={formData.confirmPassword}
            onChange={handleChange}
          />

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={loading}
            sx={{
              mt: 2,
              bgcolor: caipPalette.signalCyan,
              color: '#000',
              '&:hover': { bgcolor: caipPalette.signalCyan, opacity: 0.9 },
            }}
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </Button>
          
          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{' '}
              <Link component={RouterLink} to="/login" sx={{ color: caipPalette.signalCyan, textDecoration: 'none' }}>
                Sign In
              </Link>
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
