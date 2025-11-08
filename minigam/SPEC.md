# SPECIFICATION

## Tech stack
The game will be built on the following tech stack
- Javascript
- jquery
- html, js, css files under resources/public
- uv
- FastAPI
  - Only serves static html, js, css
  - Later the js will make websocket calls to the server for AI moves
- later, ML libraries
  - Not yet. For now the python only serves static content.

## Aesthetic

Cool, clear colors.

## Rules

See MINIGAM.md

### Board

The UI MUST be rendered in this form (in graphics, not as ascii):

```text
+-+------[6 1]---+--+
+--+             +--+
+--+ | | | | | | +--+
+--+ | | | | | | +--+
+XX+ | | | | | | +O-+
+XX+ | | O | | | +OO+
+XX+ | X O | X O +OO+
+-+--1-2-3-4-5-6-+--+
+[messages]-^v------+
```

Checkers that have borne off are not displayed.

### Keyboard Input

Character input during the AI turn are ignored.
Space to roll on your turn
1-6 to enter a checker from the bar
Consecutive key presses move or bear off. Any unrecognized characters are ignored.
b + 1-6 to bear a checker off from that point
m + 1-6 + 1-6 to move a checker from the first point to the second point
Space again restores dice and board state for the current turn. Messages remain but an "reset" message appears.
Invalid moves are reported in messages.

A digit always means “move or enter to that exact destination point,” and b1-6 always means “bear off from point N.”

Bear-off commands consume the exact die matching the distance when available. If no exact die is present, and the player has no checkers on the bar, a higher die may be used to bear off the checker farthest back (closest to bearing off: highest-numbered for the human, lowest-numbered for the AI).
If an exact die exists it must be taken before using a higher die.

In each case, the "first" checker moves. From the bar, it's the "first" checker on the
bar (they are really more of a count). From a made point it's the "top" checker. When
a blot moves, it's just that checker.

The points are numbered, so the human player moves from bar -> 1 -> 6 -> bear off.

The second player will always be AI and move directly from bar -> 6 -> 1 -> bear off.

### AI (Initial)

- Roll
- Generate all possible moves
- Randomly choose one, or pass if none
- Generate all possible moves with the next die
- Randomly choose one, or pass if none
