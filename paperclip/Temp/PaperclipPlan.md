# Paperclip Implementation Plan

## Current Status

Paperclip is deployed without errors.

The following agents and integrations are currently working:

- **Headman** — CEO, `hermes_local`
  - Mem0
  - Telegram
  - Bifrost custom provider
- **Lab Doctor** — IT Director, `hermes_gateway`
  - Remote Hermes Lab profile
- **Summarizer** — built-in agent

---

## 1. Audit Current Runtimes — ✅ COMPLETE

- [x] Verify Headman / Hermes
- [x] Verify Summarizer / OpenCode
- [x] Verify Codex → Bifrost
- [x] Verify Pi → Bifrost
- [x] Verify OpenCode → Bifrost
- [x] Verify actual model IDs, API paths, credentials, and provider routing

---

## 2. Install and Verify Plugins — ⬜ NEXT

- [ ] Workspace Changes
- [ ] LLM Wiki
- [ ] Confirm Wiki Maintainer is healthy and functional

---

## 3. Design and Create GitHub Structure — ⬜

- [ ] Create private `phoenix-rtp-wiki` repository
- [ ] Define what belongs in GitHub vs Paperclip vs Mem0 vs Wiki vs Artifacts
- [ ] Define GitHub permissions for Headman and Wiki Maintainer
- [ ] Establish branch / commit / PR policy

---

## 4. Connect LLM Wiki to GitHub — ⬜

- [ ] Establish `raw/` and `wiki/` structure
- [ ] Create baseline commit
- [ ] Test Wiki Maintainer read / write / versioning workflow

---

## 5. Add Lab Doctor — ✅ COMPLETE

- [x] Connect Hermes LXC Lab profile through `hermes_gateway`
- [x] Create Lab Doctor — IT Director
- [x] Set reporting relationship to Headman
- [x] Test remote Hermes, tools, Bifrost, and infrastructure access

---

## 6. Write Agent Instructions — ⬜

- [ ] Headman: CEO responsibilities, delegation, GitHub, memory, decision authority
- [ ] Lab Doctor: infrastructure ownership, safety, GitHub, verification, reporting
- [ ] Define clear authority boundaries between Headman and Lab Doctor

---

## 7. Validate Paperclip Work Model — ⬜

- [ ] Define when to use Issues, Cases, Artifacts, Workspaces, GitHub, and Wiki
- [ ] Test one complete workflow:
  - Issue / task
  - Workspace
  - Artifact
  - Git commit
  - Knowledge / Wiki update

---

## 8. Configure Telegram for Headman — ✅ COMPLETE

- [x] Connect Telegram bot
- [x] Restrict external access appropriately
- [x] Configure identity linking
- [x] Verify restricted-guest isolation and sandbox behavior
- [x] Test inbound Telegram message → Headman → Paperclip task → response
- [x] Verify test task `PHO-18` completed successfully

### Telegram Access Configuration

- External identity access: **Allow unlinked people**
- Unlinked people are treated as **restricted guests**
- Restricted guests run tasks only with an isolated workspace and sandbox environment
- Paperclip safely refuses requests that do not satisfy the required isolation
- Restricted guests cannot:
  - Approve
  - Hire
  - Spend
  - Manage access
  - Reassign agents
- Identity link:
  - **Phoenix RTP**
  - Linked to **Shahrooz Hamedi**

### Telegram Verification

- Conversation: `7448439880`
- Test: **Help me test this**
- Paperclip task: `PHO-18`
- Result: **Completed**

---

## 9. Final System Validation — ⬜

- [ ] Headman delegates to Lab Doctor
- [ ] Lab Doctor performs an infrastructure task
- [ ] Summarizer produces a summary
- [ ] Wiki Maintainer records durable knowledge
- [ ] GitHub records durable source / configuration
- [ ] Verify no secrets or runtime state enter GitHub

---

## 10. Only After All Tests Pass — ⬜

- [ ] Enable autonomous / recurring workflows
- [ ] Expand GitHub permissions
- [ ] Add additional agents / projects

---

## Progress Summary

| Item | Status |
|---|---|
| 1. Audit current runtimes | ✅ Complete |
| 2. Install and verify plugins | ⬜ Next |
| 3. Design and create GitHub structure | ⬜ |
| 4. Connect LLM Wiki to GitHub | ⬜ |
| 5. Add Lab Doctor | ✅ Complete |
| 6. Write agent instructions | ⬜ |
| 7. Validate Paperclip work model | ⬜ |
| 8. Configure Telegram for Headman | ✅ Complete |
| 9. Final system validation | ⬜ |
| 10. Enable autonomous workflows / expand | ⬜ |

**Current next step: Item 2 — Install and verify plugins.**
