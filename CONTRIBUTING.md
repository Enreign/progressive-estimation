# Contributing to Progressive Estimation

Thanks for your interest in improving Progressive Estimation. This guide covers how to contribute effectively.

## Ways to Contribute

### Calibration Data

The most valuable contribution is real-world calibration data. Share anonymized estimated vs. actual results to help improve default ratios.

Format your data as described in [references/calibration.md](references/calibration.md) — we need at minimum:
- Task complexity (S/M/L/XL)
- Task type
- PERT expected value
- Actual effort
- Notes on surprises or deviations

### Formula Improvements

Changes to formulas, multipliers, or lookup tables in [references/formulas.md](references/formulas.md) require:
- Research citation or empirical data supporting the change
- Before/after comparison using at least 3 of the [eval cases](evals/)
- Explanation of why the current value is wrong

### Tracker Mappings

Adding support for new trackers (Asana, Notion, Shortcut, etc.):
- Add native and embedded mappings to [references/output-schema.md](references/output-schema.md)
- Follow the existing format (canonical field → tracker field → notes)
- Test with actual tracker if possible

### Task Types

Proposing new task type multipliers:
- Describe the type of work and what overhead it includes
- Suggest a multiplier with justification
- Provide at least 2 reference examples

### Evals

Additional test cases are always welcome, especially:
- Edge cases (very small tasks, very large tasks)
- Uncommon task types
- Multi-team scenarios
- Batch with complex dependency graphs

## Development Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run all 4 eval files to check for regressions
5. Submit a pull request

## Pull Request Guidelines

- Keep PRs focused — one change per PR
- Include before/after eval results for formula changes
- Update relevant wiki pages if behavior changes
- Reference any related issues

## Eval Verification

Before submitting formula or workflow changes, run these evals and include the results:

```
evals/eval-quick.md        Quick path smoke test
evals/eval-hybrid.md       Detailed path, multi-team
evals/eval-batch.md        Batch with dependencies
evals/eval-regression.md   6 baseline cases
```

An estimate is a regression if it falls outside the expected ranges documented in each eval file.

## Reporting Issues

When reporting a bug or inaccurate estimate:
- Include the task description you estimated
- Include the full output (summary + breakdown)
- Note what you expected vs. what you got
- If you have actuals, include them

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
