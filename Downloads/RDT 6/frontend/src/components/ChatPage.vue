<template>
  <div class="chat-page">
    <div class="chat-container">
      <div class="chat-header">
        <router-link to="/" class="back-link">
          <span>←</span> Back to Home
        </router-link>
      </div>

      <div class="chat-content">
        <div v-if="currentAnswer" class="answer-section">
          <div class="answer-content" v-html="currentAnswer"></div>
          
          <div class="feedback-section">
            <div class="feedback-buttons">
              <button @click="submitFeedback(1)" class="feedback-btn like-btn">
                👍 Like
              </button>
              <button @click="submitFeedback(-1)" class="feedback-btn dislike-btn">
                👎 Dislike
              </button>
            </div>
          </div>

          <div class="quick-actions">
            <h4>Quick Actions</h4>
            <div class="actions-grid">
              <div class="action-card" @click="handleAction('jira')">
                <div class="action-icon">📋</div>
                <h5>Jira</h5>
                <p>Create ticket</p>
              </div>
              <div class="action-card" @click="handleAction('meeting')">
                <div class="action-icon">📅</div>
                <h5>Schedule a Meeting</h5>
                <p>Book time</p>
              </div>
              <div class="action-card" @click="handleAction('confluence')">
                <div class="action-icon">📚</div>
                <h5>Confluence</h5>
                <p>Document</p>
              </div>
              <div class="action-card" @click="handleAction('blogin')">
                <div class="action-icon">📝</div>
                <h5>Blogin</h5>
                <p>Create post</p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="loading-section">
          <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Processing your question...</p>
          </div>
        </div>
      </div>

      <div class="chat-input-section">
        <div class="input-container">
          <input 
            v-model="newQuery" 
            @keyup.enter="sendQuery"
            placeholder="Ask another question..."
            class="query-input"
            :disabled="isProcessing"
          />
          <button @click="sendQuery" :disabled="isProcessing || !newQuery.trim()" class="send-btn">
            Send
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ChatPage',
  data() {
    return {
      currentAnswer: '',
      newQuery: '',
      isProcessing: false,
      apiBaseUrl: 'http://localhost:8000'
    }
  },
  async mounted() {
    // Check if there's a query parameter from the home page
    const query = this.$route.query.q
    if (query) {
      this.newQuery = query
      await this.sendQuery()
    }
  },
  methods: {
    async sendQuery() {
      if (!this.newQuery.trim() || this.isProcessing) return
      
      this.isProcessing = true
      this.currentAnswer = ''
      
      const query = this.newQuery
      this.newQuery = ''
      
      try {
        const response = await axios.post(`${this.apiBaseUrl}/chat/dev`, {
          query: query,
          user_id: 'pilot_user',
          session_id: 'pilot_session',
          conversation_id: 'main_conversation'
        })
        
        this.currentAnswer = response.data.response
      } catch (error) {
        console.error('Error sending query:', error)
        this.currentAnswer = 'Sorry, I encountered an error. Please try again.'
      } finally {
        this.isProcessing = false
      }
    },
    
    async submitFeedback(score) {
      try {
        await axios.post(`${this.apiBaseUrl}/feedback`, {
          message_id: Date.now(),
          score: score,
          timestamp: new Date().toISOString()
        })
        console.log('Feedback submitted:', score)
      } catch (error) {
        console.error('Error submitting feedback:', error)
      }
    },
    
    handleAction(action) {
      // Handle different quick actions
      switch (action) {
        case 'jira':
          window.open('https://jira.company.com/create', '_blank')
          break
        case 'meeting':
          window.open('https://calendar.company.com/schedule', '_blank')
          break
        case 'confluence':
          window.open('https://confluence.company.com/create', '_blank')
          break
        case 'blogin':
          window.open('https://blogin.company.com/new', '_blank')
          break
      }
    }
  }
}
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
  background: #f8f9fa;
}

.chat-container {
  max-width: 1000px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.back-link {
  text-decoration: none;
  color: #0078d4;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-link:hover {
  color: #106ebe;
}

.chat-content {
  flex: 1;
  padding: 40px 20px;
}

.answer-section {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 24px;
}

.answer-content {
  font-size: 16px;
  line-height: 1.6;
  color: #333;
  margin-bottom: 32px;
}

.answer-content :deep(h1),
.answer-content :deep(h2),
.answer-content :deep(h3),
.answer-content :deep(h4) {
  color: #0078d4;
  margin-top: 24px;
  margin-bottom: 12px;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin: 16px 0;
  padding-left: 24px;
}

.answer-content :deep(li) {
  margin-bottom: 8px;
}

.answer-content :deep(strong) {
  font-weight: 600;
  color: #0078d4;
}

.feedback-section {
  border-top: 1px solid #e0e0e0;
  padding-top: 24px;
  margin-bottom: 32px;
}

.feedback-buttons {
  display: flex;
  gap: 16px;
}

.feedback-btn {
  padding: 12px 24px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.like-btn:hover {
  background: #e8f5e8;
  border-color: #4caf50;
  color: #4caf50;
}

.dislike-btn:hover {
  background: #ffebee;
  border-color: #f44336;
  color: #f44336;
}

.quick-actions {
  border-top: 1px solid #e0e0e0;
  padding-top: 24px;
}

.quick-actions h4 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.action-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-card:hover {
  background: white;
  border-color: #0078d4;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.action-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.action-card h5 {
  margin: 0 0 8px 0;
  color: #0078d4;
  font-size: 16px;
  font-weight: 600;
}

.action-card p {
  margin: 0;
  color: #666;
  font-size: 12px;
}

.loading-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.loading-spinner {
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0078d4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-spinner p {
  color: #666;
  margin: 0;
}

.chat-input-section {
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-container {
  display: flex;
  gap: 12px;
  max-width: 800px;
  margin: 0 auto;
}

.query-input {
  flex: 1;
  padding: 16px 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
}

.query-input:focus {
  border-color: #0078d4;
}

.query-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  padding: 16px 32px;
  background: #0078d4;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #106ebe;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .feedback-buttons {
    flex-direction: column;
  }
  
  .input-container {
    flex-direction: column;
  }
  
  .send-btn {
    width: 100%;
  }
}
</style> 