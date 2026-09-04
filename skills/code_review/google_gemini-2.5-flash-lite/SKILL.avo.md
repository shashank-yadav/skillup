---
name: code_review
description: Strategies for writing useful, accurate code review comments on a diff.
---

# Code Review

Read the diff and write a single, specific review comment about the
most important real issue, if there is one -- no preamble, no generic
praise, no restating what the diff does.

## Insights

- When a function's signature specifies a type for a parameter, avoid using a more general type hint like `Any` if a more specific type is known and enforced by the function's logic.
- When adding new exception handling, ensure that more specific exceptions are caught before more general ones to avoid unintended behavior.
- When a function signature specifies a type for a parameter, avoid adding redundant type checks within the function body.
