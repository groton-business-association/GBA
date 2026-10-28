// Site settings. Editors change only these two lines.
window.GBA = {
  // Google Calendar shown on the Calendar page.
  calendarId: "gbaconnection@gmail.com",
  // Member directory source. Today a file in this site. To run it from a Google Sheet,
  // publish the sheet as CSV (File > Share > Publish to web > CSV) and paste that link here.
  membersCsv: "data/members.csv"
};

// Mobile menu
document.addEventListener("DOMContentLoaded", function () {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!btn || !nav) return;
  btn.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  });
});
