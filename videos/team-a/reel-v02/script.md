# Waiting has a curve — final script and shot plan

**Written before rendering.** Format: 60.000 seconds, 1920×1080, 30 fps. A complete, self-contained explainer told with kinetic type, diagrams, and an original instrumental score; there is **no spoken narration**. The on-screen caption line is burned into each shot and `captions.srt` also carries the full copy for accessibility. All on-screen type is at least 40 px at 1080p.

**One idea:** As a variable system approaches its capacity, average waiting time grows disproportionately. Reserving capacity is not necessarily waste; it absorbs variability.

## Exact model behind the comparison

A single-server M/M/1 queue, FIFO, steady state, independent Poisson arrivals, exponentially distributed service times, service rate μ = 1 order/minute, utilization ρ < 1. Waiting is **before** service. The expected queue wait is `Wq = ρ / (μ × (1 − ρ))`. At ρ = 0.50, Wq = 1 minute; at ρ = 0.90, Wq = 9 minutes. This is a deliberately simple model, not a prediction for every real café; real arrival/service patterns can change the result. The animated dots are a conceptual illustration, not a simulation or a measured sample.

## Picture, copy, and timing

| Time | Picture / movement | On-screen caption (also in SRT) |
|---|---|---|
| **00:00–00:06** | **Hook.** High-contrast title: “WHY DOES WAITING EXPLODE?” A line of moving order tokens accelerates toward a bottleneck; a clock hand sweeps. | Why does waiting explode before a system is full? |
| **00:06–00:13** | Establish the system. “ONE ORDER / A MINUTE” beside an animated one-server machine. An order token crosses the counter; the dial cycles. | One barista finishes one order a minute, on average. |
| **00:13–00:21** | A rhythmic incoming stream changes from evenly spaced to bunched; tokens compress toward the counter. Large type: “REAL LIFE ISN'T EVEN.” | But arrivals and service times vary. Little rushes make a queue. |
| **00:21–00:29** | Reveal the baseline as an animated half-full utilization dial. The time ruler fills one unit. Persistent label: “SIMPLE RANDOM QUEUE MODEL.” | At 50% busy, this model predicts a 1-minute average wait. |
| **00:29–00:39** | Match cut to a 90% dial. Nine time-ruler units fill one by one; “9×” appears. The server rate has not changed. Persistent model label and “BEFORE SERVICE” remove ambiguity. | At 90% busy, the average wait is 9 minutes—before service. |
| **00:39–00:49** | A curve draws upward: horizontal axis = utilization, vertical axis = average queue wait. Mark the two computed points (50%, 1 min) and (90%, 9 min). | In this random queue model, waiting rises nonlinearly. |
| **00:49–00:56** | The overloaded capacity bar drains to leave a visible buffer. Tokens move smoothly again. | Spare capacity absorbs the unexpected instead of passing it on as delay. |
| **00:56–01:00** | **Ending.** Typographic payoff: “SPACE ISN'T WASTE. IT'S RESILIENCE.” The incoming tokens find room; the progress line reaches its end. | Leave room for the rush. |

## Sound, captioning, and pacing

A soft, original, code-synthesized electronic score advances continuously, with small percussive accents and a closing cadence. There is no stock footage, voice, commercial library, or music sample. All graphics and sound are generated in-repo; bundled fonts retain their own licence. The caption bar is part of the render, and `captions.srt` provides the same editorial text plus the music description. Shots have animated entrances and continuously moving diagrams, not static slides.

## Motion revision — written before the replacement render

The fresh audit found that the earlier piece was visually sparse and held some comparisons for too long. Keep the same exact story, model, timing, captions, colours, and original music; replace decorative holding with progressive, explanatory movement. The eight original time ranges remain the governing shot timings above.

| Time | Revised within-shot development |
|---|---|
| 00:00–00:06 | Stagger the kinetic title; a clock and a row of order tokens build towards a visible bottleneck instead of presenting a single static title card. |
| 00:06–00:13 | Introduce the average rate, then visibly move several tokens through a single service station; the service meter cycles as each token crosses. |
| 00:13–00:21 | Contrast an even stream with a bunched stream on two moving tracks; the server gate makes the rush and variability visible. |
| 00:21–00:29 | Draw the 50% gauge and reveal the one-minute ruler; then show a token traversing that short wait and reveal the room-to-recover idea. |
| 00:29–00:39 | Draw the 90% gauge and build the nine-minute ruler progressively across the shot, then land the nine-times comparison; the result remains before service. |
| 00:39–00:49 | Trace the actual queueing curve over most of the shot, deliberately revealing 50% / 1 minute first and 90% / 9 minutes near the end. |
| 00:49–00:56 | Reduce a nine-tenths-full capacity strip gradually to seven-tenths while moving the burst into the newly empty buffer; keep this conceptual, not an empirical simulation. |
| 00:56–01:00 | Stagger the payoff lines and let the tokens exit cleanly; retain the complete ending and fade of the original score. |

The replacement uses a higher average-bitrate encode as well as more substantive visual development; a larger file alone is not treated as a quality improvement. Do not add unlicensed source material or change the model assumptions.
