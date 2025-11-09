"use strict";

const { strict: assert } = require("node:assert");
const test = require("node:test");

const logic = require("../../resources/public/game_logic.js");
const Dice = require("../../resources/public/dice.js");
const gameState = require("../../resources/public/game_state.js");

test("createGameState seeds baseline fields", () => {
  const dice = new Dice(() => 1);
  const state = gameState.createGameState(logic, dice, logic.Players.HUMAN);

  assert.equal(state.currentPlayer, logic.Players.HUMAN);
  assert.equal(state.gameOver, false);
  assert.equal(state.awaitingRoll, true);
  assert.strictEqual(state.pendingDice, dice.pending);
  assert.equal(state.board.points.length, logic.POINT_COUNT);
});

test("resetGameState clears progress and rebinds dice collections", () => {
  const dice = new Dice(() => 3);
  const state = gameState.createGameState(logic, dice, logic.Players.HUMAN);

  dice.roll();
  state.board.points[0] = { owner: logic.Players.HUMAN, count: 2 };
  state.currentPlayer = logic.Players.AI;
  state.gameOver = true;
  state.turnSnapshot = { mock: true };

  gameState.resetGameState(state, logic, dice, logic.Players.HUMAN);

  assert.equal(state.currentPlayer, logic.Players.HUMAN);
  assert.equal(state.gameOver, false);
  assert.equal(state.pendingDice.length, 0);
  assert.equal(state.awaitingRoll, true);
  assert.equal(state.turnSnapshot, null);
  assert.strictEqual(state.pendingDice, dice.pending);
  assert.strictEqual(state.diceRolled, dice.rolled);
});

test("isRestartKey identifies supported keys", () => {
  assert.equal(gameState.isRestartKey(" "), true);
  assert.equal(gameState.isRestartKey("Spacebar"), true);
  assert.equal(gameState.isRestartKey("spacebar"), true);
  assert.equal(gameState.isRestartKey("Space"), false);
  assert.equal(gameState.isRestartKey("Enter"), false);
  assert.equal(gameState.isRestartKey(null), false);
});


