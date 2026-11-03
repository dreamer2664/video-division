#!/usr/bin/env python3
"""Build a self-contained, blind A–E listening page from the adjacent MP3s."""
from base64 import b64encode
from pathlib import Path

HERE = Path(__file__).resolve().parent

HEAD = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="referrer" content="no-referrer">
<title>Blind listening · Five voices</title>
<style>
:root{color-scheme:light;--ink:#222825;--muted:#626c65;--paper:#f7f6f1;--card:#fff;--line:#dedfd6;--green:#315643;--pale:#e7eee8;--focus:#176846;font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-size:16px;line-height:1.5}button,input,textarea{font:inherit}button:focus-visible,input:focus-visible,textarea:focus-visible,audio:focus-visible{outline:3px solid #69a883;outline-offset:3px}.shell{max-width:1120px;margin:auto;padding:30px 28px 74px}.mast{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #cfd3c8;padding-bottom:20px}.brand{font-size:.78rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}.brand span{color:#7f8c7e;margin:0 .55em}.badge{border:1px solid #a6b7a8;border-radius:100px;padding:6px 11px;color:var(--green);background:#f1f5ef;font-size:.68rem;font-weight:800;letter-spacing:.11em;text-transform:uppercase;white-space:nowrap}.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:38px;align-items:end;padding:56px 0 40px}.eyebrow{font-size:.72rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:var(--green);margin:0 0 13px}.hero h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(2.6rem,6vw,5rem);line-height:1.04;letter-spacing:-.035em;margin:0}.hero h1 em{font-weight:400;color:var(--green)}.lede{color:var(--muted);max-width:44ch;margin:0;font-size:1rem}.guide{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--line);border-radius:14px;background:#fdfdfb;overflow:hidden}.guide div{padding:19px 20px}.guide div+div{border-left:1px solid var(--line)}.step{font-size:.67rem;font-weight:800;color:#87938a;letter-spacing:.13em}.guide strong{display:block;font-size:.92rem;margin:6px 0 3px}.guide p{margin:0;color:var(--muted);font-size:.84rem}.section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:45px 0 17px}.section-head h2,.result h2{font-family:Georgia,"Times New Roman",serif;font-size:1.65rem;font-weight:400;margin:0}.section-head p{margin:0;color:var(--muted);font-size:.85rem}.button{border:1px solid #bfc9bd;border-radius:8px;background:#fff;color:var(--green);font-size:.82rem;font-weight:700;padding:9px 13px;cursor:pointer;white-space:nowrap}.button:hover{background:var(--pale)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.sample{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:22px;min-width:0;box-shadow:0 3px 9px #1e2a1d08}.sample-head{display:flex;align-items:center;gap:13px;margin-bottom:14px}.letter{width:44px;height:44px;display:grid;place-items:center;border-radius:50%;background:var(--pale);color:var(--green);font-family:Georgia,serif;font-size:1.5rem}.sample h3{font-size:1rem;margin:0}.sample-sub{font-size:.75rem;color:var(--muted);margin:2px 0 0}.sample audio{display:block;width:100%;height:42px;min-width:0}fieldset{border:0;padding:0;margin:19px 0 0;min-width:0}legend{font-size:.8rem;font-weight:700;padding:0;margin-bottom:9px}.scale{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.scale label{cursor:pointer;display:flex;align-items:center;gap:4px;justify-content:center;border:1px solid #d8ded6;border-radius:7px;padding:6px 9px;font-size:.78rem}.scale label:has(input:checked){border-color:var(--green);background:var(--pale)}input[type=radio]{accent-color:var(--green);margin:0}.hint{font-weight:400;color:var(--muted);font-size:.75rem}.result{background:#eff3ed;border:1px solid #d5dfd4;border-radius:14px;margin-top:36px;padding:27px}.result p{color:var(--muted);font-size:.9rem}.pick{display:flex;gap:9px;flex-wrap:wrap}.pick label{display:flex;align-items:center;gap:7px;border:1px solid #c7d3c6;border-radius:8px;padding:8px 13px;background:#fff;cursor:pointer}.note-label{display:block;margin:22px 0 8px;font-size:.85rem;font-weight:700}textarea{display:block;width:100%;min-height:90px;resize:vertical;border:1px solid #c7d3c6;border-radius:8px;padding:10px;color:var(--ink);background:#fff}.actions{display:flex;align-items:center;gap:13px;flex-wrap:wrap;margin-top:18px}.actions .primary{background:var(--green);border-color:var(--green);color:#fff}.privacy{font-size:.78rem;color:var(--muted)}footer{padding-top:24px;color:#7e877e;font-size:.75rem}
@media(max-width:700px){.shell{padding:22px 17px 55px}.mast{align-items:start}.hero{display:block;padding:44px 0 30px}.lede{margin-top:20px}.guide{grid-template-columns:1fr}.guide div+div{border-left:0;border-top:1px solid var(--line)}.grid{grid-template-columns:1fr}.section-head{align-items:start;flex-direction:column}.sample{padding:18px}}
@media print{body{background:#fff;font-size:11pt}.shell{max-width:none;padding:0}.hero{padding:20px 0}.hero h1{font-size:32pt}.guide{grid-template-columns:repeat(3,1fr)}.grid{grid-template-columns:repeat(2,1fr);gap:8pt}.sample{box-shadow:none;break-inside:avoid;padding:12pt}.sample audio,.button,.privacy{display:none}.result{break-inside:avoid;margin-top:14pt;padding:12pt}textarea{min-height:70pt}footer{padding-top:8pt}}
</style>
</head>
<body>
<div class="shell">
<header class="mast"><div class="brand">REEL <span>/</span> LISTENING LAB</div><div class="badge">Blind comparison</div></header>
<section class="hero" aria-labelledby="title"><div><p class="eyebrow">A listening exercise · 05 samples</p><h1 id="title">Five voices.<br><em>One line.</em></h1></div><p class="lede">Each sample reads the same sentence. Listen for the voice that feels most natural and believable to you. There is no marked favourite.</p></section>
<section class="guide" aria-label="How to listen"><div><span class="step">01 / SET UP</span><strong>Find a quiet space</strong><p>Use the same headphones or speakers and volume throughout.</p></div><div><span class="step">02 / LISTEN</span><strong>Play and replay</strong><p>Listen to all five before making your choice. You can change the order.</p></div><div><span class="step">03 / RECORD</span><strong>Rate your impression</strong><p>Score naturalness, choose a favourite, and note what you heard.</p></div></section>
<form id="listening-form" onsubmit="return false">
<div class="section-head"><div><p class="eyebrow">The samples</p><h2>Listen to the samples</h2><p>Level-matched excerpts · ratings are optional</p></div><button class="button" id="shuffle" type="button">Shuffle listening order</button></div>
<div class="grid" id="samples">
'''
TAIL = '''</div>
<section class="result" aria-labelledby="result-title"><p class="eyebrow">Your verdict</p><h2 id="result-title">Which felt most natural?</h2><p>Choose one, then record any hesitations, distracting qualities or pronunciation issues.</p>
<fieldset><legend>Favourite sample</legend><div class="pick">
<label><input type="radio" name="favourite" value="A"> A</label><label><input type="radio" name="favourite" value="B"> B</label><label><input type="radio" name="favourite" value="C"> C</label><label><input type="radio" name="favourite" value="D"> D</label><label><input type="radio" name="favourite" value="E"> E</label><label><input type="radio" name="favourite" value="none"> No preference</label>
</div></fieldset><label class="note-label" for="notes">Notes</label><textarea id="notes" name="notes" placeholder="What stood out? What sounded artificial or believable?"></textarea>
<div class="actions"><button class="button primary" type="button" onclick="window.print()">Print or save as PDF</button><button class="button" type="reset">Clear ratings</button><span class="privacy">Nothing is sent or saved automatically. Record or print your results before closing.</span></div></section>
</form><footer>Offline listening page · the samples contain no voice names or recommended choice</footer>
</div>
<script>
(function(){
  const audio = Array.from(document.querySelectorAll('audio'));
  audio.forEach(function(player){player.addEventListener('play',function(){audio.forEach(function(other){if(other!==player)other.pause();});});});
  document.getElementById('shuffle').addEventListener('click',function(){
    const grid=document.getElementById('samples'), cards=Array.from(grid.children);
    for(let i=cards.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[cards[i],cards[j]]=[cards[j],cards[i]];}
    cards.forEach(function(card){grid.appendChild(card);});
  });
})();
</script>
</body>
</html>
'''

def sample(letter):
    path = HERE / f'voice-{letter}.mp3'
    data = b64encode(path.read_bytes()).decode('ascii')
    choices = ''.join(f'<label><input type="radio" name="score-{letter}" value="{n}"> {n}</label>' for n in range(1, 6))
    return f'''<article class="sample" data-sample="{letter}"><div class="sample-head"><div class="letter" aria-hidden="true">{letter}</div><div><h3>Sample {letter}</h3><p class="sample-sub">Same sentence · excerpt {letter}</p></div></div>
<audio controls preload="none" aria-label="Play sample {letter}"><source src="data:audio/mpeg;base64,{data}" type="audio/mpeg">Your browser does not support inline audio.</audio>
<fieldset><legend>Naturalness <span class="hint">· 1 robotic / 5 natural</span></legend><div class="scale" aria-label="Naturalness rating for sample {letter}">{choices}</div></fieldset></article>
'''

html = HEAD + ''.join(sample(c) for c in 'ABCDE') + TAIL
(HERE / 'blind-listen.html').write_text(html, encoding='utf-8')
print('Wrote blind-listen.html with 5 embedded MP3s:', len(html.encode('utf-8')), 'bytes')
