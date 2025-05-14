import {
  Masthead,
  MastheadBrand,
  MastheadContent,
  MastheadMain,
  MastheadToggle,
  Nav,
  NavItem,
  NavList,
  Page,
  PageSidebar,
  PageSidebarBody,
  PageToggleButton,
  Title,
  ToggleGroup,
  ToggleGroupItem,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import { createFileRoute, Link, Outlet, useLocation } from '@tanstack/react-router';
import { BarsIcon, SunIcon, MoonIcon } from '@patternfly/react-icons';
import React from 'react';

export const Route = createFileRoute('/config')({
  component: ConfigLayout,
});

export const themeStorageKey = 'app-theme';

function ConfigLayout() {
  const location = useLocation();
  const [isDarkTheme, setIsDarkTheme] = React.useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);

  const onSidebarToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  // Load preferred theme from localstorage
  React.useMemo(() => {
    const isDarkThemeSaved = localStorage.getItem(themeStorageKey);
    if (isDarkThemeSaved === null) return;

    const isDark = JSON.parse(isDarkThemeSaved) as boolean;
    setIsDarkTheme(isDark);

    if (!isDark) return;

    const htmlElement = document.querySelector('html');
    if (!htmlElement) return;

    htmlElement.classList.toggle('pf-v6-theme-dark', true);
  }, []);

  const toggleDarkTheme = (
    _event: MouseEvent | React.MouseEvent<Element, MouseEvent> | React.KeyboardEvent<Element>,
    selected: boolean
  ) => {
    const darkThemeToggleClicked = !selected === isDarkTheme;
    const htmlElement = document.querySelector('html');
    if (htmlElement) {
      htmlElement.classList.toggle('pf-v6-theme-dark', darkThemeToggleClicked);
    }
    setIsDarkTheme(darkThemeToggleClicked);
    localStorage.setItem(themeStorageKey, JSON.stringify(darkThemeToggleClicked));
  };

  const nav = (
    <Nav variant="horizontal" aria-label="Main Nav">
      <NavList>
        {/* Preventing default click behavior on each NavItem for demo purposes only */}
        <NavItem itemId={0} isActive={location.pathname == '/'} to="#">
          <Link to="/">Chat</Link>
        </NavItem>
        <NavItem itemId={1} isActive={location.pathname.startsWith('/config/')} to="#">
          <Link to="/config/agents">Config</Link>
        </NavItem>
      </NavList>
    </Nav>
  );

  const toggle = (
    <PageToggleButton
      variant="plain"
      aria-label="Global navigation"
      isSidebarOpen={isSidebarOpen}
      onSidebarToggle={onSidebarToggle}
      id="main-padding-nav-toggle"
    >
      <BarsIcon />
    </PageToggleButton>
  );

  const toolbar = (
    <Toolbar
      inset={{
        default: 'insetSm',
        md: 'insetMd',
        lg: 'insetLg',
        xl: 'insetXl',
        '2xl': 'inset2xl',
      }}
      isFullHeight
    >
      <ToolbarContent>
        <ToolbarGroup align={{ default: 'alignStart' }}>
          <ToolbarItem>{nav}</ToolbarItem>
        </ToolbarGroup>
        <ToolbarGroup align={{ default: 'alignEnd' }}>
          <ToolbarItem>
            <ToggleGroup aria-label="Dark theme toggle group">
              <ToggleGroupItem
                aria-label="light theme toggle"
                icon={<SunIcon />}
                isSelected={!isDarkTheme}
                onChange={toggleDarkTheme}
              />
              <ToggleGroupItem
                aria-label="dark theme toggle"
                icon={<MoonIcon />}
                isSelected={isDarkTheme}
                onChange={toggleDarkTheme}
              />
            </ToggleGroup>
          </ToolbarItem>
        </ToolbarGroup>
      </ToolbarContent>
    </Toolbar>
  );

  const masthead = (
    <Masthead>
      <MastheadMain>
        <MastheadToggle>{location.pathname != '/' && toggle}</MastheadToggle>
        <MastheadBrand data-codemods>
          <Title headingLevel="h1">Virtual Assistant</Title>
        </MastheadBrand>
      </MastheadMain>
      <MastheadContent>{toolbar}</MastheadContent>
    </Masthead>
  );

  const sidebar = (
    <PageSidebar isSidebarOpen={isSidebarOpen} id="main-padding-sidebar">
      <PageSidebarBody>
        <Nav aria-label="Config Nav">
          <NavList>
            <NavItem itemId={0} isActive={location.pathname == '/config/agents'} to="#">
              <Link to="/config/agents">Agents</Link>
            </NavItem>
            <NavItem itemId={1} isActive={location.pathname == '/config/knowledge-bases'} to="#">
              <Link to="/config/knowledge-bases">Knowledge Bases</Link>
            </NavItem>
            <NavItem itemId={2} isActive={location.pathname == '/config/mcp-servers'} to="#">
              <Link to="/config/mcp-servers">MCP Servers</Link>
            </NavItem>
          </NavList>
        </Nav>
      </PageSidebarBody>
    </PageSidebar>
  );

  return (
    <Page sidebar={sidebar} mainContainerId={'config-page-container'} masthead={masthead}>
      <Outlet />
    </Page>
  );
}
