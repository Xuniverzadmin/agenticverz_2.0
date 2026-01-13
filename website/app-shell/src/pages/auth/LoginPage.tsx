/**
 * LoginPage - Custom UI with Clerk Headless Hooks
 *
 * RULE-AUTH-UI-001: All human authentication via Clerk
 * - Backend never sees passwords
 * - Backend only verifies JWT tokens
 * - No custom login endpoints
 * - Zero Clerk branding (headless mode)
 *
 * Reference: PIN-407, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */

import { useState, FormEvent } from 'react';
import { useSignIn, useAuth } from '@clerk/clerk-react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';

type LoginStep = 'credentials' | 'email_code';

export default function LoginPage() {
  const navigate = useNavigate();
  const { signIn, setActive, isLoaded } = useSignIn();
  const { isSignedIn } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(true); // Default to visible
  const [step, setStep] = useState<LoginStep>('credentials');

  const environment = import.meta.env.VITE_ENVIRONMENT || 'production';
  const isPreflight = import.meta.env.VITE_PREFLIGHT_MODE === 'true';
  const routePrefix = isPreflight ? '/precus' : '/cus';

  // Redirect if already signed in
  if (isSignedIn) {
    navigate(`${routePrefix}/overview`);
    return null;
  }

  const handleCredentialsSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!isLoaded || !signIn) {
      setError('Authentication service not ready');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const result = await signIn.create({
        identifier: email,
        password,
      });

      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId });
        navigate(`${routePrefix}/overview`);
      } else if (result.status === 'needs_second_factor') {
        // Check what second factor strategies are available
        const secondFactors = result.supportedSecondFactors;
        console.log('Second factor required. Available strategies:', secondFactors);

        // Look for email_code strategy
        const emailCodeStrategy = secondFactors?.find(
          (f: { strategy: string }) => f.strategy === 'email_code'
        );

        if (emailCodeStrategy) {
          // Trigger sending the verification email
          await signIn.prepareSecondFactor({
            strategy: 'email_code',
          });
          setStep('email_code');
        } else {
          setError('No supported verification method available. Please contact support.');
        }
      } else {
        console.log('Sign-in requires additional steps:', result.status);
        setError(`Additional verification required: ${result.status}`);
      }
    } catch (err: unknown) {
      const clerkError = err as { errors?: Array<{ message: string }> };
      if (clerkError.errors && clerkError.errors.length > 0) {
        setError(clerkError.errors[0].message);
      } else {
        setError('Sign in failed. Please check your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailCodeSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!isLoaded || !signIn) {
      setError('Authentication service not ready');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const result = await signIn.attemptSecondFactor({
        strategy: 'email_code',
        code: verificationCode,
      });

      if (result.status === 'complete') {
        await setActive({ session: result.createdSessionId });
        navigate(`${routePrefix}/overview`);
      } else {
        setError(`Unexpected status: ${result.status}`);
      }
    } catch (err: unknown) {
      const clerkError = err as { errors?: Array<{ message: string }> };
      if (clerkError.errors && clerkError.errors.length > 0) {
        setError(clerkError.errors[0].message);
      } else {
        setError('Invalid verification code. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const resendCode = async () => {
    if (!isLoaded || !signIn) return;

    setIsLoading(true);
    setError('');

    try {
      await signIn.prepareSecondFactor({
        strategy: 'email_code',
      });
      setError(''); // Clear any previous error
      alert('Verification code sent! Check your email.');
    } catch (err: unknown) {
      const clerkError = err as { errors?: Array<{ message: string }> };
      if (clerkError.errors && clerkError.errors.length > 0) {
        setError(clerkError.errors[0].message);
      } else {
        setError('Failed to resend code. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h1 className="text-center text-3xl font-bold text-white">
          Agenticverz AOS
        </h1>
        <p className="mt-2 text-center text-sm text-gray-400">
          {isPreflight ? 'Preflight Console' : 'Customer Console'}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-700">
          {step === 'credentials' ? (
            <form onSubmit={handleCredentialsSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded text-sm">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-300">
                  Password
                </label>
                <div className="mt-1 relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="block w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-300"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading || !isLoaded}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Signing in...' : 'Sign in'}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleEmailCodeSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded text-sm">
                  {error}
                </div>
              )}

              <div className="text-center mb-4">
                <p className="text-gray-300 text-sm">
                  We sent a verification code to
                </p>
                <p className="text-white font-medium">{email}</p>
              </div>

              <div>
                <label htmlFor="code" className="block text-sm font-medium text-gray-300">
                  Verification Code
                </label>
                <input
                  id="code"
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  autoComplete="one-time-code"
                  placeholder="000000"
                  className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 text-white text-center text-2xl tracking-widest focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  maxLength={6}
                />
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading || !isLoaded || verificationCode.length !== 6}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Verifying...' : 'Verify'}
                </button>
              </div>

              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={resendCode}
                  disabled={isLoading}
                  className="text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50"
                >
                  Resend code
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setStep('credentials');
                    setVerificationCode('');
                    setError('');
                  }}
                  className="text-sm text-gray-400 hover:text-gray-300"
                >
                  ← Back to login
                </button>
              </div>
            </form>
          )}

          {step === 'credentials' && (
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-600" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-gray-800 text-gray-400">
                    Don't have an account?
                  </span>
                </div>
              </div>

              <div className="mt-6">
                <Link
                  to="/signup"
                  className="w-full flex justify-center py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-blue-500"
                >
                  Create account
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 text-center text-xs text-gray-500">
        <p>Environment: {environment}</p>
      </div>
    </div>
  );
}
