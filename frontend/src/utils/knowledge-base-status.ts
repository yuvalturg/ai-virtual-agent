import { KnowledgeBase, KnowledgeBaseWithStatus, KnowledgeBaseStatus } from '@/types';

interface LlamaStackKnowledgeBase {
  kb_name: string;
  provider_resource_id: string;
  provider_id: string;
  type: string;
  embedding_model: string;
}

/**
 * Determines the status of a knowledge base by comparing DB and LlamaStack states
 */
function determineStatus(
  dbKb: KnowledgeBase | undefined,
  llamaStackKb: LlamaStackKnowledgeBase | undefined
): KnowledgeBaseStatus {
  if (dbKb && llamaStackKb) {
    return 'ready'; // Exists in both DB and LlamaStack
  } else if (dbKb && !llamaStackKb) {
    return 'pending'; // In DB but not LlamaStack (ingestion running)
  } else if (!dbKb && llamaStackKb) {
    return 'orphaned'; // In LlamaStack but not DB (sync issue)
  }
  // This should never happen, but just in case
  return 'pending';
}

/**
 * Simple matching by knowledge base name only
 */
function findMatchingKnowledgeBase(
  dbKb: KnowledgeBase | undefined,
  llamaStackKb: LlamaStackKnowledgeBase | undefined
): { dbMatch: KnowledgeBase | undefined; llamaStackMatch: LlamaStackKnowledgeBase | undefined } {
  return { dbMatch: dbKb, llamaStackMatch: llamaStackKb };
}

/**
 * Merges knowledge bases from database and LlamaStack, determining status for each
 */
export function mergeKnowledgeBasesWithStatus(
  dbKnowledgeBases: KnowledgeBase[],
  llamaStackKnowledgeBases: LlamaStackKnowledgeBase[]
): KnowledgeBaseWithStatus[] {
  const result: KnowledgeBaseWithStatus[] = [];
  const processedLlamaStackKbs = new Set<string>();

  // Create map for efficient lookup by primary identifier (kb_name)
  const llamaStackKbMap = new Map(llamaStackKnowledgeBases.map((kb) => [kb.kb_name, kb]));

  // Process all DB knowledge bases first
  for (const dbKb of dbKnowledgeBases) {
    const llamaStackKb = llamaStackKbMap.get(dbKb.vector_db_name);
    const { dbMatch, llamaStackMatch } = findMatchingKnowledgeBase(dbKb, llamaStackKb);
    const status = determineStatus(dbMatch, llamaStackMatch);

    result.push({
      ...dbKb,
      status,
    });

    if (llamaStackMatch) {
      processedLlamaStackKbs.add(llamaStackMatch.kb_name);
    }
  }

  // Process remaining LlamaStack knowledge bases that don't have DB matches
  for (const llamaStackKb of llamaStackKnowledgeBases) {
    if (!processedLlamaStackKbs.has(llamaStackKb.kb_name)) {
      const { dbMatch, llamaStackMatch } = findMatchingKnowledgeBase(undefined, llamaStackKb);
      const status = determineStatus(dbMatch, llamaStackMatch);

      // Create a knowledge base object from LlamaStack data for orphaned items
      result.push({
        vector_db_name: llamaStackKb.kb_name,
        name: llamaStackKb.kb_name,
        version: 'unknown',
        embedding_model: llamaStackKb.embedding_model,
        provider_id: llamaStackKb.provider_id,
        is_external: true,
        source: 'unknown',
        source_configuration: {
          provider_resource_id: llamaStackKb.provider_resource_id,
          type: llamaStackKb.type,
        },
        status,
      });
    }
  }

  return result;
}

/**
 * Gets the status color for display
 */
export function getStatusColor(status: KnowledgeBaseStatus): 'green' | 'orange' | 'red' {
  switch (status) {
    case 'ready':
      return 'green';
    case 'pending':
      return 'orange';
    case 'orphaned':
      return 'red';
    default:
      return 'orange';
  }
}

/**
 * Gets the status label for display
 */
export function getStatusLabel(status: KnowledgeBaseStatus): string {
  switch (status) {
    case 'ready':
      return 'Ready';
    case 'pending':
      return 'Pending';
    case 'orphaned':
      return 'Orphaned';
    default:
      return 'Unknown';
  }
}
