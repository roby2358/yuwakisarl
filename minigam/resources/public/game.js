(function ($, logic, moveFormatter, Dice) {
  "use strict";

  const Players = logic.Players;
  const HUMAN = Players.HUMAN;
  const AI = Players.AI;

  const gameStateTools = window.MinigamGameState;
  if (!gameStateTools) {
    throw new Error("Game state helpers unavailable.");
  }

  const DIGIT_KEYS = new Set(["1", "2", "3", "4", "5", "6"]);

  function isDigitKey(key) {
    return DIGIT_KEYS.has(key);
  }

  class InputStateMachine {
    constructor(actions) {
      this.actions = actions;
      this.mode = "await_roll";
      this.origin = null;
    }

    transitionToAwaitRoll() {
      this.mode = "await_roll";
      this.origin = null;
    }

    transitionToPrimary() {
      this.mode = "await_command";
      this.origin = null;
    }

    startBear() {
      this.mode = "await_bear_point";
      this.origin = null;
    }

    startMove() {
      this.mode = "await_move_origin";
      this.origin = null;
    }

    storeOrigin(digit) {
      this.origin = digit;
      this.mode = "await_move_target";
    }

    clearActiveCommand() {
      if (this.mode === "await_command") {
        return;
      }
      if (this.mode === "await_roll") {
        this.origin = null;
        return;
      }
      this.transitionToPrimary();
    }

    handleSpace(event) {
      event.preventDefault();
      event.stopPropagation();

      if (this.mode === "await_roll") {
        this.actions.onRoll();
        return;
      }

      if (!this.actions.hasPendingDice()) {
        this.actions.onPassTurn();
        return;
      }

      this.actions.onResetTurn();
      this.transitionToPrimary();
    }

    handlePrimaryDigit(event, digit) {
      event.preventDefault();
      if (this.actions.hasBarCheckers()) {
        this.actions.onEnter(digit);
        return;
      }
      this.actions.onRequireCommand();
    }

    handle(event) {
      const rawKey = event.key;
      if (!rawKey || rawKey.length === 0) {
        return;
      }

      if (rawKey === "Escape" || rawKey === "Esc") {
        event.preventDefault();
        event.stopPropagation();
        if (this.actions.onForcePass) {
          this.actions.onForcePass();
        }
        return;
      }

      const key = rawKey.toLowerCase();

      if (key === " ") {
        this.handleSpace(event);
        return;
      }

      if (this.mode === "await_roll") {
        if (isDigitKey(key) || key === "b" || key === "m") {
          this.actions.onPromptRoll();
        }
        return;
      }

      if (this.mode === "await_command") {
        if (key === "b") {
          event.preventDefault();
          this.startBear();
          return;
        }
        if (key === "m") {
          event.preventDefault();
          this.startMove();
          return;
        }
        if (isDigitKey(key)) {
          this.handlePrimaryDigit(event, Number(key));
        }
        return;
      }

      if (this.mode === "await_bear_point") {
        if (isDigitKey(key)) {
          event.preventDefault();
          this.actions.onBear(Number(key));
          this.transitionToPrimary();
          return;
        }
        if (key === "m") {
          event.preventDefault();
          this.startMove();
          return;
        }
        if (key === "b") {
          event.preventDefault();
          return;
        }
        return;
      }

      if (this.mode === "await_move_origin") {
        if (isDigitKey(key)) {
          event.preventDefault();
          this.storeOrigin(Number(key));
          return;
        }
        if (key === "b") {
          event.preventDefault();
          this.startBear();
          return;
        }
        if (key === "m") {
          event.preventDefault();
          return;
        }
        return;
      }

      if (this.mode === "await_move_target") {
        if (isDigitKey(key)) {
          event.preventDefault();
          const origin = this.origin;
          this.transitionToPrimary();
          this.actions.onMove(origin, Number(key));
          return;
        }
        if (key === "m") {
          event.preventDefault();
          this.startMove();
          return;
        }
        if (key === "b") {
          event.preventDefault();
          this.startBear();
          return;
        }
      }
    }
  }

  let inputMachine;
  let boardSerializer;
  const dice = new Dice(() => Math.floor(Math.random() * 6) + 1);

  const state = gameStateTools.createGameState(logic, dice, HUMAN);

  function rollDice() {
    const rolledValues = dice.roll();
    state.awaitingRoll = dice.awaitingRoll;
    if (inputMachine) {
      inputMachine.transitionToPrimary();
    }
    if (state.currentPlayer === HUMAN) {
      state.turnSnapshot = {
        board: logic.cloneState(state.board),
        dice: dice.snapshot(),
      };
    } else {
      state.turnSnapshot = null;
    }
    const rollDescription = rolledValues.join(", ");
    addMessage(`${state.currentPlayer} rolled ${rollDescription}.`);
    renderDice();
  }

  function resetDice() {
    dice.reset();
    state.awaitingRoll = dice.awaitingRoll;
    if (inputMachine) {
      inputMachine.transitionToAwaitRoll();
    }
    renderDice();
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
    renderTurnIndicator();
  }

  function renderPoints() {
    $(".point").each(function renderPoint() {
      const pointNumber = Number($(this).data("point"));
      const point = state.board.points[pointNumber - 1];
      const $point = $(this);
      $point.empty();

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

  function summarizeHumanMoves() {
    if (state.currentPlayer !== HUMAN) {
      return null;
    }

    if (state.awaitingRoll) {
      return "roll (space)";
    }

    if (state.pendingDice.length === 0) {
      return "no dice pending";
    }

    const moves = availableMovesForPlayer(state.pendingDice, HUMAN);
    if (moves.length === 0) {
      return "no legal moves";
    }

    if (!moveFormatter || typeof moveFormatter.summarizeMoves !== "function") {
      return "moves unavailable";
    }

    return moveFormatter.summarizeMoves(moves);
  }

  function renderTurnIndicator() {
    const $indicator = $("#turn-indicator");
    if (state.gameOver) {
      $indicator.text("Game Over - Press space to restart");
      return;
    }

    const base = `${state.currentPlayer.toUpperCase()} Turn`;
    if (state.currentPlayer !== HUMAN) {
      $indicator.text(base);
      return;
    }

    const detail = summarizeHumanMoves();
    if (!detail) {
      $indicator.text(base);
      return;
    }

    $indicator.text(`${base} - ${detail}`);
  }

  function resetTurnState() {
    if (!state.turnSnapshot) {
      addMessage("No moves to reset.");
      return;
    }

    const snapshot = state.turnSnapshot;
    state.board = logic.cloneState(snapshot.board);
    dice.restore(snapshot.dice);
    state.awaitingRoll = dice.awaitingRoll;
    if (inputMachine) {
      inputMachine.transitionToPrimary();
    }
    renderBoard();
    addMessage("Turn reset.");
  }

  function consumeDieValue(die) {
    const consumption = dice.consume(die);
    if (!consumption) {
      return null;
    }
    state.awaitingRoll = dice.awaitingRoll;
    renderDice();
    return consumption;
  }

  function restoreConsumedDie(consumption) {
    if (!consumption) {
      return;
    }
    dice.returnValue(consumption);
    state.awaitingRoll = dice.awaitingRoll;
    renderDice();
  }

  function maybePassAfterAction() {
    if (inputMachine) {
      inputMachine.clearActiveCommand();
    }

    if (!dice.hasPending()) {
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
      addMessage("Press space to restart the game.");
      renderDice();
      return true;
    }
    return false;
  }

  function availableMovesForPlayer(dice, player) {
    return dice.flatMap((die) => logic.listLegalMoves(state.board, player, die));
  }

  function forcePassTurn() {
    if (state.gameOver) {
      return;
    }
    if (state.currentPlayer !== HUMAN) {
      return;
    }

    addMessage("Force pass (ESC).");
    endTurn();
  }

  function endTurn() {
    if (winCheck(state.currentPlayer)) {
      return;
    }

    resetDice();
    state.currentPlayer = logic.opposite(state.currentPlayer);
    state.turnSnapshot = null;
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

  function performHumanEnter(targetPoint) {
    if (!ensureDiceAvailable()) {
      return;
    }

    if (state.board.bar[HUMAN] <= 0) {
      addMessage("No human checkers on the bar.");
      return;
    }

    const target = Number(targetPoint);
    if (!withinBoard(target)) {
      addMessage("Point out of range.");
      return;
    }

    if (!logic.isPointOpen(state.board, HUMAN, target)) {
      addMessage(`Point ${target} blocked.`);
      return;
    }

    const requiredDie = logic.entryDieForTarget(HUMAN, target);
    const consumption = consumeDieValue(requiredDie);
    if (!consumption) {
      addMessage(`Need a ${requiredDie} to enter on ${target}.`);
      return;
    }

    try {
      logic.enterFromBar(state.board, target, HUMAN);
      addMessage(`Entered on point ${target}.`);
      renderBoard();
      maybePassAfterAction();
    } catch (error) {
      addMessage(error.message);
      restoreConsumedDie(consumption);
    }
  }

  function withinBoard(point) {
    return point >= 1 && point <= logic.POINT_COUNT;
  }

  function performHumanMoveFromTo(originPoint, targetPoint) {
    if (!ensureDiceAvailable()) {
      return;
    }

    const origin = Number(originPoint);
    const target = Number(targetPoint);
    if (!withinBoard(origin) || !withinBoard(target)) {
      addMessage("Point out of range.");
      return;
    }

    if (origin === target) {
      addMessage("Origin and target must differ.");
      return;
    }

    const originPointState = state.board.points[origin - 1];
    if (!originPointState || originPointState.owner !== HUMAN || originPointState.count === 0) {
      addMessage(`No human checker on point ${origin}.`);
      return;
    }

    const distance = target - origin;
    if (distance <= 0) {
      addMessage("Human checkers move toward higher-numbered points.");
      return;
    }

    if (!logic.isPointOpen(state.board, HUMAN, target)) {
      addMessage(`Point ${target} blocked.`);
      return;
    }

    const consumption = consumeDieValue(distance);
    if (!consumption) {
      addMessage(`Need a ${distance} to move from ${origin} to ${target}.`);
      return;
    }

    try {
      logic.moveChecker(state.board, origin, target, HUMAN);
      addMessage(`Moved from ${origin} to ${target}.`);
      renderBoard();
      maybePassAfterAction();
    } catch (error) {
      addMessage(error.message);
      restoreConsumedDie(consumption);
    }
  }

  function performHumanBearOff(pointNumber) {
    if (!ensureDiceAvailable()) {
      return;
    }

    const point = Number(pointNumber);
    if (!withinBoard(point)) {
      addMessage("Point out of range.");
      return;
    }

    const dice = [...state.pendingDice].sort((a, b) => a - b);
    let dieToUse = null;
    for (const die of dice) {
      const moves = logic.listLegalMoves(state.board, HUMAN, die);
      const match = moves.find(
        (move) => move.kind === "bear" && move.source === point
      );
      if (match) {
        dieToUse = die;
        break;
      }
    }

    if (dieToUse === null) {
      const requiredDie = logic.bearingDie(point, HUMAN);
      const highestPoint = logic.closestToExitPoint(state.board, HUMAN);
      if (state.board.bar[HUMAN] === 0 && highestPoint === point) {
        addMessage(`Need a ${requiredDie} or higher to bear off from ${point}.`);
      } else {
        addMessage(`Need an exact ${requiredDie} to bear off from ${point}.`);
      }
      return;
    }

    const consumption = consumeDieValue(dieToUse);
    if (!consumption) {
      addMessage(`Die ${dieToUse} unavailable.`);
      return;
    }

    try {
      logic.bearOff(state.board, point, HUMAN);
      addMessage(`Borne off from point ${point} using ${dieToUse}.`);
    } catch (error) {
      addMessage(error.message);
      restoreConsumedDie(consumption);
      return;
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
        consumeDieValue(die);
        return;
      }

      const choice = available[Math.floor(Math.random() * available.length)];
      logic.applyMove(state.board, choice, AI);
      consumeDieValue(die);

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

  function isRestartKeyEvent(event) {
    if (!event) {
      return false;
    }
    if (gameStateTools.isRestartKey(event.key)) {
      return true;
    }
    return event.code === "Space";
  }

  function restartGame() {
    gameStateTools.resetGameState(state, logic, dice, HUMAN);
    if (inputMachine) {
      inputMachine.transitionToAwaitRoll();
    }
    renderBoard();
    addMessage("Game restarted. Press space to roll.");
  }

  function processKey(event) {
    if (state.gameOver) {
      if (isRestartKeyEvent(event)) {
        event.preventDefault();
        event.stopPropagation();
        restartGame();
        return;
      }
      addMessage("Game over. Press space to restart.");
      return;
    }

    if (state.currentPlayer !== HUMAN) {
      addMessage("Wait for the AI to finish.");
      return;
    }

    if (inputMachine) {
      inputMachine.handle(event);
    }
  }

  function tryLegacyCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", true);
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();

    let success = false;
    try {
      success = document.execCommand("copy");
    } catch (error) {
      success = false;
    }

    document.body.removeChild(textarea);
    return success;
  }

  function copyBoardToClipboard() {
    if (!boardSerializer) {
      addMessage("Copy unavailable.");
      return;
    }

    const serialized = boardSerializer.serializeState
      ? boardSerializer.serializeState(state)
      : boardSerializer.serialize(state.board);
    if (!serialized) {
      addMessage("Copy unavailable.");
      return;
    }

    const onSuccess = () => {
      addMessage("Board copied to clipboard.");
    };

    const onFailure = () => {
      addMessage("Failed to copy board.");
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard
        .writeText(serialized)
        .then(onSuccess)
        .catch(() => {
          if (tryLegacyCopy(serialized)) {
            onSuccess();
            return;
          }
          onFailure();
        });
      return;
    }

    if (tryLegacyCopy(serialized)) {
      onSuccess();
      return;
    }

    onFailure();
  }

  inputMachine = new InputStateMachine({
    onRoll: () => {
      rollDice();
      const legal = availableMovesForPlayer(state.pendingDice, HUMAN);
      if (legal.length === 0) {
        addMessage("No legal moves, passing turn.");
        endTurn();
      }
    },
    onPassTurn: () => {
      addMessage("Turn passed to AI.");
      endTurn();
    },
    onResetTurn: () => {
      resetTurnState();
    },
    hasPendingDice: () => state.pendingDice.length > 0,
    hasBarCheckers: () => state.board.bar[HUMAN] > 0,
    onEnter: performHumanEnter,
    onBear: performHumanBearOff,
    onMove: performHumanMoveFromTo,
    onRequireCommand: () => {
      addMessage("No command in progress. Use m + origin + target or b + point.");
    },
    onPromptRoll: () => {
      addMessage("Roll first (space).");
    },
    onForcePass: () => {
      forcePassTurn();
    },
  });

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

    $("#copy-board-link").on("click", (event) => {
      event.preventDefault();
      copyBoardToClipboard();
    });
  }

  function renderInitialBoard() {
    renderBoard();
    setupInitialMessages();
    attachHandlers();
  }

  $(() => {
    if (window.MinigamBoardSerializer) {
      boardSerializer = new window.MinigamBoardSerializer(logic);
    }

    renderInitialBoard();
  });
})(jQuery, window.MinigamLogic, window.MinigamMoveFormatter, window.MinigamDice);

