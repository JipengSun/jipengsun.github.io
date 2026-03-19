/**
 * GA4 click tracking for specific links (invisible to visitors).
 * Links with data-ga-event="event_name" send a gtag event on click.
 */
(function () {
  if (typeof gtag !== 'function') return;
  document.body.addEventListener('click', function (e) {
    var link = e.target.closest('a[data-ga-event]');
    if (!link) return;
    var eventName = link.getAttribute('data-ga-event');
    if (!eventName) return;
    gtag('event', eventName, {
      event_category: 'outbound',
      event_label: link.href,
      link_url: link.href
    });
  });
})();
