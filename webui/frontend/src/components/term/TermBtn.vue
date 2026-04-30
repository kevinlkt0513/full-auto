<template>
  <button
    :class="['tb', `tb--${variant}`, { 'tb--loading': loading }]"
    :disabled="loading || disabled"
    @click="onClick"
    type="button"
  >
    <span v-if="loading" class="tb-spinner">▮</span>
    <span class="tb-content"><slot /></span>
  </button>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  variant?: "primary" | "ghost" | "danger";
  loading?: boolean;
  disabled?: boolean;
}>(), { variant: "primary" });
const emit = defineEmits<{ click: [e: MouseEvent] }>();
function onClick(e: MouseEvent) { emit("click", e); }
</script>

<style scoped>
.tb {
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 8px 18px;
  font: inherit;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 12px;
  cursor: pointer;
  transition: all 60ms linear;
  border-radius: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  position: relative;
  overflow: hidden;
}
.tb::before { content: '['; opacity: 0.6; }
.tb::after { content: ']'; opacity: 0.6; }
.tb:hover:not(:disabled) { background: var(--accent); color: var(--bg-base); }
.tb:active:not(:disabled) { transform: translateY(1px); }
.tb:disabled { color: var(--fg-tertiary); border-color: var(--border); cursor: not-allowed; }

.tb--ghost { border-color: var(--border-strong); color: var(--fg-secondary); }
.tb--ghost:hover:not(:disabled) { background: var(--bg-raised); color: var(--fg-primary); }

.tb--danger { border-color: var(--err); color: var(--err); }
.tb--danger:hover:not(:disabled) { background: var(--err); color: var(--bg-base); }

.tb-spinner {
  display: inline-block;
  animation: tb-spin 0.8s steps(8) infinite;
  color: var(--accent);
}
@keyframes tb-spin {
  0% { transform: scaleY(0.2); opacity: 0.3; }
  50% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(0.2); opacity: 0.3; }
}
.tb--loading { color: var(--fg-tertiary); border-color: var(--border-strong); cursor: wait; }
.tb--loading::before, .tb--loading::after { opacity: 0.3; }
</style>
