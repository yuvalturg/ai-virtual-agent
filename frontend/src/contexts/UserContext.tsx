import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { fetchUsers, User } from '@/services/users';

interface UserContextType {
  currentUser: User | null;
  isLoading: boolean;
  error: string | null;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

interface UserProviderProps {
  children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // TODO: Replace this with actual authentication logic
        // For now, we default to the first user in the database
        const users = await fetchUsers();
        if (users.length > 0) {
          setCurrentUser(users[0]);
          console.log('Defaulting to first user:', users[0]);
        } else {
          setError('No users found in database');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch user');
        console.error('Error fetching current user:', err);
      } finally {
        setIsLoading(false);
      }
    };

    void fetchCurrentUser();
  }, []);

  const value: UserContextType = {
    currentUser,
    isLoading,
    error,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

/**
 * Custom hook to access the current user
 *
 * TODO: This currently defaults to the first user in the database.
 * Replace with proper authentication logic that:
 * 1. Checks for stored auth tokens/session
 * 2. Validates user session with backend
 * 3. Handles login/logout flows
 * 4. Redirects to login if not authenticated
 */
export const useCurrentUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useCurrentUser must be used within a UserProvider');
  }
  return context;
};
