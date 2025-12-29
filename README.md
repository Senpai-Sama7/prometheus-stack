# PROMETHEUS: Verifiable AI Execution Engine

**TL;DR:** Agents that prove every claim has evidence. Gates that refuse hallucinations. Humans in control of irreversible actions.

## Vision

AI agents are powerful. But they hallucinate. They escalate privileges. They manipulate orchestration. PROMETHEUS is a **verification engine** that:

1. **Collects evidence** for every claim (semantic entropy, sources, confidence scores)
2. **Verifies claims** through 5 mandatory gates (Evidence → Uncertainty → Security → Adversarial → Human)
3. **Maintains audit trails** for forensic reconstruction
4. **Keeps humans in control** of irreversible actions

## Architecture

```
Task Input
    ↓
[Orchestrator] Decompose → Execute → Collect Evidence
    ↓
[ClaimBundle] Wrap results in contract
    ↓
[GateStack] 5 verification gates:
    1. Evidence Gate       → FACT claims must have sources (confidence >= 0.60)
    2. Uncertainty Gate    → Defer if uncertainty > 0.75
    3. Security Gate       → Enforce privilege hierarchy
    4. Adversarial Gate    → Guardian agent monitors anomalies
    5. Human Approval Gate → High-risk actions require sign-off
    ↓
[Decision]
  ✅ PUBLISH → Output results
  ⚠️  DEFER   → Escalate to human
  ❌ REFUSE  → Reject action
  🚨 ESCALATE → Blocking high-risk action
```

## Quick Start

### 1. Bootstrap Environment

```bash
bash scripts/bootstrap.sh
```

This:
- Checks Python 3.10+
- Creates virtual environment
- Installs dependencies
- Creates source directories
- Sets up audit logging

### 2. Run Tests

```bash
bash scripts/run_tests.sh
```

### 3. Minimal Example

```python
from src.claim_bundle import (
    ClaimBundle, Claim, Uncertainty, 
    UncertaintyMethod, GateRecommendation, RiskTier, ClaimType
)
from src.gates import GateStack

# Create a claim with evidence
claim = Claim(
    statement="PROMETHEUS uses semantic entropy for hallucination detection",
    claim_type=ClaimType.FACT,
    evidence_pointers=[
        {
            "source": "https://nature.com/articles/s41586-024-07421-0",
            "source_confidence": 0.95,
            "evidence_hash": "bd24c2aaef2ef37ae95f0f9e5f7d9e7c"
        }
    ],
    uncertainty=Uncertainty(
        method=UncertaintyMethod.SEMANTIC_ENTROPY,
        value=0.15,
        interpretation="Strong empirical validation",
        gate_recommendation=GateRecommendation.EXECUTE
    ),
    risk_tier=RiskTier.READ_ONLY
)

# Create bundle
bundle = ClaimBundle(origin_agent="demo_agent", claims=[claim])

# Run through gates
result = GateStack.evaluate(bundle)

print(f"Decision: {bundle.decision.value}")
print(f"Reason: {bundle.reason}")
```

## Key Concepts

### ClaimBundle Contract

Every output is a **ClaimBundle** with:
- **Claims**: Statements (FACT, INFERENCE, DECISION) with evidence and uncertainty
- **Evidence Pointers**: Sources with confidence scores
- **Uncertainty**: Computed via semantic entropy, model disagreement, or conformal sets
- **Risk Tier**: Determines approval requirements
- **Audit Trail**: Immutable log of gates passed/failed

### Uncertainty Methods

| Method | Cost | AUROC | When to Use |
|--------|------|-------|-------------|
| **Semantic Entropy** | 5x | 0.78-0.81 | Recommended (Wang et al., Nature 2024) |
| **Model Disagreement** | 3x | ~0.70 | Fast, empirical |
| **Confidence Score** | 1x | ~0.60 | Baseline (often overconfident) |
| **Conformal Set** | O(N+k) | 1.0* | Formal guarantees (requires calibration) |

*Conformal prediction: guaranteed coverage, not AUROC

### Gate Stack

1. **Evidence Gate**: FACT claims must have evidence (confidence >= 0.60)
2. **Uncertainty Gate**: Defer if uncertainty > 0.75 (explain if > 0.50)
3. **Security Gate**: Agent tier must >= tool tier (no privilege escalation)
4. **Adversarial Gate**: Guardian agent monitors for attack patterns
5. **Human Approval Gate**: DELETE and PRIVILEGE tier require sign-off

**Flow:**
```
All gates must PASS or decision → DEFER/REFUSE/ESCALATE
```

## 16-Week Build Specification

See `BUILD_SPEC.md` for full rollout plan:

