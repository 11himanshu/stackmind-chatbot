/*
  API Service Layer
  -----------------
  Responsibilities:
  - Centralize all HTTP calls
  - Automatically attach JWT auth headers
  - Support JSON + streaming endpoints
  - NEVER pass user_id from frontend (security)
*/

const API_BASE_URL = 'http://localhost:8000'

/* =========================================================
   Helper: Auth headers
   ---------------------------------------------------------
   IMPORTANT:
   - Reads JWT from localStorage
   - Attaches Authorization header ONLY if token exists
   - Used by BOTH normal and streaming requests
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
   ---------------------------------------------------------
   Used for:
   - login
   - register
   - conversations
   Automatically:
   - sends JWT
   - parses JSON
   - throws meaningful errors
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

/*
  chatStream
  ----------
  SINGLE SOURCE OF TRUTH for chatting.

  Backend:
  - Streams assistant response
  - Emits ONE metadata frame:
      __META__{"conversation_id": X}
  - Persists messages after stream completes

  Frontend:
  - Strips metadata from UI
  - Captures conversation_id ONCE
  - Streams ONLY assistant text to renderer
*/
export const chatStream = async (
  message,
  conversationId = null,
  onChunk,
  onMeta // 👈 NEW (OPTIONAL) METADATA CALLBACK
) => {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: authHeaders(), // ✅ JWT INCLUDED
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

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    if (!chunk) continue

    // =====================================================
    // 🔥 METADATA FRAME (STRIP FROM UI)
    // Format: __META__{"conversation_id": 42}
    // =====================================================
    if (chunk.startsWith('__META__')) {
      try {
        const meta = JSON.parse(chunk.replace('__META__', ''))
        onMeta?.(meta)
      } catch (e) {
        console.error('Invalid META chunk', e)
      }
      continue
    }

    // =====================================================
    // 🔥 PURE ASSISTANT TEXT (SAFE FOR MARKDOWN)
    // =====================================================
    onChunk(chunk)
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