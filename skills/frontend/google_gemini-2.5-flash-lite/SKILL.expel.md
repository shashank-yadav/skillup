---
name: frontend
description: Strategies for implementing React components that pass Jest/React Testing Library tests.
---

# Frontend Development

Read the test file carefully -- it is the full spec. Implement exactly what
it renders, queries, and asserts: matching labels, button text, and success
or error messages verbatim. Respond with only the component code, no
explanation, no markdown code fences, no test code of your own.

## Insights

- When making API calls, ensure that the correct HTTP method (POST, GET, PUT, DELETE) is used based on the operation being performed.
- When handling form submissions, prevent the default browser behavior to avoid page reloads.
- When making API calls, include relevant data in the request body for POST and PUT requests.
- When making API calls, handle different HTTP status codes (e.g., 200, 201, 204, 400, 403, 404, 500) to provide appropriate user feedback or error messages.
- When making API calls, ensure that the request body is correctly formatted (e.g., JSON) when required by the API.
