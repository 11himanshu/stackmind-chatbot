import React, { useEffect, useState } from 'react'
import { fetchConversations, deleteConversation } from '../services/api'

/*
  Sidebar Component
  -----------------
  Responsibilities:
  - Display list of user conversations
  - Allow selecting a conversation
  - Allow deleting a conversation
  - Allow starting a new chat

  IMPORTANT:
  - user_id is derived from JWT on backend
  - Sidebar must refresh when conversations change
*/

const Sidebar = ({ activeConversationId, onSelectConversation }) => {
  const [conversations, setConversations] = useState([])

  // =========================================================
  // Load conversations from backend
  // =========================================================
  const loadConversations = () => {
    fetchConversations()          // ✅ JWT-based (NO userId)
      .then(setConversations)
      .catch(console.error)
  }

  // =========================================================
  // Initial load
  // =========================================================
  useEffect(() => {
    loadConversations()
  }, [])

  // =========================================================
  // Reload when active conversation changes
  // (CRITICAL FIX: new chats now appear)
  // =========================================================
  useEffect(() => {
    loadConversations()
  }, [activeConversationId])

  // =========================================================
  // Delete conversation
  // =========================================================
  const handleDelete = async (e, id) => {
    e.stopPropagation()
    await deleteConversation(id)   // ✅ JWT-based
    loadConversations()
  }

  // =========================================================
  // Start new chat
  // =========================================================
  const handleNewChat = () => {
    // New chat means: no active conversation
    // Backend creates conversation on first message
    onSelectConversation(null)
  }

  return (
    <div
      style={{
        width: 300,
        height: 'calc(100vh - 24px)',
        margin: 12,
        background: '#f3f4f6',
        borderRight: '1px solid #d1d5db',
        boxShadow: '8px 0 24px rgba(0,0,0,0.08)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 20
      }}
    >
      {/* ================= New Chat Button ================= */}
      <div
        style={{
          padding: 14,
          borderBottom: '1px solid #e5e7eb',
          background: '#f9fafb'
        }}
      >
        <button
          onClick={handleNewChat}
          style={{
            width: '100%',
            padding: '12px 14px',
            borderRadius: 10,
            border: '1px solid #c7d2fe',
            background: 'linear-gradient(135deg, #eef2ff, #e0e7ff)',
            color: '#1e293b',
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            boxShadow: '0 4px 10px rgba(0,0,0,0.08)'
          }}
        >
          <span style={{ fontSize: 16 }}>＋</span>
          New Chat
        </button>
      </div>

      {/* ================= Sidebar Title ================= */}
      <div
        style={{
          padding: '14px 18px',
          fontSize: 14,
          fontWeight: 600,
          color: '#0f172a',
          borderBottom: '1px solid #e5e7eb',
          flexShrink: 0
        }}
      >
        Your conversations
      </div>

      {/* ================= Conversation List ================= */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px'
        }}
      >
        {conversations.length === 0 && (
          <div
            style={{
              padding: '20px 12px',
              fontSize: 13,
              color: '#6b7280',
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
                borderRadius: 10,
                background: isActive
                  ? 'linear-gradient(135deg, #e0e7ff, #eef2ff)'
                  : 'transparent',
                border: isActive
                  ? '1px solid #c7d2fe'
                  : '1px solid transparent',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.background = '#f1f5f9'
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.background = 'transparent'
              }}
            >
              <span
                style={{
                  fontSize: 14,
                  color: '#111827',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: 200,
                  fontWeight: isActive ? 600 : 400
                }}
              >
                {c.title}
              </span>

              <span
                onClick={(e) => handleDelete(e, c.id)}
                title="Delete conversation"
                style={{
                  opacity: 0.35,
                  cursor: 'pointer',
                  marginLeft: 10,
                  fontSize: 14
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = 0.8)}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = 0.35)}
              >
                🗑
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Sidebar