import { KNOWLEDGE_BASES_API_ENDPOINT } from '@/config/api';
import { KnowledgeBase } from '@/types';

export const fetchKnowledgeBases = async (): Promise<KnowledgeBase[]> => {
  const response = await fetch(KNOWLEDGE_BASES_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  const data: unknown = response.json();
  return data as KnowledgeBase[];
};
