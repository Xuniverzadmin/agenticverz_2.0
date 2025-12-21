import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { Button, Input, Card, CardBody } from '@/components/common';
import { toastError, toastSuccess } from '@/components/common/Toast';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://agenticverz.com';

// Debug logging
const log = (msg: string, data?: unknown) => {
  console.log(`[AOS Login] ${msg}`, data || '');
};

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setTokens, setUser } = useAuthStore();

  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/console';

  log('LoginPage mounted', { API_BASE, from });

  const doLogin = async (key: string) => {
    log('Attempting login with key', { keyLength: key.length, API_BASE });

    if (!key.trim()) {
      toastError('Please enter an API key');
      return;
    }

    setLoading(true);
    try {
      // API_BASE is https://agenticverz.com (no /api/v1)
      const url = `${API_BASE}/api/v1/runtime/capabilities`;
      log('Fetching capabilities', { url });

      const response = await axios.get(url, {
        headers: { 'X-API-Key': key },
        timeout: 30000,
      });

      log('Capabilities response', { status: response.status, hasData: !!response.data });

      if (response.data) {
        // API key is valid
        setTokens(key, '');
        setUser({
          id: 'api-user',
          email: 'api@aos.local',
          name: 'API User',
          role: 'admin',
        });
        toastSuccess('Connected to AOS');
        log('Login successful, navigating to', from);
        navigate(from, { replace: true });
      }
    } catch (err: unknown) {
      const error = err as { message?: string; response?: { status: number } };
      log('Login error', { message: error.message, status: error.response?.status });
      console.error('Login error:', err);
      toastError('Invalid API key or server unavailable');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    log('Form submitted');
    await doLogin(apiKey);
  };

  const handleDemoLogin = async () => {
    log('Demo login clicked');
    setApiKey('test');
    // Auto-submit with demo key
    await doLogin('test');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-blue-600 rounded-xl flex items-center justify-center">
              <svg className="w-10 h-10 text-white" viewBox="0 0 32 32" fill="none">
                <path d="M8 22L16 10L24 22H8Z" fill="currentColor"/>
                <circle cx="16" cy="18" r="3" fill="#2563EB"/>
              </svg>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">
            AOS Console
          </h1>
          <p className="text-gray-400 mt-2">
            Agentic Operating System
          </p>
        </div>

        <Card>
          <CardBody>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="API Key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                autoFocus
              />

              <Button
                type="submit"
                className="w-full"
                loading={loading}
              >
                Connect
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white dark:bg-gray-800 text-gray-500">
                    or
                  </span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={handleDemoLogin}
              >
                Use Demo Key
              </Button>
            </form>

            <div className="mt-6 p-4 bg-gray-700/50 rounded-lg">
              <h3 className="text-sm font-medium text-white mb-2">
                Test Credentials
              </h3>
              <p className="text-xs text-gray-400">
                API Key: <code className="bg-gray-600 px-1 rounded">test</code>
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Backend: {API_BASE}
              </p>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
