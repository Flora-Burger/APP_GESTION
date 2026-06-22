const CACHE_VERSION = "flora-pwa-v1";
const RESSOURCES_STATIQUES = [
    "/static/css/style.css",
    "/static/css/mobile.css",
    "/static/img/logo.svg",
];

self.addEventListener("install", function(event) {
    event.waitUntil(
        caches.open(CACHE_VERSION).then(function(cache) {
            return cache.addAll(RESSOURCES_STATIQUES);
        })
    );
    self.skipWaiting();
});

self.addEventListener("activate", function(event) {
    event.waitUntil(
        caches.keys().then(function(cles) {
            return Promise.all(
                cles.filter(function(cle) {
                    return cle !== CACHE_VERSION;
                }).map(function(cle) {
                    return caches.delete(cle);
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener("fetch", function(event) {
    var url = new URL(event.request.url);
    if (event.request.method !== "GET") {
        return;
    }
    if (url.pathname.startsWith("/static/")) {
        event.respondWith(
            caches.match(event.request).then(function(reponseCache) {
                return reponseCache || fetch(event.request);
            })
        );
        return;
    }
    event.respondWith(
        fetch(event.request).catch(function() {
            return caches.match(event.request);
        })
    );
});
