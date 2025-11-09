"use strict";

(function initGameStateModule(globalObject) {
  const DEFAULT_SPACE_KEY = " ";
  const SPACEBAR_KEY = "spacebar";

  function validateLogic(logic) {
    if (!logic || typeof logic.createInitialState !== "function") {
      throw new Error("Logic module missing createInitialState.");
    }
    if (typeof logic.POINT_COUNT !== "number") {
      throw new Error("Logic module missing POINT_COUNT.");
    }
    if (!logic.Players || typeof logic.Players.HUMAN === "undefined") {
      throw new Error("Logic module missing Players definition.");
    }
  }

  function validateDice(dice) {
    if (!dice || !Array.isArray(dice.pending)) {
      throw new Error("Dice instance missing pending dice.");
    }
    if (!Array.isArray(dice.rolled) || !Array.isArray(dice.completed)) {
      throw new Error("Dice instance missing roll tracking.");
    }
    if (typeof dice.reset !== "function") {
      throw new Error("Dice instance missing reset.");
    }
  }

  function ensureState(state) {
    if (!state) {
      throw new Error("State object required.");
    }
  }

  function createGameState(logic, dice, humanPlayer) {
    validateLogic(logic);
    validateDice(dice);
    if (typeof humanPlayer === "undefined") {
      throw new Error("Human player identifier required.");
    }

    return {
      board: logic.createInitialState(),
      currentPlayer: humanPlayer,
      pendingDice: dice.pending,
      diceRolled: dice.rolled,
      turnCompletedDice: dice.completed,
      awaitingRoll: dice.awaitingRoll,
      gameOver: false,
      turnSnapshot: null,
    };
  }

  function resetGameState(state, logic, dice, humanPlayer) {
    ensureState(state);
    validateLogic(logic);
    validateDice(dice);
    if (typeof humanPlayer === "undefined") {
      throw new Error("Human player identifier required.");
    }

    dice.reset();
    state.board = logic.createInitialState();
    state.currentPlayer = humanPlayer;
    state.pendingDice = dice.pending;
    state.diceRolled = dice.rolled;
    state.turnCompletedDice = dice.completed;
    state.awaitingRoll = dice.awaitingRoll;
    state.gameOver = false;
    state.turnSnapshot = null;
  }

  function isRestartKey(keyValue) {
    if (typeof keyValue !== "string") {
      return false;
    }
    if (keyValue === DEFAULT_SPACE_KEY) {
      return true;
    }
    return keyValue.toLowerCase() === SPACEBAR_KEY;
  }

  const api = {
    createGameState,
    resetGameState,
    isRestartKey,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  if (globalObject) {
    globalObject.MinigamGameState = api;
  }
})(typeof window !== "undefined" ? window : globalThis);


