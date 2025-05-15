import { Agent, NewAgent } from '@/routes/config/agents';
import {
  ActionGroup,
  Alert,
  Button,
  Form,
  FormGroup,
  FormSelect,
  FormSelectOption,
  TextArea,
  TextInput,
} from '@patternfly/react-core';
import { useForm } from '@tanstack/react-form';
import { Fragment, useMemo } from 'react';
import { CustomSelectOptionProps, MultiSelect } from './multi-select';

interface ModelsFieldProps {
  models: string[];
  isLoadingModels: boolean;
  modelsError: Error | null;
}

interface KnowledgeBase {
  id: string;
  name: string;
  provider_id: string;
  type: string;
  embedding_model: string;
}

interface KnowledgeBasesFieldProps {
  knowledgeBases: KnowledgeBase[];
  isLoadingKnowledgeBases: boolean;
  knowledgeBasesError: Error | null;
}

interface Tool {
  id: string;
  name: string;
  title: string;
}

interface ToolsFieldProps {
  tools: Tool[];
  isLoadingTools: boolean;
  toolsError: Error | null;
}

interface AgentFormProps {
  defaultAgentProps?: Agent | undefined;
  modelsProps: ModelsFieldProps;
  knowledgeBasesProps: KnowledgeBasesFieldProps;
  toolsProps: ToolsFieldProps;
  onSubmit: (values: NewAgent | Agent) => void;
  isSubmitting: boolean;
  onCancel: () => void;
}

