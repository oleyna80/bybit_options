```mermaid

flowchart TD
A([START: New decision / Manage open position])

%% ------------------------
%% GLOBAL RISK GATES
%% ------------------------
A --> G1{Scenario risk used\n>= 3% of equity?}
G1 -- Yes --> G1Y([STOP: No new entries/rolls.\nOnly reduce risk or exit])
G1 -- No --> G2{DTE < 4 days\nAND price near ATM?}
G2 -- Yes --> G2Y([FORCED EXIT: Gamma risk rule])
G2 -- No --> G3{D1 close beyond\nscenario invalidation level?}
G3 -- Yes --> G3Y([EXIT: Scenario structurally invalid])
G3 -- No --> C0([Stage 0: Determine Market Structure])

%% ------------------------
%% STAGE 0: STRUCTURE
%% ------------------------
C0 --> S1{Confirmed BOS UP?}
S1 -- Yes --> MSU([Market State = TREND UP])
S1 -- No --> S2{Confirmed BOS DOWN?}
S2 -- Yes --> MSD([Market State = TREND DOWN])
S2 -- No --> MSF([Market State = FLAT/RANGE])

%% ------------------------
%% STAGE 1: IV REGIME
%% ------------------------
MSU --> IV0([Stage 1: Determine IV context])
MSD --> IV0
MSF --> IV0

IV0 --> IV1{IV Rank > 90?}
IV1 -- Yes --> IVE([IV Regime = EVENT IV])
IV1 -- No --> IV2{IV rising from <30\nAND BOS present?}
IV2 -- Yes --> IVX([IV Regime = EXPANSION IV])
IV2 -- No --> IVS([IV Regime = STRUCTURAL IV])

%% ------------------------
%% STAGE 2: STRATEGY SELECTION (3x3)
%% ------------------------
IVE --> MSEL([Stage 2: Select strategy\n(Structure + IV Rank + Regime)])
IVX --> MSEL
IVS --> MSEL

MSEL --> RIV{IV Rank bucket?}
RIV -- Low < 30 --> LBUCKET([IV Bucket = LOW])
RIV -- Med 30-60 --> MBUCKET([IV Bucket = MED])
RIV -- High > 60 --> HBUCKET([IV Bucket = HIGH])

%% TREND UP selection
MSU --> TU([TREND UP path])
TU --> RIV

LBUCKET --> TU_L{Market State = TREND UP?}
TU_L -- Yes --> STR_TU_L([ENTER: Long Call Debit Spread])
TU_L -- No --> PASS1([Continue])

MBUCKET --> TU_M{Market State = TREND UP?}
TU_M -- Yes --> STR_TU_M([ENTER: Bull Zebra])
TU_M -- No --> PASS2([Continue])

HBUCKET --> TU_H{Market State = TREND UP\nAND IV Regime = STRUCTURAL?}
TU_H -- Yes --> STR_TU_H([ENTER: Bull Put Credit Spread])
TU_H -- No --> TU_HX([AVOID: Credit in Event/Expansion.\nUse conservative/limited-risk alt.])

%% TREND DOWN selection
MSD --> TD([TREND DOWN path])
TD --> RIV

LBUCKET --> TD_L{Market State = TREND DOWN?}
TD_L -- Yes --> STR_TD_L([ENTER: Long Put Debit Spread])
TD_L -- No --> PASS3([Continue])

MBUCKET --> TD_M{Market State = TREND DOWN?}
TD_M -- Yes --> STR_TD_M([ENTER: Bear Zebra])
TD_M -- No --> PASS4([Continue])

HBUCKET --> TD_H{Market State = TREND DOWN\nAND IV Regime = STRUCTURAL?}
TD_H -- Yes --> STR_TD_H([ENTER: Bear Call Credit Spread])
TD_H -- No --> TD_HX([AVOID: Credit in Event/Expansion.\nUse conservative/limited-risk alt.])

%% FLAT selection
MSF --> FL([FLAT/RANGE path])
FL --> RIV

LBUCKET --> FL_L{Market State = FLAT?}
FL_L -- Yes --> STR_FL_L([ENTER: Long Calendar])
FL_L -- No --> PASS5([Continue])

MBUCKET --> FL_M{Market State = FLAT?}
FL_M -- Yes --> STR_FL_M([ENTER: Double Diagonal])
FL_M -- No --> PASS6([Continue])

HBUCKET --> FL_H{Market State = FLAT?}
FL_H -- Yes --> STR_FL_H([ENTER: Iron Condor])
FL_H -- No --> PASS7([Continue])

%% ------------------------
%% STAGE 3: DEFENSE (RESCUE)
%% ------------------------
STR_TU_L --> D_TU_L{Invalidation:\nClose < FVG?}
D_TU_L -- Yes --> ACT_TU_L1([DEFENSE: Close 100%])
D_TU_L -- No --> HOLD1([Manage normally / take profit rules])

STR_TU_M --> D_TU_M{Price below entry\nAND net delta < +0.50?}
D_TU_M -- Yes --> ACT_TU_M1{IV >= MED?}
ACT_TU_M1 -- Yes --> ACT_TU_M2([DEFENSE: Convert to Call Butterfly])
ACT_TU_M1 -- No --> ACT_TU_M3([DEFENSE: Close position])
D_TU_M -- No --> HOLD2([Manage normally])

STR_TU_H --> D_TU_H{Short put tested?}
D_TU_H -- No --> HOLD3([Manage normally])
D_TU_H -- Yes --> D_TU_H2{Structure intact?}
D_TU_H2 -- Yes --> ACT_TU_H1([DEFENSE: Roll Down & Out])
D_TU_H2 -- No --> ACT_TU_H2([DEFENSE: Add Bear Call => Iron Condor])

STR_TD_L --> D_TD_L{Bounce against position?}
D_TD_L -- Yes --> ACT_TD_L1{Crash risk elevated?}
ACT_TD_L1 -- Yes --> ACT_TD_L2([DEFENSE: Close position])
ACT_TD_L1 -- No --> ACT_TD_L3([DEFENSE: Put Ladder (careful)])
D_TD_L -- No --> HOLD4([Manage normally])

STR_TD_M --> D_TD_M{Move against\n(position losing)?}
D_TD_M -- Yes --> ACT_TD_M1([DEFENSE: Convert to Put Butterfly])
D_TD_M -- No --> HOLD5([Manage normally])

STR_TD_H --> D_TD_H{Short call tested?}
D_TD_H -- No --> HOLD6([Manage normally])
D_TD_H -- Yes --> D_TD_H2{Time remains for roll?}
D_TD_H2 -- Yes --> ACT_TD_H1([DEFENSE: Roll Up & Out for credit])
D_TD_H2 -- No --> ACT_TD_H2([DEFENSE: Add Bull Put => Iron Condor])

STR_FL_L --> D_FL_L{Fast BOS breakout?}
D_FL_L -- Yes --> ACT_FL_L1([DEFENSE: Close short leg,\nkeep long leg])
D_FL_L -- No --> D_FL_L2{IV dropping?}
D_FL_L2 -- Yes --> ACT_FL_L2([DEFENSE: Close calendar])
D_FL_L2 -- No --> HOLD7([Manage normally])

STR_FL_M --> D_FL_M{One side tested?}
D_FL_M -- Yes --> ACT_FL_M1([DEFENSE: Roll short leg Out])
D_FL_M -- No --> HOLD8([Manage normally])

STR_FL_H --> D_FL_H{One side tested?}
D_FL_H -- No --> HOLD9([Manage normally])
D_FL_H -- Yes --> ACT_FL_H1([DEFENSE: Roll In unchallenged side\n(attack from behind)])
ACT_FL_H1 --> D_FL_H2{Need last-resort neutralization?}
D_FL_H2 -- Yes --> ACT_FL_H2([DEFENSE: Transform towards Iron Fly\n(if justified)])
D_FL_H2 -- No --> HOLD10([Manage normally])

%% ------------------------
%% STAGE 4: FLIP SCENARIO
%% ------------------------
ACT_TU_L1 --> FLIPCHK([Flip check after exit])
ACT_TU_M3 --> FLIPCHK
ACT_TU_H2 --> FLIPCHK
ACT_TD_L2 --> FLIPCHK
ACT_TD_H2 --> FLIPCHK

FLIPCHK --> F1{Was previous trade\nbased on SFP?}
F1 -- No --> END1([END: No flip])
F1 -- Yes --> F2{Now there is\nConfirmed BOS?}
F2 -- No --> END2([END: Flip forbidden])
F2 -- Yes --> F3([FLIP: Re-enter using BOS rules\nand Stage 2 matrix])
F3 --> C0

%% END nodes
HOLD1 --> A
HOLD2 --> A
HOLD3 --> A
HOLD4 --> A
HOLD5 --> A
HOLD6 --> A
HOLD7 --> A
HOLD8 --> A
HOLD9 --> A
HOLD10 --> A
```
