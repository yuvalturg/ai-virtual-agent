import { SHIELDS_API_ENDPOINT } from '@/config/api';
import { Shield } from '@/types/auth';
import { ErrorResponse } from '@/types';

// Re-export types for backward compatibility
export type { Shield } from '@/types/auth';

interface BackendShield {
  id: string;
  name: string;
  model_type: string;
}

export const fetchShields = async (): Promise<Shield[]> => {
  const response = await fetch(SHIELDS_API_ENDPOINT);
  if (!response.ok) {
    const errorData = (await response
      .json()
      .catch(() => ({ detail: 'Network response was not ok' }))) as ErrorResponse;
    throw new Error(errorData.detail ?? 'Network response was not ok');
  }
  const data: BackendShield[] = (await response.json()) as BackendShield[];

  // Map backend response to frontend expected structure
  return data.map((shield) => ({
    identifier: shield.id,
    name: shield.name,
  }));
};
