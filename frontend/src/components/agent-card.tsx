import { Agent } from '@/routes/config/agents';
import {
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
  Title,
} from '@patternfly/react-core';
import { EditIcon, EllipsisVIcon, TrashIcon } from '@patternfly/react-icons';
import { useState } from 'react';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const onDropdownToggleClick = () => {
    setDropdownOpen(!dropdownOpen);
  };

  const onDropdownSelect = (
    _event: React.MouseEvent<Element, MouseEvent> | undefined,
    value: string | number | undefined
  ) => {
    console.log('selected', value);
    setDropdownOpen(false);
  };
  return (
    <Card>
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
              onSelect={onDropdownSelect}
              onOpenChange={(isOpen: boolean) => setDropdownOpen(isOpen)}
              toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
                <MenuToggle
                  ref={toggleRef}
                  aria-label="kebab dropdown toggle"
                  variant="plain"
                  onClick={onDropdownToggleClick}
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
                <DropdownItem isDanger icon={<TrashIcon />} value={1} key="delete">
                  Delete
                </DropdownItem>
              </DropdownList>
            </Dropdown>
          </FlexItem>
        </Flex>
        <Title className="pf-v6-u-text-color-subtle" headingLevel="h3">
          {agent.modelId}
        </Title>
      </CardHeader>
      <CardBody>Here is some info about the agent</CardBody>
    </Card>
  );
}
