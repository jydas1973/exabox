# QMR Exadata Image Version Registration and Target Version Support

- [Overview](#overview)
  - [Detailed Requirement](#detailed-requirement)
  - [Process Flow](#process-flow)
  - [Use Cases](#use-cases)
  - [Clarifications](#clarifications)
  - [JIRAS](#jiras)

---

## Overview

This document outlines the requirements for enhancements to the Exadata image version registration and patching system:

1. **QMR Version Pre-Registration**: Currently, QMR (Quarterly Maintenance Release) versions are registered on the 1st day of every quarter. However, QMRs are created 1 month before the start of the quarter, causing customers to see incorrect target versions on the console for an entire month. There is a need to register versions for a quarter ahead of time.

2. **Target Version Support for Dom0/KVM Host ELU**: Currently, Control Plane (CP) passes the "LATEST" version and the ELU version is calculated based on the exaversion series registration. The requirement is for CP to pass the explicit target version, and the back-end will use this version directly to apply ELU without any separate calculations.

3. **Customer Version Choice for Quarterly Maintenance**: Currently, quarterly infrastructure maintenance applies the latest Exadata image version with no customer control over version selection. Customers, particularly those in regulated industries, require the ability to apply specific versions (not just latest) to non-production environments before production. The proposal is to allow customers to choose any version released during the previous 2 quarters.

---

## Detailed Requirement

### QMR Version Pre-Registration (EXACS-167790)

- QMRs are created 1 month before the start of each quarter
- Current behavior: Version registration happens only on the 1st day of every quarter
- Problem: Customers see wrong target version on console for the entire month before quarter start
- Solution: Enable ability to register versions for quarters ahead of time

**Example Registration Model:**

| Quarter | Version |
|---------|---------|
| Q1      | Version X |
| Q2      | Version Y |
| Q3      | Version Z |
| Q4      | Version W |

Control Plane should be able to query the version for a specific quarter and update the target version in the customer's console accordingly.

### Target Version for Dom0/KVM Host ELU (EXACS-166854)

- Current behavior: CP passes "LATEST" and ELU version is calculated based on exaversion series registration
- New requirement: CP will pass the explicit target version
- Back-end will use this version directly to apply ELU
- No separate calculations should be done to determine the target version based on Quarterly Image Versions
- This is needed to support the reference/follow the env/service feature

### Customer Version Choice for Quarterly Maintenance (EXACS-161060)

**Current State:**
- Exadata Cloud Infrastructure Maintenance is owned and managed by Oracle
- Quarterly infrastructure maintenance applies the latest Exadata image version to both database servers and storage servers
- Monthly infrastructure maintenance applies the latest monthly security update (Exasplice) to database servers and latest Exadata image to storage servers
- Customers have no control to choose the image version
- Customers must schedule quarterly infrastructure maintenance each quarter (can reschedule up to 180 days since prior maintenance)

**Problem Statement:**
- Many customers require software updates of a particular version to be applied in non-production environments before production
- Regulated industries (e.g., Deutsche Bank) specifically require this for Oracle-managed maintenance updates
- Scheduling challenges exist due to impact of quarterly database server maintenance on applications/databases that do not follow continuous availability best practices (not "RAC" aware or single instance)
- Applying latest version every quarter, first to all non-prod then to prod, is not currently possible

**Proposed Features:**
- Allow customers to choose any version released during the previous 2 quarters for quarterly maintenance:
  - Latest (N)
  - N-1
  - N-2
  - etc.
- Allow quarterly maintenance to be scheduled as much as 6 months apart in maintenance preferences

**Note:** Monthly maintenance is less impacted as it is applied "online" for database servers, avoiding database availability impact and allowing greater scheduling flexibility.

---

## Process Flow

### QMR Version Registration Flow

1. QMR is created 1 month before quarter start
2. Version is registered against the upcoming quarter (ahead of time)
3. Multiple quarterly versions can exist in the system simultaneously
4. Control Plane queries the version for the current/target quarter
5. Customer console displays the correct target version based on the quarter

### Target Version ELU Flow

1. CP passes the explicit target version as part of the ELU request (instead of "LATEST")
2. Back-end receives the target version directly
3. ELU is applied using the passed target version
4. No implicit version calculation is performed by the back-end

### Customer Version Selection Flow

1. System maintains list of available versions from previous 2 quarters
2. Customer selects desired version (N, N-1, N-2, etc.) in maintenance preferences
3. Customer schedules quarterly maintenance window (up to 6 months apart)
4. During maintenance, the selected version is applied to:
   - Database servers
   - Storage servers
5. Customer can apply to non-prod first, then prod with the same specific version

---

## Use Cases

### Reference/Follow Environment Feature (EXACS-166854)

**Use Case A: Pre-prod as Reference for Prod**
- Customer uses their pre-prod environment as reference Exadata version
- Prod environment upgrades to match the pre-prod version
- Ensures consistency between environments

**Use Case B: Cross-Service Version Following**
- Customer can use service level version across different service types
- ExaCC to ExaCS version following
- ExaCS to ExaCC version following

### Regulated Industry Compliance (EXACS-161060)

**Use Case C: Non-Prod to Prod Version Promotion**
- Customer in regulated industry applies version N-1 to non-prod environments
- After validation and compliance checks, same version N-1 is applied to prod
- Ensures tested version is deployed to production

**Use Case D: Extended Maintenance Window**
- Customer schedules quarterly maintenance up to 6 months apart
- Provides flexibility for complex maintenance planning
- Accommodates applications not following continuous availability best practices

---

## Clarifications

### QMR Pre-Registration
- How will the quarter-to-version mapping be stored and queried?
- What is the data model for storing multiple quarterly versions?
- How will CP determine which quarter's version to query?
- What happens during quarter transitions?

### Target Version Support
- How will the "reference environment" feature determine which version to pass?
- What validation is needed when CP passes an explicit target version?
- Should there be any fallback behavior if the passed target version is invalid?

### Customer Version Choice
- How many quarters of versions should be retained and made available for selection?
- What is the UI/API for customers to select their preferred version?
- How does this interact with the maintenance preference scheduling?
- What happens if a customer-selected version has known critical issues?
- How will version compatibility between database servers and storage servers be validated?

---

## JIRAS

| JIRA ID | Title | Description |
|---------|-------|-------------|
| [EXACS-167790](https://jira.oraclecorp.com/jira/browse/EXACS-167790) | Support for QMR Exadata Image Version Registration for Every Quarter | Enable ability to register version for a quarter ahead of time to prevent customers from seeing wrong target version on console |
| [EXACS-166854](https://jira.oraclecorp.com/jira/browse/EXACS-166854) | Support target version for dom0/kvm host ELU | CP to pass explicit target version instead of LATEST, back-end uses this version directly without calculations |
| [EXACS-161060](https://jira.oraclecorp.com/jira/browse/EXACS-161060) | Customer Version Choice for Quarterly Infrastructure Maintenance | Allow customers to choose any version from previous 2 quarters (N, N-1, N-2) and schedule maintenance up to 6 months apart |
