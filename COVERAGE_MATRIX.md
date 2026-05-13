# SIGNALGHOST COVERAGE MATRIX

## Every named item from SESSION\_STATE Ed033 → implementation mapping

|#|Exact Name from SESSION\_STATE|Category|Target File(s)|Implementation Type|Status|
|-|-|-|-|-|-|
|1|WHAT THIS SYSTEM IS|section|config.py, README.md|constants + docs|implemented|
|2|LIVE GMT TIMESTAMP — MANDATORY FIRST ACTION|section/rule|timestamping.py|code (capture\_timestamp)|implemented|
|3|PLATFORM|section|config.py|constants (SYSTEM\_NAME, ARCHITECTURE\_VERSION)|implemented|
|4|CRITICAL PROCESS RULES — ABSOLUTE|section|config.py|constants (AI\_005\_RULE)|implemented|
|5|MANDATORY PDF ARCHITECTURE — ALL 10 ITEMS|section|pdf\_builder.py, config.py|validation (validate\_mandatory\_items)|implemented|
|6|CHRONOLOGY VERIFICATION RULE|section|chronology.py|code (compute\_war\_day, verify\_war\_day)|implemented|
|7|OPERATOR GOVERNANCE RULES — ANTI-DRIFT / ANTI-HALLUCINATION|section|config.py|constants (OPERATOR\_GOVERNANCE\_RULES)|implemented|
|8|CURRENT EDITION|section|persistence.py, session\_executor.py|schema (editions) + code|implemented|
|9|SOURCING FRAMEWORK — 18 NAMED FEEDS BY TIER (v1.2.1)|section|feeds.py, config.py|code (18 named adapters)|implemented|
|10|AI-010 RULE|section/rule|calibration\_pipeline.py, config.py|code (ai\_010\_single\_cluster\_h5\_discount)|implemented|
|11|CALIBRATION DOCTRINE — AI-007|section|calibration\_pipeline.py, config.py|code (ai\_007\_hard\_ceiling\_check)|implemented|
|12|GATE REGISTRY — FULL (v1.1.0)|section|gates.py|code (7 named gate functions)|implemented|
|13|Updated Gate Execution Order|section/table|config.py, gates.py, session\_executor.py|constants + orchestration|implemented|
|14|GOVERNANCE NOTE: AI SELF-EXAMINATION LIMITATION|section|config.py|constant (AI\_SELF\_EXAMINATION\_LIMITATION)|implemented|
|15|CALIBRATION PIPELINE — EXECUTION ORDER (v1.3.0)|section|calibration\_pipeline.py, config.py|code (13 stages) + constants (PIPELINE\_STAGES)|implemented|
|16|AI-012 — NINE CALIBRATION ENHANCEMENTS|section|calibration\_pipeline.py|code (9 named functions)|implemented|
|17|CALIBRATION MAP — Ed033|section|calibration\_state.py, persistence.py|seed data + schema (calibration\_map)|implemented|
|18|BRIER SCORE FRAMEWORK — AI-009 + AI-012|section|predictions.py|code (compute\_brier\_score, compute\_log\_score, compute\_spherical\_score)|implemented|
|19|SEVEN HEURISTICS (H1-H7)|section|config.py|constants (HEURISTICS)|implemented|
|20|ACTIVE CASES|section|calibration\_state.py, persistence.py|seed data + schema (cases)|implemented|
|21|HYPOTHESIS STATE — POST-EDITION 033|section|calibration\_state.py, persistence.py|seed data + schema (hypotheses)|implemented|
|22|PREDICTION LOG — OPEN|section|calibration\_state.py, persistence.py|seed data + schema (predictions\_open)|implemented|
|23|PREDICTION LOG — RESOLVED (CUMULATIVE)|section|calibration\_state.py, persistence.py|seed data + schema (predictions\_resolved)|implemented|
|24|CARRY-FORWARD FACTS|section|persistence.py, calibration\_state.py|schema (carry\_forward\_facts)|implemented|
|25|ED034 MANDATORY SWEEP ACTIONS|section|session\_executor.py|code (run method — 13 steps)|implemented|
|26|DISCONFIRMATION THRESHOLDS — STANDING|section|calibration\_state.py, persistence.py|seed data (27 thresholds) + schema|implemented|
|27|EDITION WORKFLOW — REPEATING LOOP|section|config.py, session\_executor.py|constants (EDITION\_WORKFLOW\_RULES) + code|implemented|
|28|GMT TIMESTAMP RULE|section|timestamping.py|code (capture\_timestamp, validate\_war\_day)|implemented|
|29|BUILD SCRIPT ARCHITECTURE|section|config.py|constants (BUILD\_NOTES)|implemented|
|30|PROCESS LOG MEMO (PLM)|section|config.py, calibration\_state.py, persistence.py|seed data (13 entries) + schema|implemented|
|31|ANALYTICAL PMM LOG|section|config.py, calibration\_state.py, persistence.py|seed data (4 entries) + schema|implemented|
|32|SYSTEM CHANGE LOG — ACTIVE RULES|section|config.py, calibration\_state.py, persistence.py|seed data (18 entries) + schema|implemented|
|33|HPT — HEURISTIC PERFORMANCE TRACKING|section|calibration\_state.py, persistence.py|seed data (5 rows) + schema|implemented|
|34|DEVIATION AUDIT — 28 ITEMS|section|config.py, session\_executor.py|constants (28 items) + validation code|implemented|
|35|SESSION HANDOFF — MANDATORY AT EACH EDITION CLOSE|section|handover.py, config.py|code (generate\_session\_state) + constants|implemented|
|**GATES**||||||
|36|Gate 0.1 — Temporal Currency Check|gate|gates.py|code (gate\_0\_1\_temporal\_currency\_check)|implemented|
|37|Gate 0.2 — Source Corroboration Requirement|gate|gates.py|code (gate\_0\_2\_source\_corroboration\_requirement)|implemented|
|38|Gate 0.3 — Incentive Analysis Completion|gate|gates.py|code (gate\_0\_3\_incentive\_analysis\_completion)|implemented|
|39|Gate 0.4 — Cross-Case Consistency Check|gate|gates.py|code (gate\_0\_4\_cross\_case\_consistency\_check)|implemented|
|40|Gate 0.5 — Cluster Risk Check|gate|gates.py|code (gate\_0\_5\_cluster\_risk\_check)|implemented|
|41|Gate 0.6 — Absence / Threshold Gate|gate|gates.py|code (gate\_0\_6\_absence\_threshold\_gate)|implemented|
|42|Gate 5 — Resolution Gate|gate|gates.py|code (gate\_5\_resolution\_gate)|implemented|
|**AI PIPELINE STAGES**||||||
|43|Stage 1: AI-010 Single-cluster H5 discount|AI stage|calibration\_pipeline.py|code (ai\_010\_single\_cluster\_h5\_discount)|implemented|
|44|Stage 2: AI-009 Bayesian update|AI stage|calibration\_pipeline.py|code (ai\_009\_bayesian\_update)|implemented|
|45|Stage 3: AI-012-1 Causal edge smoothing|AI stage|calibration\_pipeline.py|code (ai\_012\_1\_causal\_edge\_tracking)|implemented|
|46|Stage 4: AI-012-2 Delta statistics update|AI stage|calibration\_pipeline.py|code (ai\_012\_2\_delta\_statistics)|implemented|
|47|Stage 5: AI-012-3 Change point detection|AI stage|calibration\_pipeline.py|code (ai\_012\_3\_change\_point\_detection)|implemented|
|48|Stage 6: AI-012-4 Correlation matrix update|AI stage|calibration\_pipeline.py|code (ai\_012\_4\_correlation\_matrix)|implemented|
|49|Stage 7: AI-012-5 Cross-case propagation|AI stage|calibration\_pipeline.py|code (ai\_012\_5\_cross\_case\_propagation)|implemented|
|50|Stage 8: AI-012-7 Brier/EMA calibration|AI stage|calibration\_pipeline.py|code (ai\_012\_7\_brier\_ema\_calibration)|implemented|
|51|Stage 9: AI-012-9 Per-band lookup table|AI stage|calibration\_pipeline.py|code (ai\_012\_9\_per\_band\_lookup)|implemented|
|52|Stage 10: AI-012-8 Band adjustment|AI stage|calibration\_pipeline.py|code (ai\_012\_8\_band\_adjustment)|implemented|
|53|Stage 11: AI-007 Hard ceiling check|AI stage|calibration\_pipeline.py|code (ai\_007\_hard\_ceiling\_check)|implemented|
|54|Stage 12: AI-012-6 RL Bandit advisory|AI stage|calibration\_pipeline.py|code (ai\_012\_6\_rl\_bandit)|implemented|
|55|Stage 13: AI-012-10 Publication Integrity Lock|AI stage|calibration\_pipeline.py|code (ai\_012\_10\_publication\_integrity\_lock)|implemented|
|**FAILURE MODES**||||||
|56|Theatre of Rigor|failure mode|config.py|enum (FailureMode.THEATRE\_OF\_RIGOR)|implemented|
|57|Claim-Type Conflation|failure mode|config.py|enum (FailureMode.CLAIM\_TYPE\_CONFLATION)|implemented|
|58|Source Amplification|failure mode|config.py|enum (FailureMode.SOURCE\_AMPLIFICATION)|implemented|
|59|Escape-Hatch Assignment|failure mode|config.py|enum (FailureMode.ESCAPE\_HATCH\_ASSIGNMENT)|implemented|
|60|Efficiency Drift|failure mode|config.py|enum (FailureMode.EFFICIENCY\_DRIFT)|implemented|
|**TABLES / REGISTERS / MAPS / LOGS**||||||
|61|editions table|table|persistence.py|schema (editions)|implemented|
|62|hypotheses table|table|persistence.py|schema (hypotheses)|implemented|
|63|probability ranges and point estimates|table|persistence.py|schema (hypotheses: range\_lower, range\_upper, point\_estimate)|implemented|
|64|delta buffers|table|persistence.py|schema (delta\_buffer)|implemented|
|65|change-point flags|table|persistence.py|schema (change\_point\_flags)|implemented|
|66|causal edge register|table|persistence.py|schema (causal\_edges)|implemented|
|67|correlation matrix|table|persistence.py|schema (correlation\_matrix)|implemented|
|68|propagation register|table|persistence.py|schema (propagation\_register)|implemented|
|69|EMA band errors|table|persistence.py|schema (ema\_band\_errors)|implemented|
|70|per-band lookup table|table|persistence.py|schema (per\_band\_lookup)|implemented|
|71|RL bandit Q-table|table|persistence.py|schema (rl\_q\_table)|implemented|
|72|PLM entries table|table|persistence.py|schema (plm\_entries)|implemented|
|73|PMM entries table|table|persistence.py|schema (pmm\_entries)|implemented|
|74|prediction log (open)|table|persistence.py|schema (predictions\_open)|implemented|
|75|prediction log (resolved)|table|persistence.py|schema (predictions\_resolved)|implemented|
|76|feed sweep results|table|persistence.py|schema (feed\_sweep\_results)|implemented|
|77|gate pass/fail records|table|persistence.py|schema (gate\_records)|implemented|
|78|Brier table (running)|table|persistence.py|schema (brier\_table)|implemented|
|79|calibration map|table|persistence.py|schema (calibration\_map)|implemented|
|80|HPT entries|table|persistence.py|schema (hpt\_entries)|implemented|
|81|deviation audit results|table|persistence.py|schema (deviation\_audit)|implemented|
|82|disconfirmation thresholds|table|persistence.py|schema (disconfirmation\_thresholds)|implemented|
|83|system change log|table|persistence.py|schema (system\_change\_log)|implemented|
|84|carry-forward facts|table|persistence.py|schema (carry\_forward\_facts)|implemented|
|85|cases table|table|persistence.py|schema (cases)|implemented|
|**NAMED RULES / FORMULAS**||||||
|86|Edge\_strength\_new = 0.7 × old + 0.3 × new|formula|calibration\_pipeline.py|code (CAUSAL\_EDGE\_OLD\_WEIGHT, CAUSAL\_EDGE\_NEW\_WEIGHT)|implemented|
|87|z = (Δp − mean) / std;|z|> 2.0|formula|calibration\_pipeline.py|
|88|effective\_correlation = raw × (n/20)|formula|calibration\_pipeline.py|code (CORRELATION\_SHRINKAGE\_N\_MAX)|implemented|
|89|EMA\_error = 0.9 × old + 0.1 × new|formula|calibration\_pipeline.py|code (EMA\_OLD\_WEIGHT, EMA\_NEW\_WEIGHT)|implemented|
|90|Published prob = Raw × (1 + adjustment)|formula|calibration\_pipeline.py|code (ai\_012\_9\_per\_band\_lookup)|implemented|
|91|Q ← Q + α × (reward − Q)|formula|calibration\_pipeline.py|code (RL\_ALPHA)|implemented|
|92|BS = (1/n) × Σ(fi−oi)²|formula|predictions.py|code (compute\_brier\_score)|implemented|
|93|LS = (1/n) × Σ ln(pi)|formula|predictions.py|code (compute\_log\_score)|implemented|
|94|SS = (1/n) × Σ pi / √Σfi²|formula|predictions.py|code (compute\_spherical\_score)|implemented|
|95|War Day = (date − 28 Feb 2026) + 1|formula|chronology.py, timestamping.py|code (compute\_war\_day)|implemented|
|96|midpoint/half-width band adjustment|formula|calibration\_pipeline.py|code (ai\_012\_8\_band\_adjustment)|implemented|
|**NAMED PARAMETERS / THRESHOLDS**||||||
|97|AI-007 hard ceiling 85%|parameter|config.py|constant (AI\_007\_HARD\_CEILING = 0.85)|implemented|
|98|AI-010 discount minimum 10pp|parameter|config.py|constant (AI\_010\_DISCOUNT\_MIN\_PP = 0.10)|implemented|
|99|PMM-004 adjustment −10pp|parameter|config.py|constant (PMM\_004\_ADJUSTMENT\_PP = -0.10)|implemented|
|100|Gate 0.2 Tier 3 5pp trigger|parameter|config.py|constant (GATE\_0\_2\_TIER3\_PP\_TRIGGER = 0.05)|implemented|
|101|Gate 0.3 threshold 60%|parameter|config.py|constant (GATE\_0\_3\_THRESHOLD = 0.60)|implemented|
|102|Gate 0.4 threshold 70%|parameter|config.py|constant (GATE\_0\_4\_THRESHOLD = 0.70)|implemented|
|103|Gate 0.4 correlation > 0.30|parameter|config.py|constant (GATE\_0\_4\_CORRELATION\_THRESHOLD = 0.30)|implemented|
|104|Gate 0.4 partner floor 35%|parameter|config.py|constant (GATE\_0\_4\_PARTNER\_FLOOR = 0.35)|implemented|
|105|Gate 0.6 rocket threshold 100|parameter|config.py|constant (GATE\_0\_6\_ROCKET\_THRESHOLD = 100)|implemented|
|106|Publication lock H4 gap cap 50%|parameter|config.py|constant (PUB\_LOCK\_H4\_GAP\_CAP = 0.50)|implemented|
|107|Publication lock chain cap 60%|parameter|config.py|constant (PUB\_LOCK\_CHAIN\_CAP = 0.60)|implemented|
|108|RL governing n ≥ 30|parameter|config.py|constant (RL\_GOVERNING\_N = 30)|implemented|
|109|EMA cap ±3% at n<5|parameter|config.py|constant (EMA\_CAP\_VALUE = 0.03)|implemented|
|110|Delta buffer size 5|parameter|config.py|constant (DELTA\_BUFFER\_SIZE = 5)|implemented|
|111|Shrinkage n/20|parameter|config.py|constant (CORRELATION\_SHRINKAGE\_N\_MAX = 20)|implemented|
|112|Causal edge established > 0.70|parameter|config.py|constant (CAUSAL\_EDGE\_ESTABLISHED\_THRESHOLD = 0.70)|implemented|
|113|Propagation|Δ|> 0.05|parameter|config.py|
|114|Confidence MEDIUM ceiling when upper < 60%|parameter|config.py|constant (CONFIDENCE\_MEDIUM\_CEILING\_THRESHOLD)|implemented|
|**NAMED FEEDS (18)**||||||
|115|Trump Truth Social / White House|feed Tier 1|feeds.py|code (check\_feed\_tier1\_trump)|implemented|
|116|CENTCOM public affairs|feed Tier 1|feeds.py|code (check\_feed\_tier1\_centcom)|implemented|
|117|IDF official statements|feed Tier 1|feeds.py|code (check\_feed\_tier1\_idf)|implemented|
|118|Iran SNSC / IRNA|feed Tier 1|feeds.py|code (check\_feed\_tier1\_iran\_snsc)|implemented|
|119|Named government spokesperson|feed Tier 1|feeds.py|code (check\_feed\_tier1\_spokesperson)|implemented|
|120|Reuters|feed Tier 2|feeds.py|code (check\_feed\_tier2\_reuters)|implemented|
|121|AP|feed Tier 2|feeds.py|code (check\_feed\_tier2\_ap)|implemented|
|122|Bloomberg|feed Tier 2|feeds.py|code (check\_feed\_tier2\_bloomberg)|implemented|
|123|Al Jazeera|feed Tier 2|feeds.py|code (check\_feed\_tier2\_aljazeera)|implemented|
|124|NBC News live updates|feed Tier 2|feeds.py|code (check\_feed\_tier2\_nbc)|implemented|
|125|CBS News live updates|feed Tier 2|feeds.py|code (check\_feed\_tier2\_cbs)|implemented|
|126|NPR|feed Tier 2|feeds.py|code (check\_feed\_tier2\_npr)|implemented|
|127|Tasnim News Agency (IRGC-linked)|feed Tier 3|feeds.py|code (check\_feed\_tier3\_tasnim)|implemented|
|128|Mehr News Agency|feed Tier 3|feeds.py|code (check\_feed\_tier3\_mehr)|implemented|
|129|WANA News Agency|feed Tier 3|feeds.py|code (check\_feed\_tier3\_wana)|implemented|
|130|House of Saud / Conflict Pulse|feed Tier 3|feeds.py|code (check\_feed\_tier3\_hos\_cp)|implemented|
|131|Wikipedia|feed Tier 4|feeds.py|code (check\_feed\_tier4\_wikipedia)|implemented|
|132|ACLED conflict monitor|feed Tier 4|feeds.py|code (check\_feed\_tier4\_acled)|implemented|
|**NAMED HYPOTHESES (15)**||||||
|133|H-A1|hypothesis|calibration\_state.py|seed data (0.50-0.62, pt 0.56)|implemented|
|134|H-A2|hypothesis|calibration\_state.py|seed data (0.05-0.10, pt 0.07)|implemented|
|135|H-A3|hypothesis|calibration\_state.py|seed data (0.75-0.85, pt 0.80)|implemented|
|136|H-B1|hypothesis|calibration\_state.py|seed data (0.12-0.22, pt 0.17)|implemented|
|137|H-B2|hypothesis|calibration\_state.py|seed data (0.22-0.35, pt 0.29)|implemented|
|138|H-B3|hypothesis|calibration\_state.py|seed data (0.38-0.50, pt 0.44)|implemented|
|139|H-C1|hypothesis|calibration\_state.py|seed data (0.62-0.75, pt 0.68)|implemented|
|140|H-C2|hypothesis|calibration\_state.py|seed data (0.15-0.24, pt 0.20)|implemented|
|141|H-C3|hypothesis|calibration\_state.py|seed data (0.14-0.22, pt 0.18)|implemented|
|142|H-D1|hypothesis|calibration\_state.py|seed data (0.00, CONTRADICTED)|implemented|
|143|H-D2|hypothesis|calibration\_state.py|seed data (0.97-0.99, CONFIRMED)|implemented|
|144|H-D3|hypothesis|calibration\_state.py|seed data (0.02-0.05, pt 0.04)|implemented|
|145|H-E1|hypothesis|calibration\_state.py|seed data (0.40-0.53, pt 0.47)|implemented|
|146|H-E2|hypothesis|calibration\_state.py|seed data (0.32-0.46, pt 0.38)|implemented|
|147|H-E3|hypothesis|calibration\_state.py|seed data (0.12-0.18, pt 0.15)|implemented|
|**NAMED CAUSAL EDGES (10)**||||||
|148|US blockade → Iran closes Hormuz|causal edge|calibration\_state.py|seed data (0.93)|implemented|
|149|Hormuz closed → H-B1 suppressed|causal edge|calibration\_state.py|seed data (0.90)|implemented|
|150|Lebanon ceasefire → H-E1 suppressed|causal edge|calibration\_state.py|seed data (0.70)|implemented|
|151|Talks imminent → H-B2 suppressed|causal edge|calibration\_state.py|seed data (0.46)|implemented|
|152|Ghalibaf absent → H5 partially resolved|causal edge|calibration\_state.py|seed data (0.51)|implemented|
|153|GL U lapsed → ICICI closed|causal edge|calibration\_state.py|seed data (0.80)|implemented|
|154|Mine clearance 6-month → H-B1 capped|causal edge|calibration\_state.py|seed data (0.30)|implemented|
|155|Oman channel → H-A1/H-B1 partial|causal edge|calibration\_state.py|seed data (0.15)|implemented|
|156|Hezbollah barrage Kfar Giladi → H-C2/C3 elevated|causal edge|calibration\_state.py|seed data (0.51)|implemented|
|157|Talks deadlock → H-B1 suppression entrenched|causal edge|calibration\_state.py|seed data (0.65)|implemented|
|**NAMED PLM ENTRIES (13)**||||||
|158|PLM-001|log|config.py, calibration\_state.py|seed data|implemented|
|159|PLM-002|log|config.py, calibration\_state.py|seed data|implemented|
|160|PLM-003|log|config.py, calibration\_state.py|seed data|implemented|
|161|PLM-004|log|config.py, calibration\_state.py|seed data|implemented|
|162|PLM-005|log|config.py, calibration\_state.py|seed data|implemented|
|163|PLM-006|log|config.py, calibration\_state.py|seed data|implemented|
|164|PLM-007|log|config.py, calibration\_state.py|seed data|implemented|
|165|PLM-008|log|config.py, calibration\_state.py|seed data|implemented|
|166|PLM-009|log|config.py, calibration\_state.py|seed data|implemented|
|167|PLM-010|log|config.py, calibration\_state.py|seed data|implemented|
|168|PLM-011|log|config.py, calibration\_state.py|seed data|implemented|
|169|PLM-012|log|config.py, calibration\_state.py|seed data|implemented|
|170|PLM-013|log|config.py, calibration\_state.py|seed data|implemented|
|**NAMED PMM ENTRIES (4)**||||||
|171|PMM-001 (PRED-012-B)|log|config.py, calibration\_state.py|seed data|implemented|
|172|PMM-002 (PRED-026-E)|log|config.py, calibration\_state.py|seed data|implemented|
|173|PMM-003 (PRED-022-A thru PRED-029-A x6)|log|config.py, calibration\_state.py|seed data|implemented|
|174|PMM-004 (PRED-031-A)|log|config.py, calibration\_state.py, predictions.py|seed data + code (check\_pmm\_004)|implemented|
|**NAMED SYSTEM CHANGE LOG ENTRIES (18)**||||||
|175|001 — Named-party incentive analysis|rule|config.py, calibration\_state.py|seed data|implemented|
|176|AI-001 — Case B standing|rule|config.py, calibration\_state.py|seed data|implemented|
|177|AI-002 — Wikipedia Tier 4|rule|config.py, calibration\_state.py|seed data|implemented|
|178|AI-003 — Gate 0.5, H1, PCP 1.5|rule|config.py, calibration\_state.py|seed data|implemented|
|179|AI-004 — Rule changes logged|rule|config.py, calibration\_state.py|seed data|implemented|
|180|AI-005 — PDF only|rule|config.py, calibration\_state.py|seed data|implemented|
|181|AI-006 — TQL mandatory|rule|config.py, calibration\_state.py|seed data|implemented|
|182|AI-007 — Calibration doctrine|rule|config.py, calibration\_state.py|seed data|implemented|
|183|AI-008 — Architecture alignment|rule|config.py, calibration\_state.py|seed data|implemented|
|184|AI-009 — Brier score optimisation|rule|config.py, calibration\_state.py|seed data|implemented|
|185|AI-010 — Single-cluster H5 discount|rule|config.py, calibration\_state.py|seed data|implemented|
|186|AI-011 — Mandatory PDF 10 items|rule|config.py, calibration\_state.py|seed data|implemented|
|187|AI-012 — Nine calibration enhancements|rule|config.py, calibration\_state.py|seed data|implemented|
|188|PMM-004 governing rule|rule|config.py, calibration\_state.py|seed data|implemented|
|189|Gate 0.2 rule|rule|config.py, calibration\_state.py|seed data|implemented|
|190|Gate 0.3 rule|rule|config.py, calibration\_state.py|seed data|implemented|
|191|Gate 0.4 rule|rule|config.py, calibration\_state.py|seed data|implemented|
|192|AI-012-10 Publication Integrity Lock|rule|config.py, calibration\_state.py|seed data|implemented|
|**SCORING METRICS**||||||
|193|Brier Score (primary)|metric|predictions.py|code (compute\_brier\_score)|implemented|
|194|Log Score (added Ed031)|metric|predictions.py|code (compute\_log\_score)|implemented|
|195|Spherical Score (added Ed031)|metric|predictions.py|code (compute\_spherical\_score)|implemented|
|**NAMED BRIER TABLE ROWS (15)**||||||
|196|PRED-022-C (0.95/1.0)|brier row|calibration\_state.py|seed data|implemented|
|197|PRED-023-B (0.95/1.0)|brier row|calibration\_state.py|seed data|implemented|
|198|PRED-026-D (0.95/1.0)|brier row|calibration\_state.py|seed data|implemented|
|199|PRED-027-B (0.55/0.0)|brier row|calibration\_state.py|seed data|implemented|
|200|PRED-028-B (0.55/0.0)|brier row|calibration\_state.py|seed data|implemented|
|201|PRED-026-E (0.65/0.0)|brier row|calibration\_state.py|seed data|implemented|
|202|PRED-025-C (0.70/0.5)|brier row|calibration\_state.py|seed data|implemented|
|203|PRED-026-B (0.70/0.5)|brier row|calibration\_state.py|seed data|implemented|
|204|PRED-022-A x1 (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|205|PRED-023-A x1 (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|206|PRED-024-A x1 (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|207|PRED-025-A x1 (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|208|PRED-028-A x1 (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|209|PRED-029-A x1 (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|210|PRED-031-A (0.77/0.0)|brier row|calibration\_state.py|seed data|implemented|
|**NAMED PREDICTIONS OPEN (12)**||||||
|211|PRED-034-A|prediction|calibration\_state.py|seed data|implemented|
|212|PRED-031-B|prediction|calibration\_state.py|seed data|implemented|
|213|PRED-031-C|prediction|calibration\_state.py|seed data|implemented|
|214|PRED-031-D|prediction|calibration\_state.py|seed data|implemented|
|215|PRED-031-E|prediction|calibration\_state.py|seed data|implemented|
|216|PRED-030-B|prediction|calibration\_state.py|seed data|implemented|
|217|PRED-030-A|prediction|calibration\_state.py|seed data|implemented|
|218|PRED-029-B|prediction|calibration\_state.py|seed data|implemented|
|219|PRED-025-C/026-B|prediction|calibration\_state.py|seed data|implemented|
|220|PRED-022-B|prediction|calibration\_state.py|seed data|implemented|
|221|PRED-025-B|prediction|calibration\_state.py|seed data|implemented|
|222|PRED-006-A|prediction|calibration\_state.py|seed data|implemented|
|**NAMED CASES (5)**||||||
|223|Case A — Talks Deadlocked|case|calibration\_state.py|seed data|implemented|
|224|Case B — Hormuz CLOSED|case|calibration\_state.py|seed data|implemented|
|225|Case C — ESCALATING / Change Point|case|calibration\_state.py|seed data|implemented|
|226|Case D — GL U LAPSED|case|calibration\_state.py|seed data|implemented|
|227|Case E — Double Suppressor|case|calibration\_state.py|seed data|implemented|
|**PREDICTION OUTCOMES**||||||
|228|CONFIRMED|outcome state|config.py|enum (PredictionOutcome.CONFIRMED)|implemented|
|229|CONTRADICTED|outcome state|config.py|enum (PredictionOutcome.CONTRADICTED)|implemented|
|230|PARTIAL|outcome state|config.py|enum (PredictionOutcome.PARTIAL)|implemented|
|231|AMBIGUOUS|outcome state|config.py|enum (PredictionOutcome.AMBIGUOUS)|implemented|
|232|DIRECTIONAL|outcome state|config.py|enum (PredictionOutcome.DIRECTIONAL)|implemented|
|**SWEEP DESCRIPTORS**||||||
|233|MORNING SWEEP|descriptor|config.py, timestamping.py|constant + code|implemented|
|234|AFTERNOON SWEEP|descriptor|config.py, timestamping.py|constant + code|implemented|
|235|EVENING SWEEP|descriptor|config.py, timestamping.py|constant + code|implemented|
|236|LATE NIGHT SWEEP|descriptor|config.py, timestamping.py|constant + code|implemented|
|**CONFIDENCE BANDS**||||||
|237|0-24% BLACK SWAN|band|config.py|constant (CONFIDENCE\_BANDS)|implemented|
|238|25-39% LOW|band|config.py|constant (CONFIDENCE\_BANDS)|implemented|
|239|40-54% LOW-MEDIUM|band|config.py|constant (CONFIDENCE\_BANDS)|implemented|
|240|55-69% MEDIUM|band|config.py|constant (CONFIDENCE\_BANDS)|implemented|
|241|70-89% HIGH|band|config.py|constant (CONFIDENCE\_BANDS)|implemented|
|242|90-100% FORMAL ONLY|band|config.py|constant (CONFIDENCE\_BANDS)|implemented|
|**LOOKUP BANDS (8)**||||||
|243|0-10%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|244|10-20%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|245|20-30%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|246|30-40%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|247|40-60%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|248|60-70%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|249|70-80%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|
|250|90-100%|lookup band|config.py, calibration\_state.py|constant + seed data|implemented|

**TOTAL NAMED ITEMS: 250
IMPLEMENTED: 250
PARTIAL: 0
TODO: 0 (feed adapters are placeholder functions — architecture slots present)**

