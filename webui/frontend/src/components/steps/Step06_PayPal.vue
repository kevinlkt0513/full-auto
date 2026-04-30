<template>
  <section class="step-fade-in">
    <template v-if="store.isStepHidden(6)">
      <div class="term-divider" data-tail="──────────">步骤 06: PayPal — 已跳过</div>
      <h2 class="step-h">$&nbsp;此步已跳过<span class="term-cursor"></span></h2>
      <p class="step-sub">你在 step 1 选了"纯卡"支付，PayPal 配置不需要。</p>
      <div class="step-actions">
        <button class="term-btn term-btn--ghost" @click="goStep1">返回 step 1 修改</button>
      </div>
    </template>
    <template v-else>
      <div class="term-divider" data-tail="──────────">步骤 06: PayPal</div>
      <h2 class="step-h">$&nbsp;PayPal 凭据<span class="term-cursor"></span></h2>
      <p class="step-sub">第一次跑要人肉过一次邮箱 OTP 2FA。这里只校验字段格式，不真登录避免触发 2FA。</p>

      <div class="form-stack">
        <TermField v-model="form.email" label="PayPal 邮箱 · email" />
        <TermField v-model="form.password" label="PayPal 密码 · password" type="password" />
        <TermField v-model="form.imap_server" label="IMAP 服务器 · imap_server" placeholder="留空 = 用 Step 4" />
        <TermField v-model="form.imap_auth_code" label="IMAP 授权码 · imap_auth_code" type="password" />
      </div>

      <div v-if="warning" class="result-block result--warn" style="margin-top:16px">
        <div class="result-head">
          <span class="result-icon">▲</span>
          <span>{{ warning }}</span>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useWizardStore } from "../../stores/wizard";
import TermField from "../term/TermField.vue";

const store = useWizardStore();
const init = store.answers.paypal ?? {};
const form = ref({
  email: init.email ?? "",
  password: init.password ?? "",
  imap_server: init.imap_server ?? "",
  imap_auth_code: init.imap_auth_code ?? "",
});

const warning = computed(() => {
  if (form.value.email && !form.value.email.includes("@")) return "邮箱格式不对";
  if (form.value.password && form.value.password.length < 6) return "密码看着太短了";
  return null;
});

watch(form, () => {
  store.setAnswer("paypal", form.value);
  store.saveToServer();
}, { deep: true });

function goStep1() {
  store.setStep(1);
  store.saveToServer();
}
</script>
