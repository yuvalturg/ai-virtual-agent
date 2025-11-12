import {
  ChatMessage,
  ErrorEvent,
  OutputTextDeltaEvent,
  ReasoningTextDeltaEvent,
  ReasoningTextDoneEvent,
  ResponseCompletedEvent,
  ResponseFailedEvent,
  SimpleContentItem,
  ToolCallAddedEvent,
  ToolCallArgumentsEvent,
  ToolCallDoneEvent,
} from '@/types/chat';

/**
 * Helper functions for processing LlamaStack streaming chunks
 */

interface ChunkHandler<T = unknown> {
  (messages: ChatMessage[], chunk: T): ChatMessage[];
}

/**
 * Handle output_text delta chunks
 */
export const handleOutputTextDelta: ChunkHandler<OutputTextDeltaEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const outputTextIndex = newContent.findIndex(
    (item) =>
      item.type === 'output_text' &&
      item.id === chunk.item_id &&
      item.contentIndex === chunk.content_index
  );

  if (outputTextIndex >= 0) {
    const existing = newContent[outputTextIndex];
    const existingText = existing.type === 'output_text' ? existing.text : '';
    newContent[outputTextIndex] = {
      type: 'output_text' as const,
      text: existingText + chunk.delta,
      id: chunk.item_id,
      contentIndex: chunk.content_index,
    };
  } else {
    newContent.push({
      type: 'output_text' as const,
      text: chunk.delta,
      id: chunk.item_id,
      contentIndex: chunk.content_index,
    });
  }

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle reasoning_text delta chunks
 */
export const handleReasoningTextDelta: ChunkHandler<ReasoningTextDeltaEvent> = (
  messages,
  chunk
) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const reasoningIndex = newContent.findIndex(
    (item) =>
      item.type === 'reasoning' &&
      item.id === chunk.item_id &&
      item.contentIndex === chunk.content_index
  );

  if (reasoningIndex >= 0) {
    const existing = newContent[reasoningIndex];
    const existingText = existing.type === 'reasoning' ? existing.text : '';
    newContent[reasoningIndex] = {
      type: 'reasoning' as const,
      text: existingText + chunk.delta,
      id: chunk.item_id,
      contentIndex: chunk.content_index,
    };
  } else {
    newContent.push({
      type: 'reasoning' as const,
      text: chunk.delta,
      id: chunk.item_id,
      contentIndex: chunk.content_index,
    });
  }

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle tool call added
 */
export const handleToolCallAdded: ChunkHandler<ToolCallAddedEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  newContent.push({
    type: 'tool_call' as const,
    name: chunk.item.name,
    server_label: chunk.item.server_label,
    arguments: chunk.item.arguments || undefined,
    status: 'in_progress' as const,
    id: chunk.item.id,
  });

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle tool call arguments
 */
export const handleToolCallArguments: ChunkHandler<ToolCallArgumentsEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const toolCallIndex = newContent.findIndex(
    (item) => item.type === 'tool_call' && item.id === chunk.item_id
  );

  if (toolCallIndex >= 0) {
    const existing = newContent[toolCallIndex];
    if (existing.type === 'tool_call') {
      newContent[toolCallIndex] = {
        ...existing,
        arguments: chunk.arguments,
      };
    }
  }

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle tool call completion
 */
export const handleToolCallDone: ChunkHandler<ToolCallDoneEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const toolCallIndex = newContent.findIndex(
    (item) => item.type === 'tool_call' && item.id === chunk.item.id
  );

  if (toolCallIndex >= 0) {
    const existing = newContent[toolCallIndex];
    if (existing.type === 'tool_call') {
      newContent[toolCallIndex] = {
        ...existing,
        arguments: chunk.item.arguments,
        output: chunk.item.output,
        error: chunk.item.error,
        status: chunk.item.error ? ('failed' as const) : ('completed' as const),
      };
    }
  }

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle reasoning completion - collapse when done
 */
