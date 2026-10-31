# WARD TEN — original v08 script and timed shot list

**Premise:** A hospital night-shift handover board says ten beds; its observation chart lists ten patients, but the call log records eleven bells. Bed 11 appears without an admission. The extra record is a discharge, not an admission: the system discharges the nurse reading it. **Format:** 60.000 s, 30 fps, vertical 1080×1920 plus a 1920×1080 landscape derivative. **Signature:** coherent, readable invented hospital UI — handover board, observation chart, call log and discharge slip — with real numerical disagreement. This is fiction, not clinical guidance.

## Narration

At two seventeen a.m., you take over Ward Ten.  
The handover board says ten beds.  
The observation chart says ten patients.  
The call-bell log says eleven bells.  
The extra bell comes from Bed Eleven.  
No one was admitted to that bed.  
Your rule: answer every bell before you sign.

Ten beds are occupied. Ten names on the chart.  
Then the eleventh bell rings again.  
Down the corridor, an unmarked door stands open.  
An empty bed waits inside.  
The chart still says ten.  
The discharge printer starts.  
The form says Bed Eleven.

*[Long, deliberate pause before the betrayal.]*

The patient's name is yours.  
The ward isn't admitting anyone.  
It is discharging you.  
Your staff badge goes blank.  
The patient count stays ten.  
At shift change, the eleventh bell rings again.  
It is asking for the next nurse.

## Timed picture plan, committed before picture generation

30 hard-cut shots: a repeating 54/60/66 frames (1.8/2.0/2.2 s), **2.000 s average**, faster than v07's 2.4 s. Each has a slow eased push plus one small moving UI indicator. Shots 14–15 use genuine one-point depth, not only flat cards. Story-to-shot assignment may be adjusted to measured speech boundaries before final render, without changing the 1,800-frame total.

| Shot | Time (s) | Composition / purpose |
|---:|---:|---|
| 01 | 0.000–1.800 | Ward handover terminal: 02:17 A.M. and WARD TEN identify time and place. |
| 02 | 1.800–3.800 | Handover bed board: capacity reads TEN BEDS. |
| 03 | 3.800–6.000 | Occupied-bed tiles: ten lit slots, all accounted for. |
| 04 | 6.000–7.800 | Observation chart: TEN PATIENTS with ten numbered lines. |
| 05 | 7.800–9.800 | Chart close-up, ten patient rows and a slowly sweeping marker. |
| 06 | 9.800–12.000 | Call-bell log: ELEVEN BELLS; the total contradicts both screens. |
| 07 | 12.000–13.800 | Log isolates an eleventh call from BED 11. |
| 08 | 13.800–15.800 | Admission search for Bed 11 returns NO ADMISSION. |
| 09 | 15.800–18.000 | Admission search completes; no one was admitted to Bed 11. |
| 10 | 18.000–19.800 | Handover protocol: answer every call before signing. |
| 11 | 19.800–21.800 | Board recheck: ten beds are occupied. |
| 12 | 21.800–24.000 | Observation chart recheck: ten names. |
| 13 | 24.000–25.800 | Call-bell pulse graph and the unassigned eleventh entry. |
| 14 | 25.800–27.800 | Depth shot: one-point hospital corridor recedes to an unmarked open door. |
| 15 | 27.800–30.000 | The open unmarked doorway draws nearer through a receding corridor. |
| 16 | 30.000–31.800 | Doorway view: an empty bed inside, drawn in one-point perspective. |
| 17 | 31.800–33.800 | A closer view of the empty bed; observation chart is glimpsed. |
| 18 | 33.800–36.000 | Observation chart still totals ten as the printer wakes. |
| 19 | 36.000–37.800 | Discharge printer feeds a new form. |
| 20 | 37.800–39.800 | Printer form specifies Bed 11; identity is not yet revealed. |
| 21 | 39.800–42.000 | Unrevealed form and a quiet hold for the deliberate pause. |
| 22 | 42.000–43.800 | Close discharge form: patient field remains obscured at first. |
| 23 | 43.800–45.800 | The form identifies its patient as YOU. |
| 24 | 45.800–48.000 | The ward action changes to DISCHARGE, not admission. |
| 25 | 48.000–49.800 | The staff badge is erased from the display. |
| 26 | 49.800–51.800 | Patient chart still counts ten. |
| 27 | 51.800–54.000 | At shift change the handover board refreshes. |
| 28 | 54.000–55.800 | The eleventh bell log pulses again. |
| 29 | 55.800–57.800 | Next-shift board: one call is waiting. |
| 30 | 57.800–60.000 | Call-bell destination reads NEXT NURSE. |

## Sound and caption plan

Use the same independently selected `en-US-ChristopherNeural` voice as v07, Edge TTS rate −12% and pitch −4 Hz, capture word-level timings, and commit an offline stem. Music and dry call-bell/printer effects are newly synthesized; the music target is 8–12 LU below the isolated voice stem. Burn readable 2–5-word beats, carry an SRT, and verify actual alignment. Mix to −16 LUFS ±0.5 and true peak ≤−1 dBTP; numerical and structural checks do not constitute human listening. The sequel hook is an original next-nurse call, not the references' catchphrase.
