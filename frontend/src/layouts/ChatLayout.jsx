import React, { useState } from 'react'
import Sidebar from '../components/Sidebar'
import ChatBot from '../components/ChatBot'

/**
 * ChatLayout
 * ----------
 * Owns the full screen layout.
 * Sidebar is conditionally rendered via toggle button.
 */
const ChatLayout = () => {
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100%',
        background: '#eef1f5',
        position: 'relative'
      }}
    >
      {/* Sidebar */}
      {sidebarOpen && (
        <Sidebar
          activeConversationId={activeConversationId}
          onSelectConversation={(id) => {
            setActiveConversationId(id)
            setSidebarOpen(false) // close sidebar after selection
          }}
        />
      )}

      {/* Chat area */}
      <div style={{ flex: 1, minWidth: 0, position: 'relative' }}>
        {/* Sidebar toggle button */}
        <button
          onClick={() => setSidebarOpen(prev => !prev)}
          style={{
            position: 'absolute',
            top: 14,
            left: 14,
            zIndex: 10,
            background: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            padding: '8px 12px',
            fontSize: 18,
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
          }}
        >
          ☰
        </button>

        <ChatBot activeConversationId={activeConversationId} />
      </div>
    </div>
  )
}

export default ChatLayout
