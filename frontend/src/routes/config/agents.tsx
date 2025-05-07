import { AgentCard } from '@/components/agent-card';
import {
  ActionGroup,
  Alert,
  Button,
  Form,
  FormGroup,
  FormSelect,
  FormSelectOption,
  Gallery,
  PageSection,
  Spinner,
  TextArea,
  TextInput,
  Title,
} from '@patternfly/react-core';
import { useForm } from '@tanstack/react-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import React, { Fragment } from 'react';

// Type def for fetching agents
export interface Agent {
  id: string;
  name: string;
  modelId: string;
  prompt: string;
  // Add other relevant agent properties here
}

// Type def for creating agents
interface NewAgent {
  name: string;
  modelId: string;
  prompt: string;
}

// API Fetching Functions (these are mocked for now)

// Mock API endpoint for AI Models
const AI_MODELS_API_ENDPOINT = '/api/ai-models';
// Mock API endpoint for Agents
const AGENTS_API_ENDPOINT = '/api/agents';

const fetchAIModels = async (): Promise<string[]> => {
  // Replace with actual API call
  // For now, returning mock data
  await new Promise((resolve) => setTimeout(resolve, 500)); // Simulate network delay
  return ['llama-1', 'llama-2', 'llama-3', 'llama-4'];
  // const response = await fetch(AI_MODELS_API_ENDPOINT);
  // if (!response.ok) {
  //   throw new Error('Network response was not ok');
  // }
  // return response.json();
};

const fetchAgents = async (): Promise<Agent[]> => {
  // Replace with actual API call
  // For now, returning mock data
  await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate network delay
  return [
    { id: 'agent-1', name: 'My First Agent', modelId: 'model-1', prompt: 'You are an AI agent' },
    {
      id: 'agent-2',
      name: 'Chatbot Assistant',
      modelId: 'model-2',
      prompt: 'You are a helpful assistant',
    },
  ];
  // const response = await fetch(AGENTS_API_ENDPOINT);
  // if (!response.ok) {
  //   throw new Error('Network response was not ok');
  // }
  // return response.json();
};

const createAgent = async (newAgent: NewAgent): Promise<Agent> => {
  // Replace with actual API call
  console.log('Creating agent:', newAgent);
  await new Promise((resolve) => setTimeout(resolve, 700)); // Simulate network delay
  // This is a mock response, in a real scenario, the backend would probably return the created agent with an id
  const createdAgent: Agent = { ...newAgent, id: `agent-${Date.now()}` };
  return createdAgent;
  // const response = await fetch(AGENTS_API_ENDPOINT, {
  //   method: 'POST',
  //   headers: {
  //     'Content-Type': 'application/json',
  //   },
  //   body: JSON.stringify(newAgent),
  // });
  // if (!response.ok) {
  //   throw new Error('Network response was not ok');
  // }
  // return response.json();
};

interface ModelsFieldProps {
  models: string[];
  isLoadingModels: boolean;
  modelsError: Error | null;
}

// AgentForm Component
interface AgentFormProps {
  modelsProps: ModelsFieldProps;
  onSubmit: (values: NewAgent) => void;
  isSubmitting: boolean;
}

// This form should ideally have validation, but I didn't have time.

