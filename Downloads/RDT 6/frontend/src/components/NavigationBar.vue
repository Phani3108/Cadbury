<template>
  <nav class="navbar">
    <div class="nav-container">
      <div class="nav-left">
        <router-link to="/" class="nav-brand">
          <h2>Ramki Digital Twin</h2>
        </router-link>
      </div>
      
      <div class="nav-right">
        <router-link to="/analytics" class="nav-link">
          Analytics
        </router-link>
        <router-link to="/sources" class="nav-link">
          Sources
        </router-link>
        <div class="user-profile">
          <div class="profile-avatar">
            <span>👤</span>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'NavigationBar'
}
</script>

<style scoped>
.navbar {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
}

.nav-left {
  display: flex;
  align-items: center;
}

.nav-brand {
  text-decoration: none;
  color: #0078d4;
}

.nav-brand h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-link {
  text-decoration: none;
  color: #333;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: #f0f0f0;
  color: #0078d4;
}

.user-profile {
  display: flex;
  align-items: center;
}

.profile-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}

.profile-avatar:hover {
  background: #e0e0e0;
}

.profile-avatar span {
  font-size: 20px;
}
</style> 