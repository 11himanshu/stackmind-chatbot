/*
  API Service Layer
  -----------------
  Responsibilities:
  - Centralize all HTTP calls
  - Automatically attach JWT auth headers
  - Support JSON + streaming endpoints
  - NEVER pass user_id from frontend (security)
*/

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

/* =========================================================
   Helper: Auth headers
   ========================================================= */
const authHeaders = () => {
  const token = localStorage.getItem('token')

  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }
}

/* =========================================================
   Helper: JSON fetch wrapper
   ========================================================= */
const fetchJSON = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: authHeaders(),
    ...options
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP error ${response.status}`)
  }

  return response.json()
}

/* ========================= AUTH ========================= */

export const register = async (username, password) => {
  return fetchJSON(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
}

export const login = async (username, password) => {
  return fetchJSON(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
}

/* ===================== CHAT (STREAM + SAVE) ===================== */

export const chatStream = async (
  message,
  conversationId = null,
  onChunk,
  onMeta
) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    })
  })

  if (!response.ok || !response.body) {
    throw new Error('Chat stream failed')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')

  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // =====================================================
    // PROCESS BUFFER
    // =====================================================
    while (buffer.length) {
      // ---- META FRAME ----
      if (buffer.startsWith('__META__')) {
        const metaEnd = buffer.indexOf('\n')
        if (metaEnd === -1) break // wait for full frame

        const metaRaw = buffer.slice(8, metaEnd)
        buffer = buffer.slice(metaEnd + 1)

        try {
          const meta = JSON.parse(metaRaw)
          onMeta?.(meta)
        } catch (e) {
          console.error('Invalid META chunk', e, metaRaw)
        }

        continue
      }

      // ---- TEXT FRAME ----
      const nextMeta = buffer.indexOf('__META__')

      if (nextMeta === -1) {
        const text = buffer
        buffer = ''

        if (text.trim()) {
          onChunk?.(text)
        }
      } else {
        const text = buffer.slice(0, nextMeta)
        buffer = buffer.slice(nextMeta)

        if (text.trim()) {
          onChunk?.(text)
        }
      }
    }
  }
}

/* ===================== CONVERSATIONS ===================== */

export const fetchConversations = async () => {
  return fetchJSON(`${API_BASE_URL}/conversations`)
}

export const fetchConversationHistory = async (conversationId) => {
  return fetchJSON(`${API_BASE_URL}/conversations/${conversationId}`)
}

export const deleteConversation = async (conversationId) => {
  return fetchJSON(
    `${API_BASE_URL}/conversations/${conversationId}`,
    { method: 'DELETE' }
  )
}