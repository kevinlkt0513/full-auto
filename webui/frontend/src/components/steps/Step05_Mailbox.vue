<template>
  <section class="step-fade-in">
    <div class="term-divider" data-tail="──────────">步骤 05: 邮箱地址</div>
    <h2 class="step-h">$&nbsp;邮箱地址来源<span class="term-cursor"></span></h2>
    <p class="step-sub">选择注册时填入的邮箱地址来源。默认继续使用 Cloudflare catch-all；如果你已经准备好一批转发到 IMAP 收件箱的邮箱，就切到固定邮箱池。</p>

    <TermChoice v-model="form.mode" :options="modeOptions" :cols="2" />

    <div v-if="form.mode === 'catch_all'" class="form-stack mailbox-panel">
      <TermField
        v-model="form.catch_all_domain"
        label="Catch-all 域名 · catch_all_domain"
        placeholder="留空 = 使用 Step 03 的第一个 zone"
      />
      <div class="info-block">
        留空时导出配置会使用 Cloudflare step 里填的第一个 zone，并保留 zone 列表用于自动轮换。
      </div>
    </div>

    <div v-else class="form-stack mailbox-panel">
      <TermField
        v-model="form.email_pool_file"
        label="邮箱池文件 · email_pool_file"
        :placeholder="DEFAULT_EMAIL_POOL_FILE"
      />
      <TermField
        v-model="form.email_pool_state_path"
        label="取号状态 · email_pool_state_path"
        :placeholder="DEFAULT_EMAIL_POOL_STATE_PATH"
      />
      <label class="tf">
        <span class="tf-tag">内联邮箱 · email_pool</span>
        <textarea
          v-model="emailPoolText"
          class="tf-textarea"
          placeholder="alias-001@example.net&#10;alias-002@example.net&#10;# 井号开头是注释"
          rows="5"
        ></textarea>
      </label>
      <TermToggle v-model="form.email_pool_reuse">邮箱池用完后从头复用</TermToggle>
      <div class="info-block">
        文件格式是纯文本，一行一个邮箱；空行和 <code>#</code> 注释会跳过。固定邮箱池模式会把 <code>catch_all_domain</code> 置空。所有邮箱需要提前转发到 Step 04 的 IMAP 收件箱，并能在转发邮件头里保留原始收件地址。
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useWizardStore } from "../../stores/wizard";
import TermChoice from "../term/TermChoice.vue";
import TermField from "../term/TermField.vue";
import TermToggle from "../term/TermToggle.vue";

const store = useWizardStore();
const init = store.answers.mailbox ?? {};
const DEFAULT_EMAIL_POOL_FILE = "/opt/444/output/email_pool.txt";
const DEFAULT_EMAIL_POOL_STATE_PATH = "/opt/444/output/email_pool_state.json";

function defaultPath(value: string | undefined, legacyDefault: string, fallback: string) {
  return !value || value === legacyDefault ? fallback : value;
}

const form = ref({
  mode: init.mode ?? "catch_all",
  catch_all_domain: init.catch_all_domain ?? "",
  email_pool: (init.email_pool ?? []) as string[],
  email_pool_file: defaultPath(init.email_pool_file, "../output/email_pool.txt", DEFAULT_EMAIL_POOL_FILE),
  email_pool_state_path: defaultPath(init.email_pool_state_path, "../output/email_pool_state.json", DEFAULT_EMAIL_POOL_STATE_PATH),
  email_pool_reuse: init.email_pool_reuse ?? false,
});

const modeOptions = [
  {
    value: "catch_all",
    label: "Cloudflare catch-all",
    desc: "随机生成 name@domain，适合有域名和 Email Routing 的情况",
  },
  {
    value: "fixed_pool",
    label: "固定邮箱池",
    desc: "使用你指定的一批已转发邮箱，按顺序取号",
  },
];

const emailPoolText = computed({
  get: () => form.value.email_pool.join("\n"),
  set: (v: string) => {
    form.value.email_pool = v.split("\n").map((s) => s.trim()).filter(Boolean);
  },
});

watch(form, () => store.setAnswer("mailbox", form.value), { deep: true, immediate: true });
</script>

<style scoped>
.mailbox-panel { margin-top: 16px; }
.tf {
  display: grid;
  grid-template-columns: minmax(140px, max-content) minmax(0, 1fr);
  border: 1px solid var(--border);
  background: var(--bg-base);
  transition: border-color 80ms;
}
.tf:focus-within { border-color: var(--accent); }
.tf-tag {
  background: var(--bg-panel);
  color: var(--fg-tertiary);
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border-right: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  white-space: nowrap;
}
.tf-textarea {
  background: transparent;
  border: 0;
  padding: 10px 12px;
  color: var(--fg-primary);
  font: inherit;
  font-size: 13px;
  outline: none;
  resize: vertical;
  min-height: 100px;
  width: 100%;
}
.tf-textarea::placeholder { color: var(--fg-tertiary); opacity: 0.6; }
</style>
