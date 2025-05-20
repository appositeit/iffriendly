# Implementation Plan: iffriendly

## 1. Planning and Preparation

1.1 Review project overview and requirements
1.2 Confirm and document directory structure
1.3 Identify and evaluate existing libraries/tools (e.g., pyroute2, mac-vendor-lookup)
1.4 Set up local git repository if not already present
1.5 Establish initial development and testing environment (Python venv, requirements)

## 2. Core Library Development

2.1 Library Scaffolding
  2.1.1 Create initial Python package structure in `src/iffriendly/`
  2.1.2 Add `__init__.py` and core module files
  2.1.3 Set up Pydantic models for interface metadata

2.2 Interface Discovery
  2.2.1 Implement `get_interface_list()`
  2.2.2 Gather system interface names and low-level info (device path, MAC, IP)
  2.2.3 Integrate pyroute2 or similar for robust interface enumeration

2.3 Metadata Enrichment
  2.3.1 Implement OUI lookup for manufacturer info (mac-vendor-lookup)
  2.3.2 Add heuristics for connection method (internal PCIe, USB, Bluetooth, etc.)
  2.3.3 Use udevadm, lsusb, lspci for additional metadata
  2.3.4 Generate friendly, human-readable names

2.4 Extensibility and Integration
  2.4.1 **[Complete]** Designed for easy addition of new metadata sources/heuristics (register_enricher implemented and tested)
  2.4.2 **[Complete]** Output remains a dict suitable for UI consumption

## 3. Testing

3.1 Unit Testing
  3.1.1 Write unit tests for each module and function
  3.1.2 Achieve at least 80% test coverage

3.2 Integration Testing
  3.2.1 Test full interface discovery and metadata enrichment pipeline

3.3 Automation
  3.3.1 Create scripts for running all tests
  3.3.2 Integrate with Taskfile for unified task management

## 4. Documentation

4.1 Project Overview (see `doc/project_overview.md`)
4.2 Implementation Plan (this document)
4.3 Progress Updates
  4.3.1 Write timestamped progress reports in `doc/progress/`
  4.3.2 Reference implementation plan sections in each update
  4.3.3 Update this plan as work proceeds and requirements evolve
4.4 API Documentation
  4.4.1 Document all public functions and models

## 5. Version Control and Branching

5.1 Use git for all version control
5.2 Commit all changes before major revisions
5.3 Use branches for major features or refactors

## 6. Scripts and Tooling

6.1 Wrapper scripts for recurring processes (e.g., test runner, venv setup)
6.2 Ensure all scripts are in `bin/` or appropriate subdirectories

## 7. Logging and Debugging

7.1 Set up logging for library and scripts
7.2 Ensure logs are timestamped and symlinked to latest
7.3 Add log rotation/cleanup as needed

## 8. Future Work

8.1 Plan for JavaScript library for UI hovercards
8.2 Extend metadata and heuristics as new use cases arise

---

**Progress Tracking:**
- Each progress update should reference the relevant section(s) of this plan.
- This plan should be updated as tasks are completed or requirements change.

**Next Steps:**
- 4.x: Review and update documentation, API docs, and usage examples
- 6.x: Prepare scripts/tooling for packaging and integration 