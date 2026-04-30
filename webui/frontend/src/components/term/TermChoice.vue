<template>
  <div class="tc-grid" :style="{ gridTemplateColumns: `repeat(${cols}, 1fr)` }">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      class="tc-card"
      :class="{ active: modelValue === opt.value }"
      @click="$emit('update:modelValue', opt.value)"
    >
      <span class="tc-radio">{{ modelValue === opt.value ? '[●]' : '[ ]' }}</span>
      <span class="tc-body">
        <span class="tc-label">{{ opt.label }}</span>
        <span v-if="opt.desc" class="tc-desc">{{ opt.desc }}</span>
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  modelValue: string;
  options: { value: string; label: string; desc?: string }[];
  cols?: number;
}>(), { cols: 1 });
defineEmits<{ "update:modelValue": [v: string] }>();
</script>

<style scoped>
.tc-grid { display: grid; gap: 0; border: 1px solid var(--border); }
.tc-card {
  background: var(--bg-panel);
  border: 0;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 14px 16px;
  text-align: left;
  font: inherit;
  cursor: pointer;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  color: var(--fg-secondary);
  transition: all 80ms ease-out;
}
.tc-card:hover { background: var(--bg-raised); color: var(--fg-primary); }
.tc-card.active {
  background: var(--bg-raised);
  color: var(--fg-primary);
  box-shadow: inset 3px 0 0 var(--accent);
}
.tc-radio { color: var(--accent); font-size: 12px; padding-top: 1px; flex-shrink: 0; }
.tc-card:not(.active) .tc-radio { color: var(--fg-tertiary); }
.tc-body { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; word-break: break-word; }
.tc-label { font-weight: 700; font-size: 13px; letter-spacing: 0.04em; }
.tc-desc { color: var(--fg-tertiary); font-size: 11px; }
</style>
