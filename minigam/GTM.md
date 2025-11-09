# MINIGAM Go-To-Market Plan

## 1. Product Snapshot
- **Experience**: Browser-playable quarter-backgammon built with a FastAPI static backend and a JavaScript rules engine (`README.md`, `SPEC.md`).
- **Core Mechanics**: Eight checkers per side, forced-move compliance, random-move AI baseline, and keyboard-first controls aligned with the published ruleset (`MINIGAM.md`, `resources/public/game.js`).
- **Current State**: Playable alpha featuring static serving only; AI operates client-side with stochastic move selection; UI mirrors the six-point board specification.
- **Near-Term Roadmap**: Expand AI strength via search/self-play loop (`ML.md`), introduce websocket channel for server-side moves, refine visuals while keeping “cool, clear colors.”

## 2. Target Segments
- **Backgammon Enthusiasts (Digital Casuals)**: Players seeking a quick, rules-faithful variant that runs in the browser without installs.
- **Strategy Learners & Educators**: Coaches/classrooms wanting a simplified board to teach racing, probability, and forced-move concepts.
- **Indie Game Explorers**: Itch.io, Reddit r/boardgames, and Product Hunt users looking for polished micro-strategy experiences.
- **AI/ML Hobbyists**: Developers interested in experimenting with compact MDP domains and observing AI skill progression.

## 3. Value Proposition & Differentiators
- **Focused Variant**: Quarter-board keeps matches under five minutes while retaining meaningful tactical depth.
- **Keyboard-First Speed**: Optimized command schema (space, digits, `b`, `m`, `ESC`) delivers low-friction turns and supports power users.
- **Transparency & Tools**: Built-in board serialization and move summaries support content creation, analysis, and streaming.
- **AI Growth Story**: Public roadmap to evolve from random moves to self-play-trained agents invites the community to follow and contribute.

### Messaging Pillars
1. *“Backgammon intensity, coffee-break length.”*
2. *“Master the dice with precise keyboard control.”*
3. *“Watch the AI learn alongside you.”*

## 4. Packaging & Monetization
- **Launch Offering**: Free-to-play web experience hosted on a lightweight FastAPI endpoint.
- **Future Enhancements**:
  - Premium “analysis pass” (advanced AI opponents, rollout evaluator, saved match histories).
  - Cosmetic support bundles (board themes within the “cool, clear” palette).
  - Educational license tier with classroom dashboards once telemetry exists.
- **Distribution**: Primary—first-party site; mirrored builds on itch.io and GitHub Pages for reach. Maintain open-source core to encourage contributions.

## 5. Customer Journey & Channels
- **Discovery**: Devlog posts (Substack/Medium), Reddit AMA on r/backgammon & r/boardgames, teaser GIFs on X and Mastodon highlighting keyboard play.
- **Activation**: Interactive tutorial overlay and rules quick-reference (linked from `MINIGAM.md`) to shorten time-to-first-win.
- **Engagement**: Weekly AI “learning reports” using data from upcoming self-play runs; community challenges (beat the AI in X moves).
- **Retention**: Email or RSS updates for major AI skill upgrades; opt-in notifications for ladder resets; integrate board serialization with shareable short links.

## 6. Launch Plan
| Phase | Timeline | Goals | Activities |
| --- | --- | --- | --- |
| Closed Alpha | Weeks 1-2 | Validate core UX & keyboard mapping | Private invites, collect qualitative feedback, run automated JS/Python tests each build. |
| Open Beta | Weeks 3-4 | Grow awareness, harden telemetry | Publish playable build, launch itch.io page, add lightweight analytics, start changelog posts. |
| v1 Launch | Week 5 | Public release with stability messaging | Press kit, walkthrough video, Product Hunt launch, Reddit announcement, email blast. |
| Post-Launch | Weeks 6+ | Sustain engagement, evolve AI | Release AI upgrades, publish roadmap updates, host community tournaments. |

## 7. Success Metrics
- **Acquisition**: Unique players (30-day) ≥ 5k; newsletter sign-ups ≥ 1k.
- **Activation**: ≥ 70% of first-time players complete a full match; tutorial completion rate ≥ 60%.
- **Engagement**: Median session length ≥ 2 matches; return play (7-day) ≥ 35%.
- **Monetization (Phase 2+)**: Conversion on premium features ≥ 3%; ARPPU ≥ $4/month.
- **Community**: Discord/Matrix membership growth ≥ 15% month-over-month; user-submitted serialized boards ≥ 100/month.

## 8. Risks & Mitigations
- **AI Feels Too Weak**: Communicate roadmap, launch co-op “beat-the-dev” events, fast-track expectimax baseline from `ML.md`.
- **Rules Complexity Onboarding**: Provide inline contextual hints; embed `MINIGAM.md` summary in-game; produce short-form video tutorials.
- **Retention Plateau**: Introduce daily challenges using deterministic seeds; rotate cosmetic themes; schedule AI skill milestones.
- **Technical Scalability**: Keep static hosting for gameplay, offload telemetry via serverless endpoints; prepare websocket layer for AI upgrades.
- **Multi-Platform Controls**: Ensure accessibility (focus states, ARIA labels); ship mouse/touch support without diluting keyboard-first positioning.

## 9. Launch Readiness Checklist
- [ ] Public site deployed behind CDN with uptime monitoring.
- [ ] Analytics & error reporting wired (frontend + FastAPI).
- [ ] Automated JS (`node --test`) and Python (`uv run pytest`) suites green in CI.
- [ ] Tutorial overlay, rules reference, and copy-to-clipboard flows verified.
- [ ] Press kit (screens, logo, fact sheet) published.
- [ ] Support channel (Discord/Matrix) staffed and linked from UI.

## 10. Next Strategic Investments
- Integrate websocket-backed AI to showcase skill progression.
- Release developer docs around board serialization and move APIs for modders.
- Explore cross-promotions with tabletop influencers and strategy streamers.
- Build mini-leaderboards leveraging pending telemetry groundwork.
- Package AI training logs as educational content for ML hobbyists.


