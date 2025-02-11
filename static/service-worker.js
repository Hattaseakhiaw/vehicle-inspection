self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('vehicle-inspection-v1').then(function(cache) {
            return cache.addAll([
                '/',
                '/static/bootstrap.min.css',
                '/static/manifest.json',
                '/static/service-worker.js'
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});
