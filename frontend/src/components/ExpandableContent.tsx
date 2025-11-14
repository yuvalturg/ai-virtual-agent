import React from 'react';
import { ExpandableSection } from '@patternfly/react-core';
import ReactMarkdown from 'react-markdown';

interface ReasoningSectionProps {
  text: string;
  isComplete?: boolean;
}

export const ReasoningSection: React.FC<ReasoningSectionProps> = ({ text, isComplete = true }) => {
  const statusEmoji = isComplete ? '✅' : '⏳';

  return (
    <ExpandableSection toggleText={`${statusEmoji} Reasoning`} isIndented displaySize="default">
      <div
        style={{
          fontStyle: 'italic',
          padding: '8px',
          borderLeft: '2px solid #d2d2d2',
          color: '#6a6e73',
        }}
      >
        {text}
      </div>
    </ExpandableSection>
  );
};

interface ToolCallSectionProps {
  name: string;
  serverLabel?: string;
  status?: 'in_progress' | 'completed' | 'failed';
  arguments?: string;
  output?: string;
  error?: string;
}

export const ToolCallSection: React.FC<ToolCallSectionProps> = ({
  name,
  serverLabel,
  status = 'completed',
  arguments: args,
  output,
  error,
}) => {
  const statusEmoji = status === 'completed' ? '✅' : status === 'failed' ? '❌' : '⏳';
  const toolName = serverLabel ? `${serverLabel}::${name}` : name;

  const codeBlockStyle = {
    background: '#e8e8e8',
    padding: '8px',
    borderRadius: '4px',
    overflowX: 'auto' as const,
    marginTop: '4px',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    border: '1px solid #d2d2d2',
  };

  return (
    <ExpandableSection
      toggleText={`${statusEmoji} Tool Call: ${toolName}`}
      isIndented
      displaySize="default"
    >
      <div
        style={{
          fontStyle: 'italic',
          padding: '8px',
          borderLeft: '2px solid #d2d2d2',
          color: '#6a6e73',
        }}
      >
        {args && (
          <div style={{ marginTop: '4px' }}>
            <strong>Arguments:</strong>
            <pre style={codeBlockStyle}>
              <code>
                {(() => {
                  try {
                    return JSON.stringify(JSON.parse(args), null, 2);
                  } catch {
                    return args;
                  }
                })()}
              </code>
            </pre>
          </div>
        )}
        {output && (
          <div style={{ marginTop: '4px' }}>
            <strong>Output:</strong>
            <pre style={codeBlockStyle}>
              <code>{output}</code>
            </pre>
          </div>
        )}
        {error && (
          <div style={{ marginTop: '4px', color: '#c9190b' }}>
            <strong>Error:</strong>
            <pre style={{ ...codeBlockStyle, background: '#ffe6e6' }}>
              <code>{error}</code>
            </pre>
          </div>
        )}
      </div>
    </ExpandableSection>
  );
};

interface TextContentProps {
  text: string;
  isMarkdown?: boolean;
}

export const TextContent: React.FC<TextContentProps> = ({ text, isMarkdown = false }) => {
  if (isMarkdown) {
    return (
      <div className="markdown-content">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
    );
  }
  return <div>{text}</div>;
};

interface ImageContentProps {
  imageUrl: string;
  alt?: string;
}

export const ImageContent: React.FC<ImageContentProps> = ({ imageUrl, alt = 'Image' }) => {
  return <img src={imageUrl} alt={alt} style={{ maxWidth: '100%', height: 'auto' }} />;
};
