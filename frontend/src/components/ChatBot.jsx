import React, { useState, useRef, useEffect } from 'react'
import { chatStream, fetchConversationHistory } from '../services/api'
import CodeBlock from './CodeBlock.jsx'
import './ChatBot.css'

const ChatBot = ({ activeConversationId, onConversationCreated }) => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const conversationIdRef = useRef(activeConversationId)
  const streamingIdRef = useRef(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const prevMessageCountRef = useRef(0)

  const focusInput = () => {
    requestAnimationFrame(() => {
      inputRef.current?.focus({ preventScroll: true })
    })
  }

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

  useEffect(() => {
    const previousId = conversationIdRef.current

    if (previousId && activeConversationId === null) {
      conversationIdRef.current = null
      setMessages([])
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
      prevMessageCountRef.current = 0
      focusInput()

      fetchConversationHistory(activeConversationId)
        .then(res => setMessages(res.messages || []))
        .catch(() => {
          setMessages([
            { id: 'error', role: 'assistant', message: 'Failed to load conversation.' }
          ])
        })
    }
  }, [activeConversationId])

  const renderMessage = (text) => {
    if (!text) return null

    const blocks = text.split(/```/g)

    return blocks.map((block, index) => {
      if (index % 2 === 1) {
        const lines = block.split('\n')
        return (
          <CodeBlock
            key={index}
            language={lines[0]?.trim()}
            code={lines.slice(1).join('\n')}
          />
        )
      }

      return block.split('\n').map((line, i) => (
        <div key={`${index}-${i}`} className="msg-line">
          {line || <span className="msg-spacer" />}
        </div>
      ))
    })
  }

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

  const showWelcome =
    activeConversationId === null && messages.length === 0

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

      {/* 🔥 NOT A FORM — PREVENT SAFARI UI */}
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
              handleSend(e)
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