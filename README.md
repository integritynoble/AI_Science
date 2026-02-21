# AI Science Targeting Systems

**Live at: [sci.platformai.org](https://sci.platformai.org)**

Two precision-engineered targeting systems that industrialize scientific discovery, built on the [SolveEverything.org](https://solveeverything.org/) L0-L5 maturity framework.

## Targeting System 1: AI Paper Review

A comprehensive review system that simulates real peer review with multiple specialized AI reviewers, venue-specific benchmarks, and adversarial analysis.

### 3-Layer Architecture

| Layer | Component | Description |
|-------|-----------|-------------|
| 1 | **Standard Peer Review** | 4 AI reviewers (Methodologist, Experimenter, Novelty Expert, Clarity Expert) scoring across 5 dimensions |
| 2 | **L0-L5 Maturity Assessment** | Structured maturity evaluation based on SolveEverything.org framework |
| 3 | **Red Team & Gate Analysis** | Adversarial analysis for logical flaws, statistical validity, and reproducibility gaps |

### 9-Stage Review Workflow

```
Parse Paper → Integrity Gate → Extract Content → Meta-Review → Extract Facts
→ 4 Parallel Reviewers → Synthesize → Generate Charts → Final Report
```

### Scoring Dimensions
- Soundness / Rigor
- Empirical / Evaluation
- Novelty / Significance
- Clarity
- Reproducibility / Transparency

### 30+ Venue Standards
NeurIPS, ICLR, ICML, CVPR, ECCV, ACL, EMNLP, AAAI, IJCAI, AISTATS, JMLR, AAS, APS, JHEP, PASJ, and more. Each venue has calibrated scoring benchmarks and weighting schemes.

### Review Modes
- **Standard** — Balanced, constructive criticism
- **Friendly** — Encouraging feedback focused on improvement
- **Devil's Advocate** — Rigorous, harsh critique that stress-tests every claim

## Targeting System 2: Prompt-Paper-Generation

A multi-stage pipeline that transforms user prompts into complete scientific papers with built-in quality refinement and AI review integration.

### 7-Stage Pipeline

1. **Idea Generation** — Generate and refine research ideas from user prompt
2. **Novelty Check** — Iterative literature search validating originality
3. **Methodology Design** — AI researcher agent with critic-loop refinement
4. **Paper Composition** — Section-by-section generation (Abstract → Introduction → Methods → Results → Conclusions)
5. **Self-Reflection & Refinement** — Quality improvement on each section
6. **LaTeX Compilation** — Journal-specific templates with auto error-fixing
7. **AI Review Integration** — Automatic review by Targeting System 1

### Standards

- **Input**: Research prompt, optional data/plots/literature, journal target
- **Quality Gates**: Novelty verification, LaTeX validation, self-reflection, review score threshold
- **Output**: Complete PDF, LaTeX source, AI review report, maturity assessment

Available on [CIAS Platform (cias.comparegpt.io)](https://cias.comparegpt.io/).

## L0-L5 Maturity Framework

| Level | Name | Description |
|-------|------|-------------|
| L0 | Ill-Posed | Objectives undefined, unmeasured |
| L1 | Measurable | Clear metrics, baselines, quantified results |
| L2 | Repeatable | Reproducible, code/data available, error bars |
| L3 | Automated | End-to-end automation, scalability demonstrated |
| L4 | Industrialized | Production-ready, robustness characterized |
| L5 | Solved | Optimality proven, community consensus |

## Publishing: aiXiv & Arena

Reviewed papers are published on [aixiv.platformai.org](https://aixiv.platformai.org):

- **Tier 1 (aiXiv)** — Open publishing, papers immediately searchable with ID `aiXiv:YYMM.NNN`
- **Tier 2 (Arena)** — Quality-gated leaderboard with composite scoring and maturity bonuses

## Links

| Platform | URL |
|----------|-----|
| AI Science Targeting Systems | [sci.platformai.org](https://sci.platformai.org) |
| CIAS (Paper Generation & Review) | [cias.comparegpt.io](https://cias.comparegpt.io/) |
| aiXiv (Paper Archive) | [aixiv.platformai.org](https://aixiv.platformai.org) |
| SolveEverything.org (Framework) | [solveeverything.org](https://solveeverything.org/) |
| PlatformAI | [platformai.org](https://platformai.org) |

## Server

- **Domain**: sci.platformai.org
- **Server**: 34.63.169.185
- **Stack**: Static HTML/CSS served via Nginx with Let's Encrypt SSL
