import React, { useState, useEffect, useRef } from 'react'
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
  - Handles global UI concerns (theme toggle, user menu)
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
  // User menu state
  // =========================================================
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const userMenuRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // =========================================================
  // Derived UI tokens
  // =========================================================
  const borderColor =
    theme === 'dark'
      ? 'rgba(255,255,255,0.35)'
      : 'rgba(0,0,0,0.35)'

  // TEMP user
  const user =
    JSON.parse(localStorage.getItem('user')) || { username: 'hima' }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')

    // ✅ FIX: avoid SPA hard refresh issues
    window.location.replace('/login')
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
            position: 'sticky', // ✅ FIX: header always visible
            top: 0,
            height: 64,
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,
            background: 'var(--bg-input)',
            borderBottom: `1px solid ${borderColor}`,
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            zIndex: 100
          }}
        >
          {/* ===== Left ===== */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => setSidebarOpen(prev => !prev)}
              aria-label="Toggle sidebar"
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                border: `1px solid ${borderColor}`,
                background: 'var(--bg-input)',
                cursor: 'pointer',
                fontSize: 18,
                color: 'var(--menu-icon-color)',
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
              <div style={{ fontSize: 11, opacity: 0.65 }}>
                Powered by Himanshu
              </div>
            </div>
          </div>

          {/* ===== Right ===== */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Theme toggle */}
            <button
              onClick={() =>
                setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
              }
              aria-label="Toggle theme"
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                border: `1px solid ${borderColor}`,
                background: 'var(--bg-input)',
                cursor: 'pointer',
                fontSize: 16
              }}
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>

            {/* User menu */}
            <div ref={userMenuRef} style={{ position: 'relative' }}>
              <button
                onClick={() => setUserMenuOpen(prev => !prev)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '4px 8px',
                  borderRadius: 999,
                  border: `1px solid ${borderColor}`,
                  background: 'var(--bg-input)',
                  cursor: 'pointer'
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
                <span style={{ fontSize: 13 }}>▾</span>
              </button>

              {userMenuOpen && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: 'calc(100% + 8px)',
                    minWidth: 160,
                    background: 'var(--bg-input)',
                    border: `1px solid ${borderColor}`,
                    borderRadius: 12,
                    boxShadow: '0 12px 30px rgba(0,0,0,0.18)',
                    padding: 8,
                    zIndex: 200
                  }}
                >
                  <div
                    style={{
                      padding: '8px 10px',
                      fontSize: 13,
                      opacity: 0.7
                    }}
                  >
                    {user.username}
                  </div>

                  <div
                    onClick={handleLogout}
                    style={{
                      padding: '8px 10px',
                      cursor: 'pointer',
                      fontSize: 13,
                      borderRadius: 8
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.background = 'rgba(0,0,0,0.06)')
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.background = 'transparent')
                    }
                  >
                    🚪 Logout
                  </div>
                </div>
              )}
            </div>
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