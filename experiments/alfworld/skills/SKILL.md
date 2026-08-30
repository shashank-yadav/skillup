---
name: alfworld
description: Strategies for completing interactive household tasks in ALFWorld.
---

# ALFWorld

Complete the requested household task efficiently.

## General Strategies

1.  **Locate the target object:** Before interacting with an object, first navigate to its location.
2.  **Interact with containers:** If an object is inside a container (e.g., cabinet, drawer, fridge), open the container first.
3.  **Handle state changes:** If an object needs to be cleaned or heated, perform that action before moving it to its final destination.
4.  **Move objects:** Use the `move <object> to <location>` action to place items.
5.  **Examine for information:** Use `examine <object>` to understand its properties or contents.
6.  **Check inventory:** Use `inventory` to see what items you are currently carrying.
7.  **Be thorough:** If an object is not found in an expected location, explore other potential locations.
8.  **Close containers:** After interacting with a container, close it if it is open.

## Specific Actions

### Navigation

*   `go to <location>`: Move to a specific location.

### Object Interaction

*   `take <object> from <location>`: Pick up an object.
*   `move <object> to <location>`: Place an object in a location.
*   `open <container>`: Open a container.
*   `close <container>`: Close a container.
*   `clean <object> with <location>`: Clean an object using a sink or basin.
*   `heat <object> with <appliance>`: Heat an object using an appliance like a microwave.
*   `examine <object>`: Get more information about an object.

### State Management

*   `inventory`: Check the items currently being carried.
