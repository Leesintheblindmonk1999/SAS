# Contributing to SAS

Thank you for your interest in improving **SAS - Symbiotic Autoprotection System**.

SAS is an open-source research and engineering project focused on structural coherence auditing for generative AI systems.

## Code of Conduct

By participating in this project, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before opening a bug report:

1. Check whether the issue already exists in [GitHub Issues](https://github.com/Leesintheblindmonk1999/SAS/issues).
2. Use the **Bug Report** template.
3. Include clear steps to reproduce the problem.
4. Include logs, payloads, and environment details when possible.

### Suggesting Enhancements

For feature requests:

1. Use the **Feature Request** template.
2. Explain the use case.
3. Describe the expected behavior.
4. Include examples when possible.

### Pull Requests

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/amazing-feature
```

3. Make your changes.
4. Run tests:

```bash
pytest tests/
```

5. Commit with a clear message:

```bash
git commit -m "feat: add something useful"
```

6. Push your branch:

```bash
git push origin feature/amazing-feature
```

7. Open a Pull Request.

## Development Setup

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

## Code Style

Please follow these guidelines:

- Follow PEP 8.
- Use type hints for function signatures.
- Add docstrings for public functions.
- Keep functions focused and small.
- Avoid changing core detection behavior unless the change is explicitly documented.
- Write tests for new features.
- Keep experimental modules optional and clearly labeled.

## Testing

Run all tests:

```bash
pytest
```

Run a specific test file:

```bash
pytest tests/test_detector.py
```

Run the benchmark:

```bash
python tests/benchmark_runner.py
```

## Core Integrity Rules

When contributing to SAS, do not change the following without explicit discussion:

- `κD = 0.56`
- ISI scoring semantics
- TDA core behavior
- NIG behavior
- E9-E12 penalty semantics
- API response fields used by existing clients

If a change affects benchmark results, include before/after evidence.

## License

By contributing, you agree that your contributions will be licensed under:

```text
GPL-3.0 + Durante Invariance License
```

The Durante Invariance License requires attribution to **Gonzalo Emir Durante** for the discovery and use of `κD = 0.56` in semantic invariance detection, hallucination detection, or similar purposes.