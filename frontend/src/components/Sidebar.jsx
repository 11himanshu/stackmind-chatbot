import React, { useEffect, useState } from 'react'
import { fetchConversations, deleteConversation } from '../services/api'

const Sidebar = ({ activeConversationId, onSelectConversation }) => {
  const [conversations, setConversations] = useState([])
  const [isMobile, setIsMobile] = useState(false)

  // =========================================================
  // Detect mobile
  // =========================================================
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth <= 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  // =========================================================
  // Load conversations
  // =========================================================
  const loadConversations = () => {
    fetchConversations()
      .then(setConversations)
      .catch(console.error)
  }

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    loadConversations()
  }, [activeConversationId])

  // =========================================================
  // Actions
  // =========================================================
  const handleDelete = async (e, id) => {
    e.stopPropagation()
    await deleteConversation(id)
    loadConversations()
  }

  const handleNewChat = () => {
    // New chat = close sidebar + clear active conversation
    onSelectConversation(null)
  }

  const handleSelect = (id) => {
    // Selecting conversation also closes sidebar (mobile)
    onSelectConversation(id)
  }

  const handleClose = () => {
    // Close sidebar WITHOUT changing conversation
    onSelectConversation(activeConversationId)
  }

  return (
    <>
      {/* ================= Overlay (mobile only) ================= */}
      {isMobile && (
        <div
          onClick={handleClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.45)',
            zIndex: 39
          }}
        />
      )}

      {/* ================= Slide-in animation ================= */}
      <style>
        {`
          @keyframes sidebarSlideIn {
            from { transform: translateX(-100%); }
            to { transform: translateX(0); }
          }
        `}
      </style>

      {/* ================= Sidebar ================= */}
      <div
        style={{
          position: isMobile ? 'fixed' : 'relative',
          top: 0,
          left: 0,

          width: 300,
          maxWidth: '85vw',
          height: isMobile ? '100dvh' : 'calc(100vh - 24px)',
          margin: isMobile ? 0 : 12,

          background: 'var(--bg-input)',
          borderRight: '1px solid var(--border-strong)',
          borderRadius: isMobile ? '0 18px 18px 0' : 18,

          boxShadow: 'var(--shadow-medium)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',

          zIndex: 40,
          animation: isMobile
            ? 'sidebarSlideIn 0.35s cubic-bezier(0.4,0,0.2,1)'
            : 'none'
        }}
      >
        {/* ================= Header ================= */}
        <div
          style={{
            padding: 14,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-strong)'
          }}
        >
          <strong style={{ fontSize: 14 }}>Conversations</strong>

          {/* ✕ Close (mobile only) */}
          {isMobile && (
            <button
              onClick={handleClose}
              aria-label="Close sidebar"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: 22,
                cursor: 'pointer'
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* ================= New Chat ================= */}
        <div
          style={{
            padding: 14,
            borderBottom: '1px solid var(--border-strong)'
          }}
        >
          <button
            onClick={handleNewChat}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 14,
              background: 'var(--bg-surface)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-strong)',
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: 'var(--shadow-soft)'
            }}
          >
            ＋ New Chat
          </button>
        </div>

        {/* ================= List ================= */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 8
          }}
        >
          {conversations.length === 0 && (
            <div
              style={{
                padding: 24,
                fontSize: 13,
                textAlign: 'center',
                opacity: 0.6
              }}
            >
              No conversations yet
            </div>
          )}

          {conversations.map(c => {
            const isActive = c.id === activeConversationId

            return (
              <div
                key={c.id}
                onClick={() => handleSelect(c.id)}
                style={{
                  padding: '12px 14px',
                  marginBottom: 6,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,

                  cursor: 'pointer',
                  borderRadius: 12,
                  border: isActive
                    ? '1px solid rgba(99,102,241,0.6)'
                    : '1px solid var(--border-subtle)',
                  background: isActive
                    ? 'rgba(99,102,241,0.15)'
                    : 'transparent'
                }}
              >
                <span
                  style={{
                    fontSize: 14,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    flex: 1,
                    fontWeight: isActive ? 600 : 400
                  }}
                >
                  {c.title}
                </span>

                <span
                  onClick={(e) => handleDelete(e, c.id)}
                  style={{
                    cursor: 'pointer',
                    opacity: 0.7
                  }}
                >
                  🗑
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </>
  )
}

export default Sidebar