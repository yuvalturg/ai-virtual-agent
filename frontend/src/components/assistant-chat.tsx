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
  ChatbotWelcomePrompt,
  Conversation,
  Message,
  MessageBar,
  MessageBox,
  MessageProps,
} from "@patternfly/chatbot";
import { DropdownItem, DropdownList } from "@patternfly/react-core";
import React from "react";
// import botAvatar from "../assets/img/bot-avatar.svg";
// import userAvatar from "../assets/img/user-avatar.svg";

const footnoteProps = {
  label: "ChatBot uses AI. Check for mistakes.",
  popover: {
    title: "Verify information",
    description: `While ChatBot strives for accuracy, AI is experimental and can make mistakes. We cannot guarantee that all information provided by ChatBot is up to date or without error. You should always verify responses using reliable sources, especially for crucial information and decision making.`,
    bannerImage: {
      src: "https://cdn.dribbble.com/userupload/10651749/file/original-8a07b8e39d9e8bf002358c66fce1223e.gif",
      alt: "Example image for footnote popover",
    },
    cta: {
      label: "Dismiss",
      onClick: () => {
        alert("Do something!");
      },
    },
    link: {
      label: "View AI policy",
      url: "https://www.redhat.com/",
    },
  },
};

const fillerWelcomePrompts = [
  {
    title: "Set up account",
    message: "Choose the necessary settings and preferences for your account.",
  },
  {
    title: "Troubleshoot issue",
    message: "Find documentation and instructions to resolve your issue.",
  },
];

const fillerInitialConversations = {
  Today: [
    { id: "1", text: "Hello, can you give me an example of what you can do?" },
  ],
  "This month": [
    {
      id: "2",
      text: "Enterprise Linux installation and setup",
    },
    { id: "3", text: "Troubleshoot system crash" },
  ],
  March: [
    { id: "4", text: "Ansible security and updates" },
    { id: "5", text: "Red Hat certification" },
    { id: "6", text: "Lightspeed user documentation" },
  ],
  February: [
    { id: "7", text: "Crashing pod assistance" },
    { id: "8", text: "OpenShift AI pipelines" },
    { id: "9", text: "Updating subscription plan" },
    { id: "10", text: "Red Hat licensing options" },
  ],
  January: [
    { id: "11", text: "RHEL system performance" },
    { id: "12", text: "Manage user accounts" },
  ],
};

