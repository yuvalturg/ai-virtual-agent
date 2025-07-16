import { fetchUsers, fetchUserById, updateUserAgents, removeUserAgents, User } from '@/services/users';
import { fetchAgents } from '@/services/agents';
import { Agent } from '@/routes/config/agents';
import {
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Flex,
  FlexItem,
  PageSection,
  Title,
  Button,
  DataList,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
  Spinner,
  Alert,
  DescriptionList,
  DescriptionListGroup,
  DescriptionListTerm,
  DescriptionListDescription,
  Label,
  LabelGroup,
  Dropdown,
  DropdownList,
  DropdownItem,
  MenuToggle,
  MenuToggleElement,
  Checkbox,
  Divider
} from '@patternfly/react-core';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { ArrowLeftIcon, TimesIcon } from '@patternfly/react-icons';
import React, { useEffect, useState, useRef } from 'react';

export const Route = createFileRoute('/config/users')({
  component: Users,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      userId: search.userId as string | undefined,
    };
  },
});

function Users() {
  const { userId } = Route.useSearch();
  const navigate = useNavigate({ from: '/config/users' });

  const [users, setUsers] = useState<User[]>([]);
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Agent management state
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
  const [agentLoading, setAgentLoading] = useState<{ [key: string]: boolean }>({});
  const [agentErrors, setAgentErrors] = useState<{ [key: string]: string }>({});
  const toggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);

      try {
        if (userId) {
          // Load specific user profile
          const profile = await fetchUserById(userId);
          setUserProfile(profile);
        } else {
          // Load users list
          const usersData = await fetchUsers();
          setUsers(usersData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [userId]);

  // Load available agents when in profile view
  useEffect(() => {
    if (userId) {
      const loadAgents = async () => {
        try {
          const agents = await fetchAgents();
          setAvailableAgents(agents);
        } catch (err) {
          console.error('Error loading agents:', err);
        }
      };
      loadAgents();
    }
  }, [userId]);

  const handleAddAgent = async (agentId: string) => {
    if (!userProfile) return;

    // Clear previous errors
    setAgentErrors(prev => ({ ...prev, [agentId]: '' }));
    setAgentLoading(prev => ({ ...prev, [agentId]: true }));

    try {
      // Add the agent to the user's current agents
      const currentAgents = userProfile.agent_ids || [];
      const updatedUser = await updateUserAgents(userProfile.id, [...currentAgents, agentId]);
      setUserProfile(updatedUser);
    } catch (err) {
      setAgentErrors(prev => ({
        ...prev,
        [agentId]: err instanceof Error ? err.message : 'Failed to add agent'
      }));
    } finally {
      setAgentLoading(prev => ({ ...prev, [agentId]: false }));
    }
  };

  const handleRemoveAgent = async (agentId: string) => {
    if (!userProfile) return;

    setAgentLoading(prev => ({ ...prev, [agentId]: true }));

    try {
      const updatedUser = await removeUserAgents(userProfile.id, [agentId]);
      setUserProfile(updatedUser);
    } catch (err) {
      setAgentErrors(prev => ({
        ...prev,
        [agentId]: err instanceof Error ? err.message : 'Failed to remove agent'
      }));
    } finally {
      setAgentLoading(prev => ({ ...prev, [agentId]: false }));
    }
  };

  const handleUserClick = (user: User) => {
    navigate({ search: { userId: user.id } });
  };

  const handleBackToList = () => {
    navigate({ search: { userId: undefined } });
  };

  if (loading) {
    return (
      <PageSection>
        <Flex justifyContent={{ default: 'justifyContentCenter' }}>
          <Spinner size="lg" />
        </Flex>
      </PageSection>
    );
  }

  if (error) {
    return (
      <PageSection>
        <Alert variant="danger" title="Error loading users">
          {error}
        </Alert>
      </PageSection>
    );
  }

  // User profile view
  if (userId && userProfile) {
    return (
      <PageSection>
        <Flex direction={{ default: 'column' }} gap={{ default: 'gapMd' }}>
          <FlexItem>
            <Flex alignItems={{ default: 'alignItemsCenter' }} gap={{ default: 'gapSm' }}>
              <Button variant="link" icon={<ArrowLeftIcon />} onClick={handleBackToList}>
                Back to Users
              </Button>
              <Title headingLevel="h1">User Profile</Title>
            </Flex>
          </FlexItem>
          <FlexItem>
            <Card>
              <CardHeader>
                <CardTitle>{userProfile.username}</CardTitle>
              </CardHeader>
              <CardBody>
                <DescriptionList>
                  <DescriptionListGroup>
                    <DescriptionListTerm>ID</DescriptionListTerm>
                    <DescriptionListDescription>{userProfile.id}</DescriptionListDescription>
                  </DescriptionListGroup>
                  <DescriptionListGroup>
                    <DescriptionListTerm>Username</DescriptionListTerm>
                    <DescriptionListDescription>{userProfile.username}</DescriptionListDescription>
                  </DescriptionListGroup>
                  <DescriptionListGroup>
                    <DescriptionListTerm>Email</DescriptionListTerm>
                    <DescriptionListDescription>{userProfile.email}</DescriptionListDescription>
                  </DescriptionListGroup>
                  {userProfile.role && (
                    <DescriptionListGroup>
                      <DescriptionListTerm>Role</DescriptionListTerm>
                      <DescriptionListDescription>{userProfile.role}</DescriptionListDescription>
                    </DescriptionListGroup>
                  )}
                  <DescriptionListGroup>
                    <DescriptionListTerm>Assigned Agents</DescriptionListTerm>
                    <DescriptionListDescription>
                      <Flex direction={{ default: 'column' }} gap={{ default: 'gapSm' }}>
                        <FlexItem>
                          <Dropdown
                            isOpen={agentDropdownOpen}
                            onOpenChange={(isOpen) => setAgentDropdownOpen(isOpen)}
                            toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                              <MenuToggle
                                ref={toggleRef}
                                onClick={() => setAgentDropdownOpen(!agentDropdownOpen)}
                                isExpanded={agentDropdownOpen}
                              >
                                Add Agent
                              </MenuToggle>
                            )}
                            shouldFocusToggleOnSelect
                          >
                            <DropdownList>
                              {availableAgents.map((agent) => {
                                const isAssigned = userProfile.agent_ids?.includes(agent.id);
                                const isLoading = agentLoading[agent.id];
                                const hasError = agentErrors[agent.id];

                                return (
                                  <DropdownItem
                                    key={agent.id}
                                    onClick={() => {
                                      if (!isAssigned && !isLoading) {
                                        handleAddAgent(agent.id);
                                      }
                                    }}
                                    isDisabled={isAssigned || isLoading}
                                  >
                                    <Flex alignItems={{ default: 'alignItemsCenter' }} gap={{ default: 'gapSm' }}>
                                      <Checkbox
                                        isChecked={isAssigned}
                                        isDisabled={isLoading}
                                        id={`agent-${agent.id}`}
                                        name={`agent-${agent.id}`}
                                        onChange={() => {
                                          if (!isAssigned && !isLoading) {
                                            handleAddAgent(agent.id);
                                          }
                                        }}
                                      />
                                      <FlexItem>
                                        <span>{agent.name}</span>
                                        {isLoading && <Spinner size="sm" style={{ marginLeft: '8px' }} />}
                                        {hasError && (
                                          <span style={{ color: 'red', fontSize: '0.8em', marginLeft: '8px' }}>
                                            {hasError}
                                          </span>
                                        )}
                                      </FlexItem>
                                    </Flex>
                                  </DropdownItem>
                                );
                              })}
                            </DropdownList>
                          </Dropdown>
                        </FlexItem>
                        <FlexItem>
                          {userProfile.agent_ids && userProfile.agent_ids.length > 0 ? (
                            <LabelGroup>
                              {userProfile.agent_ids.map((agentId) => {
                                const agent = availableAgents.find(a => a.id === agentId);
                                const isLoading = agentLoading[agentId];

                                return (
                                  <Label
                                    key={agentId}
                                    color="blue"
                                    onClose={isLoading ? undefined : () => handleRemoveAgent(agentId)}
                                    closeBtnAriaLabel={`Remove ${agent?.name || agentId}`}
                                  >
                                    {agent?.name || agentId}
                                    {isLoading && <Spinner size="sm" style={{ marginLeft: '8px' }} />}
                                  </Label>
                                );
                              })}
                            </LabelGroup>
                          ) : (
                            <span style={{ color: '#6a6e73', fontStyle: 'italic' }}>No agents assigned</span>
                          )}
                        </FlexItem>
                      </Flex>
                    </DescriptionListDescription>
                  </DescriptionListGroup>
                  <DescriptionListGroup>
                    <DescriptionListTerm>Created</DescriptionListTerm>
                    <DescriptionListDescription>{new Date(userProfile.created_at).toLocaleString()}</DescriptionListDescription>
                  </DescriptionListGroup>
                  <DescriptionListGroup>
                    <DescriptionListTerm>Updated</DescriptionListTerm>
                    <DescriptionListDescription>{new Date(userProfile.updated_at).toLocaleString()}</DescriptionListDescription>
                  </DescriptionListGroup>
                </DescriptionList>
              </CardBody>
            </Card>
          </FlexItem>
        </Flex>
      </PageSection>
    );
  }

  // Users list view
  return (
    <PageSection>
      <Flex direction={{ default: 'column' }} gap={{ default: 'gapMd' }}>
        <FlexItem>
          <Title headingLevel="h1">Users</Title>
        </FlexItem>
        <FlexItem>
          <Card>
            <CardHeader>
              <CardTitle>All Users</CardTitle>
            </CardHeader>
            <CardBody>
              {users.length === 0 ? (
                <Alert variant="info" title="No users found" />
              ) : (
                <DataList aria-label="Users list">
                  {users.map((user) => (
                    <DataListItem key={user.id} aria-labelledby={`user-${user.id}`}>
                      <DataListItemRow>
                        <DataListItemCells
                          dataListCells={[
                            <DataListCell key="username">
                              @{user.username}
                            </DataListCell>,
                            <DataListCell key="email">
                              {user.email}
                            </DataListCell>,
                            <DataListCell key="role">
                              {user.role || 'User'}
                            </DataListCell>,
                            <DataListCell key="agents">
                              {user.agent_ids ? `${user.agent_ids.length} agent${user.agent_ids.length !== 1 ? 's' : ''}` : '0 agents'}
                            </DataListCell>,
                            <DataListCell key="actions">
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleUserClick(user)}
                              >
                                View Profile
                              </Button>
                            </DataListCell>
                          ]}
                        />
                      </DataListItemRow>
                    </DataListItem>
                  ))}
                </DataList>
              )}
            </CardBody>
          </Card>
        </FlexItem>
      </Flex>
    </PageSection>
  );
}
