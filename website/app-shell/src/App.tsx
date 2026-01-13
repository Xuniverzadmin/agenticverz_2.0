import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './routes';
import { Toaster } from './components/common/Toast';
import { RouteGuardAssertion } from '@/routing';
import { SimulationProvider } from '@/contexts/SimulationContext';
import { SimulationLog } from '@/components/simulation';
import { ClerkAuthSync } from '@/components/auth/ClerkAuthSync';

// Use environment variable for basename, default to '/' for subdomain deployment
const basename = import.meta.env.VITE_BASE_PATH || '/';

export default function App() {
  return (
    <BrowserRouter basename={basename}>
      {/* RULE-AUTH-UI-001: Forward Clerk tokens to API client */}
      <ClerkAuthSync />
      {/* PIN-352: Runtime assertion for routing authority (dev/preflight only) */}
      <RouteGuardAssertion />
      {/* PIN-368: Phase-2A.2 Simulation Mode */}
      <SimulationProvider initialMode="SIMULATED">
        <AppRoutes />
        <SimulationLog />
      </SimulationProvider>
      <Toaster />
    </BrowserRouter>
  );
}
