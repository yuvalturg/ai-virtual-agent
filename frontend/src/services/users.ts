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
  // Note: This adds the specified agents to the user's agent list
  // Agents are shared across users and duplicate agent IDs are prevented
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
  // Note: This removes the specified agents from the user's agent list
  // Agents remain in LlamaStack and can be assigned to other users
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
