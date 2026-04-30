<template>
  <section class="step-fade-in">
    <div class="term-divider" data-tail="──────────">步骤 10: 订阅方案</div>
    <h2 class="step-h">$&nbsp;Subscription plan<span class="term-cursor"></span></h2>
    <p class="step-sub">选 Plus 或 Team；多数字段都有默认值。</p>

    <div class="form-stack">
      <TermChoice
        v-model="form.plan_type"
        :options="[
          { value: 'team', label: 'Team', desc: 'chatgptteamplan · 多席位 · 1 个月免费' },
          { value: 'plus', label: 'Plus', desc: 'chatgptplusplan · 单用户 · 1 个月免费' },
        ]"
        :cols="2"
      />
      <TermField v-if="form.plan_type === 'team'" v-model="form.workspace_name" label="Workspace 名 · workspace_name" />
      <TermField v-if="form.plan_type === 'team'" v-model="form.seat_quantity" label="席位数 · seat_quantity" type="number" />
      <TermChoice
        v-model="form.price_interval"
        :options="[
          { value: 'month', label: '月付', desc: '按月计费' },
          { value: 'year', label: '年付', desc: '按年计费（通常有折扣）' },
        ]"
        :cols="2"
      />
      <TermField v-model="form.promo_campaign_id" :label="`优惠码 ID · promo_campaign_id`" :placeholder="defaultPromo" />
      <TermField v-model="form.billing_country" label="账单国家 · billing_country" />
      <TermField v-model="form.billing_currency" label="账单货币 · billing_currency" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useWizardStore } from "../../stores/wizard";
import TermField from "../term/TermField.vue";
import TermChoice from "../term/TermChoice.vue";

const store = useWizardStore();
const init = store.answers.team_plan ?? {};

function inferPlanType(): "team" | "plus" {
  if (init.plan_type === "plus" || init.plan_type === "team") return init.plan_type;
  if (typeof init.plan_name === "string" && init.plan_name.includes("plus")) return "plus";
  return "team";
}

const form = ref({
  plan_type: inferPlanType(),
  workspace_name: init.workspace_name ?? "MyWorkspace",
  seat_quantity: init.seat_quantity ?? 5,
  price_interval: init.price_interval ?? "month",
  promo_campaign_id: init.promo_campaign_id ?? (inferPlanType() === "plus" ? "plus-1-month-free" : "team-1-month-free"),
  billing_country: init.billing_country ?? "US",
  billing_currency: init.billing_currency ?? "USD",
});

const defaultPromo = computed(() => (form.value.plan_type === "plus" ? "plus-1-month-free" : "team-1-month-free"));

watch(
  () => form.value.plan_type,
  (next, prev) => {
    if (next === prev) return;
    const oldDefault = prev === "plus" ? "plus-1-month-free" : "team-1-month-free";
    if (!form.value.promo_campaign_id || form.value.promo_campaign_id === oldDefault) {
      form.value.promo_campaign_id = next === "plus" ? "plus-1-month-free" : "team-1-month-free";
    }
  },
);

watch(
  form,
  () => {
    const pt = form.value.plan_type;
    const out: Record<string, unknown> = {
      plan_type: pt,
      plan_name: pt === "plus" ? "chatgptplusplan" : "chatgptteamplan",
      entry_point: pt === "plus" ? "all_plans_pricing_modal" : "team_workspace_purchase_modal",
      price_interval: form.value.price_interval,
      promo_campaign_id: form.value.promo_campaign_id,
      billing_country: form.value.billing_country,
      billing_currency: form.value.billing_currency,
    };
    if (pt === "team") {
      out.workspace_name = form.value.workspace_name;
      out.seat_quantity = Number(form.value.seat_quantity) || 5;
    }
    store.setAnswer("team_plan", out);
    store.saveToServer();
  },
  { deep: true, immediate: true },
);
</script>
