# Frontend

Modern React application for the AI Virtual Agent Kickstart, providing an intuitive interface for managing AI agents, knowledge bases, and real-time chat interactions.

## Architecture Overview

The frontend is built with modern React patterns and follows a clean architecture:

```
src/
├── components/           # Reusable UI components
│   ├── chat.tsx         # Main chat interface with PatternFly Chatbot
│   ├── agent-*.tsx      # Agent management components
│   ├── knowledge-base-*.tsx # Knowledge base management
│   └── masthead.tsx     # Application header
├── hooks/               # Custom React hooks
│   └── useChat.ts       # Chat functionality with SSE streaming
├── services/            # API service layer
│   ├── agents.ts        # Agent CRUD operations
│   ├── knowledge-bases.ts # Knowledge base operations
│   └── chat-sessions.ts # Session management
├── routes/              # TanStack Router configuration
│   ├── index.tsx        # Main chat page
│   └── config/          # Configuration pages
├── contexts/            # React contexts
│   └── UserContext.tsx  # User authentication context
└── types/               # TypeScript type definitions
```

## Technology Stack

- **React 18** - Core framework with modern hooks
- **TypeScript** - Type safety and development experience
- **PatternFly** - Enterprise-grade UI component library
- **TanStack Router** - Type-safe routing
- **TanStack Query** - Server state management with caching
- **Vite** - Build tool and development server

## Key Features

### 🤖 Agent Management

- **Visual Agent Creation**: Form-based agent configuration with real-time validation
- **Tool Integration**: Multi-select interface for tools (RAG, web search, MCP servers)
- **Model Selection**: Dynamic model dropdown with real-time availability
- **Advanced Parameters**: Collapsible accordion for sampling parameters

### 💬 Real-time Chat

- **Streaming Responses**: Server-Sent Events for real-time message streaming
- **Session Management**: Persistent chat sessions with history sidebar
- **Multiple Message Types**: Support for text, tool usage, and error messages
- **PatternFly Integration**: Enterprise-grade chat UI components

### 📚 Knowledge Base Management

- **Status Tracking**: Real-time status display (READY, PENDING, ORPHANED)
- **Drag & Drop Upload**: Intuitive file upload for document ingestion
- **S3 Integration**: Configure external document sources
- **Progress Monitoring**: Track ingestion pipeline progress

### 🔧 Configuration Management

- **User Profiles**: User authentication and role management
- **MCP Servers**: External tool server configuration
- **Model Servers**: LLM provider management
- **Guardrails**: Safety shield configuration

## Development Setup

### Prerequisites

- **Node.js 18+** - Runtime environment
- **npm** - Package manager

### Installation

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Start development server**:

   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173`

### Available Scripts

```bash
# Development
npm run dev          # Start development server with hot reload
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # ESLint code analysis
npm run lint:fix     # Auto-fix linting issues
npm run format       # Format code with Prettier
npm run format:check # Check code formatting

# Type Checking
npm run type-check   # TypeScript compilation check
```

## Key Components

### Chat Component (`components/chat.tsx`)

The main chat interface using PatternFly's Chatbot component:

```typescript
// Real-time streaming chat with session management
export function Chat() {
  const {
    messages,
    sendMessage,
    isLoading,
    loadSession
  } = useChat(selectedAgent);

  // PatternFly Chatbot integration
  return (
    <Chatbot displayMode={ChatbotDisplayMode.embedded}>
      <ChatbotContent>
        <MessageBox messages={patternflyMessages} />
      </ChatbotContent>
      <ChatbotFooter>
        <MessageBar onSendMessage={sendMessage} />
      </ChatbotFooter>
    </Chatbot>
  );
}
```

### useChat Hook (`hooks/useChat.ts`)

Custom hook for real-time chat functionality:

```typescript
// HTTP + Server-Sent Events streaming
export function useChat(agentId: string, options?: UseLlamaChatOptions) {
  const sendMessage = useCallback(
    async (content: string) => {
      // 1. Add user message immediately
      setMessages((prev) => [...prev, userMessage]);

      // 2. Send HTTP POST request
      const response = await fetch(CHAT_API_ENDPOINT, {
        method: 'POST',
        body: JSON.stringify(requestBody),
      });

      // 3. Process Server-Sent Events stream
      const reader = response.body.getReader();
      // ... streaming logic
    },
    [agentId, messages]
  );

  return { messages, sendMessage, isLoading };
}
```

### Agent Form (`components/agent-form.tsx`)

Comprehensive form for agent creation with advanced configuration:

- **Dynamic Tool Selection**: Multi-select with real-time tool availability
- **Knowledge Base Integration**: Conditional KB selection when RAG tool is enabled
- **Sampling Parameters**: Collapsible advanced configuration
- **Real-time Validation**: Form validation with helpful error messages

### Service Layer

#### Agent Service (`services/agents.ts`)

```typescript
export const agentService = {
  fetchAgents(): Promise<Agent[]>
  createAgent(data: NewAgent): Promise<Agent>
  deleteAgent(id: string): Promise<void>
}
```

#### Knowledge Base Service (`services/knowledge-bases.ts`)

```typescript
export const knowledgeBaseService = {
  fetchKnowledgeBasesWithStatus(): Promise<KnowledgeBaseWithStatus[]>
  createKnowledgeBase(data: CreateKBRequest): Promise<DatabaseKB>
  syncKnowledgeBases(): Promise<DatabaseKB[]>
}
```

## State Management

### TanStack Query

Used for server state management with intelligent caching:

```typescript
// Automatic caching and background updates
const { data: agents, isLoading } = useQuery({
  queryKey: ['agents'],
  queryFn: fetchAgents,
});

