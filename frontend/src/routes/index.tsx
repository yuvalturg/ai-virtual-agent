import { AssistantChat } from '@/components/assistant-chat';
import { Page, PageSection } from '@patternfly/react-core';
import { createFileRoute } from '@tanstack/react-router';
import { Masthead } from '../components/masthead';

export const Route = createFileRoute('/')({
  component: Chat,
});

const pageId = 'primary-app-container';

function Chat() {
  return (
    <Page mainContainerId={pageId} masthead={<Masthead />}>
      <PageSection hasBodyWrapper={false}>
        <AssistantChat />
      </PageSection>
    </Page>
  );
}
