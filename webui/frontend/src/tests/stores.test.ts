import { describe, it, expect, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useWizardStore } from "../stores/wizard";

describe("wizardStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("starts at step 1 with empty answers", () => {
    const s = useWizardStore();
    expect(s.currentStep).toBe(1);
    expect(s.answers).toEqual({});
  });

  it("setAnswer updates a section", () => {
    const s = useWizardStore();
    s.setAnswer("cloudflare", { cf_token: "x" });
    expect(s.answers.cloudflare).toEqual({ cf_token: "x" });
  });

  it("setPreflight stores result by check name", () => {
    const s = useWizardStore();
    s.setPreflight("cloudflare", { status: "ok", message: "all good", checks: [] });
    expect(s.preflight.cloudflare?.status).toBe("ok");
  });

  it("setPreflight appends to preflightLog", () => {
    const s = useWizardStore();
    expect(s.preflightLog.length).toBe(0);
    s.setPreflight("cloudflare", { status: "ok", message: "all good", checks: [] });
    expect(s.preflightLog.length).toBe(1);
    expect(s.preflightLog[0].name).toBe("cloudflare");
    expect(s.preflightLog[0].status).toBe("ok");
    expect(s.preflightLog[0].message).toBe("all good");
    expect(typeof s.preflightLog[0].ts).toBe("number");
  });

  it("preflightLog caps at 30 entries", () => {
    const s = useWizardStore();
    for (let i = 0; i < 35; i++) {
      s.setPreflight(`check-${i}`, { status: "ok", message: `msg-${i}`, checks: [] });
    }
    expect(s.preflightLog.length).toBe(30);
  });

  it("isStepUnlocked returns true if previous required steps are ok", () => {
    const s = useWizardStore();
    expect(s.isStepUnlocked(1)).toBe(true);
    expect(s.isStepUnlocked(3)).toBe(false);
    s.setPreflight("system", { status: "ok", message: "", checks: [] });
    s.setPreflight("cloudflare", { status: "ok", message: "", checks: [] });
    expect(s.isStepUnlocked(4)).toBe(true);
  });
});
