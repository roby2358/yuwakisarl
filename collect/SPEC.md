This is a reinforcement learning experiment called "Collect".

# Tech stack
- python
- uv
- pygame
- Pufferfish AI Reinforcement Learning Framework

# Game

Play happens in real time, simultaneously.

The view is a playing field.
- The field dimensions are 200x200
- Field dimensions don't change.
- Each player, resource, or target occupy one cell.
- Only one thing can occupy a cell.

It is a grid of cells. On the field are
- six white diamonds indicating the players' positions
- fifteen yellow balls indicating the resources to collect
- a white open circle of the same size indicating the target where the resources will be placed

Each resource is placed randomly on the field.
After a resource is collected or dropped, it is placed again randomly on the field to maintain fifteen active resources.
The target is fixed at the center of the field (cell 100,100).

A player can move to any of the eight neighboring cells (including diagonals).
A player can hold at most one resource or be empty handed.
When holding a resource, a player can move it to the target.
When a player is in a cell adjacent to the target, it releases the resource and gains a reward.
- Score is simply +1 per resource, with no decay or penalties.
- Diagonals count. So all 8 cells diagonal to the target are good.
A player cannot move onto another player's cell. That player will lose its turn if it tries.
- If holding a resource, that resource will be released and placed randomly on the field.
- That's the full collision penalty.

The goal is simple: move to any resource, then move to the target for the reward.

After a time period of 3 minutes, the round ends and the highest scoring player is the winner.

There is a 10 second delay, then the next round starts scores rest to 0.

The human player may press
- space to pause
- enter to toggle player one (whichever that is) for keyboard control
- first escape key ends the current round
- second escape key exits the game.
- press escape once to end the round early, twice to exit the game

# Controls

There are two control modes:
- Keyboard control with Q W E A D Z X C (mapping to all 8 directions)
  - Only 1 player can use the keyboard controls, the rest are AI
  - All players may be AI
- AI control with Pufferfish AI Reinforcement Learning Framework
