---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

Observe the environment carefully before taking actions.

## Insights

- If a required object is not visible in the initial observation, search receptacles like cabinets, drawers, shelves, or containers.
- To apply a state change (heat, cool, clean) to an object, you must first have the object in your inventory and then go to the appropriate appliance (microwave, fridge, sink).
- When a task requires putting an object in a specific location, you must first obtain the object, then go to that location, and use the 'move' command.
- If an object is not in the initial observation, systematically search visible surfaces (countertops, tables, shelves) before opening closed receptacles.
- When a task requires an object with a specific property (hot, clean, cool), first locate the object, then apply the state change, then move it to the target location.
- When a task requires using a specific appliance (e.g., desklamp, microwave), you must first locate that appliance and then use the 'use' command on it.
- If a required object is not found in the initial search, systematically check all visible surfaces and receptacles, using 'examine' to get detailed contents of each location.
- For tasks requiring an object to be placed in a specific container (e.g., drawer, cabinet, fridge), you must first open the container if it is closed, then move the object into it.
