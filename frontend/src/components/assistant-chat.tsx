import React, { Fragment, useEffect, useState } from 'react';
import {
  Chatbot,
  ChatbotContent,
  ChatbotConversationHistoryNav,
  ChatbotDisplayMode,
  ChatbotFooter,
  ChatbotFootnote,
  ChatbotHeader,
  ChatbotHeaderActions,
  ChatbotHeaderMain,
  ChatbotHeaderMenu,
  ChatbotHeaderSelectorDropdown,
  ChatbotHeaderTitle,
  Conversation,
  Message,
  MessageBar,
  MessageBox,
  MessageProps,
} from '@patternfly/chatbot';
import { DropdownItem, DropdownList } from '@patternfly/react-core';
import { Agent } from '@/routes/config/agents';
import { fetchAgents } from '@/services/agents';
import { useSimpleLlamaChat } from '@/hooks/useSimpleLlamaChat';
import { fetchChatSessions, createChatSession, ChatSessionSummary } from '@/services/chat-sessions';

const footnoteProps = {
  label: 'ChatBot uses AI. Check for mistakes.',
  popover: {
    title: 'Verify information',
    description: `While ChatBot strives for accuracy, AI is experimental and can make mistakes. We cannot guarantee that all information provided by ChatBot is up to date or without error. You should always verify responses using reliable sources, especially for crucial information and decision making.`,
    bannerImage: {
      src: 'https://cdn.dribbble.com/userupload/10651749/file/original-8a07b8e39d9e8bf002358c66fce1223e.gif',
      alt: 'Example image for footnote popover',
    },
    cta: {
      label: 'Dismiss',
      onClick: () => {
        alert('Do something!');
      },
    },
    link: {
      label: 'View AI policy',
      url: 'https://www.redhat.com/',
    },
  },
};

