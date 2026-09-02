---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

## General Strategies

### Locating and Interacting with Objects

*   **Explore systematically:** When an object is not immediately visible, systematically explore containers (drawers, cabinets, fridges) and surfaces.
*   **Use `examine` and `look`:** Use `examine` on specific objects to understand their state or contents. Use `look` to get a general sense of the surroundings.
*   **Open and close containers:** To access items within containers, use `open [container]` and `close [container]`.
*   **Take and move objects:** Use `take [object] from [location]` to pick up an item and `move [object] to [location]` to place it.
*   **Check inventory:** Use `inventory` to see what items the agent is currently carrying.

### Object Manipulation and State Changes

*   **Cleaning:** Use `clean [object] with [cleaning_tool/location]` to clean an item.
*   **Heating/Cooling:** Use `heat [object] with [appliance]` or `cool [object] with [appliance]` to change an item's temperature.
*   **Using appliances:** Some tasks require using appliances like microwaves or toasters.

### Task Completion

*   **Follow task instructions precisely:** Ensure all parts of the task are addressed (e.g., "clean and put").
*   **Verify completion:** After performing an action, use `examine` on the target location or object to confirm the task is complete.

## Common Pitfalls and How to Avoid Them

*   **Missing objects:** If an object is not found in an expected location, try searching other nearby containers or surfaces.
*   **Incorrect appliance usage:** Ensure the correct appliance is used for heating or cooling.
*   **Redundant actions:** Avoid repeatedly performing the same action if it doesn't change the state or progress the task. For example, if an object is already in the desired location, do not repeatedly move it there.
*   **Not opening containers:** Ensure containers are opened before attempting to interact with items inside them.
*   **Forgetting to take items:** Before moving an item to a new location, ensure it has been picked up using the `take` command.
*   **Ignoring object states:** Pay attention to object states (e.g., "clean," "hot," "cold") as they may be relevant to the task.
*   **Over-reliance on `examine`:** While `examine` is useful, sometimes a simple `look` is sufficient to understand the environment.
*   **Incorrectly using `move`:** The `move` command is for placing items, not for picking them up. Use `take` to pick up items.
*   **Not closing containers:** After interacting with a container, it's often good practice to close it.
