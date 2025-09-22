<!-- src/components/TreeNode.vue -->
<!--
  Tree Node Component
  
  A recursive component that displays a hierarchical tree structure of nodes.
  Each node can have child nodes, which are rendered using recursive calls
  to the same component.
-->
<script setup lang="ts">
import type { components } from '@/types/api';

type NodeEntity = components['schemas']['NodeEntity'];

/**
 * Props for the TreeNode component
 * 
 * @prop node - The node entity to display
 * @prop depth - The depth level of this node in the tree (used for indentation)
 */
defineProps<{
  node: NodeEntity;
  depth: number;
}>();

/**
 * Emits events from the TreeNode component
 * 
 * @event node-click - Emitted when a node is clicked
 */
const emit = defineEmits<{
  (e: 'node-click', nodeName: string): void;
}>();

/**
 * Handles node click events
 * 
 * @param nodeName - The name of the clicked node
 */
function onNodeClick(nodeName: string) {
  emit('node-click', nodeName);
}
</script>

<template>
  <div class="tree-node">
    <!-- Display the current node -->
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

    <!-- If there are child nodes, render them by recursively calling this component -->
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