<template>
  <div class="chat-container">
    <!-- Header -->
    <div class="header">
      <h2>Digital Twin Assistant</h2>
      <div class="status" :class="{ connected: isConnected }">
        {{ isConnected ? 'Connected' : 'Disconnected' }}
      </div>
    </div>

    <!-- Chat Messages -->
    <div class="messages" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id"
        class="message"
        :class="{ user: message.isUser, assistant: !message.isUser }"
      >
        <div class="message-content">
          <div v-if="message.isUser" class="user-avatar">👤</div>
          <div v-else class="assistant-avatar">🤖</div>
          <div class="text" v-html="formatMessage(message.text)"></div>
        </div>
        <div v-if="message.timestamp" class="timestamp">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
      
      <!-- Loading indicator -->
      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          <div class="assistant-avatar">🤖</div>
          <div class="loading">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <div class="input-container">
        <textarea
          v-model="currentMessage"
          @keydown.enter.prevent="sendMessage"
          placeholder="Ask about meetings, projects, or schedule a call..."
          :disabled="isLoading"
          ref="messageInput"
        ></textarea>
        <button 
          @click="sendMessage" 
          :disabled="!currentMessage.trim() || isLoading"
          class="send-button"
        >
          Send
        </button>
      </div>
      
      <!-- Quick Actions -->
      <div class="quick-actions">
        <button 
          v-for="action in quickActions" 
          :key="action.query"
          @click="sendQuickAction(action.query)"
          class="quick-action"
          :disabled="isLoading"
        >
          {{ action.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { TeamsFx } from '@microsoft/teamsfx'

export default {
  name: 'TeamsTabChat',
  data() {
    return {
      messages: [],
      currentMessage: '',
      isLoading: false,
      isConnected: false,
      eventSource: null,
      quickActions: [
        { label: '📅 Book Meeting', query: 'Schedule a call with Ramki' },
        { label: '📊 Optum Status', query: 'What is the current status of Optum project?' },
        { label: '🎯 Create Jira', query: 'Create a Jira ticket for' },
        { label: '📈 Recent Insights', query: 'What were the key insights from recent meetings?' }
      ]
    }
  },
  async mounted() {
    await this.initializeTeams()
    this.connectSSE()
    this.addWelcomeMessage()
  },
  beforeUnmount() {
    if (this.eventSource) {
      this.eventSource.close()
    }
  },
  methods: {
    async initializeTeams() {
      try {
        const teamsfx = new TeamsFx()
        await teamsfx.getUserInfo()
        this.isConnected = true
      } catch (error) {
        console.error('Teams initialization failed:', error)
        this.isConnected = false
      }
    },

    connectSSE() {
      const baseUrl = process.env.VUE_APP_API_URL || 'http://localhost:8000'
      this.eventSource = new EventSource(`${baseUrl}/stream`)
      
      this.eventSource.onopen = () => {
        console.log('SSE connection opened')
      }
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'message') {
            this.addMessage(data.content, false)
          }
        } catch (error) {
          console.error('Error parsing SSE message:', error)
        }
      }
      
      this.eventSource.onerror = (error) => {
        console.error('SSE connection error:', error)
        this.isConnected = false
      }
    },

    addWelcomeMessage() {
      this.addMessage(
        "Hi! I'm your Digital Twin assistant. I can help you with meeting insights, project status, scheduling calls, and creating Jira tickets. What would you like to know?",
        false
      )
    },

    async sendMessage() {
      if (!this.currentMessage.trim() || this.isLoading) return

      const message = this.currentMessage.trim()
      this.addMessage(message, true)
      this.currentMessage = ''
      this.isLoading = true

      try {
        const response = await this.callAPI(message)
        this.addMessage(response.response, false)
      } catch (error) {
        console.error('API call failed:', error)
        this.addMessage('Sorry, I encountered an error. Please try again.', false)
      } finally {
        this.isLoading = false
        this.scrollToBottom()
      }
    },

    sendQuickAction(query) {
      this.currentMessage = query
      this.sendMessage()
    },

    async callAPI(message) {
      const baseUrl = process.env.VUE_APP_API_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: message,
          user_id: 'teams_user',
          session_id: 'teams_session'
        })
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }

      return await response.json()
    },

    addMessage(text, isUser) {
      this.messages.push({
        id: Date.now(),
        text,
        isUser,
        timestamp: new Date()
      })
      this.scrollToBottom()
    },

    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.messagesContainer) {
          this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
        }
      })
    },

    formatMessage(text) {
      // Convert markdown to HTML
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    }
  }
}
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #0078d4;
  color: white;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.2);
}

.status.connected {
  background: #107c10;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.user-avatar, .assistant-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.user-avatar {
  background: #0078d4;
  color: white;
}

.assistant-avatar {
  background: #f0f0f0;
  color: #333;
}

.text {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  line-height: 1.4;
}

.message.user .text {
  background: #0078d4;
  color: white;
}

.timestamp {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  text-align: right;
}

.loading {
  display: flex;
  gap: 4px;
  padding: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0078d4;
  animation: pulse 1.5s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.input-area {
  padding: 16px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-container {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.4;
  min-height: 44px;
  max-height: 120px;
}

textarea:focus {
  outline: none;
  border-color: #0078d4;
}

.send-button {
  padding: 12px 24px;
  background: #0078d4;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.send-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-action {
  padding: 8px 12px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.quick-action:hover:not(:disabled) {
  background: #e0e0e0;
}

.quick-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style> 