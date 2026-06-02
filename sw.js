// Service worker: network-first для страницы и workouts.json (свежие данные онлайн),
// cache-first для иконок/манифеста. Офлайн в зале — отдаём кэш.
const CACHE = "workout-v5";
const ASSETS = [
  "./", "./index.html", "./workouts.json", "./manifest.webmanifest",
  "./icon-192.png", "./icon-512.png", "./icon-180.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  const isData = url.pathname.endsWith("workouts.json");
  // навигация (HTML) и данные → сеть, потом кэш
  if (req.mode === "navigate" || isData) {
    const key = req.mode === "navigate" ? "./index.html" : "./workouts.json";
    e.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(key, copy));
        return res;
      }).catch(() => caches.match(key))
    );
    return;
  }
  // прочее → кэш, потом сеть
  e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
