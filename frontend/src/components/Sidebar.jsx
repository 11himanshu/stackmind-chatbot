import React, { useEffect, useState, useCallback } from 'react'
import { fetchConversations, deleteConversation } from '../services/api'

const HEADER_HEIGHT = 64

const Sidebar = ({ activeConversationId, onSelectConversation }) => {
  const [conversations, setConversations] = useState([])
  const [isMobile, setIsMobile] = useState(false)

  // 🔴 track delete-in-progress
  const [deletingId, setDeletingId] = useState(null)

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
  // Load conversations (returns promise)
  // =========================================================
  const loadConversations = useCallback(() => {
    return fetchConversations()
      .then(setConversations)
      .catch(console.error)
  }, [])

  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  // =========================================================
  // Actions
  // =========================================================
  const handleDelete = async (e, id) => {
    e.stopPropagation()

    if (deletingId) return

    try {
      setDeletingId(id)

      // 1️⃣ wait for backend delete
      await deleteConversation(id)

      // 2️⃣ refresh list AFTER delete
      await loadConversations()

    } catch (err) {
      console.error('DELETE_FAILED', err)
    } finally {
      setDeletingId(null)
    }
  }

  const handleNewChat = () => {
    onSelectConversation(null)
  }

  const handleSelect = (id) => {
    if (id === activeConversationId || deletingId) return
    onSelectConversation(id)
  }

  const handleClose = () => {}

  return (
    <>
      {/* ================= Overlay (mobile only) ================= */}
      {isMobile && (
        <div
          onClick={handleClose}
          style={{
            position: 'fixed',
            top: HEADER_HEIGHT,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.45)',
            zIndex: 49
          }}
        />
      )}

      {/* ================= Sidebar ================= */}
      <div
        style={{
          position: isMobile ? 'fixed' : 'relative',
          top: isMobile ? HEADER_HEIGHT : 0,
          left: 0,
          width: 300,
          maxWidth: '85vw',
          height: isMobile
            ? `calc(100dvh - ${HEADER_HEIGHT}px)`
            : 'calc(100vh - 24px)',
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
        {/* ================= Header ================= */}
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 60,
            padding: 14,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-input)',
            borderBottom: '1px solid var(--border-strong)'
          }}
        >
          <strong style={{ fontSize: 14 }}>Conversations</strong>

          {isMobile && (
            <button
              onClick={handleClose}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: 24,
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
              background: 'linear-gradient(135deg, #ffffff, #f8fafc)',
              color: '#0f172a',
              border: '1px solid var(--border-strong)',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            ＋ New Chat
          </button>
        </div>

        {/* ================= Conversation List ================= */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 8
          }}
        >
          {conversations.map(c => {
            const isActive = c.id === activeConversationId
            const isDeleting = deletingId === c.id

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
                  borderRadius: 12,
                  cursor: isDeleting ? 'default' : 'pointer',
                  border: isActive
                    ? '1px solid rgba(99,102,241,0.6)'
                    : '1px solid var(--border-subtle)',
                  background: isActive
                    ? 'rgba(99,102,241,0.15)'
                    : 'transparent',
                  opacity: isDeleting ? 0.6 : 1,
                  pointerEvents: isDeleting ? 'none' : 'auto'
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

                {/* 🗑 spinner stays mounted */}
                <span
                  onClick={(e) => handleDelete(e, c.id)}
                  style={{
                    opacity: isDeleting ? 0.9 : 0.7,
                    animation: isDeleting
                      ? 'spin 0.8s linear infinite'
                      : 'none'
                  }}
                >
                  🗑
                </span>
              </div>
            )
          })}
        </div>
      </div>

      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </>
  )
}

export default Sidebar