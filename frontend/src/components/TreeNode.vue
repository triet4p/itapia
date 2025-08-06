<!-- src/components/TreeNode.vue -->
<script setup lang="ts">
import type { components } from '@/types/api';

type NodeEntity = components['schemas']['NodeEntity'];

// Component này nhận vào một node và độ sâu của nó trong cây
defineProps<{
  node: NodeEntity;
  depth: number;
}>();

// Nó có thể phát ra sự kiện khi một node được click
const emit = defineEmits<{
  (e: 'node-click', nodeName: string): void;
}>();

function onNodeClick(nodeName: string) {
  emit('node-click', nodeName);
}
</script>

<template>
  <div class="tree-node">
    <!-- Hiển thị node hiện tại -->
    <div 
      class="node-content" 
      :style="{ paddingLeft: `${depth * 20}px` }" 
      @click.stop="onNodeClick(node.node_name)"
    >
      <v-icon size="small" class="mr-1">mdi-circle-small</v-icon>
      <v-chip size="small" label class="node-chip">
        {{ node.node_name }}
      </v-chip>
    </div>

    <!-- Nếu có node con, render chúng bằng cách gọi lại chính component này -->
    <div v-if="node.children && node.children.length > 0" class="node-children">
      <TreeNode 
        v-for="(child, index) in node.children" 
        :key="index"
        :node="child"
        :depth="depth + 1"
        @node-click="onNodeClick"
      />
    </div>
  </div>
</template>

<style scoped>
.node-content {
  display: flex;
  align-items: center;
  padding: 4px 0;
  cursor: pointer;
}
.node-chip {
  cursor: pointer;
  transition: background-color 0.2s;
}
.node-chip:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>