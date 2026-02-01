import React, { useState } from 'react'
import Sidebar from '../components/Sidebar'
import ChatBot from '../components/ChatBot'

/*
  ChatLayout
  ----------
  Responsibilities:
  - Owns page-level layout (header + sidebar)
  - Owns the SOURCE OF TRUTH for activeConversationId
  - Controls chat reset behavior (New Chat)
  - Receives newly-created conversation_id from ChatBot
  - NEVER lets ChatBot manage layout or global state
*/

const ChatLayout = () => {
  // =========================================================
  // Active conversation
  // null = brand new chat (no conversation yet)
  // =========================================================
  const [activeConversationId, setActiveConversationId] = useState(null)

  // =========================================================
  // Forces ChatBot remount ONLY when user explicitly:
  // - clicks "New Chat"
  // - selects a conversation from sidebar
  // =========================================================
  const [chatResetKey, setChatResetKey] = useState(0)

  // Sidebar open/close state
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // TEMP until auth context is added
  const user =
    JSON.parse(localStorage.getItem('user')) || { username: 'hima' }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        width: '100%',
        background: '#eef1f5',
        overflow: 'hidden'
      }}
    >
      {/* ====================================================
          Sidebar (overlay style)
         ==================================================== */}
      {sidebarOpen && (
        <Sidebar
          activeConversationId={activeConversationId}
          onSelectConversation={(id) => {
            // User explicitly selected a conversation OR New Chat
            setActiveConversationId(id)
            setChatResetKey(prev => prev + 1) // HARD reset ChatBot
            setSidebarOpen(false)
          }}
        />
      )}

      {/* ====================================================
          Chat Area (column layout)
         ==================================================== */}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        {/* ===================== Header ===================== */}
        <div
          style={{
            height: 64,
            padding: '0 20px',
            background: 'linear-gradient(90deg, #0f172a, #1e293b)',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0
          }}
        >
          {/* Left */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => setSidebarOpen(prev => !prev)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#ffffff',
                fontSize: 22,
                cursor: 'pointer'
              }}
            >
              ☰
            </button>

            <div>
              <div style={{ fontWeight: 600 }}>StackMind</div>
              <div style={{ fontSize: 12, opacity: 0.7 }}>
                Powered by Himanshu
              </div>
            </div>
          </div>

          {/* Right */}
          <div style={{ textAlign: 'right' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                justifyContent: 'flex-end'
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  background: '#22c55e',
                  color: '#0f172a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: 14
                }}
              >
                {user.username.charAt(0).toUpperCase()}
              </div>
              <span style={{ fontSize: 14 }}>{user.username}</span>
            </div>

            <button
              onClick={handleLogout}
              style={{
                marginTop: 4,
                background: 'transparent',
                border: 'none',
                color: '#e5e7eb',
                fontSize: 12,
                cursor: 'pointer'
              }}
            >
              Logout
            </button>
          </div>
        </div>

        {/* ================= Chat Content ================== */}
        {/* 
          CRITICAL WIRING:
          - ChatBot streams messages
          - Backend creates conversation_id on first message
          - ChatBot reports it here via onConversationCreated
          - We store it as activeConversationId
          - NO reset happens here
        */}
        <ChatBot
          key={chatResetKey}
          activeConversationId={activeConversationId}
          onConversationCreated={(newConversationId) => {
            // 🔥 THIS IS THE FIX
            // Promote newly-created conversation to layout state
            setActiveConversationId(newConversationId)
          }}
        />
      </div>
    </div>
  )
}

export default ChatLayout