import { TOOLS_API_ENDPOINT } from '@/config/api';
import { Tool } from '@/types';

export const fetchTools = async (): Promise<Tool[]> => {
  const response = await fetch(TOOLS_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = response.json();
  return data as Tool[];
};
