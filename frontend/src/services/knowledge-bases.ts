import { KNOWLEDGE_BASES_API_ENDPOINT } from '@/config/api';
import { KnowledgeBase, KnowledgeBaseWithStatus } from '@/types';

export const fetchKnowledgeBasesWithStatus = async (): Promise<KnowledgeBaseWithStatus[]> => {
  const response = await fetch(KNOWLEDGE_BASES_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as KnowledgeBaseWithStatus[];
};

export const createKnowledgeBase = async (
  newKnowledgeBase: Omit<KnowledgeBase, 'created_at' | 'updated_at'>
): Promise<KnowledgeBase> => {
  const response = await fetch(KNOWLEDGE_BASES_API_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(newKnowledgeBase),
  });
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = await response.json();
  return data as KnowledgeBase;
};

export const deleteKnowledgeBase = async (vectorStoreName: string): Promise<void> => {
  const response = await fetch(KNOWLEDGE_BASES_API_ENDPOINT + vectorStoreName, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
};
