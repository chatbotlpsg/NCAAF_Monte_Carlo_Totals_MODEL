# NCAAF Close Proxy / CLV / Postgame Audit Protocol

After games finish, the Trading Agent may audit:

```text
actual final score
bet result
entry price
close proxy price
CLV
realized ROI
raw EV vs result
blended EV vs result
conservative EV vs result
confidence bucket performance
EV bucket performance
market-family performance
correlation/concentration outcome
Monte Carlo distribution accuracy
```

Close labels must be precise:

```text
OPEN_PROXY
ENTRY
FINAL_PRE_KICK_SNAPSHOT
CLOSE_PROXY_PUBLIC
TRUE_CLOSE
```

Do not retroactively modify the frozen model because a bet won or lost. Calibration feedback belongs to future Python versions.
