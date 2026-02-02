import React, { useState, useRef, useEffect } from 'react'
import { chatStream, fetchConversationHistory } from '../services/api'
import CodeBlock from './CodeBlock.jsx'
import './ChatBot.css'

const ChatBot = ({ activeConversationId, onConversationCreated }) => {
  // =========================================================
  // Core state (SINGLE SOURCE OF TRUTH)
  // =========================================================
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const conversationIdRef = useRef(activeConversationId)
  const streamingIdRef = useRef(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const prevMessageCountRef = useRef(0)

  // =========================================================
  // Focus input safely
  // =========================================================
  const focusInput = () => {
    requestAnimationFrame(() => {
      inputRef.current?.focus({ preventScroll: true })
    })
  }

  // =========================================================
  // Scroll handling (SAFE, NO CONVERSATION IMPACT)
  // =========================================================
  useEffect(() => {
    const prev = prevMessageCountRef.current
    const curr = messages.length

    // First message: hard anchor to avoid jump
    if (prev === 0 && curr > 0) {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({
          block: 'end',
          behavior: 'auto'
        })
      })
    }

    // Subsequent messages: keep pinned to bottom
    if (prev > 0 && curr > prev) {
      messagesEndRef.current?.scrollIntoView({
        block: 'end',
        behavior: 'auto'
      })
    }

    prevMessageCountRef.current = curr
  }, [messages])

  // =========================================================
  // Handle conversation changes (ORIGINAL, UNTOUCHED LOGIC)
  // =========================================================
  useEffect(() => {
    const previousId = conversationIdRef.current

    // 1️⃣ New Chat (id → null)
    if (previousId && activeConversationId === null) {
      conversationIdRef.current = null
      streamingIdRef.current = null
      setMessages([])
      prevMessageCountRef.current = 0
      focusInput()
      return
    }

    // 2️⃣ First conversation creation (null → id)
    if (!previousId && activeConversationId) {
      conversationIdRef.current = activeConversationId
      return
    }

    // 3️⃣ Same conversation (id → id)
    if (previousId === activeConversationId) return

    // 4️⃣ Switching between existing conversations
    if (previousId && activeConversationId) {
      conversationIdRef.current = activeConversationId
      streamingIdRef.current = null
      setMessages([])
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

  // =========================================================
  // Markdown renderer (SAFE)
  // =========================================================
  const renderMessage = (text) => {
    if (!text) return null

    const blocks = text.split(/```/g)

    return blocks.map((block, index) => {
      if (index % 2 === 1) {
        const lines = block.split('\n')
        return (
          <CodeBlock
            key={`code-${index}`}
            language={lines[0]?.trim()}
            code={lines.slice(1).join('\n')}
          />
        )
      }

      return block.split('\n').map((line, i) => (
        <div key={`line-${index}-${i}`} className="msg-line">
          {line || <span className="msg-spacer" />}
        </div>
      ))
    })
  }

  // =========================================================
  // Send message (STREAMING MERGED INTO messages)
  // =========================================================
  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userText = inputMessage.trim()
    const streamingId = crypto.randomUUID()
    streamingIdRef.current = streamingId

    setInputMessage('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: 'user',
        message: userText
      },
      {
        id: streamingId,
        role: 'assistant',
        message: ''
      }
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

  // =========================================================
  // Derived UI flags
  // =========================================================
  const showWelcome =
    activeConversationId === null &&
    messages.length === 0

  // =========================================================
  // UI
  // =========================================================
  return (
    <div className="chatbot-container">
      <div className={`messages-container ${showWelcome ? 'centered' : ''}`}>

        {showWelcome && (
          <div className="message assistant welcome">
            <div className="message-content">
              Nice to meet you. What&apos;s on your mind today?
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-content">
              {renderMessage(msg.message)}
              {msg.id === streamingIdRef.current && (
                <span className="cursor">▍</span>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-container" onSubmit={handleSend}>
        <textarea
          ref={inputRef}
          className="message-input"
          value={inputMessage}
          placeholder="Ask StackMind…"
          rows={1}
          disabled={loading}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend(e)
            }
          }}
        />
        <button
          className="send-button"
          disabled={loading || !inputMessage.trim()}
        >
          Send
        </button>
      </form>
    </div>
  )
}

export default ChatBot