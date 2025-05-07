import {
  MastheadBrand,
  MastheadContent,
  MastheadMain,
  Nav,
  NavItem,
  NavList,
  Masthead as PFMasthead,
  Title,
  ToggleGroup,
  ToggleGroupItem,
  Toolbar,
  ToolbarContent,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import React from 'react';

import MoonIcon from '@patternfly/react-icons/dist/esm/icons/moon-icon';
import SunIcon from '@patternfly/react-icons/dist/esm/icons/sun-icon';
import { Link } from '@tanstack/react-router';

export const themeStorageKey = 'app-theme';

export function Masthead() {
  const [isDarkTheme, setIsDarkTheme] = React.useState(false);

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

  return (
    <PFMasthead>
      <MastheadMain>
        <MastheadBrand data-codemods>
          <Title headingLevel="h1">Virtual Assistant</Title>
        </MastheadBrand>
      </MastheadMain>
      <MastheadContent>{toolbar}</MastheadContent>
    </PFMasthead>
  );
}
