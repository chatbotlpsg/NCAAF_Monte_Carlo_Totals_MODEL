# Architecture Lock

The Python engine **prices the market**. The external NCAAF Trading Agent **trades the model output**.

Python responsibilities: source/normalize data; build team/player states; estimate tempo/possessions/drives; simulate halftime and final scores; price full-game totals, team totals and first-half totals; compute fair odds, break-even, MC/blended/conservative EV, uncertainty, confidence and correlations; generate risk-support boards; generate and validate the handoff ZIP.

External Trading Agent responsibilities: audit the ZIP, re-check live prices, interpret portfolio exposure, apply trading judgment and make the final PASS/WATCH/VALUE/ELITE trade decision.

Historical model outputs and handoffs are immutable.
