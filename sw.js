// Service worker: keeps the whole app on the device so it works offline and can be installed.
// CACHE is stamped with a hash of index.html at build time, so a new build replaces the old copy.
const CACHE = "uneasy-alliances-374721027ee7";
const ASSETS = ["./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  // every navigation (including the start URL) is answered with the cached page
  if (req.mode === "navigate") {
    e.respondWith(caches.match("./index.html").then(hit => hit || fetch(req)));
    return;
  }
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok && new URL(req.url).origin === location.origin) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match("./index.html")))
  );
});
