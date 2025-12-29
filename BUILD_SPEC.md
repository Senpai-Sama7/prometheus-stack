# PROMETHEUS: 16-Week Build Specification

## Phase 1: Contracts & Registries (Weeks 1-2)

### Goal
Boring. Critical. Prove the contract layer works.

### Deliverables

1. **MCP Server Scaffold**
   - Tool registry with explicit schemas
   - Resources (static data)
   - Prompts (interactive templates)
   - Transport: STDIO (local) + Streamable HTTP (Origin validation)

2. **ClaimBundle Implementation**
   - JSON schema validation
   - Evidence pointer verification
   - Serialization to/from JSON

3. **Audit Log (Append-Only)**
   - Immutable event logging
   - Queryable by agent, event_type, trace_id
   - Event hashing for verification

4. **Approval Queue**
   - Persistent queue (PostgreSQL + Celery)
   - Escalation rules by risk_tier
   - SLA tracking

### Acceptance Metrics
- [ ] 100% of tool calls are schema-validated
- [ ] 100% of actions logged with trace ID
- [ ] MCP Origin validation working
- [ ] Approval queue processes < 1 hour P95 latency

### Success Criterion
Zero invalid calls reach execution. You can see every action in the audit log.

---

## Phase 2: Orchestration + Uncertainty Gates (Weeks 3-5)

### Goal
Build the decision loop. Prove uncertainty detection works on your data.

### Deliverables

1. **LangGraph Workflow**
   - Decompose -> Execute -> Gate -> Invoke -> Loop
   - Checkpointing (persistence, fault tolerance)
   - Threading (multi-user execution)

2. **Uncertainty Gate**
   - Pick ONE: Semantic Entropy OR Model Disagreement
   - Threshold: defer > 0.75, explain > 0.50

3. **Test H001: Hallucination Detection**
   - Internal 100-example dataset
   - Measure AUROC of your uncertainty method
   - Target: >= 0.75

### Acceptance Metrics
- [ ] H001 AUROC >= 0.75 (testable hypothesis)
- [ ] Defer/escalate used appropriately (5-15% rate)
- [ ] Zero crashes from gate logic
- [ ] Checkpoint recovery works on process restart

### Success Criterion
You can decompose a task, run gates, and refuse to execute when uncertain.

---

## Phase 3: Security Moat (Weeks 6-9)

### Goal
Adversarial agents can't manipulate your system.

### Deliverables

1. **Security Gate**
   - Tier validation (agent_tier >= tool_tier)
   - Rate limiting per tool
   - MCP transport security (Origin validation)

2. **Guardian Agent Defense**
   - Separate agent trained on BAD-ACTS examples
   - Inline monitoring on all actions > read-only

3. **Test H002: Guardian ASR Reduction**
   - Simulate adversarial attacks
   - Measure baseline ASR (no defense)
   - Measure defended ASR (with guardian)
   - Target: >= 40% reduction

4. **Audit Logging**
   - Immutable event log (append-only)
   - Forensic-ready (queryable, complete)

### Acceptance Metrics
- [ ] H002 ASR reduction >= 40% (testable hypothesis)
- [ ] Security gate false positive rate <= 2%
- [ ] 100% of actions auditable
- [ ] Zero audit log tampering detectable

### Success Criterion
Adversarial agents struggle. Humans can forensically reconstruct what happened.

---

## Phase 4: Commercial Engine + Measurement (Weeks 10-16)

### Goal
Ship narratives that are true, measured, and brand-safe.

### Deliverables

1. **Narrative Generator**
   - 7-beat spine implementation
   - Every claim verified against evidence store
   - Unverifiable claims rewritten or rejected

2. **Test H003: MCP Integration Speed**
   - Onboard 3 new systems (Slack, HubSpot, Stripe)
   - Time each (target: < 30 min each)

3. **Test H004: Claim Integrity Rate**
   - Manual audit of 200 published claims
   - Measure: % of FACT claims with valid evidence
   - Target: >= 95%

4. **Measurement Policy**
   - Explicit decision: MMM vs MTA vs Hybrid
   - If hybrid: MTA for weekly, MMM for quarterly
   - Incrementality tests (holdouts)

5. **A/B Testing Framework**
   - Statistical significance testing
   - Holdout group management
   - Incrementality calculation

### Acceptance Metrics
- [ ] Narrative generation latency < 60s per variant
- [ ] H004 Claim Integrity Rate >= 95% (testable hypothesis)
- [ ] A/B test framework produces valid results
- [ ] Zero brand safety incidents

### Success Criterion
Every published claim has evidence. Measurement is explicit and defensible.

---

## Phase Gates (Non-Negotiable)

| Phase | Gate | Metric | Target | Status |
|-------|------|--------|--------|--------|
| 1 | Contract Validation | Tool calls schema-valid | 100% | — |
| 1 | Audit Compliance | Actions logged | 100% | — |
| 2 | H001: Hallucination Detection | Uncertainty AUROC | >= 0.75 | — |
| 2 | Deferral Appropriateness | Defer rate | 5-15% | — |
| 3 | H002: Guardian Effectiveness | ASR reduction | >= 40% | — |
| 3 | False Positive Rate | Legitimate actions blocked | <= 2% | — |
| 4 | H003: Integration Speed | MCP onboarding | < 30 min | — |
| 4 | H004: Claim Integrity | Facts with evidence | >= 95% | — |

**Rule:** All Phase N gates must PASS before proceeding to Phase N+1. No exceptions.

---

## Team Allocation (7 People, 16 Weeks)

| Role | Count | Phases | Deliverables |
|------|-------|--------|---|
| **Tech Lead** | 1 | 1-4 | Architecture decisions, gate logic, LangGraph integration |
| **Backend Eng** | 2 | 1-4 | MCP scaffold, audit log, ClaimBundle, orchestrator |
| **ML Eng** | 1 | 2-3 | Uncertainty gate (semantic entropy), guardian agent tuning |
| **Security Eng** | 1 | 3-4 | Security gate, adversarial test suite, transport security |
| **DevOps** | 1 | 1-4 | DB setup, checkpoint persistence, deployment automation |
| **Product/Measurement** | 1 | 4 | MMM/MTA policy, A/B test framework, metrics definition |

---

## Success Criteria Summary

- **Phase 1:** You have contracts and can log everything
- **Phase 2:** You can detect hallucinations on your data (H001)
- **Phase 3:** Adversarial agents struggle (H002)
- **Phase 4:** Every claim is evidenced and measured (H003, H004)

---

**Version:** 2.0 | **Updated:** December 28, 2025
