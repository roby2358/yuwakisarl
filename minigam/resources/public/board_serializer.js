class BoardSerializer {
  constructor(logic) {
    if (!logic) {
      throw new Error("logic dependency required");
    }
    this.logic = logic;
    this.players = [
      logic.Players.HUMAN,
      logic.Players.AI,
    ];
  }

  serialize(board) {
    const segments = this.#boardSegments(board);
    if (!segments) {
      return "";
    }

    return segments.join(";");
  }

  serializeState(state) {
    if (!state) {
      return "";
    }

    const segments = this.#boardSegments(state.board);
    if (!segments) {
      return "";
    }

    const snapshot = [...segments];
    snapshot.push(this.#serializeDice("pending", state.pendingDice));
    snapshot.push(this.#serializeDice("rolled", state.diceRolled));
    snapshot.push(this.#serializeDice("completed", state.turnCompletedDice));
    snapshot.push(`player=${state.currentPlayer || "-"}`);
    snapshot.push(`awaiting=${state.awaitingRoll ? "yes" : "no"}`);

    return snapshot.join(";");
  }

  #boardSegments(board) {
    if (!board) {
      return null;
    }

    const pointsSegment = this.#serializePoints(board.points);
    if (!pointsSegment) {
      return null;
    }

    const barSegment = this.#serializeBar(board.bar);
    if (!barSegment) {
      return null;
    }

    const borneSegment = this.#serializeBorneOff(board.borneOff);
    if (!borneSegment) {
      return null;
    }

    return [
      `points=${pointsSegment}`,
      `bar=${barSegment}`,
      `borne=${borneSegment}`,
    ];
  }

  #serializePoints(points) {
    if (!Array.isArray(points)) {
      return "";
    }
    if (points.length !== this.logic.POINT_COUNT) {
      return "";
    }

    return points
      .map((point, index) => {
        const pointLabel = index + 1;
        const token = this.#pointToken(point);
        if (!token) {
          return "";
        }
        return `${pointLabel}:${token}`;
      })
      .join(",");
  }

  #pointToken(point) {
    if (!point || !point.owner || point.count <= 0) {
      return "-";
    }

    const prefix = point.owner === this.logic.Players.HUMAN ? "H" : "A";
    return `${prefix}${point.count}`;
  }

  #serializeBar(bar) {
    if (!bar) {
      return "";
    }

    const entries = this.players.map((player) => {
      const prefix = player === this.logic.Players.HUMAN ? "H" : "A";
      const value = Number.isInteger(bar[player]) ? bar[player] : 0;
      return `${prefix}${value}`;
    });

    return entries.join(",");
  }

  #serializeBorneOff(borneOff) {
    if (!borneOff) {
      return "";
    }

    const entries = this.players.map((player) => {
      const prefix = player === this.logic.Players.HUMAN ? "H" : "A";
      const value = Number.isInteger(borneOff[player]) ? borneOff[player] : 0;
      return `${prefix}${value}`;
    });

    return entries.join(",");
  }

  #serializeDice(label, dice) {
    if (!label) {
      return "";
    }

    if (!Array.isArray(dice) || dice.length === 0) {
      return `${label}=-`;
    }

    const values = dice.map((die) => (Number.isInteger(die) ? die : "-"));
    return `${label}=${values.join(",")}`;
  }
}

const MinigamBoardSerializer = BoardSerializer;

if (typeof window !== "undefined") {
  window.MinigamBoardSerializer = MinigamBoardSerializer;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = MinigamBoardSerializer;
}


