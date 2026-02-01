import React, { useState, useEffect } from 'react'
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
  - Handles global UI concerns (theme toggle)
*/

const ChatLayout = () => {
  // =========================================================
  // Active conversation
  // =========================================================
  const [activeConversationId, setActiveConversationId] = useState(null)

  // Force ChatBot remount when user explicitly switches chat
  const [chatResetKey, setChatResetKey] = useState(0)

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // =========================================================
  // Theme state
  // =========================================================
  const [theme, setTheme] = useState(
    localStorage.getItem('theme') || 'light'
  )

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('theme', theme)
  }, [theme])

  // =========================================================
  // Derived UI tokens (SAFE + EXPLICIT)
  // =========================================================
  const borderColor =
    theme === 'dark'
      ? 'rgba(255, 255, 255, 0.35)' // white borders in dark mode
      : 'rgba(0, 0, 0, 0.35)'       // black borders in light mode

  // TEMP user
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
        height: '100dvh',
        width: '100%',
        background: 'var(--bg-surface)',
        overflow: 'hidden'
      }}
    >
      {/* ================= Sidebar ================= */}
      {sidebarOpen && (
        <Sidebar
          activeConversationId={activeConversationId}
          onSelectConversation={(id) => {
            setActiveConversationId(id)
            setChatResetKey(prev => prev + 1)
            setSidebarOpen(false)
          }}
        />
      )}

      {/* ================= Main Column ================= */}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        {/* ================= Header ================= */}
        <header
          style={{
            height: 64,
            padding: '0 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,

            background: 'var(--bg-input)',
            color: 'var(--text-primary)',

            borderBottom: `1px solid ${borderColor}`,
            boxShadow: '0 2px 10px rgba(0,0,0,0.06)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)'
          }}
        >
          {/* ===== Left section ===== */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 14
            }}
          >
            <button
              onClick={() => setSidebarOpen(prev => !prev)}
              aria-label="Toggle sidebar"
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: 'var(--bg-input)',
                border: `1px solid ${borderColor}`,
                color: 'var(--text-primary)',
                fontSize: 18,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              ☰
            </button>

            <div style={{ lineHeight: 1.1 }}>
              <div style={{ fontWeight: 700, fontSize: 15 }}>
                StackMind
              </div>
              <div
                style={{
                  fontSize: 11,
                  opacity: 0.65
                }}
              >
                Powered by Himanshu
              </div>
            </div>
          </div>

          {/* ===== Right section ===== */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12
            }}
          >
            {/* Theme toggle */}
            <button
              onClick={() =>
                setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
              }
              style={{
                background: 'var(--bg-input)',
                border: `1px solid ${borderColor}`,
                borderRadius: 999,
                padding: '6px 12px',
                fontSize: 12,
                cursor: 'pointer',
                color: 'var(--text-primary)',
                whiteSpace: 'nowrap',
                boxShadow: '0 2px 6px rgba(0,0,0,0.08)'
              }}
            >
              {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </button>

            {/* User */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 8px',
                borderRadius: 999,
                background: 'var(--bg-input)',
                border: `1px solid ${borderColor}`
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
                  fontWeight: 700,
                  fontSize: 13
                }}
              >
                {user.username.charAt(0).toUpperCase()}
              </div>

              <span style={{ fontSize: 13 }}>
                {user.username}
              </span>
            </div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                fontSize: 12,
                cursor: 'pointer'
              }}
            >
              Logout
            </button>
          </div>
        </header>

        {/* ================= Chat Content ================= */}
        <ChatBot
          key={chatResetKey}
          activeConversationId={activeConversationId}
          onConversationCreated={(id) => {
            setActiveConversationId(id)
          }}
        />
      </div>
    </div>
  )
}

export default ChatLayout