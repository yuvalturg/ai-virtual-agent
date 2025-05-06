import { PageSection, Title } from "@patternfly/react-core";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/config/knowledge-bases")({
  component: KnowledgeBases,
});

function KnowledgeBases() {
  return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1">Hello "/config/knowledge-bases"!</Title>
    </PageSection>
  );
}
