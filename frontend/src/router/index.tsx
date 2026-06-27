import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { Dashboard } from '@/pages/Dashboard';
import { Chat } from '@/pages/Chat';
import { Documents } from '@/pages/Documents';
import { Settings } from '@/pages/Settings';
import { Health } from '@/pages/Health';
import { NotFound } from '@/pages/NotFound';
import { ROUTES } from '@/utils/constants';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: ROUTES.chat, element: <Chat /> },
      { path: ROUTES.documents, element: <Documents /> },
      { path: ROUTES.settings, element: <Settings /> },
      { path: ROUTES.health, element: <Health /> },
      { path: '*', element: <NotFound /> },
    ],
  },
]);
