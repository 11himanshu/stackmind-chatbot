import React, { useState, useRef, useEffect } from 'react'
import { streamMessage, fetchConversationHistory } from '../services/api'
import CodeBlock from './CodeBlock.jsx'
import './ChatBot.css'

/*
  ChatBot Component
  -----------------
  Responsibilities:
  - Render chat UI
  - Handle sentence-level streaming
  - Preserve code blocks (```language ... ```)
  - Support conversation switching from sidebar
*/

const ChatBot = ({ activeConversationId }) => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef(null)

  // =========================================================
  // Streaming control refs (DO NOT MODIFY LOGIC)
  // =========================================================
  const chunkQueueRef = useRef([])
  const isProcessingRef = useRef(false)
  const sentenceBufferRef = useRef('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // =========================================================
  // Reset streaming state when switching conversations
  // =========================================================
  useEffect(() => {
    chunkQueueRef.current = []
    sentenceBufferRef.current = ''
    isProcessingRef.current = false
    setIsStreaming(false)
  }, [activeConversationId])

  // =========================================================
  // Welcome message (only when no conversation selected)
  // =========================================================
  useEffect(() => {
    if (!activeConversationId) {
      setMessages([
        {
          role: 'assistant',
          message: "Nice to meet you. What's on your mind?",
          timestamp: new Date(),
          variant: 'welcome'
        }
      ])
    }
  }, [activeConversationId])

  // =========================================================
  // Load conversation history when user selects from sidebar
  // =========================================================
  useEffect(() => {
    if (!activeConversationId) return

    fetchConversationHistory(activeConversationId, 1)
      .then(res => setMessages(res.messages))
      .catch(() => {
        setMessages([
          {
            role: 'assistant',
            message: 'Failed to load conversation.',
            timestamp: new Date(),
            error: true
          }
        ])
      })
  }, [activeConversationId])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  const sleep = (ms) => new Promise(r => setTimeout(r, ms))

  // =========================================================
  // Sentence-level streaming processor (UNCHANGED)
  // =========================================================
  const processQueue = async (assistantIndex) => {
    if (isProcessingRef.current) return
    isProcessingRef.current = true

    while (chunkQueueRef.current.length > 0) {
      const chunk = chunkQueueRef.current.shift()
      sentenceBufferRef.current += chunk

      const regex = /([^.!?]+[.!?]+)/

      let match
      while ((match = sentenceBufferRef.current.match(regex))) {
        const sentence = match[1]
        sentenceBufferRef.current =
          sentenceBufferRef.current.slice(sentence.length)

        setMessages(prev => {
          const updated = [...prev]
          if (!updated[assistantIndex]) return prev
          updated[assistantIndex].message += sentence
          return updated
        })

        await sleep(120)
      }
    }

    isProcessingRef.current = false
  }

  // =========================================================
  // NEW: Render message with fenced code block support
  // This preserves ```language ... ``` exactly like ChatGPT
  // =========================================================
  const renderMessage = (text) => {
    // Split on triple backticks
    const parts = text.split(/```/g)

    return parts.map((part, index) => {
      // Odd indexes = code blocks
      if (index % 2 === 1) {
        const lines = part.split('\n')
        const language = lines[0].trim()
        const code = lines.slice(1).join('\n')

        return (
          <CodeBlock
            key={index}
            language={language}
            code={code}
          />
        )
      }

      // Even indexes = normal text
      return (
        <span key={index}>
          {part}
        </span>
      )
    })
  }

  // =========================================================
  // Handle sending user message
  // =========================================================
  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setLoading(true)
    setIsStreaming(true)

    setMessages(prev => [
      ...prev,
      { role: 'user', message: userMessage, timestamp: new Date() }
    ])

    let assistantIndex

    setMessages(prev => {
      assistantIndex = prev.length
      return [
        ...prev,
        { role: 'assistant', message: '', timestamp: new Date() }
      ]
    })

    try {
      await streamMessage(userMessage, activeConversationId, (chunk) => {
        chunkQueueRef.current.push(chunk)
        processQueue(assistantIndex)
      })
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[assistantIndex] = {
          role: 'assistant',
          message: 'Sorry, something went wrong. Please try again.',
          timestamp: new Date(),
          error: true
        }
        return updated
      })
    } finally {
      // Flush remaining buffered text
      if (sentenceBufferRef.current) {
        setMessages(prev => {
          const updated = [...prev]
          updated[assistantIndex].message += sentenceBufferRef.current
          return updated
        })
        sentenceBufferRef.current = ''
      }

      setIsStreaming(false)
      setLoading(false)
    }
  }

  // =========================================================
  // Render UI
  // =========================================================
  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="header-left">
          <div className="logo">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <defs>
                <linearGradient id="cubeGrad" x1="0" y1="0" x2="36" y2="36">
                  <stop offset="0%" stopColor="#141e30" />
                  <stop offset="100%" stopColor="#243b55" />
                </linearGradient>
              </defs>
              <path d="M18 4L30 10L18 16L6 10L18 4Z" fill="url(#cubeGrad)" />
              <path d="M30 10V22L18 28V16L30 10Z" fill="#1f2f46" />
              <path d="M6 10V22L18 28V16L6 10Z" fill="#2c3e5a" />
            </svg>
          </div>

          <div>
            <h1>StackMind</h1>
            <p className="header-subtitle">Powered by Himanshu</p>
          </div>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.role} ${msg.variant || ''} ${msg.error ? 'error' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="message-avatar">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <rect x="3" y="3" width="14" height="14" rx="4" fill="#243b55" opacity="0.2" />
                </svg>
              </div>
            )}

            <div className="message-content">
              <div className="message-text">
                {renderMessage(msg.message)}
                {isStreaming &&
                  msg.role === 'assistant' &&
                  index === messages.length - 1 && (
                    <span className="cursor">▍</span>
                  )}
              </div>

              <div className="message-time">
                {new Date(msg.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="message-avatar user-avatar">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <circle cx="10" cy="10" r="9" fill="white" opacity="0.35" />
                </svg>
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-container" onSubmit={handleSend}>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask StackMind…"
          className="message-input"
          disabled={loading}
        />

        <button
          type="submit"
          className="send-button"
          disabled={loading || !inputMessage.trim()}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </form>
    </div>
  )
}

export default ChatBot
