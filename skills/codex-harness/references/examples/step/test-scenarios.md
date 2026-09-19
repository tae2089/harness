# Work Scenario Checks

Use the behavioral matrix in ../../skill-testing-guide.md.

For each example, verify normal execution, interruption/resume, and a rejected output. Assert that:
- work selection respects existing/new/no-issue intent;
- resumption compares work-record claims against actual artifacts;
- workers return results directly and only the main updates progress;
- failed verification remains visible;
- issue closure requires user instruction;
- no local execution-state files are prerequisites.

Use isolated projects and mocked publication tools unless live writes are authorized. Distinguish observed behavior from static policy inspection.
