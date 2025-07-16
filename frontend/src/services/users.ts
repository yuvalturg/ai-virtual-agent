import { USERS_API_ENDPOINT } from '@/config/api';

export interface User {
  id: string;
  email: string;
  username: string;
  role?: string;
  agent_ids?: string[];
  created_at: string;
  updated_at: string;
  // Add other relevant user properties that might be returned by the API
}

export const fetchUsers = async (): Promise<User[]> => {
  const response = await fetch(USERS_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as User[];
};

export const fetchUserById = async (userId: string): Promise<User> => {
  const response = await fetch(`${USERS_API_ENDPOINT}${userId}`);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as User;
};

export const updateUserAgents = async (userId: string, agentIds: string[]): Promise<User> => {
  // Note: This will clone the specified agents and assign the cloned agents to the user
  // Each agent will be cloned with a unique name including the user's username
  // Duplicate agents (same config) will be detected and prevented
  const response = await fetch(`${USERS_API_ENDPOINT}${userId}/agents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ agent_ids: agentIds }),
  });
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as User;
};

export const getUserAgents = async (userId: string): Promise<string[]> => {
  const response = await fetch(`${USERS_API_ENDPOINT}${userId}/agents`);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as string[];
};

export const removeUserAgents = async (userId: string, agentIds: string[]): Promise<User> => {
  // Note: This will remove the specified agents from the user and cleanup orphaned cloned agents
  // Orphaned cloned agents (those created specifically for this user) will be deleted from LlamaStack
  const response = await fetch(`${USERS_API_ENDPOINT}${userId}/agents`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ agent_ids: agentIds }),
  });
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as User;
};
