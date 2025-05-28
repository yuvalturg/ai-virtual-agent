import { EmbeddingModel, KnowledgeBase, Provider } from '@/types';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardBody,
  CardExpandableContent,
  CardHeader,
  CardTitle,
  Flex,
  FlexItem,
  Title,
  Alert,
} from '@patternfly/react-core';
import { PlusIcon } from '@patternfly/react-icons';
import { useState } from 'react';
import { KnowledgeBaseForm } from './knowledge-base-form';
import { fetchEmbeddingModels, fetchProviders } from '@/services/models';
import { createKnowledgeBase } from '@/services/knowledge-bases';

export function NewKnowledgeBaseCard() {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();

  const {
    data: embeddingModels,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useQuery<EmbeddingModel[], Error>({
    queryKey: ['models'],
    queryFn: fetchEmbeddingModels,
  });

  const {
    data: providers,
    isLoading: isLoadingProviders,
    error: providersError,
  } = useQuery<Provider[], Error>({
    queryKey: ['providers'],
    queryFn: fetchProviders,
  });

  const kbMutation = useMutation<
    KnowledgeBase,
    Error,
    Omit<KnowledgeBase, 'created_at' | 'updated_at'>
  >({
    mutationFn: createKnowledgeBase,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['knowledgeBases'] });
      setIsOpen(false);
      console.log('Knowledge base created successfully');
    },
    onError: (error) => {
      console.error('Error creating knowledge base:', error);
    },
  });

  const handleCreateKb = (values: KnowledgeBase) => {
    // Strip out fields that shouldn't be sent to the API
    const { created_at, updated_at, ...createPayload } = values;
    kbMutation.mutate(createPayload);
  };

  return (
    <Flex direction={{ default: 'column' }} gap={{ default: 'gapMd' }}>
      {kbMutation.isSuccess && (
        <FlexItem>
          <Alert
            timeout={5000}
            variant="success"
            title="Knowledge base created successfully!"
            className="pf-v6-u-mb-sm"
          />
        </FlexItem>
      )}
      <FlexItem>
        <Card isExpanded={isOpen} isClickable={!isOpen}>
          <CardHeader
            selectableActions={{
              onClickAction: () => setIsOpen(!isOpen),
              selectableActionAriaLabelledby: 'clickable-kb-card-title-1',
            }}
          >
            <CardTitle>
              {!isOpen ? (
                <Flex>
                  <FlexItem>
                    <PlusIcon />
                  </FlexItem>
                  <FlexItem>
                    <Title headingLevel="h3">New Knowledge Base</Title>
                  </FlexItem>
                </Flex>
              ) : (
                <Title headingLevel="h3">New Knowledge Base</Title>
              )}
            </CardTitle>
          </CardHeader>
          <CardExpandableContent>
            <CardBody>
              <Flex direction={{ default: 'column' }} gap={{ default: 'gapLg' }}>
                <FlexItem>
                  <KnowledgeBaseForm
                    embeddingModelProps={{
                      models: embeddingModels ?? [],
                      isLoadingModels,
                      modelsError,
                    }}
                    providersProps={{
                      providers: providers ?? [],
                      isLoadingProviders,
                      providersError,
                    }}
                    isSubmitting={kbMutation.isPending}
                    onSubmit={handleCreateKb}
                    onCancel={() => setIsOpen(false)}
                    error={kbMutation.isError ? kbMutation.error : null}
                  />
                </FlexItem>
                {kbMutation.isError && (
                  <FlexItem>
                    <Alert
                      variant="danger"
                      title="Failed to create knowledge base"
                      className="pf-v6-u-mt-md"
                    >
                      {kbMutation.error?.message || 'An unexpected error occurred.'}
                    </Alert>
                  </FlexItem>
                )}
              </Flex>
            </CardBody>
          </CardExpandableContent>
        </Card>
      </FlexItem>
    </Flex>
  );
}
