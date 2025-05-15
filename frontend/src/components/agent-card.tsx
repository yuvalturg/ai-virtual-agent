import { Agent } from '@/routes/config/agents';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  Dropdown,
  DropdownItem,
  DropdownList,
  Flex,
  FlexItem,
  Icon,
  MenuToggle,
  MenuToggleElement,
  Modal,
  ModalBody,
  ModalFooter,
  ModalHeader,
  Title,
} from '@patternfly/react-core';
import { EditIcon, EllipsisVIcon, TrashIcon } from '@patternfly/react-icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Fragment, useState } from 'react';
import { AgentForm } from './agent-form';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(false);

  const queryClient = useQueryClient();

  const editAgent = async (agentProps: Agent): Promise<Agent> => {
    // Replace with actual API call
    console.log('editing agent:', agentProps);
    await new Promise((resolve) => setTimeout(resolve, 700)); // Simulate network delay
    // This is a mock response, in a real scenario, the backend would probably return the created agent with an id
    const editedAgent: Agent = { ...agentProps };
    return editedAgent;
    // const response = await fetch(AGENTS_API_ENDPOINT, {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify(newAgent),
    // });
    // if (!response.ok) {
    //   throw new Error('Network response was not ok');
    // }
    // return response.json();
  };

  // Mutation for editing an Agent
  const agentMutation = useMutation<Agent, Error, Agent>({
    mutationFn: editAgent,
    onSuccess: (editedAgentData) => {
      // Invalidate and refetch the agents list to show the new agent
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      // Or, for optimistic updates:
      // queryClient.setQueryData(['agents'], (oldData: Agent[] | undefined) =>
      //   oldData ? [...oldData, newAgentData] : [newAgentData]
      // );
      console.log('Agent edited successfully:', editedAgentData);
      // Optionally reset form or show a success message
    },
    onError: (error) => {
      console.error('Error editing agent:', error);
      // Optionally show an error message
    },
  });

  const handleEditAgent = (values: Agent) => {
    if (!values.model_name) {
      // Or handle this validation within the form itself
      alert('Please select a model.');
      return;
    }
    agentMutation.mutate(values);
  };

  const toggleModal = () => {
    setModalOpen(!modalOpen);
  };
  const toggleDropdown = () => {
    setDropdownOpen(!dropdownOpen);
  };

  return (
    <Card>
      {!editing ? (
        <Fragment>
          <CardHeader>
            <Flex justifyContent={{ default: 'justifyContentSpaceBetween' }}>
              <FlexItem>
                <CardTitle>
                  <Title className="pf-v6-u-mb-sm" headingLevel="h2">
                    {agent.name}
                  </Title>
                </CardTitle>
              </FlexItem>
              <FlexItem>
                <Dropdown
                  isOpen={dropdownOpen}
                  onOpenChange={(isOpen: boolean) => setDropdownOpen(isOpen)}
                  toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                    <MenuToggle
                      ref={toggleRef}
                      aria-label="kebab dropdown toggle"
                      variant="plain"
                      onClick={toggleDropdown}
                      isExpanded={dropdownOpen}
                      icon={
                        <Icon iconSize="lg">
                          <EllipsisVIcon />
                        </Icon>
                      }
                    />
                  )}
                  shouldFocusToggleOnSelect
                  popperProps={{ position: 'right' }}
                >
                  <DropdownList>
                    <DropdownItem icon={<EditIcon />} value={0} key="edit">
                      Edit
                    </DropdownItem>
                    <DropdownItem
                      isDanger
                      onClick={() => {
                        toggleModal();
                        toggleDropdown();
                      }}
                      icon={<TrashIcon />}
                      value={1}
                      key="delete"
                    >
                      Delete
                    </DropdownItem>
                  </DropdownList>
                </Dropdown>
                <Modal
                  isOpen={modalOpen}
                  onClose={toggleModal}
                  variant="small"
                  aria-labelledby="delete-agent-modal-title"
                  aria-describedby="delete-agent-modal-desc"
                >
                  <ModalHeader title="Delete Agent" labelId="delete-agent-modal-title" />
                  <ModalBody id="delete-agent-modal-desc">
                    Are you sure you want to delete this AI agent? This action cannot be undone.
                  </ModalBody>
                  <ModalFooter>
                    <Button variant="danger">Delete</Button>
                    <Button variant="link" onClick={toggleModal}>
                      Cancel
                    </Button>
                  </ModalFooter>
                </Modal>
              </FlexItem>
            </Flex>
            <Title className="pf-v6-u-text-color-subtle" headingLevel="h4">
              {agent.model_name}
            </Title>
          </CardHeader>
          <CardBody>
            <Flex direction={{ default: 'column' }}>
              <FlexItem>{agent.prompt}</FlexItem>
              <FlexItem>{agent.knowledge_base_ids.map((kb) => kb)}</FlexItem>
              <FlexItem>{agent.tool_ids.map((tool) => tool)}</FlexItem>
            </Flex>
          </CardBody>
        </Fragment>
      ) : (
        <Fragment>
          <CardHeader>Edit Agent</CardHeader>
          <CardBody>
            <AgentForm
              defaultAgentProps={agent}
              isSubmitting={agentMutation.isPending}
              onSubmit={handleEditAgent}
            />
          </CardBody>
        </Fragment>
      )}
    </Card>
  );
}
