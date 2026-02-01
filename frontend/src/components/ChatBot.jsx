import React, { useState, useRef, useEffect } from 'react'
import { chatStream, fetchConversationHistory } from '../services/api'
import CodeBlock from './CodeBlock.jsx'
import './ChatBot.css'

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
  // =========================================================
  const conversationIdRef = useRef(activeConversationId)

  // =========================================================
  // Refs
  // =========================================================
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const chunkQueueRef = useRef([])
  const isProcessingRef = useRef(false)
  const sentenceBufferRef = useRef('')

  // =========================================================
  // Auto focus (SAFE: no scroll jump)
  // =========================================================
  const focusInput = () => {
    requestAnimationFrame(() => {
      inputRef.current?.focus({ preventScroll: true })
    })
  }

  // =========================================================
  // Auto-grow textarea (KEY FIX)
  // =========================================================
  const autoResizeTextarea = () => {
    const el = inputRef.current
    if (!el) return

    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
    el.style.overflowY = 'hidden'
  }

  // =========================================================
  // Scroll ONLY messages container
  // =========================================================
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // =========================================================
  // Reset ONLY on user conversation switch
  // =========================================================
  useEffect(() => {
    const isUserSwitch =
      conversationIdRef.current !== null &&
      conversationIdRef.current !== activeConversationId

    if (isUserSwitch) {
      chunkQueueRef.current = []
      sentenceBufferRef.current = ''
      isProcessingRef.current = false

      setIsStreaming(false)
      setMessages([])
      setInputMessage('')
      requestAnimationFrame(autoResizeTextarea)
      focusInput()
    }

    conversationIdRef.current = activeConversationId
  }, [activeConversationId])

  // =========================================================
  // Welcome message
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

    focusInput()
  }, [activeConversationId])

  // =========================================================
  // Load history
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

    focusInput()
  }, [activeConversationId])

  // =========================================================
  // Auto-scroll messages only
  // =========================================================
  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  const sleep = (ms) => new Promise(r => setTimeout(r, ms))

  // =========================================================
  // Streaming processor (UNCHANGED)
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
  // Markdown renderer (UNCHANGED)
  // =========================================================
  const renderMessage = (text) => {
    const blocks = text.split(/```/g)

    return blocks.map((block, index) => {
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

      return block.split('\n').map((rawLine, i) => {
        const line = rawLine.trim()
        if (!line) return <div key={`${index}-${i}`} className="msg-spacer" />

        if (/^#{2,4}\s+/.test(line)) {
          return (
            <div key={`${index}-${i}`} className="msg-heading">
              {line.replace(/^#{2,4}\s*/, '')}
            </div>
          )
        }

        if (/^\d+\.\s+/.test(line) || /^(\* |\+ |• )/.test(line)) {
          return (
            <div key={`${index}-${i}`} className="msg-bullet">
              <span className="bullet-dot">•</span>
              <span>{line.replace(/^(\d+\.\s+|\* |\+ |• )/, '')}</span>
            </div>
          )
        }

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
  // Send
  // =========================================================
  const handleSend = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setLoading(true)
    setIsStreaming(true)

    requestAnimationFrame(autoResizeTextarea)

    setMessages(prev => [
      ...prev,
      { role: 'user', message: userMessage, timestamp: new Date() }
    ])

    let assistantIndex
    setMessages(prev => {
      assistantIndex = prev.length
      return [...prev, { role: 'assistant', message: '', timestamp: new Date() }]
    })

    focusInput()

    try {
      await chatStream(
        userMessage,
        conversationIdRef.current,
        (chunk) => {
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
      focusInput()
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
        <textarea
          ref={inputRef}
          className="message-input"
          value={inputMessage}
          placeholder="Ask StackMind…"
          disabled={loading}
          rows={1}
          onChange={(e) => {
            setInputMessage(e.target.value)
            autoResizeTextarea()
          }}
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