const AgentForm: React.FC<AgentFormProps> = ({ modelsProps, onSubmit, isSubmitting }) => {
  const { models, isLoadingModels, modelsError } = modelsProps;
  const form = useForm({
    defaultValues: {
      name: '',
      modelId: '',
      prompt: '',
    },
    onSubmit: async ({ value }) => {
      onSubmit(value);
    },
  });

  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        form.handleSubmit();
      }}
    >
      <form.Field
        name="name"
        children={(field) => (
          <FormGroup label="Agent Name" isRequired fieldId="agent-name">
            <TextInput
              isRequired
              type="text"
              id="agent-name"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
            />
          </FormGroup>
        )}
      />

      <form.Field
        name="modelId"
        children={(field) => (
          <FormGroup label="Select AI Model" isRequired fieldId="ai-model">
            <FormSelect
              id="ai-model"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
              aria-label="Select AI Model"
              isDisabled={isLoadingModels || !!modelsError}
            >
              {isLoadingModels ? (
                <FormSelectOption key="loading" value="" label="Loading models..." isDisabled />
              ) : modelsError ? (
                <FormSelectOption key="error" value="" label="Error loading models" isDisabled />
              ) : (
                <Fragment>
                  <FormSelectOption key="placeholder" value="" label="Select a model" isDisabled />
                  {models.map((model) => (
                    <FormSelectOption key={model} value={model} label={model} />
                  ))}
                </Fragment>
              )}
            </FormSelect>
          </FormGroup>
        )}
      />

      <form.Field
        name="prompt"
        children={(field) => (
          <FormGroup label="Agent Prompt" isRequired fieldId="prompt">
            <TextArea
              isRequired
              type="text"
              id="prompt"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
            />
          </FormGroup>
        )}
      />

      <ActionGroup>
        <Button
          variant="primary"
          type="submit"
          isLoading={isSubmitting}
          isDisabled={isSubmitting || !form.state.canSubmit}
        >
          Create Agent
        </Button>
        <Button variant="link" onClick={() => form.reset()} isDisabled={isSubmitting}>
          Reset
        </Button>
      </ActionGroup>
      {form.state.submissionAttempts > 0 &&
        !form.state.isSubmitted &&
        form.state.errors.length > 0 && (
          <Alert variant="danger" title="Form submission failed" className="pf-v5-u-mt-md">
            Please check the form for errors.
          </Alert>
        )}
    </Form>
  );
};

export const Route = createFileRoute('/config/agents')({
  component: Agents,
});

// --- 5. Main AgentsPage Component ---
export function Agents() {
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

  // Query for Agents
  const {
    data: agents,
    isLoading: isLoadingAgents,
    error: agentsError,
    refetch: refetchAgents,
  } = useQuery<Agent[], Error>({
    queryKey: ['agents'],
    queryFn: fetchAgents,
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
    if (!values.modelId) {
      // Or handle this validation within the form itself
      alert('Please select a model.');
      return;
    }
    agentMutation.mutate(values);
  };

  return (
    <PageSection>
      <Title headingLevel="h1" className="pf-v5-u-mb-lg">
        Configure AI Agents
      </Title>

      <PageSection className="pf-v5-u-mb-lg">
        <Title headingLevel="h2" size="xl" className="pf-v5-u-mb-md">
          Create New Agent
        </Title>
        <AgentForm
          modelsProps={{
            models: models || [],
            isLoadingModels: isLoadingModels,
            modelsError: modelsError,
          }}
          onSubmit={handleCreateAgent}
          isSubmitting={agentMutation.isPending}
        />
        {agentMutation.isError && (
          <Alert variant="danger" title="Failed to create agent" className="pf-v5-u-mt-md">
            {agentMutation.error?.message || 'An unexpected error occurred.'}
          </Alert>
        )}
        {agentMutation.isSuccess && (
          <Alert variant="success" title="Agent created successfully!" className="pf-v5-u-mt-md" />
        )}
      </PageSection>

      <PageSection>
        <Title headingLevel="h2" size="xl" className="pf-v5-u-mb-md">
          Existing Agents
          <Button
            variant="link"
            onClick={() => refetchAgents()}
            isDisabled={isLoadingAgents}
            className="pf-v5-u-ml-sm"
          >
            {isLoadingAgents ? <Spinner size="sm" /> : 'Refresh List'}
          </Button>
        </Title>
        {isLoadingAgents && <Spinner aria-label="Loading agents" />}
        {agentsError && (
          <Alert variant="danger" title="Error loading agents">
            {agentsError.message}
          </Alert>
        )}
        {!isLoadingAgents && !agentsError && agents && agents.length === 0 && (
          <p>No agents configured yet.</p>
        )}
        {!isLoadingAgents && !agentsError && agents && agents.length > 0 && (
          <Gallery hasGutter>
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </Gallery>
        )}
      </PageSection>
    </PageSection>
  );
}
