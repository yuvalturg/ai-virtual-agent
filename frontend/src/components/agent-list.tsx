import { AgentCard } from '@/components/agent-card';
import { Agent } from '@/routes/config/agents';
import { fetchAgents } from '@/services/agents';
import { Alert, Flex, Spinner } from '@patternfly/react-core';
import { useQuery } from '@tanstack/react-query';

export function AgentList() {
  // Query for Agents
  const {
    data: agents,
    isLoading: isLoadingAgents,
    error: agentsError,
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
          {agents
            .sort((a, b) => Date.parse(b.created_at ?? '') - Date.parse(a.created_at ?? ''))
            .map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
        </Flex>
      )}
    </div>
  );
}
