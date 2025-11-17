import { PageSection, Tabs, Tab, TabTitleText } from '@patternfly/react-core';
import { createFileRoute, useNavigate, useSearch } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { ModelList } from '@/components/ModelList';
import { ProviderList } from '@/components/ProviderList';

export const Route = createFileRoute('/_protected/_admin/config/models')({
  component: Models,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      tab: (search.tab as string) || 'models',
    };
  },
});

function Models() {
  const navigate = useNavigate();
  const search = useSearch({ from: '/_protected/_admin/config/models' });
  const [activeTabKey, setActiveTabKey] = useState<string | number>(0);

  // Sync tab with URL search params
  useEffect(() => {
    if (search.tab === 'providers') {
      setActiveTabKey(1);
    } else {
      setActiveTabKey(0);
    }
  }, [search.tab]);

  const handleTabSelect = (_event: React.MouseEvent, tabIndex: string | number) => {
    setActiveTabKey(tabIndex);
    const tabName = tabIndex === 0 ? 'models' : 'providers';
    void navigate({ to: '/config/models', search: { tab: tabName } });
  };

  return (
    <PageSection hasBodyWrapper={false}>
      <Tabs
        activeKey={activeTabKey}
        onSelect={handleTabSelect}
        aria-label="Models configuration tabs"
      >
        <Tab eventKey={0} title={<TabTitleText>Models</TabTitleText>}>
          <PageSection>
            <ModelList />
          </PageSection>
        </Tab>
        <Tab eventKey={1} title={<TabTitleText>Providers</TabTitleText>}>
          <PageSection>
            <ProviderList />
          </PageSection>
        </Tab>
      </Tabs>
    </PageSection>
  );
}
