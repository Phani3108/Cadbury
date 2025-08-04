<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>Digital Twin</h2>
      <p>Ask me anything about our projects, meetings, and insights</p>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-for="message in messages" :key="message.id" class="message">
        <div class="message-content">
          <div class="message-text" v-html="message.content"></div>
          <div class="message-meta">
            <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
            <div class="feedback" v-if="message.type === 'assistant'">
              <button @click="submitFeedback(message.id, 1)" class="feedback-btn">👍</button>
              <button @click="submitFeedback(message.id, -1)" class="feedback-btn">👎</button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="isStreaming" class="streaming-indicator">
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <div class="input-container">
        <input 
          v-model="currentQuery" 
          @keyup.enter="sendMessage"
          placeholder="Ask about projects, meetings, or insights..."
          :disabled="isStreaming"
          class="query-input"
        />
        <button @click="sendMessage" :disabled="isStreaming || !currentQuery.trim()" class="send-btn">
          Send
        </button>
      </div>
      
      <div v-if="followUpSuggestions.length > 0" class="follow-up-suggestions">
        <p>Quick follow-ups:</p>
        <div class="suggestion-buttons">
          <button 
            v-for="suggestion in followUpSuggestions" 
            :key="suggestion"
            @click="sendFollowUp(suggestion)"
            class="suggestion-btn"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ChatStream',
  data() {
    return {
      messages: [],
      currentQuery: '',
      isStreaming: false,
      followUpSuggestions: [],
      apiBaseUrl: 'http://localhost:8000'
    }
  },
  methods: {
    async sendMessage() {
      if (!this.currentQuery.trim() || this.isStreaming) return
      
      const userMessage = {
        id: Date.now(),
        content: this.currentQuery,
        type: 'user',
        timestamp: new Date()
      }
      
      this.messages.push(userMessage)
      this.scrollToBottom()
      
      const query = this.currentQuery
      this.currentQuery = ''
      this.isStreaming = true
      this.followUpSuggestions = []
      
      try {
        await this.streamResponse(query)
      } catch (error) {
        console.error('Error streaming response:', error)
        this.messages.push({
          id: Date.now() + 1,
          content: 'Sorry, I encountered an error. Please try again.',
          type: 'assistant',
          timestamp: new Date()
        })
      } finally {
        this.isStreaming = false
        this.scrollToBottom()
      }
    },
    
    async streamResponse(query) {
      const response = await fetch(`${this.apiBaseUrl}/stream/dev`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query,
          user_id: 'pilot_user',
          session_id: 'pilot_session'
        })
      })
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = {
        id: Date.now() + 1,
        content: '',
        type: 'assistant',
        timestamp: new Date()
      }
      
      this.messages.push(assistantMessage)
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'token') {
                assistantMessage.content += data.content
                this.scrollToBottom()
              } else if (data.type === 'complete') {
                // Extract follow-up suggestions from the response
                this.extractFollowUps(assistantMessage.content)
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    },
    
    extractFollowUps(content) {
      // Simple extraction of follow-up suggestions
      const followUpPattern = /\*\*Next\?\*\*\s*\n((?:[0-9]+\.\s*[^\n]+\n?)+)/g
      const match = followUpPattern.exec(content)
      
      if (match) {
        const suggestions = match[1]
          .split('\n')
          .filter(line => line.trim())
          .map(line => line.replace(/^\d+\.\s*/, ''))
          .slice(0, 3) // Limit to 3 suggestions
        
        this.followUpSuggestions = suggestions
      }
    },
    
    sendFollowUp(suggestion) {
      this.currentQuery = suggestion
      this.sendMessage()
    },
    
    async submitFeedback(messageId, score) {
      try {
        await axios.post(`${this.apiBaseUrl}/feedback`, {
          message_id: messageId,
          score: score,
          timestamp: new Date().toISOString()
        })
        console.log('Feedback submitted:', score)
      } catch (error) {
        console.error('Error submitting feedback:', error)
      }
    },
    
    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }
  }
}
</script>

<style scoped>
.chat-container {
  max-width: 800px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.chat-header {
  background: #0078d4;
  color: white;
  padding: 20px;
  text-align: center;
}

.chat-header h2 {
  margin: 0 0 10px 0;
}

.chat-header p {
  margin: 0;
  opacity: 0.9;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message {
  display: flex;
  margin-bottom: 15px;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message.user .message-content {
  background: #0078d4;
  color: white;
  margin-left: auto;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.7;
}

.feedback {
  display: flex;
  gap: 5px;
}

.feedback-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 2px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.feedback-btn:hover {
  background-color: rgba(0,0,0,0.1);
}

.streaming-indicator {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0078d4;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input {
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-container {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.query-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.query-input:focus {
  outline: none;
  border-color: #0078d4;
}

.send-btn {
  padding: 12px 24px;
  background: #0078d4;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #106ebe;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.follow-up-suggestions {
  margin-top: 15px;
}

.follow-up-suggestions p {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
}

.suggestion-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-btn {
  padding: 8px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  background: #e0e0e0;
  border-color: #0078d4;
}
</style> 