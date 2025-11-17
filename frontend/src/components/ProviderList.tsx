import { Alert, Flex, Spinner, Title } from '@patternfly/react-core';
import { useModelsManagement } from '@/hooks/useModelsManagement';
import { NewProviderCard } from '@/components/NewProviderCard';
import { ProviderCard } from '@/components/ProviderCard';

export function ProviderList() {
  const { providers, isLoadingProviders, providersError } = useModelsManagement();

  // Filter to only show inference providers
  const inferenceProviders = providers?.filter((p) => p.api === 'inference') || [];

  return (
    <div>
      <Title headingLevel="h2" className="pf-v6-u-mb-md">
        Providers
      </Title>

      {isLoadingProviders && <Spinner aria-label="Loading providers" />}
      {providersError && (
        <Alert variant="danger" title="Error loading providers">
          {providersError.message}
        </Alert>
      )}

      <Flex direction={{ default: 'column' }} gap={{ default: 'gapMd' }}>
        <NewProviderCard />

        {!isLoadingProviders &&
          !providersError &&
          inferenceProviders.length > 0 &&
          inferenceProviders.map((provider) => (
            <ProviderCard key={provider.provider_id} provider={provider} />
          ))}

        {!isLoadingProviders && !providersError && inferenceProviders.length === 0 && (
          <p>No providers configured yet.</p>
        )}
      </Flex>
    </div>
  );
}
