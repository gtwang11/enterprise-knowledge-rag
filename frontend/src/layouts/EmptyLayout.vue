<template>
  <div class="empty-layout">
    <slot />
  </div>
</template>

<style scoped>
.empty-layout { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f0f2f5; }
</style>
