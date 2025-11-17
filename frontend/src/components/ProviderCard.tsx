import {
  Card,
  CardHeader,
  CardTitle,
  CardBody,
  CardExpandableContent,
  Title,
  Flex,
  FlexItem,
  Label,
} from '@patternfly/react-core';
import { useState } from 'react';
import { ModelProvider } from '@/types/models';

interface ProviderCardProps {
  provider: ModelProvider;
}

export function ProviderCard({ provider }: ProviderCardProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  const onExpand = () => setIsExpanded(!isExpanded);

  return (
    <Card
      id={`expandable-provider-card-${provider.provider_id}`}
      isExpanded={isExpanded}
      className="pf-v6-u-mb-md"
    >
      <CardHeader
        onExpand={onExpand}
        toggleButtonProps={{
          id: `toggle-provider-button-${provider.provider_id}`,
          'aria-label': 'Details',
          'aria-labelledby': `expandable-provider-title-${provider.provider_id} toggle-provider-button-${provider.provider_id}`,
          'aria-expanded': isExpanded,
        }}
      >
        <CardTitle id={`expandable-provider-title-${provider.provider_id}`}>
          <Flex alignItems={{ default: 'alignItemsCenter' }} gap={{ default: 'gapSm' }}>
            <FlexItem>
              <Title className="pf-v6-u-mb-0" headingLevel="h2">
                {provider.provider_id}
              </Title>
            </FlexItem>
            <FlexItem>
              <Label color="blue">{provider.api}</Label>
            </FlexItem>
            <FlexItem>
              <Label color="grey">{provider.provider_type}</Label>
            </FlexItem>
          </Flex>
        </CardTitle>
      </CardHeader>
      <CardExpandableContent>
        <CardBody>
          <Flex direction={{ default: 'column' }}>
            <FlexItem>
              <span className="pf-v6-u-text-color-subtle">Provider Type: </span>
              {provider.provider_type}
            </FlexItem>
            <FlexItem>
              <span className="pf-v6-u-text-color-subtle">API: </span>
              {provider.api}
            </FlexItem>
            {provider.config && Object.keys(provider.config).length > 0 && (
              <FlexItem>
                <span className="pf-v6-u-text-color-subtle">Configuration: </span>
                <pre className="pf-v6-u-font-size-sm pf-v6-u-mt-xs">
                  {JSON.stringify(provider.config, null, 2)}
                </pre>
              </FlexItem>
            )}
          </Flex>
        </CardBody>
      </CardExpandableContent>
    </Card>
  );
}
