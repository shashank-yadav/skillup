---
name: frontend
description: Strategies for implementing React components that pass Jest/React Testing Library tests.
---

# Frontend Development

Read the test file carefully -- it is the full spec. Implement exactly what
it renders, queries, and asserts: matching labels, button text, and success
or error messages verbatim. Respond with only the component code, no
explanation, no markdown code fences, no test code of your own.

## General Strategies

### Handling API Calls

*   **State Management:** Use `useState` to manage component state, including data fetched from APIs, loading states, and error messages.
*   **Fetching Data:** Use `useEffect` to perform data fetching when the component mounts or when dependencies change.
*   **Error Handling:** Implement `try...catch` blocks around `fetch` calls to gracefully handle network errors and non-OK HTTP responses. Display user-friendly error messages.
*   **Success Feedback:** Provide clear success messages to the user after a successful API operation.
*   **Request Body:** When sending data in the request body (e.g., for POST or PUT requests), ensure it's properly stringified using `JSON.stringify`.
*   **Form Data for File Uploads:** For file uploads, use `FormData` to construct the request body.

### User Interaction

*   **Event Handlers:** Attach event handlers (e.g., `onClick`, `onChange`) to interactive elements like buttons and input fields.
*   **Input Changes:** For input fields, update the component's state with the input's current value.
*   **Form Submission:** Use `onSubmit` for forms and prevent the default behavior to handle submission manually.
*   **Conditional Rendering:** Render UI elements based on the component's state (e.g., show loading indicators, error messages, or success messages).

### Test Interaction

*   **Querying Elements:** Use `screen.getByLabelText`, `screen.getByText`, `screen.getByPlaceholderText`, and `screen.getByTestId` to find elements in the DOM.
*   **Simulating Events:** Use `fireEvent` to simulate user interactions like `change` and `click`.
*   **Asynchronous Operations:** Wrap asynchronous operations within `act` to ensure React updates are processed correctly before assertions.
