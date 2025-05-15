import { Agent, NewAgent } from '@/routes/config/agents';
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

const AI_MODELS_API_ENDPOINT = '/api/llama_stack/llms';
const KNOWLEDGE_BASES_API_ENDPOINT = '/api/llama_stack/knowledge_bases';
const TOOLS_API_ENDPOINT = '/api/llama_stack/mcp_servers';
const AGENTS_API_ENDPOINT = '/api/virtual_assistants';

const fetchAIModels = async (): Promise<string[]> => {
  const response = await fetch(AI_MODELS_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
};
const fetchKnowledgeBases = async (): Promise<string[]> => {
  const response = await fetch(KNOWLEDGE_BASES_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
};
const fetchTools = async (): Promise<string[]> => {
  const response = await fetch(TOOLS_API_ENDPOINT);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
};

const createAgent = async (newAgent: NewAgent): Promise<Agent> => {
  const response = await fetch(AGENTS_API_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(newAgent),
  });
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json();
};

export function NewAgentCard() {
  const [isOpen, setIsOpen] = useState(false);
  // Or whatever name fits your routing setup e.g. ConfigAgents
  const queryClient = useQueryClient();

  // Query for AI Models
  const {
    data: models,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useQuery<string[], Error>({
    queryKey: ['aiModels'],
    queryFn: fetchAIModels,
  });
  // Query for Knowledge bases
  const {
    data: knowledgeBases,
    isLoading: isLoadingKnowledgeBases,
    error: knowledgeBasesError,
  } = useQuery<string[], Error>({
    queryKey: ['knowledgeBases'],
    queryFn: fetchKnowledgeBases,
  });
  // Query for tools
  const {
    data: tools,
    isLoading: isLoadingTools,
    error: toolsError,
  } = useQuery<string[], Error>({
    queryKey: ['tools'],
    queryFn: fetchTools,
  });

  // Mutation for creating an Agent
  const agentMutation = useMutation<Agent, Error, NewAgent>({
    mutationFn: createAgent,
    onSuccess: (newAgentData) => {
      // Invalidate and refetch the agents list to show the new agent
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      // Or, for optimistic updates:
      // queryClient.setQueryData(['agents'], (oldData: Agent[] | undefined) =>
      //   oldData ? [...oldData, newAgentData] : [newAgentData]
      // );
      console.log('Agent created successfully:', newAgentData);
      // Optionally reset form or show a success message
    },
    onError: (error) => {
      console.error('Error creating agent:', error);
      // Optionally show an error message
    },
  });

  const handleCreateAgent = (values: NewAgent) => {
    if (!values.model_name) {
      // Or handle this validation within the form itself
      alert('Please select a model.');
      return;
    }
    agentMutation.mutate(values);
  };
  return (
    <Card isExpanded={isOpen} isClickable={!isOpen}>
      <CardHeader
        selectableActions={{
          // eslint-disable-next-line no-console
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
