import { useState, useEffect } from 'react';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { toastError, toastSuccess } from '@/components/common/Toast';
import { getPostAuthRoute, ONBOARDING_ROUTES } from '@/routing';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '';

// OAuth provider icons
const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

const MicrosoftIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 21 21">
    <rect x="1" y="1" width="9" height="9" fill="#F25022"/>
    <rect x="11" y="1" width="9" height="9" fill="#7FBA00"/>
    <rect x="1" y="11" width="9" height="9" fill="#00A4EF"/>
    <rect x="11" y="11" width="9" height="9" fill="#FFB900"/>
  </svg>
);

const EmailIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { setTokens, setUser, setTenant, isAuthenticated, onboardingComplete } = useAuthStore();

  const [showEmailForm, setShowEmailForm] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [usePassword, setUsePassword] = useState(true); // Default to password for dev convenience

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || ONBOARDING_ROUTES.connect;

  // Handle OAuth callback tokens from URL
  useEffect(() => {
    const token = searchParams.get('token');
    const refresh = searchParams.get('refresh_token');
    const error = searchParams.get('error');

    if (error) {
      toastError(decodeURIComponent(error));
      return;
    }

    if (token && refresh) {
      setTokens(token, refresh);
      // Fetch user info
      fetchUserInfo(token);
    }
  }, [searchParams]);

  // Redirect if already authenticated
  // PIN-352: Environment-aware routing via routing authority
  useEffect(() => {
    if (isAuthenticated) {
      navigate(getPostAuthRoute(onboardingComplete), { replace: true });
    }
  }, [isAuthenticated, onboardingComplete, navigate]);

  // Countdown timer for OTP resend
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const fetchUserInfo = async (token: string) => {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const user = response.data;
      setUser({
        id: user.id,
        email: user.email,
        name: user.name || user.email.split('@')[0],
        role: 'admin',
        oauth_provider: user.oauth_provider,
        email_verified: user.email_verified,
      });
      if (user.default_tenant_id) {
        setTenant(user.default_tenant_id);
      }
      toastSuccess('Welcome to Agenticverz!');
      navigate(ONBOARDING_ROUTES.connect, { replace: true });
    } catch (err) {
      console.error('Failed to fetch user info:', err);
      toastError('Failed to load user profile');
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/v1/auth/login/google`);
      if (response.data.authorization_url) {
        window.location.href = response.data.authorization_url;
      }
    } catch (err) {
      console.error('Google login error:', err);
      toastError('Failed to initiate Google login');
      setLoading(false);
    }
  };

  const handleAzureLogin = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/v1/auth/login/azure`);
      if (response.data.authorization_url) {
        window.location.href = response.data.authorization_url;
      }
    } catch (err) {
      console.error('Azure login error:', err);
      toastError('Failed to initiate Microsoft login');
      setLoading(false);
    }
  };

  const handleSendOtp = async () => {
    if (!email.trim() || !email.includes('@')) {
      toastError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_BASE}/api/v1/auth/signup/email`, { email });
      setOtpSent(true);
      setCountdown(60);
      toastSuccess('Verification code sent to your email');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toastError(error.response?.data?.detail || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otp.trim() || otp.length !== 6) {
      toastError('Please enter the 6-digit code');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/v1/auth/verify/email`, {
        email,
        otp
      });
      const { access_token, refresh_token, user } = response.data;
      setTokens(access_token, refresh_token);
      setUser({
        id: user.id,
        email: user.email,
        name: user.name || user.email.split('@')[0],
        role: 'admin',
        oauth_provider: 'email',
        email_verified: true,
      });
      if (user.default_tenant_id) {
        setTenant(user.default_tenant_id);
      }
      toastSuccess('Email verified! Welcome to Agenticverz');
      navigate(ONBOARDING_ROUTES.connect, { replace: true });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      toastError(error.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async () => {
    if (!email.trim() || !email.includes('@')) {
      toastError('Please enter a valid email address');
      return;
    }
    if (!password.trim()) {
      toastError('Please enter your password');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/v1/auth/login/password`, {
        email,
        password
      });
      const { access_token, refresh_token, user } = response.data;
      setTokens(access_token, refresh_token);
      setUser({
        id: user.id,
        email: user.email,
        name: user.name || user.email.split('@')[0],
        role: 'admin',
        oauth_provider: 'password',
        email_verified: true,
      });
      if (user.default_tenant_id) {
        setTenant(user.default_tenant_id);
      }
      toastSuccess('Welcome to Agenticverz!');
      navigate(ONBOARDING_ROUTES.connect, { replace: true });
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      const detail = error.response?.data?.detail;
      // AUTH_DESIGN.md: Password login removed. All human auth via Clerk.
      // This handler is legacy - entire page should be replaced with Clerk components.
      if (detail?.includes('Password login is not enabled')) {
        toastError('Password login not available. Please use Clerk authentication.');
        setUsePassword(false);
      } else {
        toastError(detail || 'Authentication failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-10 h-10 text-white" viewBox="0 0 32 32" fill="none">
                <path d="M8 22L16 10L24 22H8Z" fill="currentColor"/>
                <circle cx="16" cy="18" r="3" fill="rgba(255,255,255,0.3)"/>
              </svg>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Sign in to Agenticverz
          </h1>
          <p className="text-slate-400 mt-2">
            AI Agent Governance Platform
          </p>
        </div>

        {/* Auth Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          {!showEmailForm ? (
            <div className="space-y-3">
              {/* Google Button */}
              <button
                onClick={handleGoogleLogin}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-white hover:bg-gray-50 text-gray-700 font-medium rounded-xl transition-colors disabled:opacity-50"
              >
                <GoogleIcon />
                Continue with Google
              </button>

              {/* Microsoft Button */}
              <button
                onClick={handleAzureLogin}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors border border-slate-700 disabled:opacity-50"
              >
                <MicrosoftIcon />
                Continue with Microsoft
              </button>

              {/* Divider */}
              <div className="relative py-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-700" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-3 bg-slate-900 text-slate-500">or</span>
                </div>
              </div>

              {/* Email Button */}
              <button
                onClick={() => setShowEmailForm(true)}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors border border-slate-700 disabled:opacity-50"
              >
                <EmailIcon />
                Continue with Email
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Back button */}
              <button
                onClick={() => {
                  setShowEmailForm(false);
                  setOtpSent(false);
                  setOtp('');
                  setPassword('');
                }}
                className="text-slate-400 hover:text-white text-sm flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back
              </button>

              {usePassword && !otpSent ? (
                /* Password Login Form (browser can save credentials) */
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Email address
                    </label>
                    <input
                      type="email"
                      name="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@company.com"
                      autoFocus
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Password
                    </label>
                    <input
                      type="password"
                      name="password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter password"
                      onKeyDown={(e) => e.key === 'Enter' && handlePasswordLogin()}
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    onClick={handlePasswordLogin}
                    disabled={loading || !email.trim() || !password.trim()}
                    className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Signing in...' : 'Sign in'}
                  </button>
                  <button
                    onClick={() => setUsePassword(false)}
                    className="w-full text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    Use email verification code instead
                  </button>
                </>
              ) : !otpSent ? (
                /* OTP Request Form */
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Email address
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@company.com"
                      autoFocus
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    onClick={handleSendOtp}
                    disabled={loading || !email.trim()}
                    className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Sending...' : 'Send verification code'}
                  </button>
                  <button
                    onClick={() => setUsePassword(true)}
                    className="w-full text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    Use password instead
                  </button>
                </>
              ) : (
                /* OTP Verification Form */
                <>
                  <div className="text-center mb-4">
                    <p className="text-slate-300">
                      We sent a 6-digit code to
                    </p>
                    <p className="text-white font-medium">{email}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Verification code
                    </label>
                    <input
                      type="text"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder="000000"
                      autoFocus
                      maxLength={6}
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white text-center text-2xl tracking-widest font-mono placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <button
                    onClick={handleVerifyOtp}
                    disabled={loading || otp.length !== 6}
                    className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Verifying...' : 'Verify & Continue'}
                  </button>
                  <button
                    onClick={handleSendOtp}
                    disabled={loading || countdown > 0}
                    className="w-full text-sm text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                  >
                    {countdown > 0 ? `Resend code in ${countdown}s` : 'Resend code'}
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-slate-500 text-sm mt-6">
          By continuing, you agree to our{' '}
          <a href="#" className="text-blue-400 hover:text-blue-300">Terms of Service</a>
          {' '}and{' '}
          <a href="#" className="text-blue-400 hover:text-blue-300">Privacy Policy</a>
        </p>
      </div>
    </div>
  );
}
