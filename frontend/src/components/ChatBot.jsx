import React, { useState, useRef, useEffect } from 'react'
import { chatStream, fetchConversationHistory, uploadFile } from '../services/api'
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

  const [attachedFiles, setAttachedFiles] = useState([])
  const [showAttachMenu, setShowAttachMenu] = useState(false)

  const [lightboxImage, setLightboxImage] = useState(null)
  const [copiedMsgId, setCopiedMsgId] = useState(null)

  /* ================= REFS ================= */

  const conversationIdRef = useRef(null)
  const streamingIdRef = useRef(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const fileInputRef = useRef(null)
  const imageInputRef = useRef(null)
  const attachMenuRef = useRef(null)

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
      setAttachedFiles([])
      prevMessageCountRef.current = 0
      return
    }

    if (conversationIdRef.current === activeConversationId) return

    const requestedId = activeConversationId
    conversationIdRef.current = requestedId

    setHideWelcome(true)
    setMessages([])
    setAttachedFiles([])
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

  /* ================= ATTACH MENU OUTSIDE CLICK ================= */

  useEffect(() => {
    if (!showAttachMenu) return

    const handleClickOutside = (e) => {
      if (
        attachMenuRef.current &&
        !attachMenuRef.current.contains(e.target)
      ) {
        setShowAttachMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showAttachMenu])

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

  /* ================= FILE UPLOAD ================= */

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return

    try {
      setLoading(true)
      for (const file of files) {
        const uploaded = await uploadFile(file)
        setAttachedFiles(prev => [...prev, uploaded])
      }
    } catch (err) {
      console.error('FILE_UPLOAD_FAILED', err)
      alert('Failed to upload file')
    } finally {
      setLoading(false)
      e.target.value = ''
    }
  }

  const removeFile = (fileId) => {
    setAttachedFiles(prev => prev.filter(f => f.file_id !== fileId))
  }

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
        attachedFiles.map(f => f.file_id),
        (chunk) => {
          if (chunk.startsWith('data:image') || chunk.length > 5000) return
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
                      imageRequested: meta.images.length,
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
      setAttachedFiles([])

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

        const images = Array.isArray(msg.images) ? msg.images : []
        const page = msg.imagePage || 1
        const perPage = 3

        const totalImages = msg.imageRequested || images.length
        const totalPages = Math.ceil(totalImages / perPage)

        const start = (page - 1) * perPage
        const end = start + perPage
        const visibleImages = images.slice(start, end)

        return (
          <div
            key={msg.id}
            className={`message ${msg.role} ${isStreaming ? 'streaming' : ''}`}
          >
            <div className="message-content">

              {/* ✅ SHOW GENERATING ONLY WHILE TEXT IS EMPTY */}
              {msg.role === 'assistant' && isStreaming && !msg.message && (
                <div className="thinking">
                  <span className="thinking-dot" />
                  <span className="thinking-dot" />
                  <span className="thinking-dot" />
                  <span>Generating</span>
                </div>
              )}

              {renderMessage(msg.message)}

              {/* ✅ IMAGE PAGINATION — 3 PER PAGE */}
              {visibleImages.length > 0 && (
                <div className="assistant-image-grid">
                  {visibleImages.map((img, idx) => (
                    <img
                      key={idx}
                      src={img.url}
                      alt={img.alt || 'generated'}
                      className="chat-image"
                      onClick={() => setLightboxImage(img)}
                    />
                  ))}
                </div>
              )}

              {/* ✅ PAGINATION CONTROLS */}
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
                    Prev
                  </button>

                  <span>{page} / {totalPages}</span>

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
                    Next
                  </button>
                </div>
              )}

            </div>
          </div>
        )
      })}

      {/* ✅ SCROLL ANCHOR RESTORED */}
      <div ref={messagesEndRef} />

    </div> {/* ✅ messages-container CLOSED */}

    <div className="input-container">

      {attachedFiles.length > 0 && (
        <div className="attached-files">
          {attachedFiles.map(file => (
            <div key={file.file_id} className="file-chip">
              <span>{file.filename}</span>
              <button onClick={() => removeFile(file.file_id)}>×</button>
            </div>
          ))}
        </div>
      )}

      <div className="input-row">
        <div className="attach-wrapper" ref={attachMenuRef}>
          <button
            className="attach-button"
            disabled={loading}
            onClick={() => setShowAttachMenu(v => !v)}
          >
            📎
          </button>

          {showAttachMenu && (
            <div className="attach-menu">
              <button onClick={() => {
                setShowAttachMenu(false)
                fileInputRef.current?.click()
              }}>
                Upload file
              </button>

              <button onClick={() => {
                setShowAttachMenu(false)
                imageInputRef.current?.click()
              }}>
                Upload photo
              </button>
            </div>
          )}
        </div>

        <textarea
          ref={inputRef}
          className="message-input"
          value={inputMessage}
          placeholder="StackMind will solve that for you…"
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

      <input ref={fileInputRef} type="file" multiple hidden onChange={handleFileSelect} />
      <input ref={imageInputRef} type="file" accept="image/*" multiple hidden onChange={handleFileSelect} />
    </div>

    {lightboxImage && (
      <div className="image-lightbox" onClick={() => setLightboxImage(null)}>
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