export function AssistantChat() {
  const [messages, setMessages] = React.useState<MessageProps[]>([]);
  const [selectedModel, setSelectedModel] = React.useState("Granite 7B");
  const [isSendButtonDisabled, setIsSendButtonDisabled] = React.useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = React.useState(false);
  const [conversations, setConversations] = React.useState<
    Conversation[] | { [key: string]: Conversation[] }
  >(fillerInitialConversations);
  const [announcement, setAnnouncement] = React.useState<string>();
  const scrollToBottomRef = React.useRef<HTMLDivElement>(null);
  const historyRef = React.useRef<HTMLButtonElement>(null);

  const displayMode = ChatbotDisplayMode.embedded;

  const onSelectModel = (
    _event: React.MouseEvent<Element, MouseEvent> | undefined,
    value: string | number | undefined
  ) => {
    setSelectedModel(value as string);
  };
  const findMatchingItems = (targetValue: string) => {
    let filteredConversations = Object.entries(
      fillerInitialConversations
    ).reduce((acc, [key, items]) => {
      const filteredItems = items.filter((item) =>
        item.text.toLowerCase().includes(targetValue.toLowerCase())
      );
      if (filteredItems.length > 0) {
        acc[key] = filteredItems;
      }
      return acc;
    }, {});

    // append message if no items are found
    if (Object.keys(filteredConversations).length === 0) {
      filteredConversations = [
        { id: "13", noIcon: true, text: "No results found" },
      ];
    }
    return filteredConversations;
  };

  //TODO: REPLACE THIS WITH ACTUAL IDs
  const generateId = () => {
    const id = Date.now() + Math.random();
    return id.toString();
  };

  const handleSend = (message: string) => {
    setIsSendButtonDisabled(true);
    const newMessages: MessageProps[] = [];
    // We can't use structuredClone since messages contains functions, but we can't mutate
    // items that are going into state or the UI won't update correctly
    messages.forEach((message) => newMessages.push(message));
    // It's important to set a timestamp prop since the Message components re-render.
    // The timestamps re-render with them.
    const date = new Date();
    newMessages.push({
      id: generateId(),
      role: "user",
      content: message,
      name: "User",
      avatar: "userAvatar",
      timestamp: date.toLocaleString(),
      avatarProps: { isBordered: true },
    });
    newMessages.push({
      id: generateId(),
      role: "bot",
      content: "API response goes here",
      name: "Bot",
      avatar: "botAvatar",
      isLoading: true,
      timestamp: date.toLocaleString(),
    });
    setMessages(newMessages);
    // make announcement to assistive devices that new messages have been added
    setAnnouncement(
      `Message from User: ${message}. Message from Bot is loading.`
    );

    // this is for demo purposes only; in a real situation, there would be an API response we would wait for
    setTimeout(() => {
      const loadedMessages: MessageProps[] = [];
      // we can't use structuredClone since messages contains functions, but we can't mutate
      // items that are going into state or the UI won't update correctly
      newMessages.forEach((message) => loadedMessages.push(message));
      loadedMessages.pop();
      loadedMessages.push({
        id: generateId(),
        role: "bot",
        content: "API response goes here",
        name: "Bot",
        avatar: patternflyAvatar,
        isLoading: false,
        actions: {
          // eslint-disable-next-line no-console
          positive: { onClick: () => console.log("Good response") },
          // eslint-disable-next-line no-console
          negative: { onClick: () => console.log("Bad response") },
          // eslint-disable-next-line no-console
          copy: { onClick: () => console.log("Copy") },
          // eslint-disable-next-line no-console
          share: { onClick: () => console.log("Share") },
          // eslint-disable-next-line no-console
          listen: { onClick: () => console.log("Listen") },
        },
        timestamp: date.toLocaleString(),
      });
      setMessages(loadedMessages);
      // make announcement to assistive devices that new message has loaded
      setAnnouncement(`Message from Bot: API response goes here`);
      setIsSendButtonDisabled(false);
    }, 5000);
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
        // eslint-disable-next-line no-console
        onSelectActiveItem={(e, selectedItem) =>
          console.log(`Selected history item with id ${selectedItem}`)
        }
        conversations={conversations}
        onNewChat={() => {
          setIsDrawerOpen(!isDrawerOpen);
          setMessages([]);
        }}
        handleTextInputChange={(value: string) => {
          if (value === "") {
            setConversations(fillerInitialConversations);
          }
          // this is where you would perform search on the items in the drawer
          // and update the state
          const newConversations: { [key: string]: Conversation[] } =
            findMatchingItems(value);
          setConversations(newConversations);
        }}
        drawerContent={
          <>
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
                  value={selectedModel}
                  onSelect={onSelectModel}
                >
                  <DropdownList>
                    <DropdownItem value="Granite 7B" key="granite">
                      Granite 7B
                    </DropdownItem>
                    <DropdownItem value="Llama 3.0" key="llama">
                      Llama 3.0
                    </DropdownItem>
                    <DropdownItem value="Mistral 3B" key="mistral">
                      Mistral 3B
                    </DropdownItem>
                  </DropdownList>
                </ChatbotHeaderSelectorDropdown>
              </ChatbotHeaderActions>
            </ChatbotHeader>
            <ChatbotContent>
              {/* Update the announcement prop on MessageBox whenever a new message is sent
                 so that users of assistive devices receive sufficient context  */}
              <MessageBox announcement={announcement}>
                <ChatbotWelcomePrompt
                  title="Hi, ChatBot User!"
                  description="How can I help you today?"
                  prompts={fillerWelcomePrompts}
                />
                {/* This code block enables scrolling to the top of the last message.
                  You can instead choose to move the div with scrollToBottomRef on it below 
                  the map of messages, so that users are forced to scroll to the bottom.
                  If you are using streaming, you will want to take a different approach; 
                  see: https://github.com/patternfly/chatbot/issues/201#issuecomment-2400725173 */}
                {messages.map((message, index) => {
                  if (index === messages.length - 1) {
                    return (
                      <>
                        <div ref={scrollToBottomRef}></div>
                        <Message key={message.id} {...message} />
                      </>
                    );
                  }
                  return <Message key={message.id} {...message} />;
                })}
              </MessageBox>
            </ChatbotContent>
            <ChatbotFooter>
              <MessageBar
                onSendMessage={handleSend}
                hasMicrophoneButton
                isSendButtonDisabled={isSendButtonDisabled}
              />
              <ChatbotFootnote {...footnoteProps} />
            </ChatbotFooter>
          </>
        }
      ></ChatbotConversationHistoryNav>
    </Chatbot>
  );
}
