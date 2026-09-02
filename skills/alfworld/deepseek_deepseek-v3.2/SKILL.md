---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

Observe the environment carefully before taking actions.

## General Strategies

1. **Interpret the task.** Identify the required object(s), any required state changes (e.g., heat, cool, clean), and the target location.
2. **Search systematically.** If the needed object is not immediately visible, search likely containers (fridge, cabinets, drawers, shelves) and surfaces (countertops, tables). Use `examine` to see contents of open containers.
3. **Acquire the object first.** Before modifying an object (heating, cooling, cleaning), you must be holding it. Take it from its current location.
4. **Use the correct appliance.** For heating, use the microwave (or stove). For cooling, use the fridge. For cleaning, use the sinkbasin.
5. **Verify state changes.** After using an appliance, `examine` the object to confirm its new state (e.g., "hot", "cold", "clean").
6. **Complete the delivery.** After the object is in the correct state, go to the target location and `move` the object there.
7. **Avoid loops.** If you are repeating actions without progress (e.g., opening/closing the same container, examining the same object), you are stuck. Reassess the situation: Do you have the correct object? Is it in the required state? Is the target location correct?
8. **For "look at X under the desklamp" or "examine X with the desklamp" tasks:** You must first be holding the object, then `use desklamp 1`. The task completes after using the desklamp.
9. **For "find two X and put them in Y" tasks:** You must locate and move two instances of the object. Pick up one, move it to the target, then repeat for the second.
10. **Keep inventory light.** If you pick up an unrelated object, drop it or put it aside to avoid confusion. Use `inventory` to check what you are carrying.
