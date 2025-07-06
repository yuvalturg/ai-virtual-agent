import { useForm } from '@tanstack/react-form';
import { MCPServer, MCPServerCreate } from '@/types';
import {
  Button,
  ActionGroup,
  Form,
  FormGroup,
  TextInput,
  TextArea,
  Alert,
} from '@patternfly/react-core';
import { PaperPlaneIcon } from '@patternfly/react-icons';

interface MCPServerFormProps {
  defaultServer?: MCPServer;
  isSubmitting: boolean;
  onSubmit: (values: MCPServerCreate) => void;
  onCancel: () => void;
  error?: Error | null;
}

export function MCPServerForm({
  defaultServer,
  isSubmitting,
  onSubmit,
  onCancel,
  error,
}: MCPServerFormProps) {
  const initialData: MCPServerCreate = defaultServer
    ? {
        name: defaultServer.name,
        description: defaultServer.description || '',
        endpoint_url: defaultServer.endpoint_url,
        configuration: defaultServer.configuration || {},
      }
    : {
        name: '',
        description: '',
        endpoint_url: '',
        configuration: {},
      };

  const form = useForm({
    defaultValues: initialData,
    onSubmit: ({ value }) => {
      // Convert configuration from string to object if needed
      let finalValue = { ...value };
      
      // If configuration is a string, try to parse it as JSON
      if (typeof value.configuration === 'string') {
        try {
          finalValue.configuration = value.configuration.trim() 
            ? JSON.parse(value.configuration) 
            : {};
        } catch (e) {
          // If parsing fails, keep it as empty object
          finalValue.configuration = {};
        }
      }

      onSubmit(finalValue);
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
        validators={{ 
          onChange: ({ value }) => (!value ? 'Name is required' : undefined) 
        }}
      >
        {(field) => (
          <FormGroup label="Name" isRequired fieldId="mcp-form-name">
            <TextInput
              isRequired
              id="mcp-form-name"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
              placeholder="Enter MCP server name"
            />
            {field.state.meta.errors.length > 0 && (
              <div style={{ color: '#c9190b', fontSize: '14px', marginTop: '4px' }}>
                {field.state.meta.errors[0]}
              </div>
            )}
          </FormGroup>
        )}
      </form.Field>

      <form.Field name="description">
        {(field) => (
          <FormGroup label="Description" fieldId="mcp-form-description">
            <TextInput
              id="mcp-form-description"
              value={field.state.value || ''}
              onChange={(_e, v) => field.handleChange(v)}
              placeholder="Optional description"
            />
          </FormGroup>
        )}
      </form.Field>

      <form.Field
        name="endpoint_url"
        validators={{ 
          onChange: ({ value }) => {
            if (!value) return 'Endpoint URL is required';
            try {
              new URL(value);
              return undefined;
            } catch {
              return 'Please enter a valid URL';
            }
          }
        }}
      >
        {(field) => (
          <FormGroup label="Endpoint URL" isRequired fieldId="mcp-form-endpoint">
            <TextInput
              isRequired
              id="mcp-form-endpoint"
              value={field.state.value}
              onChange={(_e, v) => field.handleChange(v)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
              placeholder="https://example.com/mcp"
            />
            {field.state.meta.errors.length > 0 && (
              <div style={{ color: '#c9190b', fontSize: '14px', marginTop: '4px' }}>
                {field.state.meta.errors[0]}
              </div>
            )}
          </FormGroup>
        )}
      </form.Field>

      <form.Field
        name="configuration"
        validators={{
          onChange: ({ value }) => {
            if (!value || typeof value !== 'string') return undefined;
            if (value.trim() === '') return undefined;
            try {
              JSON.parse(value);
              return undefined;
            } catch {
              return 'Invalid JSON format';
            }
          }
        }}
      >
        {(field) => (
          <FormGroup label="Configuration (JSON)" fieldId="mcp-form-config">
            <TextArea
              id="mcp-form-config"
              value={
                typeof field.state.value === 'string' 
                  ? field.state.value 
                  : JSON.stringify(field.state.value || {}, null, 2)
              }
              onChange={(_e, v) => field.handleChange(v)}
              validated={
                !field.state.meta.isTouched
                  ? 'default'
                  : field.state.meta.errors.length > 0
                    ? 'error'
                    : 'success'
              }
              rows={4}
              placeholder='{"key": "value"}'
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
          selector={(state) => [state.canSubmit, state.isSubmitting, state.isPristine]}
        >
          {([canSubmit, isSubmittingForm, isPristine]) => (
            <Button
              icon={<PaperPlaneIcon />}
              type="submit"
              variant="primary"
              isDisabled={!canSubmit || isSubmittingForm || isPristine}
              isLoading={isSubmitting || isSubmittingForm}
            >
              {defaultServer ? 'Update' : 'Create'}
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