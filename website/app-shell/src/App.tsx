import { BrowserRouter } from 'react-router-dom';
import { AppRoutes } from './routes';
import { Toaster } from './components/common/Toast';

export default function App() {
  return (
    <BrowserRouter basename="/console">
      <AppRoutes />
      <Toaster />
    </BrowserRouter>
  );
}
