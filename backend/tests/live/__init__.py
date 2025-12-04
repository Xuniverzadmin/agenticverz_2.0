# tests/live/__init__.py
"""
Live Integration Tests

These tests make REAL API calls to external services.
Only run in secure CI environments with proper credentials.

Environment variables:
- ANTHROPIC_API_KEY: For Claude API tests
- OPENAI_API_KEY: For OpenAI API tests (future)
- SKIP_LIVE_TESTS: Set to "true" to skip all live tests
"""
