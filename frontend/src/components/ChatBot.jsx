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
  const [hideWelcome, setHideWelcome] = useState(false)

  const [lightboxImage, setLightboxImage] = useState(null)
  const [copiedMsgId, setCopiedMsgId] = useState(null)

  const conversationIdRef = useRef(null)
  const streamingIdRef = useRef(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const prevMessageCountRef = useRef(0)

  /* ================= SCROLL ================= */

  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      messagesEndRef.current?.scrollIntoView({ block: 'end' })
    }
    prevMessageCountRef.current = messages.length
  }, [messages])

  /* ================= LIGHTBOX ESC ================= */

  useEffect(() => {
    if (!lightboxImage) return

    const onKeyDown = (e) => {
      if (e.key === 'Escape') setLightboxImage(null)
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKeyDown)

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [lightboxImage])

  /* ================= CONVERSATION SWITCH ================= */

  useEffect(() => {
    if (activeConversationId === null) {
      conversationIdRef.current = null
      setMessages([])
      setHideWelcome(false)
      prevMessageCountRef.current = 0
      return
    }

    if (conversationIdRef.current === activeConversationId) return

    const requestedId = activeConversationId
    conversationIdRef.current = requestedId

    setHideWelcome(true)
    setMessages([])
    prevMessageCountRef.current = 0

    fetchConversationHistory(requestedId)
      .then(res => {
        if (conversationIdRef.current !== requestedId) return
        setMessages(res.messages || [])
      })
      .catch(() => {
        if (conversationIdRef.current !== requestedId) return
        setMessages([
          {
            id: 'error',
            role: 'assistant',
            message: 'Failed to load conversation.'
          }
        ])
      })
  }, [activeConversationId])

  /* ================= MARKDOWN ================= */

  const renderMessage = (text) => {
    if (!text) return null

    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: () => null,
          a({ href, children }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            )
          },
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
            return <code className="inline-code">{children}</code>
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

  /* ================= IMAGE PAGE FETCH ================= */
  const fetchImagePage = () => {}

  /* ================= SEND ================= */

  const handleSend = async (e) => {
    if (e) e.preventDefault()
    if (!inputMessage.trim() || loading) return

    const userText = inputMessage.trim()
    const streamingId = crypto.randomUUID()
    streamingIdRef.current = streamingId

    setHideWelcome(true)
    setInputMessage('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', message: userText },
      {
        id: streamingId,
        role: 'assistant',
        message: '',
        images: [],
        imagePage: 1,
        imageRequested: 0
      }
    ])

    let finalText = ''
    let finalImages = []

    try {
      await chatStream(
        userText,
        conversationIdRef.current,
        (chunk) => {
          finalText += chunk
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

          if (meta?.images) {
            finalImages = meta.images

            setMessages(prev =>
              prev.map(msg =>
                msg.id === streamingId
                  ? {
                      ...msg,
                      images: meta.images,
                      imageRequested: meta.requested || meta.images.length,
                      imagePage: 1
                    }
                  : msg
              )
            )
          }
        }
      )
    } finally {
      streamingIdRef.current = null
      setLoading(false)

      setMessages(prev =>
        prev.map(msg => {
          if (msg.id !== streamingId) return msg

          if (!finalText && finalImages.length === 0) {
            return {
              ...msg,
              message:
                'I want to get this right for you. StackMind could not fully understand the request. Please add a bit more detail and I will continue from there.',
              images: []
            }
          }

          return {
            ...msg,
            message: finalText,
            images: finalImages
          }
        })
      )
    }
  }

  /* ================= UI ================= */

  const showWelcome = activeConversationId === null && !hideWelcome

  return (
    <div className="chatbot-container">
      <div className={`messages-container ${showWelcome ? 'centered' : ''}`}>

        {showWelcome && (
          <div className="message assistant welcome">
            <div className="message-content">
              Nice to meet you. What’s on your mind today?
            </div>
          </div>
        )}

        {messages.map(msg => {
          const isStreaming = msg.id === streamingIdRef.current
          const page = msg.imagePage || 1
          const perPage = 3

          /* ✅ FIX: normalize images safely */
          const images = Array.isArray(msg.images) ? msg.images : []
          const totalImages = msg.imageRequested || images.length

          const start = (page - 1) * perPage
          const end = start + perPage
          const visibleImages = images.slice(start, end)

          const totalPages = Math.ceil(totalImages / perPage)

          return (
            <div
              key={msg.id}
              className={`message ${msg.role} ${isStreaming ? 'streaming' : ''}`}
            >
              <div className="message-content">

                {msg.role === 'assistant' && isStreaming && (
                  <div className="thinking">
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span>Generating</span>
                  </div>
                )}

                {msg.role === 'assistant' && visibleImages.length > 0 && (
                  <>
                    <div className="assistant-image-grid">
                      {visibleImages.map((img, i) => (
                        <img
                          key={i}
                          src={img.url}
                          alt={img.alt}
                          loading="lazy"
                          onClick={() => setLightboxImage(img)}
                        />
                      ))}
                    </div>

                    {totalPages > 1 && (
                      <div className="image-pagination">
                        <button
                          disabled={page === 1}
                          onClick={() =>
                            setMessages(prev =>
                              prev.map(m =>
                                m.id === msg.id
                                  ? { ...m, imagePage: page - 1 }
                                  : m
                              )
                            )
                          }
                        >
                          ‹
                        </button>
                        <span>
                          {page} / {totalPages}
                        </span>
                        <button
                          disabled={page === totalPages}
                          onClick={() =>
                            setMessages(prev =>
                              prev.map(m =>
                                m.id === msg.id
                                  ? { ...m, imagePage: page + 1 }
                                  : m
                              )
                            )
                          }
                        >
                          ›
                        </button>
                      </div>
                    )}
                  </>
                )}

                {msg.role === 'assistant' && msg.message && (
                  <button
                    className={`assistant-copy-btn ${
                      copiedMsgId === msg.id ? 'copied' : ''
                    }`}
                    onClick={() => copyAssistantText(msg.id, msg.message)}
                  >
                    {copiedMsgId === msg.id ? 'Copied ✓' : 'Copy'}
                  </button>
                )}

                {renderMessage(msg.message)}
              </div>
            </div>
          )
        })}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <textarea
          ref={inputRef}
          className="message-input"
          value={inputMessage}
          placeholder="StackMind will solve that for you Ask Stackmind…"
          disabled={loading}
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

      {lightboxImage && (
        <div
          className="image-lightbox"
          onClick={() => setLightboxImage(null)}
        >
          <img
            src={lightboxImage.url}
            alt={lightboxImage.alt}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  )
}

export default ChatBot