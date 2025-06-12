import { KnowledgeBaseCard } from '@/components/knowledge-base-card';
import { fetchKnowledgeBasesWithStatus, deleteKnowledgeBase } from '@/services/knowledge-bases';
import { KnowledgeBaseWithStatus } from '@/types';
import { Alert, Button, Flex, FlexItem, Spinner, Title } from '@patternfly/react-core';
import { SyncIcon } from '@patternfly/react-icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { NewKnowledgeBaseCard } from './new-knowledge-base-card';

export function KnowledgeBaseList() {
  const queryClient = useQueryClient();
  const [lastFetchTime, setLastFetchTime] = useState<string>('');

  // Query for Knowledge Bases with status
  const {
    data: knowledgeBases,
    isLoading: isLoadingKnowledgeBases,
    error: knowledgeBasesError,
    dataUpdatedAt,
  } = useQuery<KnowledgeBaseWithStatus[], Error>({
    queryKey: ['knowledgeBases'],
    queryFn: fetchKnowledgeBasesWithStatus,
  });

  // Update timestamp when data is fetched
  React.useEffect(() => {
    if (dataUpdatedAt) {
      setLastFetchTime(new Date(dataUpdatedAt).toLocaleString());
    }
  }, [dataUpdatedAt]);

  // Delete knowledge base mutation
  const deleteKnowledgeBaseMutation = useMutation({
    mutationFn: deleteKnowledgeBase,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['knowledgeBases'] });
      console.log('Knowledge base deleted successfully');
    },
    onError: (error) => {
      console.error('Error deleting knowledge base:', error);
    },
  });

  const handleDeleteKb = (vectorDbName: string) => {
    deleteKnowledgeBaseMutation.mutate(vectorDbName);
  };

  const handleRefresh = () => {
    void queryClient.invalidateQueries({ queryKey: ['knowledgeBases'] });
  };

  return (
    <div>
      {/* Header with title, refresh button, and timestamp */}
      <Flex
        justifyContent={{ default: 'justifyContentSpaceBetween' }}
        alignItems={{ default: 'alignItemsCenter' }}
        className="pf-v6-u-mb-md"
      >
        <FlexItem>
          <Title headingLevel="h2">Knowledge Bases</Title>
        </FlexItem>
        <FlexItem>
          <Flex alignItems={{ default: 'alignItemsCenter' }} gap={{ default: 'gapSm' }}>
            {lastFetchTime && (
              <FlexItem>
                <span className="pf-v6-u-text-color-subtle pf-v6-u-font-size-sm">
                  Last updated: {lastFetchTime}
                </span>
              </FlexItem>
            )}
            <FlexItem>
              <Button
                variant="plain"
                icon={<SyncIcon />}
                onClick={handleRefresh}
                isLoading={isLoadingKnowledgeBases}
                aria-label="Refresh knowledge bases"
              >
                Refresh
              </Button>
            </FlexItem>
          </Flex>
        </FlexItem>
      </Flex>

      {/* Content */}
      {isLoadingKnowledgeBases && <Spinner aria-label="Loading knowledge bases" />}
      {knowledgeBasesError && (
        <Alert variant="danger" title="Error loading knowledge bases">
          {knowledgeBasesError.message}
        </Alert>
      )}
      <Flex direction={{ default: 'column' }}>
        <FlexItem>
          <NewKnowledgeBaseCard />
        </FlexItem>
        {!isLoadingKnowledgeBases &&
          !knowledgeBasesError &&
          knowledgeBases &&
          knowledgeBases.length > 0 &&
          knowledgeBases
            .sort((a, b) => Date.parse(b.created_at ?? '') - Date.parse(a.created_at ?? ''))
            .map((knowledgeBase) => (
              <KnowledgeBaseCard
                key={knowledgeBase.vector_db_name}
                knowledgeBase={knowledgeBase}
                onDelete={handleDeleteKb}
                isDeleting={deleteKnowledgeBaseMutation.isPending}
              />
            ))}
        {!isLoadingKnowledgeBases &&
          !knowledgeBasesError &&
          knowledgeBases &&
          knowledgeBases.length === 0 && <p>No knowledge bases configured yet.</p>}
      </Flex>
    </div>
  );
}