// Optimistic updates for better UX
const createMutation = useMutation({
  mutationFn: createAgent,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['agents'] });
  },
});
```

### React Context

- **UserContext**: Authentication and user profile management
- **Component State**: Local state with React hooks (useState, useReducer)

## Type Safety

### Key Types (`types/index.d.ts`)

```typescript
interface Agent {
  id: string;
  name: string;
  model_name: string;
  prompt: string;
  knowledge_base_ids: string[];
  tools: ToolAssociationInfo[];
  sampling_strategy: 'greedy' | 'top-p' | 'top-k';
  // ... other properties
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

## UI/UX Patterns

### PatternFly Integration

- **Consistent Design**: Enterprise-grade design system
- **Accessibility**: Built-in ARIA attributes and keyboard navigation
- **Responsive Layout**: Mobile-friendly components
- **Theme Support**: Consistent color scheme and typography

### Error Handling

- **Graceful Degradation**: Meaningful error messages and fallback states
- **Loading States**: Skeleton loaders and progress indicators
- **Retry Mechanisms**: Automatic retries for failed requests

### Real-time Updates

- **Optimistic Updates**: Immediate UI feedback for user actions
- **Background Sync**: Automatic data refresh without user intervention
- **Connection Status**: Visual indicators for connection health

## Performance Optimizations

### Code Splitting

- **Route-based Splitting**: Automatic code splitting by routes
- **Component Lazy Loading**: Dynamic imports for large components

### Caching Strategy

- **TanStack Query**: Intelligent server state caching
- **React Query DevTools**: Development debugging tools

### Bundle Optimization

- **Tree Shaking**: Automatic removal of unused code
- **Asset Optimization**: Optimized images and static assets

## Development Guidelines

### Component Structure

```typescript
// Consistent component structure
interface ComponentProps {
  // Props interface
}

export function Component({ prop1, prop2 }: ComponentProps) {
  // Hooks at the top
  const [state, setState] = useState();
  const { data } = useQuery(...);

  // Event handlers
  const handleAction = useCallback(() => {
    // Handler logic
  }, [dependencies]);

  // Render
  return (
    <PatternFlyComponent>
      {/* JSX content */}
    </PatternFlyComponent>
  );
}
```

### Code Style

- **TypeScript Strict Mode**: Full type checking enabled
- **ESLint Rules**: React, TypeScript, and accessibility rules
- **Prettier Formatting**: Consistent code formatting
- **Pre-commit Hooks**: Automatic formatting and linting

### Testing (Future)

- **Component Testing**: React Testing Library
- **E2E Testing**: Playwright or Cypress
- **API Mocking**: MSW for service layer testing

## Troubleshooting

### Common Issues

**Frontend won't start:**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Type errors:**

```bash
# Run type checking
npm run type-check

# Check for TypeScript configuration issues
npx tsc --noEmit
```

**Build failures:**

```bash
# Check for linting issues
npm run lint

# Fix auto-fixable issues
npm run lint:fix
```

**API connection issues:**

- Verify backend is running on `http://localhost:8000`
- Check browser network tab for CORS errors
- Ensure API endpoints match backend routes

### Development Tools

**Browser Extensions:**

- **React Developer Tools**: Component debugging
- **TanStack Query DevTools**: Server state inspection
- **Vite DevTools**: Build analysis

**VSCode Extensions:**

- **TypeScript Importer**: Automatic import organization
- **ESLint**: Real-time code analysis
- **Prettier**: Automatic formatting
