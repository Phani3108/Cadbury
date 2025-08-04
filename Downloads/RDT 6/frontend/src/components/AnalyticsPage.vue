<template>
  <div class="analytics-page">
    <div class="container">
      <div class="page-header">
        <h1>Analytics Dashboard</h1>
        <p>Monitor system performance and user interactions</p>
      </div>

      <div class="analytics-grid">
        <div class="metric-card">
          <h3>Total Queries</h3>
          <div class="metric-value">1,247</div>
          <div class="metric-change positive">+12% from last week</div>
        </div>

        <div class="metric-card">
          <h3>Response Time</h3>
          <div class="metric-value">2.3s</div>
          <div class="metric-change negative">+0.5s from last week</div>
        </div>

        <div class="metric-card">
          <h3>Success Rate</h3>
          <div class="metric-value">94.2%</div>
          <div class="metric-change positive">+2.1% from last week</div>
        </div>

        <div class="metric-card">
          <h3>Active Users</h3>
          <div class="metric-value">156</div>
          <div class="metric-change positive">+8% from last week</div>
        </div>
      </div>

      <div class="charts-section">
        <div class="chart-card">
          <h3>Query Volume Over Time</h3>
          <div class="chart-placeholder">
            <div class="chart-bars">
              <div class="bar" style="height: 60%"></div>
              <div class="bar" style="height: 80%"></div>
              <div class="bar" style="height: 45%"></div>
              <div class="bar" style="height: 90%"></div>
              <div class="bar" style="height: 70%"></div>
              <div class="bar" style="height: 85%"></div>
              <div class="bar" style="height: 75%"></div>
            </div>
            <p>Last 7 days</p>
          </div>
        </div>

        <div class="chart-card">
          <h3>Popular Topics</h3>
          <div class="topics-list">
            <div class="topic-item">
              <span class="topic-name">Optum Project</span>
              <span class="topic-count">234 queries</span>
            </div>
            <div class="topic-item">
              <span class="topic-name">Mississippi Project</span>
              <span class="topic-count">189 queries</span>
            </div>
            <div class="topic-item">
              <span class="topic-name">Team Structure</span>
              <span class="topic-count">156 queries</span>
            </div>
            <div class="topic-item">
              <span class="topic-name">Sigma Project</span>
              <span class="topic-count">123 queries</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalyticsPage'
}
</script>

<style scoped>
.analytics-page {
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

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.metric-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}

.metric-card h3 {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  color: #0078d4;
  margin-bottom: 8px;
}

.metric-change {
  font-size: 14px;
  font-weight: 500;
}

.metric-change.positive {
  color: #4caf50;
}

.metric-change.negative {
  color: #f44336;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.chart-card h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.chart-placeholder {
  text-align: center;
  padding: 40px 0;
}

.chart-bars {
  display: flex;
  align-items: end;
  justify-content: center;
  gap: 8px;
  height: 200px;
  margin-bottom: 16px;
}

.bar {
  width: 30px;
  background: #0078d4;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}

.chart-placeholder p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.topics-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.topic-item:last-child {
  border-bottom: none;
}

.topic-name {
  font-weight: 500;
  color: #333;
}

.topic-count {
  color: #666;
  font-size: 14px;
}

@media (max-width: 768px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
}
</style> 