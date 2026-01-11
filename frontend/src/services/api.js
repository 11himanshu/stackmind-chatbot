const API_BASE_URL = 'http://localhost:8000'

const fetchJSON = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

/* ================= AUTH ================= */

export const register = async (username, password) => {
  return fetchJSON(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export const login = async (username, password) => {
  return fetchJSON(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

/* ================= CHAT (NON-STREAM) ================= */

export const sendMessage = async (message, conversationId = null) => {
  return fetchJSON(`${API_BASE_URL}/chat`, {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    }),
  })
}

/* ================= CHAT (STREAMING) ================= */

export const streamMessage = async (
  message,
  conversationId = null,
  onChunk
) => {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId
    }),
  })

  if (!response.ok || !response.body) {
    throw new Error('Streaming request failed')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    if (chunk) {
      onChunk(chunk)
    }
  }
}

/* ================= CONVERSATIONS ================= */

export const fetchConversations = async (userId) => {
  return fetchJSON(`${API_BASE_URL}/conversations?user_id=${userId}`)
}

export const fetchConversationHistory = async (conversationId, userId) => {
  return fetchJSON(
    `${API_BASE_URL}/conversations/${conversationId}?user_id=${userId}`
  )
}


export const deleteConversation = async (conversationId, userId) => {
  return fetchJSON(
    `${API_BASE_URL}/conversations/${conversationId}?user_id=${userId}`,
    { method: 'DELETE' }
  )
}
