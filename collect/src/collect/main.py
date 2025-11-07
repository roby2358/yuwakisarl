"""Entry point for the Collect game."""

from __future__ import annotations

from .game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

