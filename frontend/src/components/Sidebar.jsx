import React, { useEffect, useState } from 'react'
import { fetchConversations, deleteConversation } from '../services/api'

const Sidebar = ({ activeConversationId, onSelectConversation }) => {
  const [conversations, setConversations] = useState([])
  const [isMobile, setIsMobile] = useState(false)

  // =========================================================
  // Detect mobile once on mount
  // =========================================================
  useEffect(() => {
    setIsMobile(window.innerWidth <= 768)
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
  // Delete conversation
  // =========================================================
  const handleDelete = async (e, id) => {
    e.stopPropagation()
    await deleteConversation(id)
    loadConversations()
  }

  // =========================================================
  // New chat
  // =========================================================
  const handleNewChat = () => {
    onSelectConversation(null)
  }

  return (
    <>
      {/* ================= Slide-in Animation (INLINE) ================= */}
      <style>
        {`
          @keyframes sidebarSlideIn {
            from {
              transform: translateX(-100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>

      <div
        style={{
          width: 300,
          height: 'calc(100vh - 24px)',
          margin: 12,

          background: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 16,

          boxShadow: 'var(--shadow-medium)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 40,

          /* 🔥 MOBILE SLIDE-IN */
          animation: isMobile
            ? 'sidebarSlideIn 0.35s cubic-bezier(0.4, 0, 0.2, 1)'
            : 'none'
        }}
      >
        {/* ================= New Chat ================= */}
        <div
          style={{
            padding: 14,
            borderBottom: '1px solid var(--border-subtle)'
          }}
        >
          <button
            onClick={handleNewChat}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 14,
              border: '1px solid var(--border-subtle)',
              background:
                'linear-gradient(135deg, rgba(99,102,241,0.18), rgba(99,102,241,0.08))',
              color: 'var(--text-primary)',
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              boxShadow: 'var(--shadow-soft)'
            }}
          >
            <span style={{ fontSize: 18 }}>＋</span>
            New Chat
          </button>
        </div>

        {/* ================= Title ================= */}
        <div
          style={{
            padding: '14px 18px',
            fontSize: 14,
            fontWeight: 600,
            color: 'var(--text-secondary)',
            borderBottom: '1px solid var(--border-subtle)'
          }}
        >
          Your conversations
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
                padding: '24px 12px',
                fontSize: 13,
                color: 'var(--text-secondary)',
                textAlign: 'center'
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
                onClick={() => onSelectConversation(c.id)}
                style={{
                  padding: '12px 14px',
                  marginBottom: 6,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,

                  borderRadius: 12,
                  border: `1px solid ${
                    isActive
                      ? 'rgba(99,102,241,0.45)'
                      : 'var(--border-subtle)'
                  }`,
                  background: isActive
                    ? 'rgba(99,102,241,0.15)'
                    : 'transparent',

                  transition: 'all 0.15s ease'
                }}
              >
                <span
                  style={{
                    fontSize: 14,
                    color: 'var(--text-primary)',
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
                  title="Delete conversation"
                  style={{
                    opacity: 0.6,
                    cursor: 'pointer',
                    fontSize: 14
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = 1)}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = 0.6)}
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