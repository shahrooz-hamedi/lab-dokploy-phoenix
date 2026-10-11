# Paperclip Implementation Plan
## Phoenix-RTP Infrastructure Management — Before Power Platform

### Objective

Build a reliable, controlled, and maintainable AI management workflow for Phoenix-RTP infrastructure.

The immediate goal is to teach the agents to understand, document, verify, and maintain infrastructure knowledge. Infrastructure automation and the Power Platform project come later.

---

## 1. Current Status — ✅ COMPLETE

- [x] Deploy Paperclip and verify its operation.
- [x] Verify Headman (CEO) using `hermes_local`.
- [x] Verify Lab Doctor using `hermes_gateway`.
- [x] Verify Summarizer.
- [x] Verify Codex, Pi, and OpenCode integrations through Bifrost.
- [x] Install and verify Workspace Changes.
- [x] Install and verify LLM Wiki.
- [x] Activate Wiki Maintainer's three daily maintenance routines.
- [x] Configure Headman's Mem0, Telegram, and Bifrost.
- [x] Verify Telegram-to-Paperclip workflow using PHO-18.
- [x] Verify Lab Doctor's connection to the remote Hermes Lab profile.

**Naming update:** Lab Doctor will become **Bernard Halland — Infrastructure Director**. Update his agent identity and instructions accordingly.

---

## 2. Define the Information Architecture — ⬜ NEXT

Establish clear responsibilities for each system.

| Component | Responsibility |
|---|---|
| Paperclip | Tasks, delegation, approvals, accountability, and execution history. |
| GitHub | Version-controlled source files, configuration, documentation changes, and review history. |
| LLM Wiki | Organized, searchable, cross-project knowledge and verified documentation. |
| Mem0 | Persistent contextual memory for Headman and Bernard. |
| Artifacts | Task-specific deliverables, reports, and evidence. |
| Workspaces | Isolated working environments for agents and their changes. |

Define what belongs in each component to avoid duplication and conflicting sources of truth.

### Wiki spaces

- [ ] **Default space:** Phoenix-RTP company information, agent responsibilities, reporting relationships, policies, and company-wide procedures.
- [ ] **Infrastructure space:** Network topology, sites, devices, applications, storage, volumes, backups, monitoring, dependencies, and operational procedures.
- [ ] **Power Platform space:** Deferred until the infrastructure workflow is ready.

Use one Wiki root and, initially, one GitHub repository for all Wiki spaces.

**Important:** Confirm how the plugin handles multiple spaces and Git synchronization before implementing this structure. Paperclip ingestion currently targets the default space, so infrastructure knowledge must not depend on automatic ingestion into the infrastructure space.

---

## 3. Design and Create the GitHub Structure — ⬜

- [ ] Create a private `phoenix-rtp-wiki` repository.
- [ ] Decide how the repository maps to `/paperclip/llm-wiki`.
- [ ] Define the repository's directory structure and documentation conventions.
- [ ] Establish the baseline commit.
- [ ] Configure a development branch and protected `main` branch.
- [ ] Define agent permissions and approval requirements.
- [ ] Define exclusions for secrets, credentials, runtime state, and sensitive operational data.

### Proposed change workflow

1. Bernard or Wiki Maintainer prepares documentation changes.
2. Changes are committed to the development branch.
3. Wiki Maintainer checks structure, accuracy, provenance, and consistency.
4. Headman coordinates review and requests the required approval.
5. Authorized approval is obtained before merging into `main`.

Do not assume that connecting a repository to the LLM Wiki project automatically synchronizes the Wiki root. Test the actual integration or establish a documented Git workflow.

---

## 4. Validate Wiki and Git Integration — ⬜

- [ ] Confirm the authoritative Wiki root and directory structure.
- [ ] Confirm how `default/` and additional spaces map to disk.
- [ ] Configure the Git repository without disrupting existing Wiki content.
- [ ] Verify reading existing pages.
- [ ] Verify creating and updating pages.
- [ ] Verify commits, branches, and change review.
- [ ] Verify that Wiki maintenance routines do not overwrite or bypass approved changes.
- [ ] Verify that a failed synchronization cannot silently lose documentation.
- [ ] Test recovery from an incorrect documentation change.

**Exit criterion:** Wiki content is readable, writable, version-controlled, and recoverable through a tested workflow.

---

## 5. Define Agent Responsibilities and Authority — ⬜

### Headman — CEO

- Coordinate company-wide priorities and agent assignments.
- Delegate infrastructure knowledge tasks to Bernard.
- Coordinate Wiki Maintainer and Summarizer.
- Maintain appropriate CEO memory in Mem0.
- Coordinate Git reviews and request approvals.
- Respect explicit authority boundaries and approval requirements.

### Bernard Halland — Infrastructure Director

**Initial mode: Read-only infrastructure access.**