export function AgentForm({
  defaultAgentProps,
  modelsProps,
  knowledgeBasesProps,
  toolsProps,
  onSubmit,
  isSubmitting,
  onCancel,
}: AgentFormProps) {
  const { models, isLoadingModels, modelsError } = modelsProps;
  const { knowledgeBases, isLoadingKnowledgeBases, knowledgeBasesError } = knowledgeBasesProps;
  const { tools, isLoadingTools, toolsError } = toolsProps;

  const initialAgentData: NewAgent = defaultAgentProps ?? {
    name: '',
    model_name: '',
    prompt: '',
    knowledge_base_ids: [],
    tool_ids: [],
  };

  const form = useForm({
    defaultValues: initialAgentData,
    onSubmit: async ({ value }) => {
      onSubmit(value);
    },
  });

  const handleCancel = () => {
    onCancel();
    form.reset();
  };

  const knowledgeBaseOptions = useMemo((): CustomSelectOptionProps[] => {
    if (isLoadingKnowledgeBases) {
      return [
        {
          value: 'loading_kb',
          children: 'Loading knowledge bases...',
          isDisabled: true,
          id: 'loading_kb_opt',
        },
      ];
    }
    if (knowledgeBasesError) {
      return [
        {
          value: 'error_kb',
          children: 'Error loading knowledge bases',
          isDisabled: true,
          id: 'error_kb_opt',
        },
      ];
    }
    if (!knowledgeBases || knowledgeBases.length === 0) {
      return [
        {
          value: 'no_kb_options',
          children: 'No knowledge bases available',
          isDisabled: true,
          id: 'no_kb_options_opt',
        },
      ];
    }
    return knowledgeBases.map((kb) => ({
      value: kb.id, // The ID will be stored in form.knowledge_base_ids
      children: kb.name, // The name will be displayed
      id: `kb-option-${kb.id}`, // Unique ID for React key and ARIA
    }));
  }, [knowledgeBases, isLoadingKnowledgeBases, knowledgeBasesError]);

  const toolsOptions = useMemo((): CustomSelectOptionProps[] => {
    if (isLoadingTools) {
      return [
        {
          value: 'loading_tools',
          children: 'Loading tools...',
          isDisabled: true,
          id: 'loading_tools_opt',
        },
      ];
    }
    if (toolsError) {
      return [
        {
          value: 'error_tools',
          children: 'Error loading tools',
          isDisabled: true,
          id: 'error_tools_opt',
        },
      ];
    }
    if (!tools || tools.length === 0) {
      return [
        {
          value: 'no_tools_options',
          children: 'No tools available',
          isDisabled: true,
          id: 'no_tools_options_opt',
        },
      ];
    }
    return tools.map((tool) => ({
      value: tool.id, // The ID will be stored in form.tools_ids
      children: tool.name, // The name will be displayed
      id: `tools-option-${tool.id}`, // Unique ID for React key and ARIA
    }));
  }, [tools, isLoadingTools, toolsError]);

  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        form.handleSubmit();
      }}
    >
      <form.Field
        name="name"
        children={(field) => (
          <FormGroup label="Agent Name" isRequired fieldId="agent-name">
            <TextInput
              isRequired
              type="text"
              id="agent-name"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
            />
          </FormGroup>
        )}
      />

      <form.Field
        name="model_name"
        children={(field) => (
          <FormGroup label="Select AI Model" isRequired fieldId="ai-model">
            <FormSelect
              id="ai-model"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
              aria-label="Select AI Model"
              isDisabled={isLoadingModels || !!modelsError}
            >
              {isLoadingModels ? (
                <FormSelectOption key="loading" value="" label="Loading models..." isDisabled />
              ) : modelsError ? (
                <FormSelectOption key="error" value="" label="Error loading models" isDisabled />
              ) : (
                <Fragment>
                  <FormSelectOption key="placeholder" value="" label="Select a model" isDisabled />
                  {models.map((model) => (
                    <FormSelectOption key={model} value={model} label={model} />
                  ))}
                </Fragment>
              )}
            </FormSelect>
          </FormGroup>
        )}
      />

      <form.Field
        name="prompt"
        children={(field) => (
          <FormGroup label="Agent Prompt" isRequired fieldId="prompt">
            <TextArea
              isRequired
              type="text"
              id="prompt"
              name={field.name}
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(_event, value) => field.handleChange(value)}
            />
          </FormGroup>
        )}
      />
      <form.Field
        name="knowledge_base_ids" // This field expects string[]
        children={(field) => (
          <FormGroup
            label="Select Knowledge Bases"
            fieldId="knowledge-bases-multiselect" // Unique ID for the FormGroup
          >
            <MultiSelect
              id="knowledge-bases-multiselect-component" // Unique ID for the MultiSelect component itself
              value={field.state.value} // Pass the array of IDs
              options={knowledgeBaseOptions} // Pass the prepared options
              onBlur={field.handleBlur}
              onChange={(selectedIds) => field.handleChange(selectedIds)} // Pass the new array directly
              ariaLabel="Select Knowledge Bases"
              isDisabled={
                isLoadingKnowledgeBases ||
                knowledgeBasesError != null ||
                (knowledgeBases &&
                  knowledgeBases.length === 0 &&
                  !isLoadingKnowledgeBases &&
                  !knowledgeBasesError)
              }
              placeholder="Type or select knowledge bases..."
            />
          </FormGroup>
        )}
      />
      <form.Field
        name="tool_ids" // This field expects string[]
        children={(field) => (
          <FormGroup
            label="Select Tools"
            fieldId="tools-multiselect" // Unique ID for the FormGroup
          >
            <MultiSelect
              id="tools-multiselect-component" // Unique ID for the MultiSelect component itself
              value={field.state.value} // Pass the array of IDs
              options={toolsOptions} // Pass the prepared options
              onBlur={field.handleBlur}
              onChange={(selectedIds) => field.handleChange(selectedIds)} // Pass the new array directly
              ariaLabel="Select Tools"
              isDisabled={
                isLoadingTools ||
                toolsError != null ||
                (tools && tools.length === 0 && !isLoadingTools && !toolsError)
              }
              placeholder="Type or select tools..."
            />
          </FormGroup>
        )}
      />

      <ActionGroup>
        <Button
          variant="primary"
          type="submit"
          isLoading={isSubmitting}
          isDisabled={isSubmitting || !form.state.canSubmit}
        >
          Create Agent
        </Button>
        <Button variant="link" onClick={handleCancel} isDisabled={isSubmitting}>
          Cancel
        </Button>
      </ActionGroup>
      {form.state.submissionAttempts > 0 &&
        !form.state.isSubmitted &&
        form.state.errors.length > 0 && (
          <Alert variant="danger" title="Form submission failed" className="pf-v5-u-mt-md">
            Please check the form for errors.
          </Alert>
        )}
    </Form>
  );
}
