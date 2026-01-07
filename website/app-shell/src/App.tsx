import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './routes';
import { Toaster } from './components/common/Toast';

// Use environment variable for basename, default to '/' for subdomain deployment
const basename = import.meta.env.VITE_BASE_PATH || '/';

export default function App() {
  return (
    <BrowserRouter basename={basename}>
      <AppRoutes />
      <Toaster />
    </BrowserRouter>
  );
}