export const handleReasoningTextDone: ChunkHandler<ReasoningTextDoneEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent = [...lastMsg.content];
  const reasoningIndex = newContent.findIndex(
    (item) =>
      item.type === 'reasoning' &&
      item.id === chunk.item_id &&
      item.contentIndex === chunk.content_index
  );

  if (reasoningIndex >= 0) {
    const existing = newContent[reasoningIndex];
    newContent[reasoningIndex] = {
      type: 'reasoning' as const,
      text: chunk.text || (existing.type === 'reasoning' ? existing.text : ''),
      id: chunk.item_id,
      contentIndex: chunk.content_index,
      isComplete: true,
    };
  }

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle error chunks
 */
export const handleError: ChunkHandler<ErrorEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  const newContent: SimpleContentItem[] = [
    {
      type: 'output_text',
      text: `⚠️ ${chunk.content}`,
    },
  ];

  // Update the last message content and timestamp
  const updated = [...messages];
  updated[updated.length - 1] = {
    ...lastMsg,
    content: newContent,
    timestamp: new Date(),
  };
  return updated;
};

/**
 * Handle response completion - check for empty responses
 */
export const handleResponseCompleted: ChunkHandler<ResponseCompletedEvent> = (messages, _chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  // Check if message has any output_text with actual text
  // NOTE: We only check output_text, NOT reasoning - reasoning is internal thinking
  const hasOutputText = lastMsg.content.some((item) => {
    if (item.type === 'output_text') {
      return item.text && item.text.trim() !== '';
    }
    return false;
  });

  if (!hasOutputText) {
    // No output text - append warning message after tool calls/reasoning
    // First, filter out empty output_text items
    const filteredContent = lastMsg.content.filter((item) => {
      if (item.type === 'output_text') {
        return item.text && item.text.trim() !== '';
      }
      return true; // Keep reasoning and tool_call items
    });

    const updated = [...messages];
    updated[updated.length - 1] = {
      ...lastMsg,
      content: [
        ...filteredContent,
        {
          type: 'output_text' as const,
          text: "⚠️ The assistant couldn't generate a text response. Please try again or rephrase your request.",
        },
      ],
      timestamp: new Date(),
    };
    return updated;
  }

  // Has output text - return as-is
  return messages;
};

/**
 * Handle response failure - show error message or check for empty content
 */
export const handleResponseFailed: ChunkHandler<ResponseFailedEvent> = (messages, chunk) => {
  const lastMsg = messages[messages.length - 1];
  if (!lastMsg || lastMsg.role !== 'assistant') return messages;

  // If there's an error in the response, show it
  if (chunk.response?.error) {
    const updated = [...messages];
    updated[updated.length - 1] = {
      ...lastMsg,
      content: [
        {
          type: 'output_text' as const,
          text: `⚠️ Error: ${chunk.response.error.message}`,
        },
      ],
      timestamp: new Date(),
    };
    return updated;
  }

  // No error details - check if message has output_text (same as completed)
  // NOTE: We only check output_text, NOT reasoning - reasoning is internal thinking
  const hasOutputText = lastMsg.content.some((item) => {
    if (item.type === 'output_text') {
      return item.text && item.text.trim() !== '';
    }
    return false;
  });

  if (!hasOutputText) {
    // No output text - append warning message after tool calls/reasoning
    // First, filter out empty output_text items
    const filteredContent = lastMsg.content.filter((item) => {
      if (item.type === 'output_text') {
        return item.text && item.text.trim() !== '';
      }
      return true; // Keep reasoning and tool_call items
    });

    const updated = [...messages];
    updated[updated.length - 1] = {
      ...lastMsg,
      content: [
        ...filteredContent,
        {
          type: 'output_text' as const,
          text: "⚠️ The assistant couldn't generate a text response. Please try again or rephrase your request.",
        },
      ],
      timestamp: new Date(),
    };
    return updated;
  }

  // Has output text - return as-is
  return messages;
};
