// A test of the link simulated in the page (site/link.js), without a network: six bodies of known sizes, all there
// at once, go through one link at 2 Mbit/s while the page's thread is blocked for 0.4 s in the middle (what a long
// task does). Checked against the rule itself:
//   turns   two chunks in a row never go to the same download while another has bytes waiting;
//   order   the downloads end in the order their sizes give under equal turns;
//   times   each ends within 0.15 s of the time the rule gives (slots of chunk / rate, the pause's loss beyond the
//           0.1 s burst added);
//   rate    the whole transfer's rate, the pause's loss taken out, is within 2 % of the set rate.
// module=URL tests another copy of the link (an earlier one must fail "turns": the test's own control).
const Q = new URLSearchParams(location.search);
const out = document.getElementById('out');
const say = (s) => { out.textContent += s + '\n'; };
window.testerState = () => null;

async function main() {
  const { PageLink } = await import(Q.get('module') || '../../site/link.js');
  const RATE = 250000, SIZES = [300000, 200000, 250000, 150000, 100000, 220000], STALL_AT = 1.0, STALL = 0.4;
  const link = new PageLink();
  link.reset();
  link.setRate(RATE);
  const chunk = link.chunk();
  const body = (n) => new ReadableStream({ start(c) { for (let o = 0; o < n; o += 65536) c.enqueue(new Uint8Array(Math.min(65536, n - o))); c.close(); } });
  const t0 = performance.now() / 1000;
  const ends = [], got = SIZES.map(() => 0);
  setTimeout(() => { const until = performance.now() + STALL * 1000; while (performance.now() < until) { /* the page's thread is busy */ } }, STALL_AT * 1000);
  await Promise.all(SIZES.map((n, i) => link.send(body(n).getReader(), (v) => { got[i] += v.length; }, 'body ' + i).then(() => { ends[i] = performance.now() / 1000 - t0; })));
  const log = link.log;
  // turns: between two chunks of the same download in a row, no other download may have had bytes waiting
  const left = SIZES.slice();
  let runs = 0, longest = 1, cur = 1;
  for (let k = 0; k < log.length; k++) {
    const i = +log[k][2].slice(5);
    left[i] -= log[k][1];
    if (k + 1 < log.length && log[k + 1][2] === log[k][2]) {
      const others = left.some((b, j) => j !== i && b > 0);
      if (others) { runs++; cur++; longest = Math.max(longest, cur); }
    } else cur = 1;
  }
  // the rule's own times: chunks in turn, a slot each; the pause loses its length beyond the burst
  const rem = SIZES.slice(), ideal = [];
  let slot = 0, live = SIZES.map((_, i) => i);
  while (live.length) {
    for (const i of live.slice()) { const n = Math.min(chunk, rem[i]); rem[i] -= n; slot += n / RATE; if (rem[i] === 0) { ideal[i] = slot; live = live.filter((x) => x !== i); } }
  }
  const lost = Math.max(0, STALL - 0.1);
  const expect = ideal.map((t) => t - 0.1 + (t - 0.1 > STALL_AT ? lost : 0));
  const worst = Math.max(...ends.map((t, i) => Math.abs(t - expect[i])));
  const order = ends.map((t, i) => [t, i]).sort((a, b) => a[0] - b[0]).map((x) => x[1]);
  const want = ideal.map((t, i) => [t, i]).sort((a, b) => a[0] - b[0]).map((x) => x[1]);
  const total = SIZES.reduce((a, b) => a + b, 0);
  const span = log[log.length - 1][0] - log[0][0] - lost;
  const rate = (total - log[0][1]) / span;
  const R = {
    module: Q.get('module') || 'site/link.js', chunks: log.length, bytes: got, complete: got.every((b, i) => b === SIZES[i]),
    turns: { sameDownloadTwiceWhileAnotherWaited: runs, longestRun: longest, pass: runs === 0 },
    order: { got: order, want, pass: JSON.stringify(order) === JSON.stringify(want) },
    times: { ends: ends.map((t) => +t.toFixed(3)), rule: expect.map((t) => +t.toFixed(3)), worst: +worst.toFixed(3), pass: worst <= 0.15 },
    rate: { measured: Math.round(rate * 8), set: RATE * 8, error: +(rate / RATE - 1).toFixed(4), pass: Math.abs(rate / RATE - 1) <= 0.02 },
  };
  R.pass = R.complete && R.turns.pass && R.order.pass && R.times.pass && R.rate.pass;
  say(JSON.stringify(R, null, 1));
  window.testerResult = JSON.stringify(R);
}
main().catch((e) => { say('failed: ' + (e.stack || e)); window.testerResult = JSON.stringify({ failed: String(e.stack || e), pass: false }); });
