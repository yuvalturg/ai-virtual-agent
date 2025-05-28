import { useForm } from '@tanstack/react-form';
import { EmbeddingModel, KnowledgeBase, Provider } from '@/types';
import { Button, ActionGroup, Form, FormGroup, TextInput, Alert } from '@patternfly/react-core';
import {
  FormSelect,
  FormSelectOption,
} from '@patternfly/react-core/dist/esm/components/FormSelect';
import { Fragment } from 'react';

// Define source options at the top for easy configuration
const KB_SOURCE_OPTIONS = [
  { value: '', label: 'Select a source', disabled: true },
  { value: 'S3', label: 'S3', disabled: false },
  { value: 'GITHUB', label: 'GITHUB', disabled: false },
  { value: 'URL', label: 'URL', disabled: false },
];

interface EmbeddingModelsFieldProps {
  models: EmbeddingModel[];
  isLoadingModels: boolean;
  modelsError: Error | null;
}

interface ProvidersFieldProps {
  providers: Provider[];
  isLoadingProviders: boolean;
  providersError: Error | null;
}

interface KnowledgeBaseFormProps {
  embeddingModelProps: EmbeddingModelsFieldProps;
  providersProps: ProvidersFieldProps;
  defaultKnowledgeBase?: KnowledgeBase;
  isSubmitting: boolean;
  onSubmit: (values: KnowledgeBase) => void;
  onCancel: () => void;
  error?: Error | null;
}

export function KnowledgeBaseForm({
  embeddingModelProps,
  providersProps,
  defaultKnowledgeBase,
  isSubmitting,
  onSubmit,
  onCancel,
  error,
}: KnowledgeBaseFormProps) {
  const { models, isLoadingModels, modelsError } = embeddingModelProps;
  const { providers, isLoadingProviders, providersError } = providersProps;

  const initialData: KnowledgeBase = defaultKnowledgeBase ?? {
    name: '',
    version: '',
    embedding_model: '',
    provider_id: '',
    vector_db_name: '',
    is_external: false,
    source: '',
    source_configuration: '{}',
  };

  const form = useForm({
    defaultValues: initialData,
    onSubmit: ({ value }) => {
      // Parse source_configuration JSON string into object before submitting
      try {
        const parsedValue = {
          ...value,
          source_configuration: JSON.parse(value.source_configuration || '{}'),
        };
        onSubmit(parsedValue);
      } catch (error) {
        console.error('Invalid JSON in source_configuration:', error);
        // Don't submit if JSON is invalid - let the form validation handle it
      }
    },
  });

  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
    >
      {error && <Alert variant="danger" title={error.message} />}
      <form.Field
        name="name"
        validators={{ onChange: ({ value }) => (!value ? 'Name is required' : undefined) }}
      >
        {(field) => (
          <FormGroup label="Name" isRequired fieldId="kb-form-name">
            <TextInput
              isRequired
              id="kb-form-name"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            />
          </FormGroup>
        )}
      </form.Field>
      <form.Field
        name="version"
        validators={{ onChange: ({ value }) => (!value ? 'Version is required' : undefined) }}
      >
        {(field) => (
          <FormGroup label="Version" isRequired fieldId="kb-form-version">
            <TextInput
              isRequired
              id="kb-form-version"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            />
          </FormGroup>
        )}
      </form.Field>
      <form.Field
        name="embedding_model"
        validators={{
          onChange: ({ value }) => (!value ? 'Embedding Model is required' : undefined),
        }}
      >
        {(field) => (
          <FormGroup label="Embedding Model" isRequired fieldId="kb-form-embedding-model">
            <FormSelect
              isRequired
              id="kb-form-embedding-model"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
              aria-label="Select Embedding Model"
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            >
              {isLoadingModels ? (
                <FormSelectOption key="loading" value="" label="Loading models..." isDisabled />
              ) : modelsError ? (
                <FormSelectOption key="error" value="" label="Error loading models" isDisabled />
              ) : (
                <Fragment>
                  <FormSelectOption key="placeholder" value="" label="Select a model" isDisabled />
                  {models.map((opt) => (
                    <FormSelectOption key={opt.name} value={opt.name} label={opt.name} />
                  ))}
                </Fragment>
              )}
            </FormSelect>
          </FormGroup>
        )}
      </form.Field>
      <form.Field
        name="provider_id"
        validators={{ onChange: ({ value }) => (!value ? 'Provider ID is required' : undefined) }}
      >
        {(field) => (
          <FormGroup label="Provider" isRequired fieldId="kb-form-provider-id">
            <FormSelect
              isRequired
              id="kb-form-provider-id"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
              aria-label="Select Provider"
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            >
              {isLoadingProviders ? (
                <FormSelectOption key="loading" value="" label="Loading providers..." isDisabled />
              ) : providersError ? (
                <FormSelectOption key="error" value="" label="Error loading providers" isDisabled />
              ) : (
                <Fragment>
                  <FormSelectOption
                    key="placeholder"
                    value=""
                    label="Select a provider"
                    isDisabled
                  />
                  {providers.map((provider) => (
                    <FormSelectOption
                      key={provider.provider_id}
                      value={provider.provider_id}
                      label={`${provider.provider_id} (${provider.provider_type})`}
                    />
                  ))}
                </Fragment>
              )}
            </FormSelect>
          </FormGroup>
        )}
      </form.Field>
      <form.Field
        name="vector_db_name"
        validators={{
          onChange: ({ value }) => (!value ? 'Vector DB Name is required' : undefined),
        }}
      >
        {(field) => (
          <FormGroup label="Vector DB Name" isRequired fieldId="kb-form-vector-db-name">
            <TextInput
              isRequired
              id="kb-form-vector-db-name"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            />
          </FormGroup>
        )}
      </form.Field>
      <form.Field
        name="source"
        validators={{ onChange: ({ value }) => (!value ? 'Source is required' : undefined) }}
      >
        {(field) => (
          <FormGroup label="Source" isRequired fieldId="kb-form-source">
            <FormSelect
              isRequired
              id="kb-form-source"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
              aria-label="Select Source"
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            >
              {KB_SOURCE_OPTIONS.map((opt) => (
                <FormSelectOption
                  key={opt.value}
                  value={opt.value}
                  label={opt.label}
                  isDisabled={opt.disabled}
                />
              ))}
            </FormSelect>
          </FormGroup>
        )}
      </form.Field>
      <form.Field
        name="source_configuration"
        validators={{
          onChange: ({ value }) => {
            if (!value) return 'Source Configuration is required';
            try {
              JSON.parse(value);
              return undefined;
            } catch {
              return 'Source Configuration must be valid JSON';
            }
          },
        }}
      >
        {(field) => (
          <FormGroup label="Source Configuration (JSON)" isRequired fieldId="kb-form-source-config">
            <TextInput
              isRequired
              id="kb-form-source-config"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v)}
              isDisabled={form.state.values.is_external}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
            />
          </FormGroup>
        )}
      </form.Field>
      <ActionGroup>
        <form.Subscribe
          selector={(state) => [state.canSubmit, state.isSubmitting, state.isPristine]}
        >
          {([canSubmit, isSubmitting, isPristine]) => (
            <Button
              type="submit"
              variant="primary"
              isDisabled={!canSubmit || isSubmitting || isPristine}
              isLoading={isSubmitting}
            >
              Save
            </Button>
          )}
        </form.Subscribe>
        <Button variant="link" onClick={onCancel} isDisabled={isSubmitting}>
          Cancel
        </Button>
      </ActionGroup>
    </Form>
  );
}
