<template>
  <div class="sources-page">
    <div class="container">
      <div class="page-header">
        <h1>Knowledge Sources</h1>
        <p>Ramki's office hours calls and related documentation</p>
      </div>

      <div class="sources-grid">
        <div class="source-card">
          <div class="source-header">
            <h3>Office Hours Calls</h3>
            <span class="source-count">2653 chunks</span>
          </div>
          <div class="source-details">
            <p>Transcribed conversations from Ramki's regular office hours sessions covering project updates, team discussions, and strategic insights.</p>
            <div class="source-meta">
              <span class="meta-item">📅 Date Range: 2024-2025</span>
              <span class="meta-item">🎯 Topics: Projects, Teams, Strategy</span>
              <span class="meta-item">📊 Format: Transcribed Audio</span>
            </div>
          </div>
        </div>

        <div class="source-card">
          <div class="source-header">
            <h3>Project Check-ins</h3>
            <span class="source-count">1,247 chunks</span>
          </div>
          <div class="source-details">
            <p>Regular project status updates and milestone reviews including Optum, Mississippi, Sigma, and other key initiatives.</p>
            <div class="source-meta">
              <span class="meta-item">📅 Frequency: Weekly/Monthly</span>
              <span class="meta-item">🎯 Projects: Optum, Mississippi, Sigma</span>
              <span class="meta-item">📊 Format: Meeting Transcripts</span>
            </div>
          </div>
        </div>

        <div class="source-card">
          <div class="source-header">
            <h3>Team Discussions</h3>
            <span class="source-count">892 chunks</span>
          </div>
          <div class="source-details">
            <p>Team structure discussions, organizational insights, and leadership conversations about team dynamics and growth.</p>
            <div class="source-meta">
              <span class="meta-item">📅 Frequency: As needed</span>
              <span class="meta-item">🎯 Focus: Organization, Leadership</span>
              <span class="meta-item">📊 Format: Discussion Transcripts</span>
            </div>
          </div>
        </div>

        <div class="source-card">
          <div class="source-header">
            <h3>Strategic Insights</h3>
            <span class="source-count">456 chunks</span>
          </div>
          <div class="source-details">
            <p>High-level strategic discussions, technology decisions, and business insights shared during various meetings and sessions.</p>
            <div class="source-meta">
              <span class="meta-item">📅 Frequency: Quarterly</span>
              <span class="meta-item">🎯 Focus: Strategy, Technology</span>
              <span class="meta-item">📊 Format: Strategic Discussions</span>
            </div>
          </div>
        </div>
      </div>

      <div class="data-quality-section">
        <h2>Data Quality & Processing</h2>
        <div class="quality-grid">
          <div class="quality-item">
            <h4>📝 Transcription</h4>
            <p>High-quality audio transcription with speaker identification and timestamp markers</p>
          </div>
          <div class="quality-item">
            <h4>🔍 Chunking</h4>
            <p>Semantic sentence boundary detection for optimal context preservation</p>
          </div>
          <div class="quality-item">
            <h4>🏷️ Metadata</h4>
            <p>Rich metadata including dates, participants, topics, and source identification</p>
          </div>
          <div class="quality-item">
            <h4>🔒 Privacy</h4>
            <p>Enterprise-grade security with data anonymization and access controls</p>
          </div>
        </div>
      </div>

      <div class="update-info">
        <h3>Last Updated</h3>
        <p>Knowledge base last refreshed: <strong>August 4, 2025</strong></p>
        <p>Next scheduled update: <strong>August 11, 2025</strong></p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SourcesPage'
}
</script>

<style scoped>
.sources-page {
  padding: 40px 0;
  background: #f8f9fa;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 32px;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.source-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s;
}

.source-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.source-header h3 {
  margin: 0;
  color: #0078d4;
  font-size: 18px;
  font-weight: 600;
}

.source-count {
  background: #e3f2fd;
  color: #0078d4;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.source-details p {
  margin: 0 0 16px 0;
  color: #666;
  line-height: 1.5;
}

.source-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  font-size: 14px;
  color: #888;
}

.data-quality-section {
  margin-bottom: 40px;
}

.data-quality-section h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 24px;
}

.quality-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.quality-item {
  background: white;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.quality-item h4 {
  margin: 0 0 12px 0;
  color: #0078d4;
  font-size: 16px;
  font-weight: 600;
}

.quality-item p {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.update-info {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.update-info h3 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 18px;
}

.update-info p {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
}

.update-info p:last-child {
  margin-bottom: 0;
}

.update-info strong {
  color: #0078d4;
}

@media (max-width: 768px) {
  .sources-grid {
    grid-template-columns: 1fr;
  }
  
  .quality-grid {
    grid-template-columns: 1fr;
  }
  
  .source-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style> 