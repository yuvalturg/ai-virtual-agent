import { AgentCard } from '@/components/agent-card';
import { Agent } from '@/routes/config/agents';
import { Alert, Flex, Spinner } from '@patternfly/react-core';
import { useQuery } from '@tanstack/react-query';

export function AgentList() {
  const fetchAgents = async (): Promise<Agent[]> => {
    // Replace with actual API call
    // For now, returning mock data
    await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate network delay
    return [
      {
        id: 'agent-1',
        name: 'My First Agent',
        model_name: 'model-1',
        prompt: 'You are an AI agent',
      },
      {
        id: 'agent-2',
        name: 'Chatbot Assistant',
        model_name: 'model-2',
        prompt: 'You are a helpful assistant',
      },
    ];
    // const response = await fetch(AGENTS_API_ENDPOINT);
    // if (!response.ok) {
    //   throw new Error('Network response was not ok');
    // }
    // return response.json();
  };

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

  return (
    <div>
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
        <Flex direction={{ default: 'column' }}>
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </Flex>
      )}
    </div>
  );
}
