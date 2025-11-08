(function ($, logic) {
  "use strict";

  const Players = logic.Players;
  const HUMAN = Players.HUMAN;
  const AI = Players.AI;

  const state = {
    board: logic.createInitialState(),
    currentPlayer: HUMAN,
    pendingDice: [],
    diceRolled: [],
    turnCompletedDice: [],
    awaitingRoll: true,
    gameOver: false,
  };

  function randomDie() {
    return Math.floor(Math.random() * 6) + 1;
  }

  function rollDice() {
    const d1 = randomDie();
    const d2 = randomDie();
    state.diceRolled = [d1, d2];
    state.pendingDice = [d1, d2];
    state.turnCompletedDice = [];
    state.awaitingRoll = false;
    addMessage(`${state.currentPlayer} rolled ${d1} and ${d2}.`);
    renderDice();
  }

  function resetDice() {
    state.pendingDice = [];
    state.diceRolled = [];
    state.turnCompletedDice = [];
    state.awaitingRoll = true;
  }

  function addMessage(text) {
    const $log = $("#log");
    const logElement = $log.get(0);
    const previousScrollHeight = logElement ? logElement.scrollHeight : 0;
    const previousScrollTop = logElement ? $log.scrollTop() : 0;
    const timestamp = new Date().toLocaleTimeString();
    $("<div>", { class: "message", text: `[${timestamp}] ${text}` }).prependTo(
      $log
    );
    if (logElement) {
      const heightDelta = logElement.scrollHeight - previousScrollHeight;
      $log.scrollTop(previousScrollTop + heightDelta);
    }
  }

  function renderDice() {
    const $dice = $("#dice");
    $dice.empty();
    state.pendingDice.forEach((die, index) => {
      $("<div>", {
        class: "die",
        text: die,
        title: `Die ${index + 1}`,
      }).appendTo($dice);
    });
    if (state.pendingDice.length === 0 && !state.awaitingRoll) {
      $("<div>", { class: "die", text: "—" }).appendTo($dice);
    }
    $("#turn-indicator").text(
      state.gameOver ? "Game Over" : `${state.currentPlayer.toUpperCase()} Turn`
    );
  }

  function renderPoints() {
    $(".point").each(function renderPoint() {
      const pointNumber = Number($(this).data("point"));
      const point = state.board.points[pointNumber - 1];
      const $point = $(this);
      $point.empty();

      const aiLabel = $point.data("ai");
      if (aiLabel) {
        $("<div>", { class: "point-label top", text: aiLabel }).appendTo($point);
      }
      $("<div>", { class: "point-label bottom", text: pointNumber }).appendTo($point);

      const stack = $("<div>", { class: "checker-stack" }).appendTo($point);
      if (point && point.count > 0) {
        for (let i = 0; i < point.count; i += 1) {
          $("<div>", {
            class: `checker ${point.owner}`,
          }).appendTo(stack);
        }
      }
    });
  }

  function renderBar() {
    const humanStack = $("#human-bar");
    const aiStack = $("#ai-bar");
    humanStack.empty();
    aiStack.empty();

    for (let i = 0; i < state.board.bar[HUMAN]; i += 1) {
      $("<div>", { class: "checker human" }).appendTo(humanStack);
    }

    for (let i = 0; i < state.board.bar[AI]; i += 1) {
      $("<div>", { class: "checker ai" }).appendTo(aiStack);
    }
  }

  function renderBoard() {
    renderPoints();
    renderBar();
    renderDice();
  }

  function removeDieValue(die) {
    const index = state.pendingDice.indexOf(die);
    if (index === -1) {
      return false;
    }
    state.pendingDice.splice(index, 1);
    state.turnCompletedDice.push(die);
    renderDice();
    return true;
  }

  function maybePassAfterAction() {
    if (state.pendingDice.length === 0) {
      endTurn();
      return;
    }

    const remainingMoves = availableMovesForPlayer(state.pendingDice, HUMAN);
    if (remainingMoves.length === 0) {
      addMessage("No legal moves remain. Passing turn.");
      endTurn();
    }
  }

  function winCheck(player) {
    if (state.board.borneOff[player] >= logic.CHECKERS_PER_PLAYER) {
      state.gameOver = true;
      addMessage(`${player} wins!`);
      renderDice();
      return true;
    }
    return false;
  }

  function availableMovesForPlayer(dice, player) {
    return dice.flatMap((die) => logic.listLegalMoves(state.board, player, die));
  }

  function endTurn() {
    if (winCheck(state.currentPlayer)) {
      return;
    }

    resetDice();
    state.currentPlayer = logic.opposite(state.currentPlayer);
    renderBoard();

    if (state.currentPlayer === AI && !state.gameOver) {
      window.setTimeout(runAiTurn, 600);
    }
  }

  function ensureDiceAvailable() {
    if (state.awaitingRoll) {
      addMessage("Roll first (space).");
      return false;
    }
    if (state.pendingDice.length === 0) {
      addMessage("No dice left. End turn with space.");
      return false;
    }
    return true;
  }

  function performHumanMoveTo(targetPoint) {
    if (!ensureDiceAvailable()) {
      return;
    }

    const target = Number(targetPoint);
    if (!logic.isPointOpen(state.board, HUMAN, target)) {
      addMessage(`Point ${target} blocked.`);
      return;
    }

    if (state.board.bar[HUMAN] > 0) {
      const requiredDie = logic.entryDieForTarget(HUMAN, target);
      if (!removeDieValue(requiredDie)) {
        addMessage(`Need a ${requiredDie} to enter on ${target}.`);
        return;
      }
      logic.enterFromBar(state.board, target, HUMAN);
      addMessage(`Entered on point ${target}.`);
      renderBoard();
      maybePassAfterAction();
      return;
    }

    const dieIndex = state.pendingDice.findIndex((die) => {
      const origin = logic.computeOrigin(target, die, HUMAN);
      return withinBoard(origin) &&
        state.board.points[origin - 1].owner === HUMAN;
    });

    if (dieIndex === -1) {
      addMessage(`No human checker can land on ${target}.`);
      return;
    }

    const die = state.pendingDice[dieIndex];
    const origin = logic.computeOrigin(target, die, HUMAN);
    if (!removeDieValue(die)) {
      addMessage(`Die ${die} unavailable.`);
      return;
    }
    logic.moveChecker(state.board, origin, target, HUMAN);
    addMessage(`Moved from ${origin} to ${target}.`);
    renderBoard();
    maybePassAfterAction();
  }

  function withinBoard(point) {
    return point >= 1 && point <= logic.POINT_COUNT;
  }

  function performHumanBearOff(pointNumber) {
    if (!ensureDiceAvailable()) {
      return;
    }

    if (state.board.bar[HUMAN] > 0) {
      addMessage("Enter from the bar before bearing off.");
      return;
    }

    const point = Number(pointNumber);
    if (!withinBoard(point)) {
      addMessage("Point out of range.");
      return;
    }

    const requiredDie = logic.bearingDie(point, HUMAN);
    if (!removeDieValue(requiredDie)) {
      addMessage(`Need a ${requiredDie} to bear off from ${point}.`);
      return;
    }

    try {
      logic.bearOff(state.board, point, HUMAN);
      addMessage(`Borne off from point ${point}.`);
    } catch (error) {
      addMessage(error.message);
      state.pendingDice.push(requiredDie);
    }

    renderBoard();
    maybePassAfterAction();
  }

  function runAiTurn() {
    if (state.currentPlayer !== AI || state.gameOver) {
      return;
    }

    rollDice();

    const diceToPlay = [...state.pendingDice];
    diceToPlay.forEach((die) => {
      const available = logic.listLegalMoves(state.board, AI, die);
      if (available.length === 0) {
        addMessage(`AI passes on die ${die}.`);
        removeDieValue(die);
        return;
      }

      const choice = available[Math.floor(Math.random() * available.length)];
      logic.applyMove(state.board, choice, AI);
      removeDieValue(die);

      if (choice.kind === "enter") {
        addMessage(`AI enters on ${choice.target}.`);
      } else if (choice.kind === "move") {
        addMessage(`AI moves from ${choice.source} to ${choice.target}.`);
      } else {
        addMessage(`AI bears off from ${choice.source}.`);
      }
      renderBoard();
    });

    endTurn();
  }

  function processKey(event) {
    const key = event.key.toLowerCase();

    if (state.gameOver) {
      addMessage("Game over. Refresh to restart.");
      return;
    }

    if (state.currentPlayer !== HUMAN) {
      addMessage("Wait for the AI to finish.");
      return;
    }

    if (key === " ") {
      event.preventDefault();
      event.stopPropagation();

      if (!state.awaitingRoll) {
        if (state.pendingDice.length === 0) {
          addMessage("Turn passed to AI.");
          endTurn();
          return;
        }
        const remaining = availableMovesForPlayer(state.pendingDice, HUMAN);
        if (remaining.length === 0) {
          addMessage("No legal moves remain. Passing turn.");
          endTurn();
          return;
        }
        addMessage("Finish your dice before ending the turn.");
        return;
      }

      rollDice();

      const legal = availableMovesForPlayer(state.pendingDice, HUMAN);
      if (legal.length === 0) {
        addMessage("No legal moves, passing turn.");
        endTurn();
      }
      return;
    }

    if (key.startsWith("b")) {
      event.preventDefault();
      const point = key.slice(1);
      performHumanBearOff(point);
      return;
    }

    const digit = Number(key);
    if (Number.isInteger(digit) && withinBoard(digit)) {
      event.preventDefault();
      performHumanMoveTo(digit);
    }
  }

  function setupInitialMessages() {
    addMessage("Welcome to MINIGAM!");
    addMessage("Press space to roll and begin.");
  }

  function attachHandlers() {
    $(document).on("keydown", (event) => {
      if (event.target !== document.body) {
        return;
      }

      processKey(event);
    });
  }

  function renderInitialBoard() {
    renderBoard();
    setupInitialMessages();
    attachHandlers();
  }

  $(() => {
    renderInitialBoard();
  });
})(jQuery, window.MinigamLogic);

