<template>
  <div class="home-page">
    <div class="hero-section">
      <div class="search-container">
        <div class="search-box">
          <input 
            v-model="searchQuery" 
            @keyup.enter="handleSearch"
            placeholder="Ask Ramki Digital Twin"
            class="search-input"
          />
          <button @click="handleSearch" class="search-btn">
            <span>🔍</span>
          </button>
        </div>
        <p class="search-subtitle">
          Ask anything about our tech stack, insights and discussions.
        </p>
        <p class="knowledge-note">
          The knowledge sources are limited to 'Ramki's office hours' calls.
        </p>
      </div>
    </div>

    <div class="container">
      <section class="popular-topics">
        <h3>Popular Topics</h3>
        <div class="topics-grid">
          <div class="topic-card" @click="searchTopic('Optum project status')">
            <h4>Optum Project</h4>
            <p>Current status and deliverables</p>
          </div>
          <div class="topic-card" @click="searchTopic('Mississippi project progress')">
            <h4>Mississippi Project</h4>
            <p>Latest updates and milestones</p>
          </div>
          <div class="topic-card" @click="searchTopic('Sigma project insights')">
            <h4>Sigma Project</h4>
            <p>Key insights and discussions</p>
          </div>
          <div class="topic-card" @click="searchTopic('team structure and organization')">
            <h4>Team Structure</h4>
            <p>Organizational insights</p>
          </div>
        </div>
      </section>

      <section class="core-features">
        <h3>Core Features</h3>
        <div class="features-grid">
          <div class="feature-card">
            <h4>FastAPI Framework</h4>
            <p>RESTful API endpoints for chat, search, health monitoring, analytics, and agent communication</p>
            <div class="feature-details" v-if="expandedFeatures.includes('fastapi')">
              <ul>
                <li>Containerized via Docker Compose for local/development deployment</li>
                <li>Scalable architecture designed for production deployment</li>
              </ul>
            </div>
            <button @click="toggleFeature('fastapi')" class="expand-btn">
              {{ expandedFeatures.includes('fastapi') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>Natural Language Understanding (NLU) & Natural Language Processing (NLP)</h4>
            <p>Advanced NLU capabilities for understanding user queries and intent recognition</p>
            <div class="feature-details" v-if="expandedFeatures.includes('nlu')">
              <ul>
                <li>NLP processing for text analysis, entity extraction, and semantic understanding</li>
                <li>Context-aware conversation handling for maintaining dialogue state</li>
              </ul>
            </div>
            <button @click="toggleFeature('nlu')" class="expand-btn">
              {{ expandedFeatures.includes('nlu') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>Knowledge Base & Vector Database</h4>
            <p>Vector database for semantic search and similarity matching</p>
            <div class="feature-details" v-if="expandedFeatures.includes('kb')">
              <ul>
                <li>Knowledge base integration for storing and retrieving domain-specific information</li>
                <li>Document indexing and retrieval system for accessing relevant information</li>
              </ul>
            </div>
            <button @click="toggleFeature('kb')" class="expand-btn">
              {{ expandedFeatures.includes('kb') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>Agent System</h4>
            <p>Multi-agent communication framework for specialized task handling</p>
            <div class="feature-details" v-if="expandedFeatures.includes('agent')">
              <ul>
                <li>Agent orchestration for complex query resolution</li>
                <li>Feedback loop system for continuous improvement of agent responses</li>
              </ul>
            </div>
            <button @click="toggleFeature('agent')" class="expand-btn">
              {{ expandedFeatures.includes('agent') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>Memory and Context Management</h4>
            <p>Conversation History Storage: Maintains a complete record of all user interactions and system responses</p>
            <div class="feature-details" v-if="expandedFeatures.includes('memory')">
              <ul>
                <li>Context Tracking: Preserves context across multiple turns of conversation for coherent dialogue</li>
                <li>Memory Prioritization: Intelligently prioritizes relevant information from past conversations</li>
                <li>Long-term Memory Storage: Persists important information across sessions for returning users</li>
              </ul>
            </div>
            <button @click="toggleFeature('memory')" class="expand-btn">
              {{ expandedFeatures.includes('memory') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>Tool Calling Capabilities</h4>
            <p>External API Integration: Seamlessly connects with third-party services and data sources</p>
            <div class="feature-details" v-if="expandedFeatures.includes('tools')">
              <ul>
                <li>Dynamic Tool Selection: Intelligently chooses appropriate tools based on user needs</li>
                <li>Parameter Handling: Extracts and formats parameters from natural language for tool calls</li>
                <li>Result Processing: Interprets and presents tool outputs in human-readable format</li>
              </ul>
            </div>
            <button @click="toggleFeature('tools')" class="expand-btn">
              {{ expandedFeatures.includes('tools') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>Vector Search Integration</h4>
            <p>Semantic Matching: Finds conceptually similar information beyond keyword matching</p>
            <div class="feature-details" v-if="expandedFeatures.includes('vector')">
              <ul>
                <li>Embedding Generation: Creates vector representations of documents and queries</li>
                <li>Relevance Ranking: Prioritizes search results based on semantic similarity scores</li>
                <li>Multi-modal Search: Supports searching across text, code, and structured data</li>
              </ul>
            </div>
            <button @click="toggleFeature('vector')" class="expand-btn">
              {{ expandedFeatures.includes('vector') ? 'Show less' : 'Show more' }}
            </button>
          </div>

          <div class="feature-card">
            <h4>MCP (Model Context Protocol) Support</h4>
            <p>Agent Communication Framework: Standardized protocol for information exchange between AI agents</p>
            <div class="feature-details" v-if="expandedFeatures.includes('mcp')">
              <ul>
                <li>Context Preservation: Maintains coherent context when transferring control between agents</li>
                <li>Specialized Agent Routing: Directs queries to domain-specific expert agents as needed</li>
                <li>Collaborative Problem Solving: Enables multiple agents to work together on complex tasks</li>
              </ul>
            </div>
            <button @click="toggleFeature('mcp')" class="expand-btn">
              {{ expandedFeatures.includes('mcp') ? 'Show less' : 'Show more' }}
            </button>
          </div>
        </div>
      </section>
    </div>

    <footer class="footer">
      <div class="container">
        <div class="footer-content">
          <div class="footer-left">
            <div class="zeta-logo-text">ZETA</div>
          </div>
          <div class="footer-right">
            <p class="disclaimer">
              Powered by Enterprise Apps & Productivity Team. (c) 2025 Zeta. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'HomePage',
  data() {
    return {
      searchQuery: '',
      expandedFeatures: []
    }
  },
  methods: {
    handleSearch() {
      if (this.searchQuery.trim()) {
        this.$router.push({
          path: '/chat',
          query: { q: this.searchQuery }
        })
      }
    },
    searchTopic(topic) {
      this.$router.push({
        path: '/chat',
        query: { q: topic }
      })
    },
    toggleFeature(feature) {
      const index = this.expandedFeatures.indexOf(feature)
      if (index > -1) {
        this.expandedFeatures.splice(index, 1)
      } else {
        this.expandedFeatures.push(feature)
      }
    }
  }
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.hero-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.search-container {
  text-align: center;
  max-width: 600px;
  width: 100%;
}

.search-box {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 50px;
  padding: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  border: none;
  padding: 16px 24px;
  font-size: 18px;
  outline: none;
  background: transparent;
  color: #333;
}

.search-input::placeholder {
  color: #999;
}

.search-btn {
  background: #0078d4;
  color: white;
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  transition: background 0.2s;
}

.search-btn:hover {
  background: #106ebe;
}

.search-subtitle {
  font-size: 18px;
  margin: 0 0 10px 0;
  opacity: 0.9;
}

.knowledge-note {
  font-size: 14px;
  margin: 0;
  opacity: 0.7;
  font-style: italic;
}

.container {
  padding: 60px 20px;
}

.popular-topics {
  margin-bottom: 60px;
}

.popular-topics h3 {
  font-size: 28px;
  margin-bottom: 30px;
  color: #333;
  text-align: center;
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.topic-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.topic-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  border-color: #0078d4;
  transform: translateY(-2px);
}

.topic-card h4 {
  margin: 0 0 10px 0;
  color: #0078d4;
  font-size: 18px;
}

.topic-card p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.core-features h3 {
  font-size: 28px;
  margin-bottom: 30px;
  color: #333;
  text-align: center;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.feature-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s;
  border: 1px solid #e0e0e0;
}

.feature-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.feature-card h4 {
  margin: 0 0 12px 0;
  color: #0078d4;
  font-size: 16px;
  font-weight: 600;
}

.feature-card p {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.feature-details {
  margin-bottom: 16px;
}

.feature-details ul {
  margin: 0;
  padding-left: 20px;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.feature-details li {
  margin-bottom: 8px;
}

.expand-btn {
  background: none;
  border: none;
  color: #0078d4;
  cursor: pointer;
  font-size: 14px;
  text-decoration: underline;
  padding: 0;
}

.expand-btn:hover {
  color: #106ebe;
}

.footer {
  background: #333;
  color: white;
  padding: 40px 0;
  margin-top: auto;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left {
  display: flex;
  align-items: center;
}

.zeta-logo-text {
  font-size: 24px;
  font-weight: bold;
  color: white;
}

.footer-right {
  text-align: right;
}

.disclaimer {
  margin: 0;
  font-size: 14px;
  opacity: 0.8;
}

@media (max-width: 768px) {
  .search-input {
    font-size: 16px;
    padding: 14px 20px;
  }
  
  .topics-grid {
    grid-template-columns: 1fr;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
}
</style> 