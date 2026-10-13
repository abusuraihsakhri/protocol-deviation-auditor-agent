/**
 * Browser-only demonstration of the existing agents/workers.py rules.
 * It does not attest compliance with a study protocol or create signed audit records.
 */
export const DEMO_RULES = Object.freeze({
  primaryUpperBound: 25,
  secondaryUpperBound: 12,
  warningDescriptors: ["DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT"],
});

function safeIdentifier(value, name) {
  if (typeof value !== "string" || !/^[A-Za-z0-9_-]{1,64}$/.test(value)) {
    throw new Error(`${name} must contain 1–64 letters, digits, hyphens or underscores. Use a synthetic ID.`);
  }
  return value;
}

export function evaluateTask(input) {
  const taskId = safeIdentifier(input.task_id, "Task ID");
  const target = safeIdentifier(input.target_identifier, "Target ID");
  if (typeof input.status_descriptor !== "string" ||
      !/^[A-Za-z0-9_-]{1,128}$/.test(input.status_descriptor)) {
    throw new Error("Status descriptor must contain 1–128 letters, digits, hyphens or underscores.");
  }
  if (!Number.isFinite(input.primary_metric) || !Number.isFinite(input.secondary_metric)) {
    throw new Error("Both metrics must be finite numeric values.");
  }
  if (typeof input.is_critical_flag !== "boolean") {
    throw new Error("Critical flag must be true or false.");
  }

  const alerts = [];
  if (input.primary_metric > DEMO_RULES.primaryUpperBound) {
    alerts.push({
      worker: "InvariantQCWorker", urgency: "ELEVATED_RISK",
      summary: "Primary metric exceeds the example bound of 25.",
      remediation: "Review the study-specific protocol before interpreting this flag.",
    });
  }
  if (input.is_critical_flag || input.secondary_metric > DEMO_RULES.secondaryUpperBound) {
    alerts.push({
      worker: "SafetyEscalationWorker",
      urgency: input.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
      summary: "Example safety rule triggered.",
      remediation: "Escalate according to the applicable study procedures.",
    });
  }
  if (DEMO_RULES.warningDescriptors.some(term => input.status_descriptor.toUpperCase().includes(term))) {
    alerts.push({
      worker: "ProtocolConformanceWorker", urgency: "ELEVATED_RISK",
      summary: "Descriptor matched an example anomaly keyword.",
      remediation: "Review source records and applicable protocol requirements.",
    });
  }
  const critical = alerts.filter(a => a.urgency === "CRITICAL_STAT_PANIC").length;
  const overall = critical ? "CRITICAL_STAT_PANIC" : alerts.length ? "ELEVATED_RISK" : "ROUTINE";
  return {
    mode: "Illustrative local evaluation — not a GCP compliance determination",
    task_id: taskId, target_identifier: target,
    overall_urgency: overall,
    integrity_status: critical ? "RECALIBRATION_REQUIRED" :
      alerts.length ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    total_alerts: alerts.length,
    critical_alerts_count: critical,
    alerts,
    rules: DEMO_RULES,
  };
}

if (typeof document !== "undefined") {
  const form = document.getElementById("audit-form");
  const output = document.getElementById("outputConsole");
  const exportButton = document.getElementById("export-json");
  let latest = null;
  let count = 0;

  form.addEventListener("submit", event => {
    event.preventDefault();
    try {
      const metric = id => {
        const value = document.getElementById(id).value.trim();
        return value === "" ? NaN : Number(value);
      };
      const result = evaluateTask({
        task_id: document.getElementById("task_id").value.trim(),
        target_identifier: document.getElementById("target_id").value.trim(),
        primary_metric: metric("primary_metric"),
        secondary_metric: metric("secondary_metric"),
        status_descriptor: document.getElementById("status_descriptor").value.trim(),
        is_critical_flag: document.getElementById("is_critical").checked,
      });
      latest = result;
      count += 1;
      document.getElementById("m-status").textContent = result.overall_urgency;
      document.getElementById("m-tasks").textContent = String(count);
      document.getElementById("m-audit").textContent = String(result.total_alerts);
      output.textContent = JSON.stringify(result, null, 2);
      exportButton.disabled = false;
    } catch (error) {
      latest = null;
      exportButton.disabled = true;
      output.textContent = `Input error: ${error.message}`;
    }
  });

  exportButton.addEventListener("click", () => {
    if (!latest) return;
    const blob = new Blob([JSON.stringify(latest, null, 2) + "\n"], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "demo-audit-result.json";
    link.click();
    URL.revokeObjectURL(url);
  });
}
