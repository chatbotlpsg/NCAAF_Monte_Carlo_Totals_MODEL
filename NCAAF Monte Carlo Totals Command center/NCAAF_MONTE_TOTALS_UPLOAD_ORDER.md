# NCAAF Monte Totals Upload Order

1. Upload/install `ncaaf-monte-totals-trading-agents-support-plugin-v0.1.0.zip`.
2. Upload `ncaaf-monte-totals-command-center-md-package-v0.1.0.zip` to Project Knowledge.
3. Paste `NCAAF_MONTE_TOTALS_COMMAND_CENTER_PROJECT_INSTRUCTIONS.md` into Project Instructions.
4. Add `NCAAF_MONTE_TOTALS_AGENT_ROUTER_PATCH.md` near the top of Project Instructions.
5. Upload the weekly `NCAAF_MONTE_TOTALS_*_TRADING_AGENT_HANDOFF.zip`.
6. Run `/print-ncaaf-totals-boards`.
7. For pre-kick close capture, attach close-proxy snapshot files and run `/capture-ncaaf-close-proxy`.
8. After games, attach final results/close snapshots and run `/postgame-ncaaf-audit`.
9. Run `/build-ncaaf-recap` to create the permanent calibration/audit record.
