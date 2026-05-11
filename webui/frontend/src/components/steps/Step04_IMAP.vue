<template>
  <section class="step-fade-in">
    <div class="term-divider" data-tail="──────────">步骤 04: IMAP</div>
    <h2 class="step-h">$&nbsp;IMAP 收件箱<span class="term-cursor"></span></h2>
    <p class="step-sub">这里只配置实际收验证码的收件箱。下一步再选择注册时填 catch-all 随机邮箱，还是从固定邮箱池顺序取地址。</p>

    <div class="form-stack">
      <TermField v-model="form.imap_server" label="IMAP 服务器 · imap_server" placeholder="imap.qq.com" />
      <TermField v-model="form.imap_port" label="端口 · imap_port" type="number" />
      <TermField v-model="form.email" label="邮箱 · email" />
      <TermField v-model="form.auth_code" label="授权码 · auth_code" type="password" />
    </div>

    <div class="step-actions">
      <TermBtn :loading="loading" @click="run">登录测试</TermBtn>
    </div>

    <div v-if="result" class="result-block" :class="`result--${result.status}`">
      <div class="result-head">
        <span class="result-icon">{{ icon(result.status) }}</span>
        <span>{{ result.message }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useWizardStore } from "../../stores/wizard";
import type { PreflightResult } from "../../api/client";
import TermField from "../term/TermField.vue";
import TermBtn from "../term/TermBtn.vue";

const store = useWizardStore();
const init = store.answers.imap ?? {};
const form = ref({
  imap_server: init.imap_server ?? "imap.qq.com",
  imap_port: init.imap_port ?? 993,
  email: init.email ?? "",
  auth_code: init.auth_code ?? "",
});
const loading = ref(false);
const result = ref<PreflightResult | null>(store.preflight.imap ?? null);

async function run() {
  store.setAnswer("imap", form.value);
  await store.saveToServer();
  loading.value = true;
  try {
    result.value = await store.runPreflight("imap", form.value);
  } finally {
    loading.value = false;
  }
}

watch(form, () => store.setAnswer("imap", form.value), { deep: true });
function icon(s: string) {
  return s === "ok" ? "✓" : s === "fail" ? "✗" : s === "warn" ? "▲" : "○";
}
</script>
