import { Agent, NewAgent } from '@/routes/config/agents';
import { createAgent } from '@/services/agents';
import { fetchKnowledgeBases } from '@/services/knowledge-bases';
import { fetchModels } from '@/services/models';
import { fetchTools } from '@/services/tools';
import { KnowledgeBase, Model, Tool } from '@/types';
import {
  Alert,
  Card,
  CardBody,
  CardExpandableContent,
  CardHeader,
  CardTitle,
  Flex,
  FlexItem,
  Title,
} from '@patternfly/react-core';
import { PlusIcon } from '@patternfly/react-icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { AgentForm } from './agent-form';

export function NewAgentCard() {
  const [isOpen, setIsOpen] = useState(false);
  // Or whatever name fits your routing setup e.g. ConfigAgents
  const queryClient = useQueryClient();

  // Query for AI Models
  const {
    data: models,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useQuery<Model[], Error>({
    queryKey: ['models'],
    queryFn: fetchModels,
  });
  // Query for Knowledge bases
  const {
    data: knowledgeBases,
    isLoading: isLoadingKnowledgeBases,
    error: knowledgeBasesError,
  } = useQuery<KnowledgeBase[], Error>({
    queryKey: ['knowledgeBases'],
    queryFn: fetchKnowledgeBases,
  });
  // Query for tools
  const {
    data: tools,
    isLoading: isLoadingTools,
    error: toolsError,
  } = useQuery<Tool[], Error>({
    queryKey: ['tools'],
    queryFn: fetchTools,
  });

  // Mutation for creating an Agent
  const agentMutation = useMutation<Agent, Error, NewAgent>({
    mutationFn: createAgent,
    onSuccess: async (newAgentData) => {
      await queryClient.invalidateQueries({ queryKey: ['agents'] });
      console.log('Agent created successfully:', newAgentData);
    },
    onError: (error) => {
      console.error('Error creating agent:', error);
      // Show an error message
    },
  });

  const handleCreateAgent = (values: NewAgent) => {
    agentMutation.mutate(values);
  };

  return (
    <Card isExpanded={isOpen} isClickable={!isOpen}>
      <CardHeader
        selectableActions={{
          onClickAction: () => setIsOpen(!isOpen),
          selectableActionAriaLabelledby: 'clickable-card-example-title-1',
        }}
      >
        <CardTitle>
          {!isOpen ? (
            <Flex>
              <FlexItem>
                <PlusIcon />
              </FlexItem>
              <FlexItem>
                <Title headingLevel="h3">New Agent</Title>
              </FlexItem>
            </Flex>
          ) : (
            <Title headingLevel="h1">New Agent</Title>
          )}
        </CardTitle>
      </CardHeader>
      <CardExpandableContent className="pf-v5-u-mb-lg">
        <CardBody>
          <AgentForm
            modelsProps={{
              models: models || [],
              isLoadingModels,
              modelsError,
            }}
            knowledgeBasesProps={{
              knowledgeBases: knowledgeBases || [],
              isLoadingKnowledgeBases,
              knowledgeBasesError,
            }}
            toolsProps={{
              tools: tools || [],
              isLoadingTools,
              toolsError,
            }}
            onSubmit={handleCreateAgent}
            isSubmitting={agentMutation.isPending}
            onCancel={() => setIsOpen(false)}
          />
          {agentMutation.isError && (
            <Alert variant="danger" title="Failed to create agent" className="pf-v5-u-mt-md">
              {agentMutation.error?.message || 'An unexpected error occurred.'}
            </Alert>
          )}

          {agentMutation.isSuccess && (
            <Alert
              variant="success"
              title="Agent created successfully!"
              className="pf-v5-u-mt-md"
            />
          )}
        </CardBody>
      </CardExpandableContent>
    </Card>
  );
}
