import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRootRoute, Outlet } from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';
import { UserProvider } from '@/contexts/UserContext';

export const Route = createRootRoute({
  component: () => {
    const queryClient = new QueryClient();
    return (
      <UserProvider>
        <QueryClientProvider client={queryClient}>
          <Outlet />
          <TanStackRouterDevtools />
        </QueryClientProvider>
      </UserProvider>
    );
  },
});
