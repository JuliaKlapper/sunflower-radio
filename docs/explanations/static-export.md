# Why static export? (D5 / Q14, plain-language explanation)

A Next.js app can be served two fundamentally different ways.

## (A) The "live server" way (normal Next.js)

You run Next.js as a *constantly-running program* (`next start`). Every
time a browser asks for a page, that program builds the page on the spot
and sends it. It's powerful — it can do work on the server per-request —
but it's a **second always-on process** that eats memory and must be kept
alive, restarted on crashes, updated, etc.

## (B) Static export (what we chose)

Instead of running Next.js live, you run `next build` **once on your
laptop**. It pre-bakes the entire app into a folder of plain files — HTML,
JavaScript, CSS — called `out/`. Those are just *dead files*. No Next.js
program runs anywhere. You copy that folder to the Pi, and the Pi's
FastAPI (already running for the radio API) just hands those files to the
browser like any plain web page. The browser downloads the JavaScript and
the app "comes alive" *in the browser*, then talks to the Pi's `/api` for
radio data.

## Why (B) for this project

1. **The Pi Zero 2 W has only 512 MB of RAM.** Option (A) means running
   *two* programs on that tiny box: Python (radio + API) **and** a Node.js
   Next.js server. Static export means **one** program (FastAPI) serves
   both the API and the web files. Half the memory footprint, half the
   things that can crash. **This is the big one.**

2. **You don't need anything the live server offers.** Option (A)'s whole
   value is doing work *on the server per request* — server-side
   rendering, database calls, etc. This UI is a simple control panel: it
   just needs to show the current station/volume and send commands. All of
   that is the *browser* talking to FastAPI `/api`. There's no server-side
   work for Next.js to do, so you'd pay for a second daemon and get
   nothing back.

3. **One device, one URL, one program.** Phone, laptop, tablet all open
   `http://192.168.1.106/`. FastAPI serves the web page at `/` and the API
   at `/api`. Because it's all **one origin**, you also dodge CORS and auth
   headaches (ties into D5 and D10).

4. **Simpler deployment.** Deploying is just "copy a folder of files to the
   Pi." No Node runtime to install on the Pi, no Next.js server process to
   supervise, no `next start` in systemd. The static files are trivial for
   even a weak Pi to serve.

## What you give up (and why it doesn't hurt)

No Server Components, no server actions, no Next route handlers, no Pi-side
image optimization — none of which a JSON-driven radio remote needs. And
it's **not a one-way door**: if a future feature ever truly needs a live
Next server, switching to (A) is mechanical.

## One sentence

Static export means Next.js pre-bakes your UI into plain files on your
laptop, so the memory-starved Pi runs just *one* program (FastAPI) to serve
both the web page and the radio API — instead of babysitting a second
always-on Node server it would gain nothing from.

---

*Related decisions: D4 (merged async process), D5/C1 (static export served
by the Pi), Q14 (App Router), D10 (LAN-only, no auth).*
