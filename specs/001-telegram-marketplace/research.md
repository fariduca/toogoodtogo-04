# Research: Telegram Marketplace Clarifications

Date: 2025-11-13
Branch: 001-telegram-marketplace
Spec: ./spec.md

## 1. Image Hosting Strategy
- **Decision**: Store originals briefly on local disk for preprocessing; upload to object storage (S3-compatible) with signed public URLs; CDN layer optional post-MVP.
- **Rationale**: Local preprocessing (resize/compress) reduces bandwidth and standardizes dimensions; object storage separates concerns and scales; defers CDN cost until traffic justifies.
- **Alternatives Considered**:
  - Local-only storage: Simple but risks disk growth and lacks geo performance.
  - Immediate CDN integration: Better global performance but premature complexity/cost.
  - Telegram file_id reuse only: Limits branding control and transformation.

## 2. Discovery Ranking Extension
- **Decision**: MVP uses latest + simple popularity (purchase count) with optional manual pinning; later add geo proximity using coordinates when available.
- **Rationale**: Early usage needs freshness and simple social proof; geo integration requires reliable coordinates and adds complexity—can be deferred.
- **Alternatives Considered**:
  - Full geo ranking from start: Overhead in data collection & accuracy not justified early.
  - Category-weighted ranking: Needs taxonomy and consistent tagging not yet defined.
  - ML-based relevance: Overkill for initial scale.

## 3. Observability Enhancement
- **Decision**: Structured JSON logging (correlation IDs) + minimal error reporting; integrate Sentry only after first production pilot.
- **Rationale**: Logging already supports debugging; Sentry adds value under higher volume but introduces maintenance overhead early.
- **Alternatives Considered**:
  - Adopt Sentry immediately: Faster triage but incurs setup and DSN secret management now.
  - Logging only forever: Limits alerting and stack trace aggregation at scale.

## Resolution Summary
All outstanding clarifications resolved; plan.md will be updated to remove NEEDS CLARIFICATION markers during Phase 1 adjustments.

## Next Steps
Proceed to Phase 1: data-model, contracts, quickstart, agent context update.
