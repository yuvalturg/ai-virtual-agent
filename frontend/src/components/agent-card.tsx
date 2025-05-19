import { Agent } from '@/routes/config/agents';
import { deleteAgent, editAgent, UpdateAgentProps } from '@/services/agents';
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
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Fragment, useState } from 'react';
import { AgentForm } from './agent-form';
import { fetchModels } from '@/services/models';
import { fetchKnowledgeBases } from '@/services/knowledge-bases';
import { fetchTools } from '@/services/tools';
import { KnowledgeBase, Model, Tool } from '@/types';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(false);

  const queryClient = useQueryClient();

  // Query for AI Models
  const {
    data: models,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useQuery<Model[], Error>({
    queryKey: ['models'],
    queryFn: fetchModels,
  });
  // Query for Knowledge bases
  const {
    data: knowledgeBases,
    isLoading: isLoadingKnowledgeBases,
    error: knowledgeBasesError,
  } = useQuery<KnowledgeBase[], Error>({
    queryKey: ['knowledgeBases'],
    queryFn: fetchKnowledgeBases,
  });
  // Query for tools
  const {
    data: tools,
    isLoading: isLoadingTools,
    error: toolsError,
  } = useQuery<Tool[], Error>({
    queryKey: ['tools'],
    queryFn: fetchTools,
  });

  // Mutation for editing an Agent
  const editAgentMutation = useMutation<Agent, Error, UpdateAgentProps>({
    mutationFn: editAgent,
    onSuccess: (editedAgentData) => {
      // Invalidate and refetch the agents list to show the new agent
      void queryClient.invalidateQueries({ queryKey: ['agents'] });
      setEditing(false);
      console.log('Agent edited successfully:', editedAgentData);
    },
    onError: (error) => {
      console.error('Error editing agent:', error);
      // Optionally show an error message
    },
  });

  // Mutation for deleting an Agent
  const deleteAgentMutation = useMutation<void, Error, string>({
    mutationFn: deleteAgent,
    onSuccess: () => {
      // Invalidate and refetch the agents list to show the new agent
      void queryClient.invalidateQueries({ queryKey: ['agents'] });
      setModalOpen(false);
      console.log('Agent deleted successfully');
    },
    onError: (error) => {
      console.error('Error deleting agent:', error);
      // Optionally show an error message
    },
  });

  const handleEditAgent = (values: UpdateAgentProps) => {
    editAgentMutation.mutate(values);
  };
  const handleDeleteAgent = () => {
    deleteAgentMutation.mutate(agent.id);
  };

  const toggleModal = () => {
    setModalOpen(!modalOpen);
  };
  const toggleDropdown = () => {
    setDropdownOpen(!dropdownOpen);
  };
  const toggleEditing = () => {
    setEditing(!editing);
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
                    <DropdownItem
                      onClick={() => {
                        toggleEditing();
                        setDropdownOpen(false);
                      }}
                      icon={<EditIcon />}
                      value={0}
                      key="edit"
                    >
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
                    <Button
                      isLoading={deleteAgentMutation.isPending}
                      onClick={handleDeleteAgent}
                      variant="danger"
                    >
                      Delete
                    </Button>
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
              <FlexItem>
                <span className="pf-v6-u-text-color-subtle">Knowledge Bases: </span>
                {agent.prompt}
              </FlexItem>
              <FlexItem>
                <span className="pf-v6-u-text-color-subtle">Knowledge Bases: </span>
                {agent.knowledge_base_ids.length > 0
                  ? agent.knowledge_base_ids.map((kb) => kb)
                  : 'None'}
              </FlexItem>
              <FlexItem>
                <span className="pf-v6-u-text-color-subtle">Tools: </span>
                {agent.tool_ids.length > 0 ? agent.tool_ids.map((tool) => tool) : 'None'}
              </FlexItem>
            </Flex>
          </CardBody>
        </Fragment>
      ) : (
        <Fragment>
          <CardHeader>
            <Title headingLevel="h3">Edit {agent.name}</Title>
          </CardHeader>
          <CardBody>
            <AgentForm
              defaultAgentProps={agent}
              modelsProps={{
                models: models || [],
                isLoadingModels,
                modelsError,
              }}
              knowledgeBasesProps={{
                knowledgeBases: knowledgeBases || [],
                isLoadingKnowledgeBases,
                knowledgeBasesError,
              }}
              toolsProps={{
                tools: tools || [],
                isLoadingTools,
                toolsError,
              }}
              isSubmitting={editAgentMutation.isPending}
              onSubmit={handleEditAgent}
              onCancel={toggleEditing}
            />
          </CardBody>
        </Fragment>
      )}
    </Card>
  );
}
