---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

Observe the environment carefully before taking actions.

## Insights

- If the task requires an object with a property (e.g., hot, clean, cool), first find the object, then apply the property-changing action using the appropriate appliance (e.g., microwave for heating, sink for cleaning, fridge for cooling).
- When searching for an object, systematically examine containers (like cabinets, drawers, fridge) and surfaces (like countertops, tables, shelves) in the environment, using 'look' or 'examine' to see their contents.
- When the task requires finding multiple instances of an object (e.g., 'two pencil'), search systematically across all containers and surfaces, and continue searching after finding the first instance until the required number is collected.
