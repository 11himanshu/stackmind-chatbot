import React, { useEffect, useState } from 'react'
import { fetchConversations, deleteConversation } from '../services/api'

const Sidebar = ({ activeConversationId, onSelectConversation }) => {
  const [conversations, setConversations] = useState([])
  const userId = 1

  const loadConversations = () => {
    fetchConversations(userId)
      .then(setConversations)
      .catch(console.error)
  }

  useEffect(() => {
    loadConversations()
  }, [])

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    await deleteConversation(id, userId)
    loadConversations()
  }

  return (
    <div
      style={{
        width: 280,
        height: '100vh',
        background: '#ffffff',
        borderRight: '1px solid #d1d5db',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Sidebar title */}
      <div
        style={{
          padding: '16px',
          fontSize: 14,
          fontWeight: 600,
          borderBottom: '1px solid #e5e7eb',
          flexShrink: 0
        }}
      >
        Your conversations
      </div>

      {/* Scrollable conversation list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto'
        }}
      >
        {conversations.map(c => (
          <div
            key={c.id}
            onClick={() => onSelectConversation(c.id)}
            style={{
              padding: '10px 14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #f1f5f9',
              background:
                c.id === activeConversationId ? '#eef2f7' : 'transparent'
            }}
          >
            <span
              style={{
                fontSize: 14,
                color: '#111827',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: 180
              }}
            >
              {c.title}
            </span>

            <span
              onClick={(e) => handleDelete(e, c.id)}
              style={{
                opacity: 0.35,
                cursor: 'pointer'
              }}
            >
              🗑
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Sidebar
