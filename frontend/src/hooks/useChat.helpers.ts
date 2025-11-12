import {
  ChatMessage,
  ErrorEvent,
  ReasoningEvent,
  ResponseEvent,
  SimpleContentItem,
  ToolCallEvent,
} from '@/types/chat';

/**
 * Helper functions for processing simplified streaming events from backend
 */

interface ChunkHandler<T = unknown> {
  (messages: ChatMessage[], event: T): ChatMessage[];
}

/**
 * Handle reasoning events (in_progress and completed)
 */
export const handleReasoning: ChunkHandler<ReasoningEvent> = (messages, event) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const reasoningIndex = newContent.findIndex(
    (item) => item.type === 'reasoning' && item.id === event.id
  );

  if (reasoningIndex >= 0) {
    // Update existing reasoning item
    newContent[reasoningIndex] = {
      type: 'reasoning' as const,
      text: event.text,
      id: event.id,
      isComplete: event.status === 'completed',
    };
  } else {
    // Add new reasoning item
    newContent.push({
      type: 'reasoning' as const,
      text: event.text,
      id: event.id,
      isComplete: event.status === 'completed',
    });
  }

  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle tool call events (in_progress, completed, failed)
 */
export const handleToolCall: ChunkHandler<ToolCallEvent> = (messages, event) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const toolCallIndex = newContent.findIndex(
    (item) => item.type === 'tool_call' && item.id === event.id
  );

  if (toolCallIndex >= 0) {
    // Update existing tool call
    newContent[toolCallIndex] = {
      type: 'tool_call' as const,
      name: event.name,
      server_label: event.server_label,
      arguments: event.arguments,
      output: event.output,
      error: event.error,
      status: event.status,
      id: event.id,
    };
  } else {
    // Add new tool call
    newContent.push({
      type: 'tool_call' as const,
      name: event.name,
      server_label: event.server_label,
      arguments: event.arguments,
      output: event.output,
      error: event.error,
      status: event.status,
      id: event.id,
    });
  }

  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle response events (in_progress and completed)
 */
export const handleResponse: ChunkHandler<ResponseEvent> = (messages, event) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const responseIndex = newContent.findIndex(
    (item) => item.type === 'output_text' && item.id === event.id
  );

  if (responseIndex >= 0) {
    // Update existing response text
    newContent[responseIndex] = {
      type: 'output_text' as const,
      text: event.text,
      id: event.id,
    };
  } else {
    // Add new response text
    newContent.push({
      type: 'output_text' as const,
      text: event.text,
      id: event.id,
    });
  }

  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle error events
 */
export const handleError: ChunkHandler<ErrorEvent> = (messages, event) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  // Append error to existing content (don't replace reasoning/tool calls)
  const newContent: SimpleContentItem[] = [
    ...lastMsg.content,
    {
      type: 'output_text',
      text: `⚠️ ${event.message}`,
    },
  ];

  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};
