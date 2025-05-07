import {
  Nav,
  NavItem,
  NavList,
  Page,
  PageSidebar,
  PageSidebarBody,
} from "@patternfly/react-core";
import {
  createFileRoute,
  Link,
  Outlet,
  useLocation,
} from "@tanstack/react-router";
import { Masthead } from "../../components/masthead";

export const Route = createFileRoute("/config")({
  component: ConfigLayout,
});

function ConfigLayout() {
  const location = useLocation();

  const sidebar = (
    <PageSidebar>
      <PageSidebarBody>
        <Nav aria-label="Config Nav">
          <NavList>
            {/* Preventing default click behavior on each NavItem for demo purposes only */}
            <NavItem
              itemId={0}
              isActive={location.pathname == "/config/agents"}
              to="#"
            >
              <Link to="/config/agents">Agents</Link>
            </NavItem>
            <NavItem
              itemId={1}
              isActive={location.pathname == "/config/knowledge-bases"}
              to="#"
            >
              <Link to="/config/knowledge-bases">Knowledge Bases</Link>
            </NavItem>
            <NavItem
              itemId={2}
              isActive={location.pathname == "/config/mcp-servers"}
              to="#"
            >
              <Link to="/config/mcp-servers">MCP Servers</Link>
            </NavItem>
          </NavList>
        </Nav>
      </PageSidebarBody>
    </PageSidebar>
  );

  return (
    <Page
      sidebar={sidebar}
      mainContainerId={"config-page-container"}
      masthead={<Masthead />}
    >
      <Outlet />
    </Page>
  );
}
