import { PageSection } from "@patternfly/react-core";
import { AssistantChat } from "../../components/assistant-chat";

export default function Chat() {
  return (
    <PageSection hasBodyWrapper={false}>
      <AssistantChat />
    </PageSection>
  );
}
