import { CHAT_SESSIONS_API_ENDPOINT } from '@/config/api';
import { ChatSessionSummary, ChatSessionDetail } from '@/types/chat';
import { ErrorResponse } from '@/types';

// Re-export types for backward compatibility
export type { ChatSessionSummary, ChatSessionDetail } from '@/types/chat';

export async function fetchChatSessions(agentId?: string): Promise<ChatSessionSummary[]> {
  const url = agentId
    ? `${CHAT_SESSIONS_API_ENDPOINT}?agent_id=${agentId}`
    : CHAT_SESSIONS_API_ENDPOINT;

  const response = await fetch(url);
  if (!response.ok) {
    const errorData = (await response
      .json()
      .catch(() => ({ detail: 'Failed to fetch chat sessions' }))) as ErrorResponse;
    throw new Error(errorData.detail ?? 'Failed to fetch chat sessions');
  }
  return response.json() as Promise<ChatSessionSummary[]>;
}

export async function fetchChatSession(
  sessionId: string,
  agentId: string,
  page: number = 1,
  pageSize: number = 50,
  loadMessages: boolean = true
): Promise<ChatSessionDetail> {
  const params = new URLSearchParams({
    agent_id: agentId,
    page: page.toString(),
    page_size: pageSize.toString(),
    load_messages: loadMessages.toString(),
  });

  const response = await fetch(`${CHAT_SESSIONS_API_ENDPOINT}${sessionId}?${params}`);
  if (!response.ok) {
    const errorData = (await response
      .json()
      .catch(() => ({ detail: 'Failed to fetch chat session' }))) as ErrorResponse;
    throw new Error(errorData.detail ?? 'Failed to fetch chat session');
  }
  return response.json() as Promise<ChatSessionDetail>;
}

export async function deleteChatSession(sessionId: string, agentId: string): Promise<void> {
  const response = await fetch(`${CHAT_SESSIONS_API_ENDPOINT}${sessionId}?agent_id=${agentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errorData = (await response
      .json()
      .catch(() => ({ detail: 'Failed to delete chat session' }))) as ErrorResponse;
    throw new Error(errorData.detail ?? 'Failed to delete chat session');
  }
}

export async function createChatSession(
  agentId: string,
  sessionName?: string
): Promise<ChatSessionDetail> {
  const response = await fetch(CHAT_SESSIONS_API_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      agent_id: agentId,
      session_name: sessionName,
    }),
  });

  if (!response.ok) {
    const errorData = (await response
      .json()
      .catch(() => ({ detail: 'Failed to create chat session' }))) as ErrorResponse;
    throw new Error(errorData.detail ?? 'Failed to create chat session');
  }
  return response.json() as Promise<ChatSessionDetail>;
}
