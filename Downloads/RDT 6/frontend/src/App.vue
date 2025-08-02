<template>
  <div id="app">
    <ChatStream />
  </div>
</template>

<script>
import ChatStream from './components/ChatStream.vue'

export default {
  name: 'App',
  components: {
    ChatStream
  }
}
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  margin: 0;
  padding: 0;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background: #f5f5f5;
}
</style> 