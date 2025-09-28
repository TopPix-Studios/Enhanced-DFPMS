const cacheName = "DFPS-v1";
const staticAssets = [
  "/",
  "/offline/",
  "/static/manifest.json",

  // 🟦 CSS Files
  "/static/res-360/freelancer-content-360.css",
  "/static/res-360/guest-content-r360.css",

  "/static/admin-content-1.css",
  "/static/admin_index.css",
  "/static/announcement.css",
  "/static/calendar.css",
  "/static/certificate-view.css",
  "/static/cropping.css",
  "/static/event-tab-prof.css",
  "/static/event-tab.css",
  "/static/event.css",
  "/static/experience-pagination.css",
  "/static/experience-view.css",
  "/static/footer.css",
  "/static/graphs.css",
  "/static/guest-content.css",
  "/static/guest_event.css",
  "/static/guest_priv.css",
  "/static/header.css",
  "/static/home.css",
  "/static/language-view.css",
  "/static/login.css",
  "/static/notification.css",
  "/static/priv_modal.css",
  "/static/profile_page.css",
  "/static/project.css",
  "/static/resume-project-form.css",
  "/static/select2.css",
  "/static/settings.css",
  "/static/sidebar.css",
  "/static/signup-1.css",
  "/static/skill-view.css",
  "/static/ticket.css",

  // 🟨 JS Files
  "/static/js/chart.js",
  "/static/js/event_admin.js",
  "/static/js/generateEventPDF.js",
  "/static/js/generateEventStatistic.js",
  "/static/js/generatePDF.js",
  "/static/js/location_map.js",
  "/static/js/map_widget_ann.js",
  "/static/js/map_widget_eve.js",

  // 🗺️ JSON / GEO
  "/static/js/boundary.geojson",
  "/static/js/gensan.json",

  // 🖼️ Icons & Images (sample)
  "/static/icons/icon-192x192.png",
  "/static/icons/icon-512x512.png",
  "/static/img/header.jpeg",
  "/static/img/logo.png",
  "/static/img/error_404.png",
  "/static/img/gensan-bg.jpg",
  "/static/img/Login Image.png",
];

self.addEventListener("install", event => {
    event.waitUntil(
      caches.open(cacheName).then(cache => {
        console.log("Installing and caching:", staticAssets);
        return Promise.allSettled(
          staticAssets.map(url => {
            return cache.add(url).catch(err => {
              console.error("❌ Failed to cache:", url, err);
            });
          })
        );
      })
    );
  });
  

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== cacheName).map(key => caches.delete(key))
      );
    })
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    fetch(event.request).catch(() => {
      if (event.request.mode === "navigate") {
        return caches.match("/offline/");
      }
      return caches.match(event.request);
    })
  );
});
