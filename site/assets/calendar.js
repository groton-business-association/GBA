// GBA calendar: reads the public Google Calendar feed (proxied by Netlify at calendar.ics)
// and lists upcoming events by date. Falls back to Google's own calendar view if the feed can't load.
(function () {
  var TZ = "America/New_York";
  var MONTHS_AHEAD = 12;

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }
  var fmtDate = new Intl.DateTimeFormat("en-US", { timeZone: TZ, month: "long", day: "numeric", year: "numeric" });
  var fmtTime = new Intl.DateTimeFormat("en-US", { timeZone: TZ, hour: "numeric", minute: "2-digit" });
  var fmtKey = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" });
  function time(d) { return fmtTime.format(d).replace(" AM", " am").replace(" PM", " pm"); }

  function fallback() {
    var box = document.getElementById("gba-events");
    box.innerHTML = "";
    var f = document.createElement("iframe");
    f.className = "cal-frame";
    f.title = "GBA meeting and event calendar";
    f.loading = "lazy";
    f.src = "https://calendar.google.com/calendar/embed?src=" + encodeURIComponent(window.GBA.calendarId) +
      "&ctz=America%2FNew_York&mode=AGENDA&showTitle=0&showPrint=0&showCalendars=0&showTz=0";
    box.appendChild(f);
  }

  function collect(text) {
    var comp = new ICAL.Component(ICAL.parse(text));
    comp.getAllSubcomponents("vtimezone").forEach(function (tz) { ICAL.TimezoneService.register(tz); });
    var vevents = comp.getAllSubcomponents("vevent");
    var masters = {}, exceptions = [];
    vevents.forEach(function (v) {
      var ev = new ICAL.Event(v);
      if (v.hasProperty("recurrence-id")) exceptions.push(ev); else masters[ev.uid] = ev;
    });
    exceptions.forEach(function (ex) {
      if (masters[ex.uid]) masters[ex.uid].relateException(ex);
    });

    var now = new Date();
    var startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var end = new Date(now.getFullYear(), now.getMonth() + MONTHS_AHEAD, now.getDate());
    var out = [];

    function push(item, start, finish) {
      var status = (item.component.getFirstPropertyValue("status") || "").toUpperCase();
      if (status === "CANCELLED") return;
      var s = start.toJSDate(), e = finish ? finish.toJSDate() : null;
      if (s > end) return;
      if ((e || s) < startOfToday) return;
      out.push({ title: item.summary || "GBA event", location: item.location || "", description: item.description || "",
        start: s, end: e, allDay: start.isDate });
    }

    Object.keys(masters).forEach(function (uid) {
      var ev = masters[uid];
      if (ev.isRecurring()) {
        var it = ev.iterator(), next, guard = 0;
        while ((next = it.next()) && guard++ < 500) {
          if (next.toJSDate() > end) break;
          var d = ev.getOccurrenceDetails(next);
          push(d.item, d.startDate, d.endDate);
        }
      } else {
        push(ev, ev.startDate, ev.endDate);
      }
    });
    // Exceptions whose series is missing still count as single events
    exceptions.forEach(function (ex) { if (!masters[ex.uid]) push(ex, ex.startDate, ex.endDate); });
    out.sort(function (a, b) { return a.start - b.start; });
    return out;
  }

  function render(events) {
    var box = document.getElementById("gba-events");
    box.innerHTML = "";
    if (!events.length) {
      box.appendChild(el("p", "dir-empty", "No upcoming events are on the calendar yet. Meetings are usually the third Wednesday of the month at 5:00 pm."));
      return;
    }
    var groups = [], byKey = {};
    events.forEach(function (ev) {
      var key = ev.allDay ? ev.start.toISOString().slice(0, 10) : fmtKey.format(ev.start);
      if (!byKey[key]) { byKey[key] = { label: ev.allDay ? new Intl.DateTimeFormat("en-US", { timeZone: "UTC", month: "long", day: "numeric", year: "numeric" }).format(ev.start) : fmtDate.format(ev.start), items: [] }; groups.push(byKey[key]); }
      byKey[key].items.push(ev);
    });
    groups.forEach(function (g) {
      var day = el("section", "cal-day");
      var h = el("h2", "cal-date", g.label);
      day.appendChild(h);
      g.items.forEach(function (ev) {
        var item = el("article", "cal-event");
        item.appendChild(el("h3", "cal-title", ev.title));
        var when = ev.allDay ? g.label : g.label + " @ " + time(ev.start) + (ev.end ? " to " + time(ev.end) : "");
        item.appendChild(el("p", "cal-when", when));
        if (ev.location) item.appendChild(el("p", "cal-where", ev.location));
        if (ev.description) item.appendChild(el("p", "cal-desc", ev.description.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()));
        day.appendChild(item);
      });
      box.appendChild(day);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var link = document.getElementById("gba-cal-link");
    if (link) link.href = "https://calendar.google.com/calendar/u/0?cid=" + btoa(window.GBA.calendarId);
    if (location.protocol === "file:" || !window.ICAL) { fallback(); return; }
    fetch("calendar.ics", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (t) { if (t.indexOf("BEGIN:VCALENDAR") === -1) throw new Error("not a calendar"); render(collect(t)); })
      .catch(fallback);
  });
})();
