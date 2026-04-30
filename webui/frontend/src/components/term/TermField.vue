<template>
  <label class="tf" :class="{ 'tf--focus': focused, 'tf--error': error, 'tf--ok': ok }">
    <span class="tf-tag">{{ label }}</span>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @focus="focused = true"
      @blur="focused = false; $emit('blur')"
    />
    <span v-if="ok" class="tf-status tf-status--ok">✓</span>
    <span v-else-if="error" class="tf-status tf-status--err">✗</span>
  </label>
</template>

<script setup lang="ts">
import { ref } from "vue";
defineProps<{
  modelValue: string | number;
  label: string;
  type?: string;
  placeholder?: string;
  error?: boolean;
  ok?: boolean;
}>();
defineEmits<{ "update:modelValue": [v: string]; blur: [] }>();
const focused = ref(false);
</script>

<style scoped>
.tf {
  display: grid;
  grid-template-columns: minmax(140px, max-content) minmax(0, 1fr) auto;
  align-items: stretch;
  border: 1px solid var(--border);
  background: var(--bg-base);
  position: relative;
  transition: border-color 80ms ease-out;
}
.tf:hover { border-color: var(--border-strong); }
.tf--focus { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
.tf--error { border-color: var(--err); }
.tf--ok { border-color: var(--ok); }
.tf-tag {
  background: var(--bg-panel);
  color: var(--fg-tertiary);
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border-right: 1px solid var(--border);
  display: flex;
  align-items: center;
  white-space: nowrap;
}
.tf--focus .tf-tag { color: var(--accent); }
.tf input {
  background: transparent;
  border: 0;
  padding: 10px 12px;
  color: var(--fg-primary);
  font: inherit;
  font-size: 13px;
  outline: none;
  min-width: 0;
}
.tf input::placeholder { color: var(--fg-tertiary); opacity: 0.6; }
/* Hide native number spinner */
.tf input[type="number"]::-webkit-inner-spin-button,
.tf input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.tf input[type="number"] { -moz-appearance: textfield; }
.tf-status {
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-weight: 700;
  font-size: 14px;
}
.tf-status--ok { color: var(--ok); }
.tf-status--err { color: var(--err); }
</style>
