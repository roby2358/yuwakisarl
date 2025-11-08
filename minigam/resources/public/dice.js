(function initDiceModule(global) {
  "use strict";

  const MIN_VALUE = 1;
  const MAX_VALUE = 6;

  function isValidDie(value) {
    return Number.isInteger(value) && value >= MIN_VALUE && value <= MAX_VALUE;
  }

  function expandedRoll(first, second) {
    if (!isValidDie(first) || !isValidDie(second)) {
      throw new Error("Invalid die value");
    }
    if (first === second) {
      return [first, first, first, first];
    }
    return [first, second];
  }

  function clearAndFill(target, values) {
    target.length = 0;
    target.push(...values);
  }

  class Dice {
    constructor(randomGenerator) {
      if (typeof randomGenerator !== "function") {
        throw new Error("Random generator function required");
      }
      this.randomGenerator = randomGenerator;
      this.pending = [];
      this.rolled = [];
      this.completed = [];
      this.awaitingRoll = true;
    }

    roll() {
      const first = this.randomGenerator();
      const second = this.randomGenerator();
      const values = expandedRoll(first, second);
      clearAndFill(this.pending, values);
      clearAndFill(this.rolled, values);
      this.completed.length = 0;
      this.awaitingRoll = false;
      return [...values];
    }

    reset() {
      this.pending.length = 0;
      this.rolled.length = 0;
      this.completed.length = 0;
      this.awaitingRoll = true;
    }

    hasPending() {
      return this.pending.length > 0;
    }

    consume(value) {
      if (!isValidDie(value)) {
        return null;
      }
      const index = this.pending.indexOf(value);
      if (index === -1) {
        return null;
      }
      const [removed] = this.pending.splice(index, 1);
      this.completed.push(removed);
      return { value: removed, index };
    }

    returnValue(entry) {
      if (!entry || !isValidDie(entry.value)) {
        return;
      }
      const completedIndex = this.completed.lastIndexOf(entry.value);
      if (completedIndex !== -1) {
        this.completed.splice(completedIndex, 1);
      }
      const targetIndex =
        Number.isInteger(entry.index) && entry.index >= 0
          ? Math.min(entry.index, this.pending.length)
          : this.pending.length;
      this.pending.splice(targetIndex, 0, entry.value);
    }

    snapshot() {
      return {
        pending: [...this.pending],
        rolled: [...this.rolled],
        completed: [...this.completed],
        awaitingRoll: this.awaitingRoll,
      };
    }

    restore(snapshot) {
      if (!snapshot) {
        this.reset();
        return;
      }

      const { pending, rolled, completed, awaitingRoll } = snapshot;
      if (
        !Array.isArray(pending) ||
        !Array.isArray(rolled) ||
        !Array.isArray(completed) ||
        typeof awaitingRoll !== "boolean"
      ) {
        this.reset();
        return;
      }

      clearAndFill(this.pending, pending);
      clearAndFill(this.rolled, rolled);
      clearAndFill(this.completed, completed);
      this.awaitingRoll = awaitingRoll;
    }
  }

  Dice.MIN_VALUE = MIN_VALUE;
  Dice.MAX_VALUE = MAX_VALUE;
  Dice.expandedRoll = expandedRoll;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = Dice;
  }

  if (global) {
    global.MinigamDice = Dice;
  }
})(typeof window !== "undefined" ? window : globalThis);


