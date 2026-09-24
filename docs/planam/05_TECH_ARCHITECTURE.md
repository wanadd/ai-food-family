# Technical Architecture

The current implementation remains a modular monolith with explicit logical ownership boundaries. The accepted target keeps that deployment shape while introducing canonical module contracts, adapters, projections, and one authoritative writer per capability.

Cross-domain database reads are prohibited by default. Use application contracts or projections. New Core identifiers use UUIDv7. Durable jobs and an outbox are the first job-durability target. Numeric SLO/RPO/RTO values await baseline measurement. This document does not authorize ORM adoption, backfill, or production change.
