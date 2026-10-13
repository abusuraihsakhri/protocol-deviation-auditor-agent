import test from "node:test";
import assert from "node:assert/strict";
import { evaluateTask } from "../web/audit.mjs";

const payload = {
  task_id: "DEMO-001", target_identifier: "SYNTHETIC-01",
  primary_metric: 12, secondary_metric: 3,
  status_descriptor: "NOMINAL", is_critical_flag: false,
};

test("routine and boundary conditions match server example rules", () => {
  assert.equal(evaluateTask(payload).overall_urgency, "ROUTINE");
  assert.equal(evaluateTask({...payload, primary_metric: 25}).total_alerts, 0);
  assert.equal(evaluateTask({...payload, primary_metric: 25.1}).total_alerts, 1);
  assert.equal(evaluateTask({...payload, secondary_metric: 12}).total_alerts, 0);
  assert.equal(evaluateTask({...payload, secondary_metric: 12.1}).overall_urgency, "ELEVATED_RISK");
});

test("critical flag takes priority and descriptors raise independent alerts", () => {
  const report = evaluateTask({...payload, is_critical_flag: true, status_descriptor: "DISCORDANT"});
  assert.equal(report.overall_urgency, "CRITICAL_STAT_PANIC");
  assert.equal(report.total_alerts, 2);
  assert.equal(report.critical_alerts_count, 1);
});

test("invalid or nonfinite values are rejected", () => {
  assert.throws(() => evaluateTask({...payload, primary_metric: Infinity}));
  assert.throws(() => evaluateTask({...payload, secondary_metric: NaN}));
  assert.throws(() => evaluateTask({...payload, target_identifier: "Patient Jane Smith"}));
  assert.throws(() => evaluateTask({...payload, task_id: ""}));
});
