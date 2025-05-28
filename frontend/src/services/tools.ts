import { TOOLS_API_ENDPOINT } from '@/config/api';
import { ToolGroup } from '@/types';

export const fetchTools = async (): Promise<ToolGroup[]> => {
  const response = await fetch(TOOLS_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as ToolGroup[];
};