- **Phase 1 (Weeks 1-2):** Contracts, Registries, Audit Log
- **Phase 2 (Weeks 3-5):** Orchestration, Uncertainty Gates, H001 Test
- **Phase 3 (Weeks 6-9):** Security, Guardian Agent, H002 Test
- **Phase 4 (Weeks 10-16):** Commercial Engine, Measurement, H003/H004 Tests

## Testable Hypotheses

Every claim is testable. See `docs/HYPOTHESIS_TESTING.md`:

| ID | Hypothesis | Threshold | Timeline |
|----|-----------|-----------|----------|
| **H001** | Semantic entropy AUROC >= 0.75 | 0.75 | Week 4 |
| **H002** | Guardian ASR reduction >= 40% | 0.40 | Week 9 |
| **H003** | MCP integration < 30 min per system | 30 min | Week 2 |
| **H004** | Claim integrity rate >= 95% | 0.95 | Week 16 |

## Documentation

- **[CONTRACTS.md](docs/CONTRACTS.md)**: ClaimBundle specification, evidence rules, serialization
- **[GATES.md](docs/GATES.md)**: Gate implementations, uncertainty methods, security specs
- **[HYPOTHESIS_TESTING.md](docs/HYPOTHESIS_TESTING.md)**: 4 testable hypotheses (H001-H004)
- **[BUILD_SPEC.md](BUILD_SPEC.md)**: 16-week rollout plan with team allocation
- **[INTERFACE_PACK.json](INTERFACE_PACK.json)**: JSON schema for all interfaces

## Source Code

```
src/
├── __init__.py              # Package initialization
├── claim_bundle.py          # ClaimBundle contract + serialization
├── gates.py                 # Evidence, Uncertainty, Security, Adversarial, Human gates
├── orchestrator.py          # LangGraph orchestration stub
├── gates/                   # Gate implementations (per-file in phase 2+)
├── uncertainty/             # Uncertainty methods (semantic_entropy, model_disagreement, etc.)
├── mcp/                     # Model Context Protocol integration
└── audit/                   # Immutable event logging
```

## Testing

```bash
# Unit tests
pytest tests/ -v

# Acceptance tests (hypotheses)
pytest tests/acceptance/ -v

# H001: Semantic entropy AUROC
pytest tests/acceptance/test_h001_semantic_entropy.py -v

# H002: Guardian defense
pytest tests/acceptance/test_h002_guardian_defense.py -v

# H003: MCP integration speed
pytest tests/acceptance/test_h003_mcp_speed.py -v

# H004: Claim integrity
pytest tests/acceptance/test_h004_claim_integrity.py -v
```

## Configuration

Create `.env` for local development:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/prometheus
REDIS_URL=redis://localhost:6379

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Uncertainty method
UNCERTAINTY_METHOD=semantic_entropy  # or model_disagreement

# Gate thresholds
DEFER_THRESHOLD=0.75
EXPLAIN_THRESHOLD=0.50

# Security
ALLOWED_ORIGINS=http://localhost:3000,https://example.com
```

## References

### Key Papers

1. **Semantic Entropy** (Wang et al., Nature 2024)
   - AUROC 0.78-0.81 for hallucination detection
   - Generate k=5 answers, cluster by NLI, compute entropy
   - https://nature.com/articles/s41586-024-07421-0

2. **BAD-ACTS** (Nöther et al., Aug 2025)
   - Attack-trained models reduce ASR by 25-50%
   - Guardian agent defense patterns
   - https://arxiv.org/abs/2408.xxxxx

3. **MCP Spec** (Anthropic, June 2025)
   - Model Context Protocol for tool integration
   - DNS rebinding protection for HTTP transport
   - https://spec.modelcontextprotocol.io

### Standards

- JSON Schema for ClaimBundle: `INTERFACE_PACK.json`
- Python 3.10+ type hints throughout
- OpenAPI 3.0 for HTTP endpoints (phase 3+)
- IEEE 1012 for verification & validation

## Status

- ✅ **Repository initialized** with contracts, gates, orchestrator skeleton
- ⏳ **Phase 1 (Weeks 1-2):** In progress (you are here)
- ⏳ **Phase 2 (Weeks 3-5):** Scheduled
- ⏳ **Phase 3 (Weeks 6-9):** Scheduled
- ⏳ **Phase 4 (Weeks 10-16):** Scheduled

## Contributing

Follow the 16-week spec. All code must:
1. Pass unit tests (`pytest tests/`)
2. Pass type checking (`mypy src/`)
3. Follow style guide (`black`, `flake8`)
4. Include docstrings (Google format)
5. Have audit trail for all gate-relevant changes

## License

Proprietary. See LICENSE file.

---

**PROMETHEUS: AI agents that prove their claims.**

Built by humans. Verified by humans. Controlled by humans.
