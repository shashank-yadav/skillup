---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

Observe the environment carefully before taking actions.


## General Strategies

1. **Prioritize task-relevant locations**: If the task involves a specific object property (e.g., "clean", "hot", "cool"), go directly to the relevant appliance (e.g., sinkbasin, microwave, fridge) or container where the object is likely stored.

2. **Use `look` and `examine` strategically**: After moving to a new location, use `look` to scan surroundings. Use `examine` on containers (cabinets, drawers, fridge) to check contents. Avoid redundant `look` or `examine` actions once the state is known.

3. **Minimize backtracking**: Plan the sequence of actions to reduce unnecessary travel. For example, pick up the object, perform required transformations (clean, heat, cool), then deliver to target location in one continuous path.

4. **Handle multi-object tasks efficiently**: For tasks requiring two of an object, retrieve one at a time. After placing the first, return to the last known location where the object was found or systematically search likely locations.

5. **Use appliances correctly**: 
   - To clean: use `clean [object] with sinkbasin`.
   - To heat: use `heat [object] with microwave`.
   - To cool: use `cool [object] with fridge`.
   - Always open containers (fridge, microwave, cabinets, drawers) before interacting with contents.

6. **For "under desklamp" tasks**: 
   - First, go to the location with the desklamp.
   - Use `use desklamp` to turn it on.
   - Then retrieve the target object (often from elsewhere) and examine or interact with it under the light.

7. **Avoid infinite loops**: If the same observation repeats, do not repeat the same action. Instead, re-evaluate the environment and try a different location or action.

8. **Inventory management**: Pick up objects before moving them. Ensure you are carrying the correct object before proceeding to the next step.

9. **Verify object state**: After transformation (cleaning, heating, cooling), proceed directly to the goal location. Do not re-examine unless the task explicitly requires inspection.

10. **Systematic search**: If an object is not found in one container, check others of the same type (e.g., all cabinets or drawers), but avoid revisiting empty ones repeatedly.
