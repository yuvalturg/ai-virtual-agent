import { PageSection, Title } from "@patternfly/react-core";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/config/agents")({
  component: Agents,
});

function Agents() {
  return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1">Hello "/config/agents"!</Title>
    </PageSection>
  );
}
