import React, { useState, useRef, useEffect } from 'react'
import { chatStream, fetchConversationHistory } from '../services/api'
import CodeBlock from './CodeBlock.jsx'
import './ChatBot.css'

/*
  ChatBot Component
  ----------------
  Responsibilities:
  - Render chat messages (user + assistant)
  - Stream assistant responses from backend
  - Preserve markdown formatting (**bold**, bullets, headings, code blocks)
  - Load conversation history when selected
  - Report newly-created conversation_id to parent (ChatLayout)

  ARCHITECTURE GUARANTEES:
  - ChatBot does NOT own layout (header/sidebar)
  - ChatBot does NOT own global conversation state
  - ChatBot NEVER resets itself on conversation creation
*/

const ChatBot = ({ activeConversationId, onConversationCreated }) => {
  // =========================================================
  // UI state
  // =========================================================
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)

  // =========================================================
  // Conversation id reference
  // ---------------------------------------------------------
  // IMPORTANT:
  // - This ref DOES NOT cause re-render
  // - Persists conversation_id across streaming
  // =========================================================
  const conversationIdRef = useRef(activeConversationId)

  // =========================================================
  // Refs for scrolling + streaming control
  // =========================================================
  const messagesEndRef = useRef(null)
  const chunkQueueRef = useRef([])
  const isProcessingRef = useRef(false)
  const sentenceBufferRef = useRef('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // =========================================================
  // 🔥 CRITICAL FIX — SAFE RESET LOGIC
  // ---------------------------------------------------------
  // Reset ONLY when USER switches conversations
  // NOT when backend creates a conversation_id
  // =========================================================
  useEffect(() => {
    const isUserSwitch =
      conversationIdRef.current !== null &&
      conversationIdRef.current !== activeConversationId

    if (isUserSwitch) {
      // Hard reset streaming state
      chunkQueueRef.current = []
      sentenceBufferRef.current = ''
      isProcessingRef.current = false

      setIsStreaming(false)
      setMessages([])
    }

    // ALWAYS sync ref AFTER decision
    conversationIdRef.current = activeConversationId
  }, [activeConversationId])

  // =========================================================
  // Welcome message (ONLY for brand new chat)
  // =========================================================
  useEffect(() => {
    if (activeConversationId !== null) return

    setMessages([
      {
        role: 'assistant',
        message: "Nice to meet you. What's on your mind?",
        timestamp: new Date(),
        variant: 'welcome'
      }
    ])
  }, [activeConversationId])

  // =========================================================
  // Load conversation history
  // =========================================================
  useEffect(() => {
    if (!activeConversationId) return

    fetchConversationHistory(activeConversationId)
      .then(res => setMessages(res.messages || []))
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

  // =========================================================
  // Auto-scroll
  // =========================================================
  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  const sleep = (ms) => new Promise(r => setTimeout(r, ms))

  // =========================================================
  // Sentence-level streaming processor
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
  // MARKDOWN RENDERER (EDGE-CASE COMPLETE)
  // =========================================================
  const renderMessage = (text) => {
    const blocks = text.split(/```/g)

    return blocks.map((block, index) => {
      // ---------- Code block ----------
      if (index % 2 === 1) {
        const lines = block.split('\n')
        return (
          <CodeBlock
            key={index}
            language={lines[0].trim()}
            code={lines.slice(1).join('\n')}
          />
        )
      }

      // ---------- Normal text ----------
      return block.split('\n').map((rawLine, i) => {
        const line = rawLine.trim()

        if (!line) {
          return <div key={`${index}-${i}`} className="msg-spacer" />
        }

        // Headings ###, ####
        if (/^#{2,4}\s+/.test(line)) {
          return (
            <div key={`${index}-${i}`} className="msg-heading">
              {line.replace(/^#{2,4}\s*/, '')}
            </div>
          )
        }

        // Numbered lists
        if (/^\d+\.\s+/.test(line)) {
          return (
            <div key={`${index}-${i}`} className="msg-bullet">
              <span className="bullet-dot">•</span>
              <span>{line.replace(/^\d+\.\s+/, '')}</span>
            </div>
          )
        }

        // Bullets *, +, •
        if (/^(\* |\+ |• )/.test(line)) {
          return (
            <div key={`${index}-${i}`} className="msg-bullet">
              <span className="bullet-dot">•</span>
              <span>{line.replace(/^(\* |\+ |• )/, '')}</span>
            </div>
          )
        }

        // Inline bold **text**
        const parts = line.split(/(\*\*.*?\*\*)/g)

        return (
          <div key={`${index}-${i}`} className="msg-line">
            {parts.map((part, j) =>
              part.startsWith('**') ? (
                <strong key={j}>{part.replace(/\*\*/g, '')}</strong>
              ) : (
                <span key={j}>{part}</span>
              )
            )}
          </div>
        )
      })
    })
  }

  // =========================================================
  // Handle send (STREAM + SAVE)
  // =========================================================
  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setLoading(true)
    setIsStreaming(true)

    // Push user message immediately
    setMessages(prev => [
      ...prev,
      { role: 'user', message: userMessage, timestamp: new Date() }
    ])

    // Placeholder assistant message
    let assistantIndex
    setMessages(prev => {
      assistantIndex = prev.length
      return [...prev, { role: 'assistant', message: '', timestamp: new Date() }]
    })

    try {
      await chatStream(
        userMessage,
        conversationIdRef.current,
        (chunk) => {
          // 🔥 META MESSAGE (STRING, SENT ONCE)
          if (chunk.startsWith('__META__')) {
            const meta = JSON.parse(chunk.replace('__META__', '').trim())
            conversationIdRef.current = meta.conversation_id
            onConversationCreated?.(meta.conversation_id)
            return
          }

          chunkQueueRef.current.push(chunk)
          processQueue(assistantIndex)
        }
      )
    } finally {
      // Flush remaining buffer
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
  // UI
  // =========================================================
  return (
    <div className="chatbot-container">
      <div className="messages-container">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.role} ${msg.variant || ''} ${msg.error ? 'error' : ''}`}
          >
            <div className="message-content">
              <div className="message-text">
                {renderMessage(msg.message)}
                {isStreaming &&
                  msg.role === 'assistant' &&
                  i === messages.length - 1 && (
                    <span className="cursor">▍</span>
                  )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-container" onSubmit={handleSend}>
        <input
          className="message-input"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask StackMind…"
          disabled={loading}
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