- Learn the complete infrastructure topology across LAB, HUB, and AWS.
- Inventory networks, devices, services, applications, storage, volumes, backups, monitoring, notifications, and dependencies.
- Identify authoritative configuration sources and documentation gaps.
- Develop reusable skills and verified procedures.
- Submit discoveries, evidence, and proposed documentation changes.
- Verify that his instructions, skills, and documented knowledge remain consistent.
- Report uncertainty instead of inventing missing information.

Bernard must not change production infrastructure during this phase.

### Wiki Maintainer

- Maintain the Wiki's information architecture and documentation quality.
- Organize and validate Bernard's discoveries.
- Check provenance, consistency, duplication, and stale information.
- Maintain indexes and run the existing maintenance routines.
- Preserve the distinction between verified facts, hypotheses, and proposed changes.

### Summarizer

- Produce concise summaries of tasks, findings, decisions, and unresolved issues.
- Help transfer important findings into the documentation workflow.
- Avoid treating unverified claims as established facts.

---

## 6. Establish Bernard's Learning and Documentation Workflow — ⬜

- [ ] Provide Bernard with an accurate infrastructure inventory and topology.
- [ ] Grant read-only access to the required infrastructure assets.
- [ ] Identify authoritative sources for each system.
- [ ] Create an inventory of missing documentation and knowledge gaps.
- [ ] Establish a standard procedure for recording discoveries and evidence.
- [ ] Have Bernard submit findings for Wiki Maintainer to organize and validate.
- [ ] Develop skills only where a repeatable procedure provides real value.
- [ ] Version-control approved documentation and skills through Git.
- [ ] Define how Mem0 stores useful context without replacing authoritative documentation.

**Priority:** Bernard must learn reliably, document correctly, and follow his instructions before being trusted with operational work.

---

## 7. Validate the Paperclip Work Model — ⬜

Define when to use:

- Issues and tasks.
- Projects.
- Workspaces and Workspace Changes.
- Artifacts.
- Git branches and pull requests.
- Wiki pages.
- Mem0.

Then test one complete workflow:

1. Headman assigns a documentation task.
2. Bernard investigates the infrastructure using read-only access.
3. Bernard records findings and supporting evidence.
4. Summarizer produces a concise report.
5. Wiki Maintainer validates and organizes the documentation.
6. Changes are committed to the development branch.
7. Headman coordinates the review and required approval.
8. The approved changes are merged into `main`.
9. The task is completed with links to the resulting documentation and commit.

Verify that each stage has a clear owner and that failed stages are visible rather than silently treated as successful.

---

## 8. Define Infrastructure Safety and Security — ⬜

- [ ] Keep Bernard read-only during the learning phase.
- [ ] Separate infrastructure access from GitHub write access.
- [ ] Apply least-privilege permissions.
- [ ] Keep credentials and secrets outside Git.
- [ ] Prevent agents from treating proposed changes as approved changes.
- [ ] Record the evidence and approval associated with consequential changes.
- [ ] Define backup and recovery expectations before introducing automation.

Any future permission to modify infrastructure must be introduced as a separate, explicitly approved phase.

---

## 9. Final Validation — ⬜

- [ ] Headman delegates a real infrastructure documentation task.
- [ ] Bernard investigates without modifying infrastructure.
- [ ] Bernard provides accurate findings with traceable evidence.
- [ ] Summarizer produces a useful report.
- [ ] Wiki Maintainer produces accurate, organized documentation.
- [ ] Git records the changes and preserves review history.
- [ ] The approval workflow prevents unauthorized promotion to `main`.
- [ ] Mem0 retains useful context without becoming the source of truth.
- [ ] All existing Wiki maintenance routines continue to work.
- [ ] Recovery from a bad documentation change is tested.
- [ ] No secrets or unintended runtime state enter GitHub.

---

## 10. Expand Only After Validation — ⬜

After the workflow passes its tests:

- [ ] Finalize Bernard's reusable infrastructure skills.
- [ ] Consider limited operational permissions through a separate approval process.
- [ ] Evaluate whether a dedicated VoIP Specialist is necessary.
- [ ] Add monitoring and maintenance automation incrementally.
- [ ] Establish the Power Platform space and its separate development workflow.
- [ ] Introduce a Power Platform Lead when that project begins.

Do not add agents or autonomous workflows merely to increase the agent count.

---

## Progress Summary

| Phase | Status |
|---|---|
| 1. Runtime and plugin verification | ✅ Complete |
| 2. Information architecture | ⬜ Next |
| 3. GitHub structure and permissions | ⬜ |
| 4. Wiki/Git integration | ⬜ |
| 5. Agent responsibilities and authority | ⬜ |
| 6. Bernard's learning workflow | ⬜ |
| 7. Paperclip workflow validation | ⬜ |
| 8. Safety and security | ⬜ |
| 9. End-to-end validation | ⬜ |
| 10. Operational expansion and Power Platform preparation | ⬜ |

### Immediate Next Step

**Finalize the Wiki information architecture and verify the actual Wiki-to-Git workflow before creating the repository.**

Once those decisions are clear, implement the Git structure and validate the documentation pipeline before expanding Bernard's access or responsibilities.