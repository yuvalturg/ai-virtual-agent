// Type for trace entries
export interface ReasoningEntry {
  type: 'reasoning';
  text: string;
}

export interface ToolCallEntry {
  type: 'tool_call';
  name: string;
  server_label?: string;
  arguments?: unknown;
  output?: unknown;
  error?: string;
  status: 'completed' | 'failed';
}

export type TraceEntry = ReasoningEntry | ToolCallEntry;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: SimpleContentItem[];
  timestamp: Date;
  trace_entries?: TraceEntry[];
}

export interface TextContentItem {
  type: 'input_text';
  text: string;
}

export interface OutputTextContentItem {
  type: 'output_text';
  text: string;
  id?: string; // Internal: item_id from LlamaStack
  contentIndex?: number; // Internal: content_index from LlamaStack
}

export interface ReasoningContentItem {
  type: 'reasoning';
  text: string;
  id?: string; // Internal: item_id from LlamaStack
  contentIndex?: number; // Internal: content_index from LlamaStack
  isComplete?: boolean;
}

export interface ToolCallContentItem {
  type: 'tool_call';
  name: string;
  server_label?: string;
  arguments?: string;
  output?: string;
  error?: string;
  status?: 'in_progress' | 'completed' | 'failed';
  id?: string; // Internal: item.id from LlamaStack
}

export interface ImageContentItem {
  type: 'input_image';
  image_url: string;
}

export type SimpleContentItem =
  | TextContentItem
  | OutputTextContentItem
  | ReasoningContentItem
  | ToolCallContentItem
  | ImageContentItem;

export interface UseLlamaChatOptions {
  onError?: (error: Error) => void;
  onFinish?: (message: ChatMessage) => void;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  agent_name: string;
  updated_at: string;
  created_at: string;
}

export interface ChatSessionDetail {
  id: string;
  title: string;
  agent_name: string;
  agent_id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

/**
 * LlamaStack Server-Sent Events (SSE) streaming event types
 * These match the event types sent from the LlamaStack streaming API
 */
export interface BaseStreamEvent {
  type: string;
  session_id?: string;
  item_id?: string;
  output_index?: number;
  content_index?: number;
  sequence_number?: number;
}

export interface OutputTextDeltaEvent extends BaseStreamEvent {
  type: 'response.output_text.delta';
  delta: string;
  item_id: string;
  content_index: number;
}

export interface ReasoningTextDeltaEvent extends BaseStreamEvent {
  type: 'response.reasoning_text.delta';
  delta: string;
  item_id: string;
  content_index: number;
}

export interface ReasoningTextDoneEvent extends BaseStreamEvent {
  type: 'response.reasoning_text.done';
  text: string;
  item_id: string;
  content_index: number;
}

export interface ToolCallAddedEvent extends BaseStreamEvent {
  type: 'response.output_item.added';
  item: {
    id: string;
    name: string;
    server_label?: string;
    arguments?: string;
    type: string;
    error: string | null;
    output: string | null;
  };
}

export interface ToolCallArgumentsEvent extends BaseStreamEvent {
  type: 'response.mcp_call.arguments.done' | 'response.function_call_arguments.delta';
  arguments: string;
  item_id: string;
}

export interface ToolCallDoneEvent extends BaseStreamEvent {
  type: 'response.output_item.done';
  item: {
    id: string;
    name: string;
    server_label?: string;
    arguments?: string;
    output?: string;
    error?: string;
    type: string;
  };
}

export interface ResponseCompletedEvent extends BaseStreamEvent {
  type: 'response.completed';
  response?: {
    error?: {
      message: string;
    };
  };
}

export interface ResponseFailedEvent extends BaseStreamEvent {
  type: 'response.failed';
  response?: {
    error?: {
      message: string;
    };
  };
}

export interface ErrorEvent extends BaseStreamEvent {
  type: 'error';
  content: string;
}

export type StreamEvent =
  | OutputTextDeltaEvent
  | ReasoningTextDeltaEvent
  | ReasoningTextDoneEvent
  | ToolCallAddedEvent
  | ToolCallArgumentsEvent
  | ToolCallDoneEvent
  | ResponseCompletedEvent
  | ResponseFailedEvent
  | ErrorEvent
  | BaseStreamEvent;
