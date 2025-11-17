import { Model, ModelCreate } from '@/types/models';
import {
  Card,
  CardBody,
  CardExpandableContent,
  CardHeader,
  CardTitle,
  Flex,
  FlexItem,
  Title,
} from '@patternfly/react-core';
import { PlusIcon } from '@patternfly/react-icons';
import { useState, useEffect } from 'react';
import { ModelForm } from './ModelForm';
import { useModelsManagement } from '@/hooks/useModelsManagement';

interface NewModelCardProps {
  editingModel?: Model | null;
  onEditComplete?: () => void;
}

export function NewModelCard({ editingModel, onEditComplete }: NewModelCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Use custom hooks
  const {
    createModel,
    updateModel,
    isCreating,
    isUpdating,
    createError,
    updateError,
    resetCreateError,
    resetUpdateError,
  } = useModelsManagement();

  // Open card when editing model is set
  useEffect(() => {
    if (editingModel) {
      setIsOpen(true);
    }
  }, [editingModel]);

  // Clear errors when switching between create/edit or changing which model is being edited
  useEffect(() => {
    resetCreateError();
    resetUpdateError();
  }, [editingModel, resetCreateError, resetUpdateError]);

  const handleSubmit = (values: ModelCreate) => {
    void (async () => {
      try {
        if (editingModel) {
          // Update existing model
          await updateModel(editingModel.model_id, {
            provider_id: values.provider_id,
            provider_model_id: values.provider_model_id,
            metadata: values.metadata,
          });
          console.log('Model updated successfully');
          onEditComplete?.();
        } else {
          // Create new model
          await createModel(values);
          console.log('Model created successfully');
        }
        setIsOpen(false);
      } catch (error) {
        console.error('Error with model operation:', error);
      }
    })();
  };

  const handleCancel = () => {
    resetCreateError();
    resetUpdateError();
    setIsOpen(false);
    onEditComplete?.();
  };

  const isSubmitting = isCreating || isUpdating;
  const error = createError || updateError;

  return (
    <Card isExpanded={isOpen} isClickable={!isOpen} style={{ overflow: 'visible' }}>
      <CardHeader
        selectableActions={{
          onClickAction: () => setIsOpen(!isOpen),
          selectableActionAriaLabelledby: 'clickable-model-card-title-1',
        }}
      >
        <CardTitle>
          {!isOpen ? (
            <Flex>
              <FlexItem>
                <PlusIcon />
              </FlexItem>
              <FlexItem>
                <Title headingLevel="h3">
                  {editingModel ? `Edit ${editingModel.model_id}` : 'Register New Model'}
                </Title>
              </FlexItem>
            </Flex>
          ) : (
            <Title headingLevel="h3">
              {editingModel ? `Edit ${editingModel.model_id}` : 'Register New Model'}
            </Title>
          )}
        </CardTitle>
      </CardHeader>
      <CardExpandableContent style={{ overflow: 'visible' }}>
        <CardBody style={{ overflow: 'visible' }}>
          <ModelForm
            defaultModel={editingModel || undefined}
            isSubmitting={isSubmitting}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            error={error}
            isEditing={!!editingModel}
          />
        </CardBody>
      </CardExpandableContent>
    </Card>
  );
}