export function AssistantChat() {
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [conversations, setConversations] = useState<
    Conversation[] | { [key: string]: Conversation[] }
  >([]);
  const [announcement, setAnnouncement] = useState<string>('');
  const [chatSessions, setChatSessions] = useState<ChatSessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const scrollToBottomRef = React.useRef<HTMLDivElement>(null);
  const historyRef = React.useRef<HTMLButtonElement>(null);

  // Use our custom hook for chat functionality
  const {
    messages: chatMessages,
    input,
    handleInputChange,
    append,
    isLoading,
    resetSession,
    loadSession,
  } = useSimpleLlamaChat(selectedAgent || 'default', {
    onError: (error: Error) => {
      console.error('Chat error:', error);
      setAnnouncement(`Error: ${error.message}`);
    },
    onFinish: () => {
      setAnnouncement(`Message from assistant complete`);
      if (scrollToBottomRef.current) {
        scrollToBottomRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    },
  });

  // Convert our chat messages to PatternFly format
  const messages = React.useMemo(
    () =>
      chatMessages.map(
        (msg): MessageProps => ({
          id: msg.id,
          role: msg.role === 'user' ? 'user' : 'bot',
          content: msg.content,
          name: msg.role === 'user' ? 'You' : 'Assistant',
          timestamp: msg.timestamp.toLocaleString(),
          avatar: '',
          avatarProps: { isBordered: true },
          isLoading:
            msg.role === 'assistant' &&
            isLoading &&
            msg.id === chatMessages[chatMessages.length - 1]?.id,
        })
      ),
    [chatMessages, isLoading]
  );

  const displayMode = ChatbotDisplayMode.embedded;

  const onSelectAgent = async (
    _event: React.MouseEvent<Element, MouseEvent> | undefined,
    value: string | number | undefined
  ) => {
    if (value) {
      const agentId = value.toString();
      setSelectedAgent(agentId);
      // Reset chat when changing agents
      resetSession();
      setSelectedSessionId(null);
      // Fetch sessions for the new agent
      await fetchSessionsData(agentId);
    }
  };

  const onSelectActiveItem = async (_e: any, selectedItem: string | number | undefined) => {
    if (!selectedItem || typeof selectedItem !== 'string') return;

    try {
      setSelectedSessionId(selectedItem);
      await loadSession(selectedItem);
      setIsDrawerOpen(false); // Close sidebar after selection
    } catch (error) {
      console.error('Error loading session:', error);
      setAnnouncement('Failed to load chat session');
    }
  };

  const onNewChat = async () => {
    if (!selectedAgent) return;

    try {
      // Create a new session for the current agent
      const newSession = await createChatSession(selectedAgent);
      setSelectedSessionId(newSession.id);

      // Reset chat messages
      resetSession();

      // Refresh sessions list to include the new session
      await fetchSessionsData(selectedAgent);

      setIsDrawerOpen(false);
    } catch (error) {
      console.error('Error creating new session:', error);
      setAnnouncement('Failed to create new chat session');
    }
  };

  const findMatchingItems = (targetValue: string) => {
    const filteredConversations = chatSessions.filter((session) =>
      session.title.toLowerCase().includes(targetValue.toLowerCase())
    );

    // Convert to PatternFly conversation format
    const conversations = filteredConversations.map((session) => ({
      id: session.id,
      text: session.title,
      description: session.agent_name,
      timestamp: new Date(session.updated_at).toLocaleDateString(),
    }));

    // append message if no items are found
    if (conversations.length === 0) {
      conversations.push({
        id: '13',
        text: 'No results found',
        description: '',
        timestamp: '',
      });
    }
    return conversations;
  };

  const fetchSessionsData = async (agentId?: string) => {
    try {
      const sessions = await fetchChatSessions(agentId);
      setChatSessions(sessions);

      // Convert to PatternFly conversation format
      const conversations = sessions.map((session) => ({
        id: session.id,
        text: session.title,
        description: session.agent_name,
        timestamp: new Date(session.updated_at).toLocaleDateString(),
      }));

      setConversations(conversations);

      // Auto-select most recent session if none selected and sessions exist
      if (!selectedSessionId && sessions.length > 0) {
        const mostRecentSession = sessions[0]; // They're ordered by updated_at desc
        setSelectedSessionId(mostRecentSession.id);
        await loadSession(mostRecentSession.id);
      } else if (sessions.length === 0 && agentId) {
        // Create a new session if agent has no sessions
        try {
          const newSession = await createChatSession(agentId);
          setSelectedSessionId(newSession.id);
          // The session starts empty so no need to load messages
          // Just refresh the sessions list
          await fetchSessionsData(agentId);
        } catch (error) {
          console.error('Error creating initial session:', error);
          setAnnouncement('Failed to create initial session');
        }
      }
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
    }
  };

  // Fetch available agents on mount
  useEffect(() => {
    const fetchAgentsData = async () => {
      try {
        const agents = await fetchAgents();
        setAvailableAgents(agents);
        if (agents.length > 0) {
          const firstAgent = agents[0].id;
          setSelectedAgent(firstAgent);
          // Fetch sessions for the first agent
          await fetchSessionsData(firstAgent);
        }
      } catch (err) {
        console.error('Error fetching agents:', err);
        setAnnouncement('Failed to load agents');
      }
    };

    void fetchAgentsData();
  }, []);

  // Handle message sending
  const handleSendMessage = (message: string | number) => {
    console.log('handleSendMessage called with:', message, 'selectedAgent:', selectedAgent);
    if (typeof message === 'string' && message.trim() && selectedAgent) {
      console.log('Sending message via append:', message);
      // Add the message to the chat
      append({
        role: 'user',
        content: message.toString(),
      });
    } else {
      console.log('Message not sent - conditions not met:', {
        messageType: typeof message,
        messageLength: typeof message === 'string' ? message.trim().length : 0,
        selectedAgent: selectedAgent,
      });
    }
  };

  return (
    <Chatbot displayMode={displayMode}>
      <ChatbotConversationHistoryNav
        displayMode={displayMode}
        onDrawerToggle={() => {
          setIsDrawerOpen(!isDrawerOpen);
        }}
        isDrawerOpen={isDrawerOpen}
        setIsDrawerOpen={setIsDrawerOpen}
        activeItemId="1"
        onSelectActiveItem={onSelectActiveItem}
        conversations={conversations}
        onNewChat={onNewChat}
        handleTextInputChange={(value: string) => {
          if (value === '') {
            // Convert sessions to conversations format
            const conversations = chatSessions.map((session) => ({
              id: session.id,
              text: session.title,
              description: session.agent_name,
              timestamp: new Date(session.updated_at).toLocaleDateString(),
            }));
            setConversations(conversations);
          }
          const newConversations = findMatchingItems(value);
          setConversations(newConversations);
        }}
        drawerContent={
          <Fragment>
            <ChatbotHeader>
              <ChatbotHeaderMain>
                <ChatbotHeaderMenu
                  ref={historyRef}
                  aria-expanded={isDrawerOpen}
                  onMenuToggle={() => setIsDrawerOpen(!isDrawerOpen)}
                />
                <ChatbotHeaderTitle>Chat</ChatbotHeaderTitle>
              </ChatbotHeaderMain>
              <ChatbotHeaderActions>
                <ChatbotHeaderSelectorDropdown
                  value={
                    availableAgents.find((agent) => agent.id === selectedAgent)?.name ||
                    'Select Agent'
                  }
                  onSelect={onSelectAgent}
                  tooltipContent="Select Agent"
                >
                  <DropdownList>
                    {availableAgents.map((agent) => (
                      <DropdownItem value={agent.id} key={agent.id}>
                        {agent.name}
                      </DropdownItem>
                    ))}
                  </DropdownList>
                </ChatbotHeaderSelectorDropdown>
              </ChatbotHeaderActions>
            </ChatbotHeader>
            <ChatbotContent>
              <MessageBox announcement={announcement}>
                {messages.map((message, index) => {
                  if (index === messages.length - 1) {
                    return (
                      <Fragment key={message.id}>
                        <div ref={scrollToBottomRef}></div>
                        <Message key={message.id} {...message} />
                      </Fragment>
                    );
                  }
                  return <Message key={message.id} {...message} />;
                })}
              </MessageBox>
            </ChatbotContent>
            <ChatbotFooter>
              <MessageBar
                onSendMessage={handleSendMessage as (message: string | number) => void}
                hasMicrophoneButton
                isSendButtonDisabled={isLoading || !selectedAgent}
                value={input}
                onChange={handleInputChange}
              />
              <ChatbotFootnote {...footnoteProps} />
            </ChatbotFooter>
          </Fragment>
        }
      ></ChatbotConversationHistoryNav>
    </Chatbot>
  );
}
