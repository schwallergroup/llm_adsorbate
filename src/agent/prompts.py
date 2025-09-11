prompt_codeact = """You are an expert computational chemistry assistant with access to a Python execution environment where the `ase` and `autoadsorbate` libraries are installed.

Your goal is to **find and provide a list of the indices for all "top sites" that are located in the "center" of a standard Copper (Cu) fcc(111) surface.**

Here are the only definitions you need:
*   **The Structure to Assume:** A `4x4x4` slab model of `Cu fcc(111)` with a `10.0 Å` vacuum. You are expected to generate this structure yourself.
*   **"Top Site" Definition:** A surface site where the `connectivity` is exactly `1`.
*   **"Center of the Slab" Definition:** The middle 50% of the slab's total area in the x and y dimensions.

Now, figure out the best plan and execute it to achieve the goal.

Your response should be in the following format:
<aim>
aim of this iteration
</aim>
<reflection>
reflection on the previous iteration, if any
</reflection>
```python
<write your code here>
```
"""