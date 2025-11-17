import { useForm } from '@tanstack/react-form';
import { useEffect } from 'react';
import { Model, ModelCreate, ModelType } from '@/types/models';
import {
  Button,
  ActionGroup,
  Form,
  FormGroup,
  TextInput,
  TextArea,
  Alert,
  FormSelect,
  FormSelectOption,
} from '@patternfly/react-core';
import { PaperPlaneIcon } from '@patternfly/react-icons';
import { useModelsManagement } from '@/hooks/useModelsManagement';

interface ModelFormProps {
  defaultModel?: Model;
  isSubmitting: boolean;
  onSubmit: (values: ModelCreate) => void;
  onCancel: () => void;
  error?: Error | null;
  isEditing?: boolean;
}

export function ModelForm({
  defaultModel,
  isSubmitting,
  onSubmit,
  onCancel,
  error,
  isEditing = false,
}: ModelFormProps) {
  const { providers, isLoadingProviders } = useModelsManagement();

  // Filter to only show inference providers
  const inferenceProviders = providers?.filter((p) => p.api === 'inference') || [];

  const initialData: ModelCreate = defaultModel
    ? {
        model_id: defaultModel.model_id,
        provider_id: defaultModel.provider_id,
        provider_model_id: defaultModel.provider_model_id,
        model_type: defaultModel.model_type,
        metadata: defaultModel.metadata || {},
      }
    : {
        model_id: '',
        provider_id: null,
        provider_model_id: null,
        model_type: 'llm' as ModelType,
        metadata: {},
      };

  const form = useForm({
    defaultValues: initialData,
    onSubmit: ({ value }) => {
      const finalValue = { ...value };

      // If metadata is a string, try to parse it as JSON
      if (typeof value.metadata === 'string') {
        try {
          finalValue.metadata = value.metadata
            ? (JSON.parse(value.metadata) as Record<string, unknown>)
            : {};
        } catch (_e) {
          finalValue.metadata = {};
        }
      }

      // Auto-generate model_id from provider_id and provider_model_id if not editing
      if (!isEditing && value.provider_id && value.provider_model_id) {
        finalValue.model_id = `${value.provider_id}/${value.provider_model_id}`;
      }

      onSubmit(finalValue);
    },
  });

  // Reset form when defaultModel changes
  useEffect(() => {
    if (defaultModel) {
      const newData: ModelCreate = {
        model_id: defaultModel.model_id,
        provider_id: defaultModel.provider_id,
        provider_model_id: defaultModel.provider_model_id,
        model_type: defaultModel.model_type,
        metadata: defaultModel.metadata || {},
      };

      form.reset();
      (
        Object.entries(newData) as [keyof ModelCreate, string | Record<string, unknown> | null][]
      ).forEach(([key, value]) => {
        form.setFieldValue(key, value);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultModel]);

  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
    >
      {error && <Alert variant="danger" title={error.message} />}

      {isEditing && (
        <Alert variant="info" title="Editing Model" isInline>
          Model ID: {defaultModel?.model_id}
        </Alert>
      )}

      {/* Model Type field */}
      <form.Field
        name="model_type"
        validators={{
          onChange: ({ value }) => (!value ? 'Model type is required' : undefined),
        }}
      >
        {(field) => (
          <FormGroup label="Model Type" isRequired fieldId="model-form-type">
            <FormSelect
              id="model-form-type"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v as ModelType)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
              isDisabled={isEditing}
            >
              <FormSelectOption value="llm" label="LLM (Large Language Model)" />
            </FormSelect>
            {field.state.meta.errors.length > 0 && (
              <div style={{ color: '#c9190b', fontSize: '14px', marginTop: '4px' }}>
                {field.state.meta.errors[0]}
              </div>
            )}
          </FormGroup>
        )}
      </form.Field>

      {/* Provider ID field */}
      <form.Field
        name="provider_id"
        validators={{
          onChange: ({ value }) => (!value ? 'Provider is required' : undefined),
        }}
      >
        {(field) => (
          <FormGroup label="Provider" isRequired fieldId="model-form-provider">
            <FormSelect
              id="model-form-provider"
              value={field.state.value || ''}
              onChange={(_e, v) => field.handleChange(v || null)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
              isDisabled={isLoadingProviders}
            >
              <FormSelectOption value="" label="Select a provider" isDisabled />
              {inferenceProviders.map((provider) => (
                <FormSelectOption
                  key={provider.provider_id}
                  value={provider.provider_id}
                  label={`${provider.provider_id} (${provider.api} - ${provider.provider_type})`}
                />
              ))}
            </FormSelect>
            {field.state.meta.errors.length > 0 && (
              <div style={{ color: '#c9190b', fontSize: '14px', marginTop: '4px' }}>
                {field.state.meta.errors[0]}
              </div>
            )}
          </FormGroup>
        )}
      </form.Field>

      {/* Provider Model ID field */}
      <form.Field name="provider_model_id">
        {(field) => (
          <FormGroup label="Provider Model ID" fieldId="model-form-provider-model">
            <TextInput
              id="model-form-provider-model"
              value={field.state.value || ''}
              onChange={(_e, v) => field.handleChange(v || null)}
              placeholder="e.g., meta-llama/Llama-3-8b-Instruct"
            />
          </FormGroup>
        )}
      </form.Field>

      {/* Metadata field */}
      <form.Field
        name="metadata"
        validators={{
          onChange: ({ value }) => {
            if (!value || typeof value !== 'string') return undefined;
            if (value === '') return undefined;
            try {
              JSON.parse(value);
              return undefined;
            } catch {
              return 'Invalid JSON format';
            }
          },
        }}
      >
        {(field) => (
          <FormGroup label="Metadata (JSON)" fieldId="model-form-metadata">
            <TextArea
              id="model-form-metadata"
              value={
                typeof field.state.value === 'string'
                  ? field.state.value
                  : JSON.stringify(field.state.value || {}, null, 2)
              }
              onChange={(_e, v) => field.handleChange(v as unknown as Record<string, unknown>)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
              rows={4}
              placeholder='{"max_tokens": 4096, "temperature": 0.7}'
            />
            {field.state.meta.errors.length > 0 && (
              <div style={{ color: '#c9190b', fontSize: '14px', marginTop: '4px' }}>
                {field.state.meta.errors[0]}
              </div>
            )}
          </FormGroup>
        )}
      </form.Field>

      <ActionGroup>
        <form.Subscribe
          selector={(state) => [
            state.isSubmitting,
            state.values.provider_id,
            state.values.provider_model_id,
            state.errors,
          ]}
        >
          {([isSubmittingForm, provider_id, provider_model_id, errors]) => {
            const hasRequiredFields = Boolean(provider_id && provider_model_id);
            const hasErrors = Array.isArray(errors) && errors.length > 0;
            const shouldDisable = Boolean(isSubmittingForm) || !hasRequiredFields || hasErrors;

            return (
              <Button
                icon={<PaperPlaneIcon />}
                type="submit"
                variant="primary"
                isDisabled={Boolean(shouldDisable)}
                isLoading={Boolean(isSubmitting || isSubmittingForm)}
              >
                {isEditing ? 'Update' : 'Register'}
              </Button>
            );
          }}
        </form.Subscribe>
        <Button variant="link" onClick={onCancel} isDisabled={isSubmitting}>
          Cancel
        </Button>
      </ActionGroup>
    </Form>
  );
}
