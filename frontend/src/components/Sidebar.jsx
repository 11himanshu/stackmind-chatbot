import React, { useEffect, useState } from 'react'
import { fetchConversations, deleteConversation } from '../services/api'

const Sidebar = ({ activeConversationId, onSelectConversation }) => {
  const [conversations, setConversations] = useState([])
  const [isMobile, setIsMobile] = useState(false)

  // =========================================================
  // Detect mobile (iOS-safe)
  // =========================================================
  useEffect(() => {
    const media = window.matchMedia('(max-width: 768px)')
    const update = () => setIsMobile(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
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
    onSelectConversation(null)
  }

  const handleSelect = (id) => {
    onSelectConversation(id)
  }

  const handleClose = () => {
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
            zIndex: 49
          }}
        />
      )}

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
          zIndex: 50
        }}
      >
        {/* ================= STICKY HEADER (FIX) ================= */}
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 60,
            padding: 14,
            paddingTop: 'calc(14px + env(safe-area-inset-top))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-input)',
            borderBottom: '1px solid var(--border-strong)'
          }}
        >
          <strong style={{ fontSize: 14 }}>Conversations</strong>

          {/* ✕ Close (mobile only — ALWAYS visible now) */}
          {isMobile && (
            <button
              onClick={handleClose}
              aria-label="Close sidebar"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: 24,
                cursor: 'pointer',
                lineHeight: 1
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
                  style={{ cursor: 'pointer', opacity: 0.7 }}
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