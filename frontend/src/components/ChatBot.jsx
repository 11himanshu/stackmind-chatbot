import React, { useState, useRef, useEffect } from 'react'
import { chatStream, fetchConversationHistory } from '../services/api'
import CodeBlock from './CodeBlock.jsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './ChatBot.css'

const ChatBot = ({ activeConversationId, onConversationCreated }) => {
  /* ================= STATE ================= */

  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)

  // Controls welcome hero fade-out
  const [hideWelcome, setHideWelcome] = useState(false)

  const conversationIdRef = useRef(activeConversationId)
  const streamingIdRef = useRef(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const prevMessageCountRef = useRef(0)

  const [copiedMsgId, setCopiedMsgId] = useState(null)

  const focusInput = () => {
    requestAnimationFrame(() => {
      inputRef.current?.focus({ preventScroll: true })
    })
  }

  /* ================= SCROLL ================= */

  useEffect(() => {
    const prev = prevMessageCountRef.current
    const curr = messages.length

    if (curr > prev) {
      messagesEndRef.current?.scrollIntoView({
        block: 'end',
        behavior: 'auto'
      })
    }

    prevMessageCountRef.current = curr
  }, [messages])

  /* ================= CONVERSATION ================= */

  useEffect(() => {
    const previousId = conversationIdRef.current

    if (previousId && activeConversationId === null) {
      conversationIdRef.current = null
      setMessages([])
      setHideWelcome(false)
      prevMessageCountRef.current = 0
      focusInput()
      return
    }

    if (!previousId && activeConversationId) {
      conversationIdRef.current = activeConversationId
      return
    }

    if (previousId === activeConversationId) return

    if (previousId && activeConversationId) {
      conversationIdRef.current = activeConversationId
      setMessages([])
      setHideWelcome(true)
      prevMessageCountRef.current = 0
      focusInput()

      fetchConversationHistory(activeConversationId)
        .then(res => setMessages(res.messages || []))
        .catch(() => {
          setMessages([
            {
              id: 'error',
              role: 'assistant',
              message: 'Failed to load conversation.'
            }
          ])
        })
    }
  }, [activeConversationId])

  /* ================= MARKDOWN ================= */

  const renderMessage = (text) => {
    if (!text) return null

    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ inline, className, children }) {
            const match = /language-(\w+)/.exec(className || '')

            if (!inline && match) {
              return (
                <CodeBlock
                  language={match[1]}
                  code={String(children).replace(/\n$/, '')}
                />
              )
            }

            return (
              <code className="inline-code">
                {children}
              </code>
            )
          }
        }}
      >
        {text}
      </ReactMarkdown>
    )
  }

  /* ================= COPY ================= */

  const copyAssistantText = (msgId, text) => {
    if (!text) return

    const cleaned = text.replace(/```[\s\S]*?```/g, '').trim()
    navigator.clipboard.writeText(cleaned)

    setCopiedMsgId(msgId)
    setTimeout(() => setCopiedMsgId(null), 1200)
  }

  /* ================= SEND ================= */

  const handleSend = async (e) => {
    if (e) e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userText = inputMessage.trim()
    const streamingId = crypto.randomUUID()
    streamingIdRef.current = streamingId

    // Trigger welcome fade-out ON FIRST USER ACTION
    setHideWelcome(true)

    setInputMessage('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', message: userText },
      { id: streamingId, role: 'assistant', message: '' }
    ])

    try {
      await chatStream(
        userText,
        conversationIdRef.current,
        (chunk) => {
          setMessages(prev =>
            prev.map(msg =>
              msg.id === streamingId
                ? { ...msg, message: msg.message + chunk }
                : msg
            )
          )
        },
        (meta) => {
          if (!conversationIdRef.current && meta?.conversation_id) {
            conversationIdRef.current = meta.conversation_id
            onConversationCreated?.(meta.conversation_id)
          }
        }
      )
    } finally {
      streamingIdRef.current = null
      setLoading(false)
      focusInput()
    }
  }

  /* ================= WELCOME VISIBILITY ================= */

  const showWelcome =
    activeConversationId === null && !hideWelcome

  /* ================= UI ================= */

  return (
    <div className="chatbot-container">
      <div className={`messages-container ${showWelcome ? 'centered' : ''}`}>

        {/* ===== WELCOME HERO ===== */}
        {showWelcome && (
          <div className={`message assistant welcome ${hideWelcome ? 'fade-out' : ''}`}>
            <div className="message-content">
              Nice to meet you. What’s on your mind today?
            </div>
          </div>
        )}

        {/* ===== CHAT MESSAGES ===== */}
        {messages.map(msg => {
          const isStreaming = msg.id === streamingIdRef.current

          return (
            <div
              key={msg.id}
              className={`message ${msg.role} ${isStreaming ? 'streaming' : ''}`}
            >
              <div className="message-content">

                {/* THINKING INDICATOR — ABOVE TEXT */}
                {msg.role === 'assistant' && isStreaming && (
                  <div className="thinking">
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span>Generating</span>
                  </div>
                )}

                {/* COPY BUTTON */}
                {msg.role === 'assistant' && msg.message && (
                  <button
                    className={`assistant-copy-btn ${
                      copiedMsgId === msg.id ? 'copied' : ''
                    }`}
                    onClick={() => copyAssistantText(msg.id, msg.message)}
                    aria-label="Copy response"
                  >
                    {copiedMsgId === msg.id ? 'Copied ✓' : 'Copy'}
                  </button>
                )}

                {renderMessage(msg.message)}

                {isStreaming && (
                  <span className="cursor">▍</span>
                )}
              </div>
            </div>
          )
        })}

        <div ref={messagesEndRef} />
      </div>

      {/* ===== INPUT ===== */}
      <div className="input-container">
        <textarea
          ref={inputRef}
          className="message-input"
          value={inputMessage}
          placeholder="Ask StackMind…"
          disabled={loading}
          inputMode="text"
          enterKeyHint="send"
          autoCorrect="off"
          autoCapitalize="off"
          autoComplete="off"
          spellCheck={false}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
        />

        <button
          className="send-button"
          disabled={loading || !inputMessage.trim()}
          onClick={handleSend}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default ChatBot