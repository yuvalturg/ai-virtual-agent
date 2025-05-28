import { Agent } from '@/routes/config/agents';
import { deleteAgent, editAgent, UpdateAgentProps } from '@/services/agents';
import {
  Button,
  Card,
  CardBody,
  CardExpandableContent,
  CardHeader,
  CardTitle,
  Dropdown,
  DropdownItem,
  DropdownList,
  Flex,
  FlexItem,
  Label,
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
  const [isExpanded, setIsExpanded] = useState(false);

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
  const toggleEditing = () => {
    setEditing(!editing);
  };

  const onExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const onSelect = () => setDropdownOpen(!dropdownOpen);

  return (
    <Fragment>
      <Card id={`expandable-agent-card-${agent.id}`} isExpanded={isExpanded}>
        {!editing ? (
          <Fragment>
            <CardHeader
              actions={{
                actions: (
                  <Dropdown
                    onSelect={onSelect}
                    toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                      <MenuToggle
                        ref={toggleRef}
                        isExpanded={dropdownOpen}
                        onClick={() => setDropdownOpen(!dropdownOpen)}
                        variant="plain"
                        aria-label="Card kebab toggle"
                        icon={<EllipsisVIcon />}
                      />
                    )}
                    isOpen={dropdownOpen}
                    onOpenChange={(isOpen: boolean) => setDropdownOpen(isOpen)}
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
                          setDropdownOpen(false);
                        }}
                        icon={<TrashIcon />}
                        value={1}
                        key="delete"
                      >
                        Delete
                      </DropdownItem>
                    </DropdownList>
                  </Dropdown>
                ),
              }}
              onExpand={onExpand}
              toggleButtonProps={{
                id: `toggle-agent-button-${agent.id}`,
                'aria-label': 'Details',
                'aria-labelledby': `expandable-agent-title-${agent.id} toggle-agent-button-${agent.id}`,
                'aria-expanded': isExpanded,
              }}
            >
              <CardTitle id={`expandable-agent-title-${agent.id}`}>
                <Flex gap={{ default: 'gapMd' }} alignItems={{ default: 'alignItemsCenter' }}>
                  <FlexItem>
                    <Title headingLevel="h2" size="lg">
                      {agent.name}
                    </Title>
                  </FlexItem>
                  <FlexItem>
                    <Title className="pf-v6-u-text-color-subtle" headingLevel="h5" size="md">
                      {agent.model_name}
                    </Title>
                  </FlexItem>
                </Flex>
              </CardTitle>
            </CardHeader>
            <CardExpandableContent>
              <CardBody>
                <Flex direction={{ default: 'column' }}>
                  <FlexItem>
                    <span className="pf-v6-u-text-color-subtle">Prompt: </span>
                    {agent.prompt}
                  </FlexItem>
                  <FlexItem>
                    <Flex gap={{ default: 'gapSm' }}>
                      <FlexItem>
                        <span className="pf-v6-u-text-color-subtle">Knowledge Bases: </span>
                      </FlexItem>
                      {agent.knowledge_base_ids.length > 0
                        ? agent.knowledge_base_ids.map((kb) => (
                            <FlexItem key={kb}>
                              <Label color="blue">{kb}</Label>
                            </FlexItem>
                          ))
                        : 'None'}
                    </Flex>
                  </FlexItem>
                  <FlexItem>
                    <Flex gap={{ default: 'gapSm' }}>
                      <FlexItem>
                        <span className="pf-v6-u-text-color-subtle">Tools: </span>
                      </FlexItem>
                      {agent.tools.length > 0
                        ? agent.tools.map((tool, index) => (
                            <FlexItem key={index}>
                              <Label color="orange">{tool.toolgroup_id}</Label>
                            </FlexItem>
                          ))
                        : 'None'}
                    </Flex>
                  </FlexItem>
                </Flex>
              </CardBody>
            </CardExpandableContent>
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
    </Fragment>
  );
}
