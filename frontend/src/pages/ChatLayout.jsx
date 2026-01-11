import React, { useState } from 'react'
import ChatBot from '../components/ChatBot'
import Sidebar from '../components/Sidebar'

const ChatLayout = () => {
  const [conversationId, setConversationId] = useState(null)

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sidebar
        activeConversationId={conversationId}
        onSelectConversation={setConversationId}
      />

      <ChatBot
        conversationId={conversationId}
        setConversationId={setConversationId}
      />
    </div>
  )
}

export default ChatLayout