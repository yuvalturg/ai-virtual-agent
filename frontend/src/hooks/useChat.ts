import { useState, useCallback, useEffect, useRef } from 'react';
import { CHAT_API_ENDPOINT } from '../config/api';
import { fetchChatSession, createChatSession } from '@/services/chat-sessions';
import {
  ChatMessage,
  UseLlamaChatOptions,
  SimpleContentItem,
  StreamEvent,
  OutputTextDeltaEvent,
  ReasoningTextDeltaEvent,
  ReasoningTextDoneEvent,
  ToolCallAddedEvent,
  ToolCallArgumentsEvent,
  ToolCallDoneEvent,
  ErrorEvent,
  ResponseCompletedEvent,
  ResponseFailedEvent,
} from '@/types/chat';
import {
  handleOutputTextDelta,
  handleReasoningTextDelta,
  handleReasoningTextDone,
  handleToolCallAdded,
  handleToolCallArguments,
  handleToolCallDone,
  handleError,
  handleResponseCompleted,
  handleResponseFailed,
} from './useChat.helpers';

// Re-export types for backward compatibility
export type { ChatMessage, UseLlamaChatOptions } from '@/types/chat';

/**
 * Simple chat hook that directly handles LlamaStack without the AI SDK overhead
 */
export function useChat(agentId: string, options?: UseLlamaChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);

  // Use a ref to track the current session ID for streaming responses
  const currentSessionIdRef = useRef<string | null>(sessionId);

  // Batching mechanism to reduce re-renders during streaming
  const pendingUpdatesRef = useRef<((prev: ChatMessage[]) => ChatMessage[])[]>([]);
  const rafIdRef = useRef<number | null>(null);

  // Use ref to store the scheduleUpdate function for stable reference
  const scheduleUpdateRef = useRef((updateFn: (prev: ChatMessage[]) => ChatMessage[]) => {
    pendingUpdatesRef.current.push(updateFn);

    if (rafIdRef.current === null) {
      rafIdRef.current = requestAnimationFrame(() => {
        const updates = pendingUpdatesRef.current;
        pendingUpdatesRef.current = [];
        rafIdRef.current = null;

        // Apply all pending updates in sequence
        setMessages((prev) => {
          let current = prev;
          for (const update of updates) {
            current = update(current);
          }
          return current;
        });
      });
    }
  });

  // Expose a stable function reference
  const scheduleUpdate = scheduleUpdateRef.current;

  // Use ref to store the flushPendingUpdates function for stable reference
  const flushPendingUpdatesRef = useRef(() => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;

      // Apply all pending updates immediately
      const updates = pendingUpdatesRef.current;
      pendingUpdatesRef.current = [];

      if (updates.length > 0) {
        setMessages((prev) => {
          let current = prev;
          for (const update of updates) {
            current = update(current);
          }
          return current;
        });
      }
    }
  });

  // Expose a stable function reference
  const flushPendingUpdates = flushPendingUpdatesRef.current;

  // Update the ref whenever sessionId changes
  useEffect(() => {
    currentSessionIdRef.current = sessionId;
  }, [sessionId]);
  const handleInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>, value?: string | number) => {
      const newValue = value !== undefined ? String(value) : event.target.value;
      setInput(newValue);
    },
    []
  );
  const loadSession = useCallback(
    async (sessionId: string) => {
      try {
        // Set the session ID immediately to prevent race conditions
        setSessionId(sessionId);

        setIsLoading(true);

        // Fetch session with messages from LlamaStack Conversations API
        const sessionDetail = await fetchChatSession(sessionId, agentId, true);
        if (!sessionDetail) {
          throw new Error(`Session ${sessionId} not found for agent ${agentId}`);
        }

        // Convert messages - parse timestamp string to Date
        const convertedMessages: ChatMessage[] = sessionDetail.messages.map((msg) => ({
          ...msg,
          timestamp: new Date(msg.timestamp as unknown as string),
        }));

        setMessages(convertedMessages);

        // Update agent if different
        if (sessionDetail.agent_id && sessionDetail.agent_id !== agentId) {
          console.warn(`Loaded session for different agent: ${sessionDetail.agent_id}`);
          // Optionally handle this case, e.g., notify user or reset state
        }
      } catch (error) {
        console.error('Error loading session:', error);
        options?.onError?.(error as Error);
      } finally {
        setIsLoading(false);
      }
    },
    [agentId, options]
  );

  const clearAttachedFiles = useCallback(() => {
    setAttachedFiles([]);
  }, []);

  const sendMessage = useCallback(
    async (content: SimpleContentItem[]) => {
      if (isLoading) return;

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: content,
        timestamp: new Date(),
      };

      // Add user message immediately
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setIsLoading(true);

      // Create assistant message immediately to show loading state
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      try {
        // Create session if it doesn't exist
        let currentSessionId = sessionId;
        if (!currentSessionId) {
          const newSession = await createChatSession(agentId);
          currentSessionId = newSession.id;
          setSessionId(currentSessionId);
        }

        // Prepare request - send the new user message
        const requestBody = {
          virtualAgentId: agentId,
          message: {
            role: userMessage.role,
            content: userMessage.content,
          },
          stream: true,
          sessionId: currentSessionId,
        };

        const response = await fetch(CHAT_API_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error('No response body');
        }

        // Process stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();

              if (data === '[DONE]') {
                // Stream finished - check if we have any content
                setIsLoading(false);
                setMessages((prev) => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];

                  if (lastMsg && lastMsg.role === 'assistant') {
                    // Check if message has any meaningful content
                    const hasContent = lastMsg.content.some((item) => {
                      if (item.type === 'output_text' || item.type === 'reasoning') {
                        return item.text.trim() !== '';
                      }
                      if (item.type === 'tool_call') {
                        return true; // Tool calls count as content
                      }
                      return false;
                    });

                    if (!hasContent) {
                      // No content - add error message
                      updated[updated.length - 1] = {
                        ...lastMsg,
                        content: [
                          {
                            type: 'output_text' as const,
                            text: '⚠️ No response generated. The model may have encountered an issue.',
                          },
                        ],
                      };
                    }

                    options?.onFinish?.(updated[updated.length - 1]);
                  }
                  return updated;
                });
                continue;
              }

              try {
                const chunk = JSON.parse(data) as StreamEvent;
                // console.log('Received chunk:', chunk); // Disabled to prevent memory bloat

                // Extract and set session ID if present
                if (chunk.session_id && !sessionId) {
                  setSessionId(chunk.session_id);
                }

                // Only process chunks that belong to the current session
                if (chunk.session_id && chunk.session_id !== currentSessionIdRef.current) {
                  continue;
                }

                // Process chunk based on type - batch updates using RAF
                if (chunk.type === 'response.output_text.delta') {
                  setIsLoading(false);
                  scheduleUpdate((prev) =>
                    handleOutputTextDelta(prev, chunk as OutputTextDeltaEvent)
                  );
                } else if (chunk.type === 'response.reasoning_text.delta') {
                  setIsLoading(false);
                  scheduleUpdate((prev) =>
                    handleReasoningTextDelta(prev, chunk as ReasoningTextDeltaEvent)
                  );
                } else if (chunk.type === 'response.reasoning_text.done') {
                  scheduleUpdate((prev) =>
                    handleReasoningTextDone(prev, chunk as ReasoningTextDoneEvent)
                  );
                } else if (chunk.type === 'response.output_item.added') {
                  setIsLoading(false);
                  scheduleUpdate((prev) => handleToolCallAdded(prev, chunk as ToolCallAddedEvent));
                } else if (chunk.type === 'response.mcp_call.arguments.done') {
                  scheduleUpdate((prev) =>
                    handleToolCallArguments(prev, chunk as ToolCallArgumentsEvent)
                  );
                } else if (chunk.type === 'response.output_item.done') {
                  scheduleUpdate((prev) => handleToolCallDone(prev, chunk as ToolCallDoneEvent));
                } else if (chunk.type === 'error') {
                  console.error('Stream error:', (chunk as ErrorEvent).content);
                  setIsLoading(false);
                  scheduleUpdate((prev) => handleError(prev, chunk as ErrorEvent));
                }

                // Handle completion or failure
                if (chunk.type === 'response.completed' || chunk.type === 'response.failed') {
                  setIsLoading(false);

                  // Flush any pending batched updates before finalizing
                  flushPendingUpdates();

                  // Handle completed responses - check for empty content
                  if (chunk.type === 'response.completed') {
                    setMessages((prev) => {
                      const updated = handleResponseCompleted(
                        prev,
                        chunk as ResponseCompletedEvent
                      );
                      const lastMsg = updated[updated.length - 1];
                      if (lastMsg && lastMsg.role === 'assistant') {
                        options?.onFinish?.(lastMsg);
                      }
                      return updated;
                    });
                  }

                  // Handle failed responses - show error
                  if (chunk.type === 'response.failed') {
                    const failedChunk = chunk as ResponseFailedEvent;
                    const errorResponse = failedChunk.response;
                    if (errorResponse?.error?.message) {
                      console.error('Response failed:', errorResponse.error.message);
                    }

                    setMessages((prev) => {
                      const updated = handleResponseFailed(prev, failedChunk);
                      const lastMsg = updated[updated.length - 1];
                      if (lastMsg && lastMsg.role === 'assistant') {
                        options?.onFinish?.(lastMsg);
                      }
                      return updated;
                    });
                  }
                }
              } catch (_error) {
                // Ignore parse errors
              }
            }
          }
        }
      } catch (error) {
        console.error('Chat error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        options?.onError?.(new Error(errorMessage));
        setIsLoading(false);

        // Remove the loading assistant message on error
        setMessages((prev) =>
          prev.filter((msg) => {
            // Keep non-assistant messages and assistant messages with actual content
            if (msg.role !== 'assistant') return true;

            // Keep if it has any content items with non-empty text
            return msg.content.some((item) => {
              if (item.type === 'output_text' || item.type === 'reasoning') {
                return item.text.trim() !== '';
              }
              if (item.type === 'tool_call') {
                return true; // Keep tool calls
              }
              return false;
            });
          })
        );
      }
    },
    [agentId, sessionId, isLoading, options, scheduleUpdate, flushPendingUpdates]
  );

  const handleAttach = useCallback((data: File[]) => {
    setAttachedFiles((prev: File[]) => [...prev, ...data]);
  }, []);

  const append = useCallback(
    (message: { role: 'user' | 'assistant'; content: SimpleContentItem[] }) => {
      void sendMessage(message.content);
    },
    [sendMessage]
  );

  // Reset state when agentId changes
  useEffect(() => {
    setMessages([]);
    setInput('');
    setAttachedFiles([]);
    setIsLoading(false);
    setSessionId(null);
  }, [agentId]);

  return {
    messages,
    input,
    handleInputChange,
    handleAttach,
    append,
    isLoading,
    loadSession,
    sessionId,
    setSessionId,
    attachedFiles,
    clearAttachedFiles,
    setAttachedFiles,
    flushPendingUpdates,
  };
}
