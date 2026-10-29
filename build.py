import sys
import pathlib
ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent / "site")  # folder holding the site files

NAV = [("index.html", "Home"), ("about.html", "About"), ("calendar.html", "Calendar"),
       ("members.html", "Members"), ("https://www.grotonfest.com", "GrotonFest"), ("contact.html", "Contact"), ("join.html", "Join the GBA")]

# ---------- Member data: members/*.json (edited on the /admin page) -> site/data/*.csv ----------
import json as _json0, os as _os
REPO = ROOT.parent
CMS_CONFIG = ROOT / "admin" / "config.yml"

def _strip_the(name):
    n = name.lower()
    return n[4:] if n.startswith("the ") else n

def generate_member_data():
    folder = REPO / "members"
    if not folder.is_dir():
        return
    import csv as _c
    rows = []
    for f in sorted(folder.glob("*.json")):
        try:
            d = _json0.loads(f.read_text())
        except ValueError as e:
            raise SystemExit(f"Member file {f.name} is not valid: {e}")
        if not str(d.get("name", "")).strip():
            continue
        logo = str(d.get("logo") or "").strip()
        rows.append({
            "name": str(d.get("name", "")).strip(),
            "categories": "; ".join(c.strip() for c in (d.get("categories") or []) if str(c).strip()),
            "specialty": str(d.get("specialty") or "").strip(),
            "contact": str(d.get("contact") or "").strip(),
            "website": str(d.get("website") or "").strip(),
            "email": str(d.get("email") or "").strip(),
            "phone": str(d.get("phone") or "").strip(),
            "town": str(d.get("town") or "").strip(),
            "description": " ".join(str(d.get("description") or "").split()),
            "logo": logo.rsplit("/", 1)[-1],
            "active": "no" if d.get("active") is False else "yes",
        })
    rows.sort(key=lambda r: _strip_the(r["name"]))
    fields = ["name", "categories", "specialty", "contact", "website", "email", "phone", "town", "description", "logo", "active"]
    with open(ROOT / "data/members.csv", "w", newline="") as fh:
        w = _c.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    # Category list: the editor settings hold the master list
    if CMS_CONFIG.exists():
        t = CMS_CONFIG.read_text()
        cfg = _json0.loads(t[t.index("{"):])
        cats = []
        for col in cfg.get("collections", []):
            for fld in col.get("fields", []):
                if fld.get("name") == "categories":
                    cats = fld.get("options", [])
        if cats:
            with open(ROOT / "data/categories.csv", "w", newline="") as fh:
                w = _c.writer(fh)
                w.writerow(["category"])
                for c in cats:
                    w.writerow([c])
        # On Netlify, point the editor at this site's own GitHub repository
        repo_url = _os.environ.get("REPOSITORY_URL", "")
        if "github.com" in repo_url:
            slug = repo_url.rstrip("/")
            if slug.endswith(".git"):
                slug = slug[:-4]
            slug = "/".join(slug.split("/")[-2:])
            cfg["backend"]["repo"] = slug
            head = t[:t.index("{")]
            CMS_CONFIG.write_text(head + _json0.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print(f"member data: {len(rows)} members")

generate_member_data()

import csv as _csv, html as _html
def member_links():
    rows = [r for r in _csv.DictReader(open(ROOT / "data/members.csv"))
            if r["name"] and r.get("active", "yes").strip().lower() not in ("no", "n", "false", "0")]
    rows.sort(key=lambda r: _strip_the(r["name"]))
    out = []
    for r in rows:
        name = _html.escape(r["name"])
        url = r["website"].strip()
        if url and not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        if url:
            out.append(f'          <li><a href="{_html.escape(url)}" rel="noopener">{name}</a></li>')
        else:
            out.append(f'          <li><a href="/members">{name}</a></li>')
    return "\n".join(out)

def page(fname, title, desc, body, scripts=""):
    items = []
    for href, label in NAV:
        cls = ' class="nav-join"' if href == "join.html" else ""
        cur = ' aria-current="page"' if href == fname else ""
        if href.startswith("http"):
            items.append(f'<li><a href="{href}" rel="noopener">{label}</a></li>')
            continue
        url = "/" if href == "index.html" else "/" + href.replace(".html", "")
        items.append(f'<li><a href="{url}"{cls}{cur}>{label}</a></li>')
    nav = "\n        ".join(items)
    full_title = "Groton Business Association" if fname == "index.html" else f"{title} | Groton Business Association"
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; frame-src https://calendar.google.com; connect-src 'self'; form-action 'self'; base-uri 'self'; object-src 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{full_title}</title>
  <meta name="description" content="{desc}">
  
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/style.css">
  <script src="/assets/site.js" defer></script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <a class="banner" href="/" aria-label="Groton Business Association home">
    <img src="/assets/gba-banner.png" width="1260" height="240" alt="Groton Business Association, Community and Commerce. An illustration of Groton with farms, a church steeple, and a winding road.">
  </a>
  <header class="site-header">
    <div class="wrap">
      <a class="brand" href="/">Groton Business Association<small>Community and commerce in Groton, Massachusetts</small></a>
      <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav">Menu</button>
      <nav id="site-nav" class="site-nav" aria-label="Main">
        <ul>
        {nav}
        </ul>
      </nav>
    </div>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site-footer">
    <div class="wrap cols cols-3">
      <div>
        <h2>Groton Business Association</h2>
        <address>161 Main Street<br>Groton, MA 01450</address>
      </div>
      <div>
        <h2>Monthly meetings</h2>
        <p>Third Wednesday of the month, 5:00 pm, September to June. Hosted at a member business.</p>
      </div>
      <div>
        <h2>Find your way</h2>
        <ul>
          <li><a href="/calendar">Meeting calendar</a></li>
          <li><a href="/members">Member directory</a></li>
          <li><a href="/join">Membership application</a></li>
          <li><a href="https://www.grotonfest.com" rel="noopener">GrotonFest</a></li>
        </ul>
      </div>
    </div>
    <div class="wrap"><p class="fine">The Groton Business Association is a non-profit organization.</p></div>
  </footer>
{scripts}
</body>
</html>
"""
    (ROOT / fname).write_text(html)

# ---------- Home ----------
page("index.html", "Home",
 "The Groton Business Association connects Groton-area businesses, farms, and organizations. Monthly meetings, the GrotonFest festivals, Destination Groton, and a member directory.",
"""    <section class="hero">
      <div class="wrap hero-grid">
        <div>
          <h1>Groton Business Association</h1>
          <p class="lede">In the fall of 2010, a group of Groton businesspeople formed the Groton Board of Trade to build a network of businesses, farms, and business-minded individuals within the town.</p>
          <p class="lede">Now known as the Groton Business Association (GBA), we encourage all business owners, even in surrounding towns, to become part of this organization to energize the local economy.</p>
          <div class="actions">
            <a class="btn" href="/join">Apply for membership</a>
            <a class="btn btn-quiet" href="/members">Browse members</a>
          </div>
        </div>
        <aside class="table-card" aria-labelledby="meet-h">
          <h2 id="meet-h">Come to a meeting</h2>
          <dl>
            <dt>When</dt><dd>Third Wednesday, 5:00 pm</dd>
            <dt>Season</dt><dd>September to June</dd>
            <dt>Where</dt><dd>A different member business each month</dd>
            <dt>Dinner</dt><dd>Members free. First visit free. Non-members $30 at the door.</dd>
          </dl>
          <a href="/calendar">See dates and locations</a>
        </aside>
      </div>
    </section>

    <div class="wrap home-grid">
      <div class="home-main">
        <section class="home-block">
          <h2>Who?</h2>
          <p>The GBA is a group of storefront businesses, farmers and agricultural business owners, corporations, home-based businesses, individuals, and organizations that want to work together to foster the relationship between local businesses and Groton residents.</p>
        </section>

        <section class="home-block" id="grotonfest">
          <h2>GrotonFest Family of Festivals</h2>
          <p>GBA collaborates with the <a href="https://www.grotonma.gov" rel="noopener">Town of Groton</a>, our <a href="https://www.grotonfest.com/oursponsors" rel="noopener">sponsors</a>, the local artisan community, the <a href="https://prescottscc.org/" rel="noopener">Prescott Community Center</a>, <a href="https://www.thegrotoninn.com/" rel="noopener">the Groton Inn</a>, and <a href="https://www.grotonma.gov/government/boards-and-committees/destination-groton-committee/" rel="noopener">Destination Groton</a> to produce the GrotonFest Family of Festivals: four major "Heart &amp; Soul" annual Groton events.</p>
          <ul class="festivals">
            <li><a href="https://www.grotonfest.com/grotonfestspring" rel="noopener">GrotonFest Spring<span>Spring</span></a></li>
            <li><a href="https://www.grotonfest.com/grotonfestskids" rel="noopener">GrotonFest Kids<span>Summer</span></a></li>
            <li><a href="https://www.grotonfest.com/grotonfestfall" rel="noopener">GrotonFest Fall<span>Fall</span></a></li>
            <li><a href="https://www.grotonfest.com/grotonfestwinter" rel="noopener">GrotonFest Winter<span>December</span></a></li>
          </ul>
        </section>

        <section class="home-block">
          <h2>Destination Groton</h2>
          <p>GBA conceived the idea and initiative behind what is now <a href="https://www.grotonma.gov/government/boards-and-committees/destination-groton-committee/" rel="noopener">Destination Groton</a>, and the newly established town-appointed committee, the <a href="https://www.grotonma.gov/government/boards-and-committees/destination-groton-committee/" rel="noopener">Destination Groton Committee</a>.</p>
          <p>In the fall of 2020, GBA formed a six-person Working Group to study and create a 100+ page report focusing on the arrival of the Groton Hill Music Center in the fall of 2022. The Working Group studied Groton Hill's inherent contribution to the growth of the Town of Groton. GBA's report concludes that Groton will continue to inherently expand the many facets of the community that have made it a "Destination Community," a place where people come from other places to enjoy the town's culture, history, art, and natural resources. How we engage as a community of stakeholders (town residents, business community, and town leaders) over the coming years will determine whether we get out in front of it, or sit back and wait to react to it.</p>
          <p><a href="https://portal.grotonma.gov/storage/Destination_Groton_Committee/Destination-Groton-Report.pdf" rel="noopener">The report is designed to be a resource for the Town as it faces the opportunities and challenges the future holds (PDF).</a></p>
          <p class="hint">GBA is responsible for the report's contents, findings, and conclusions.</p>
        </section>

        <section class="home-block">
          <h2>Why?</h2>
          <p>The primary goal of the GBA is to foster business and agricultural growth that enhances both the cultural and economic qualities of life in the Town of Groton. The GBA plays an active role in developing Groton, expanding the tax base, and creating local jobs.</p>
          <p>The GBA is dedicated to promoting economic progress for its members and advocating for a positive business environment within the Town of Groton.</p>
        </section>

        <section class="home-block">
          <h2>What's in it for you?</h2>
          <p>There are many benefits of membership:</p>
          <ul class="benefits">
            <li><strong>Increased business.</strong> One of the principles upon which the GBA is founded is the idea that people do business with others that they know and trust. Networking is a very valuable and effective way of doing business in a small-town environment.</li>
            <li><strong>Online Town of Groton business listing visibility.</strong> The Town of Groton's website, <a href="https://www.grotonma.gov" rel="noopener">GrotonMA.gov</a>, serves as a direct portal to the GBA website.</li>
            <li><strong>Strength in numbers.</strong> When issues arise that could affect the Groton business and farming community (for example, changes in the sign bylaw), being part of a group gives you a stronger voice.</li>
            <li><strong>Common cause.</strong> As a group, Groton businesses and farms can identify opportunities for one-time or recurring events that benefit the residents and businesses (for example, Shop Groton Local).</li>
            <li><strong>Business advocacy.</strong> The GBA is used as a means of advocating for businesses in general or for a specific business before Town boards, and often Town Meetings.</li>
            <li><strong>Community service.</strong> The GBA does many positive things in the community (see GBA programs below). As a member, you'll enjoy the benefits of the equity that the GBA builds with Groton residents. It is considerably more effective to serve the community as part of a group than it is to do so individually. Over time, giving back to the community is not only good karma, it is good business.</li>
          </ul>
        </section>

        <section class="home-block">
          <h2>When and where?</h2>
          <p>If you are interested in joining GBA, please attend one of our monthly meetings and be our guest!</p>
          <p>GBA meetings are usually held on the 3rd Wednesday of each month, from September to June (on hiatus for July and August). The Annual Kickoff Meeting is held in September! Meetings are held at local establishments and start at 5:00 pm for dinner. They are usually catered by the host establishment or a local professional caterer. The meeting agenda will vary, but it will always be informative. GBA meeting and event dates and times can be found on the <a href="/calendar">GBA Calendar</a>.</p>
          <p>For GBA members, meals are always complimentary. For prospective members, your first visit will be complimentary. For non-members, meals are $30 at the door.</p>
        </section>

        <section class="home-block">
          <h2>Organizational structure</h2>
          <p>The Executive Committee of the GBA is made up of six persons and responsibilities:</p>
          <ul class="plain-list">
            <li>President</li>
            <li>Vice President</li>
            <li>Treasurer</li>
            <li>Clerk</li>
            <li>Director of Marketing and Events</li>
            <li>Director of Giving</li>
          </ul>
          <p>The Board of Directors is comprised of the Executive Committee and up to seven other GBA members. The Executive Committee and the Board of Directors serve voluntarily, without term limits. The administrative year begins on January 1 and ends on December 31.</p>
          <p>The GBA has two subcommittees:</p>
          <ul class="plain-list">
            <li><strong>Community Outreach Committee.</strong> This committee is chartered to increase GBA's reach and positive effect in the Groton community.</li>
            <li><strong>Giving Committee.</strong> This committee is chartered with determining and awarding annual local student scholarships, grants, or donations to various entrepreneurial business initiatives.</li>
          </ul>
          <p><a href="/about#leadership">See the current leadership</a></p>
        </section>

        <section class="home-block">
          <h2>GBA programs</h2>
          <p><strong>Information for new and changing businesses.</strong> The Groton Business Association is working with the Land Use Department in Town Hall to develop one or more documents intended to help businesses understand the permitting process in town. These documents, once complete, will be helpful for both businesses considering starting up in town as well as businesses considering changing certain characteristics.</p>
        </section>
      </div>

      <aside class="home-side" aria-labelledby="cc-h">
        <h2 id="cc-h">Community and commerce</h2>
        <p class="hint">Our members. Each name links to the member's own website.</p>
        <p><a href="/members"><strong>See all GBA businesses and profiles</strong></a></p>
        <ul class="member-links">
@@MEMBER_LINKS@@
        </ul>
      </aside>
    </div>
""".replace("@@MEMBER_LINKS@@", member_links()))

# ---------- About ----------
page("about.html", "About",
 "The Groton Business Association's vision, goals, leadership, and governing documents.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>About the GBA</h1>
        <p class="lede">We foster local business, agricultural, cultural, and educational growth in the Town of Groton.</p>
      </div>
    </section>

    <section class="section">
      <div class="wrap">
        <h2>Our vision</h2>
        <p>Through a series of local festivals and events, the Groton Business Association promotes community programs, activities, health, education, and the arts. These events showcase local artists, non-profits, and businesses. Profits are donated to community projects and scholarships throughout the town. The GBA is a non-profit organization operated exclusively for charitable purposes under section 501(c)(3).</p>
        <p>Our role in economic development has several parts. We help new and existing businesses understand how to work with the Town to expand or change services. We provide a platform for networking and business education. We encourage local shopping, including at the many farms in Groton. We watch for anything that could disrupt the town's culture, charm, and assets. Growth is inevitable, and we want to help our elected officials shape it.</p>
        <h3>Our goals</h3>
        <ul class="plain-list">
          <li>Generate more business for members.</li>
          <li>Create business opportunities and promote positive business and agricultural growth.</li>
          <li>Encourage residents, organizations, and businesses to shop Groton.</li>
          <li>Connect with the community through hands-on and financial community service.</li>
          <li>Work with other groups and organizations to deliver these goals.</li>
          <li>Keep evaluating the value of GBA membership and make sure members are satisfied.</li>
        </ul>
      </div>
    </section>

    <section class="section section-tint">
      <div class="wrap cols cols-2">
        <div>
          <h2>Growing membership</h2>
          <p>More members means our message reaches more businesses and farms, and residents get a clearer picture of what local businesses do. We are committed to explaining to every Groton business what the GBA is and how it can help them succeed.</p>
        </div>
        <div>
          <h2>Charitable giving</h2>
          <p>The GBA may give each year to local student scholarships, grants, or donations to entrepreneurial business initiatives. The Director of Giving leads a subcommittee that decides which contributions will best benefit Groton and how they are delivered.</p>
        </div>
      </div>
    </section>

    <section class="section" id="leadership">
      <div class="wrap cols cols-2">
        <div>
          <h2>Leadership</h2>
          <p class="hint">Effective January 1, 2024</p>
          <h3>Executive Committee</h3>
          <ul class="people">
            <li><strong>Jeff Gordon</strong><span>President</span></li>
            <li><strong>Holly Varney</strong><span>Vice President</span></li>
            <li><strong>Elani Coetzer</strong><span>Director of Marketing and Events</span></li>
            <li><strong>Sadie Guichard</strong><span>Director of Giving</span></li>
          </ul>
          <h3>Board of Advisors</h3>
          <ul class="people">
            <li><strong>Steve Lane</strong><span>CEO, Interactive Management Solutions, LLC</span></li>
            <li><strong>Dominique Larkin</strong><span></span></li>
          </ul>
        </div>
        <div>
          <h2>How we are organized</h2>
          <p>The Executive Committee has six roles: President, Vice President, Treasurer, Clerk, Director of Marketing and Events, and Director of Giving. The Board of Directors is the Executive Committee plus up to seven other members. All serve as volunteers, without term limits. The administrative year runs January 1 to December 31.</p>
          <h3>Subcommittees</h3>
          <ul class="plain-list">
            <li><strong>Community Outreach</strong> builds channels for businesses and residents to connect with the GBA and makes it easier for businesses to grow in Groton.</li>
            <li><strong>Giving</strong> decides and awards annual student scholarships, grants, and donations.</li>
          </ul>
          <h3>Governing documents</h3>
          <p>The Restated Articles of Incorporation (June 19, 2024) and Bylaws (July 19, 2024) are being added. To request a copy now, <a href="/contact">contact the GBA</a>.</p>
        </div>
      </div>
    </section>
""")

# ---------- Calendar ----------
page("calendar.html", "Calendar",
 "Dates and locations for Groton Business Association meetings and events.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>Meetings and events</h1>
        <p class="lede">Meetings are usually the third Wednesday of the month at 5:00 pm, September to June, with dinner at the host business. The kickoff meeting is in September.</p>
        <p>Members eat free. Your first visit as a prospective member is free. Non-members pay $30 at the door.</p>
      </div>
    </section>
    <section class="wrap">
      <div id="gba-events" class="cal-list" aria-live="polite"><p class="dir-count">Loading events</p></div>
      <p class="hint mt-s">Times are Eastern. <a id="gba-cal-link" href="#" rel="noopener">Open the calendar in Google Calendar</a> to add it to your own.</p>
    </section>
""",
"""  <script src="/assets/vendor/ical.min.js" defer></script>
  <script src="/assets/calendar.js" defer></script>""")

# ---------- Members ----------
page("members.html", "Members",
 "Directory of Groton Business Association member businesses and organizations.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>Member directory</h1>
        <p class="lede">Groton-area businesses, farms, and organizations that belong to the GBA.</p>
      </div>
    </section>
    <section class="wrap dir-layout">
      <aside class="dir-filters" aria-labelledby="cat-h">
        <details class="cat-panel" open>
          <summary id="cat-h">Filter by category</summary>
          <p class="hint">Check one or more. You'll see members in any of the categories you check. A main category includes its subcategories.</p>
          <p><button type="button" id="cat-clear" class="link-btn" hidden>Clear all categories</button></p>
          <div id="cat-tree" class="cat-tree"></div>
        </details>
      </aside>
      <div class="dir-results">
        <div class="field">
          <label for="dir-search">Search members</label>
          <input id="dir-search" type="search" placeholder="Name, service, or keyword" autocomplete="off">
        </div>
        <p id="cat-chosen" class="cat-chosen" aria-live="polite"></p>
        <p id="dir-count" class="dir-count" aria-live="polite">Loading members</p>
        <ul id="dir-list" class="dir-list"></ul>
        <div class="note mt-m">
          <p>Is your business a member and your listing needs a change? <a href="/contact">Send us the update</a>. Not a member yet? <a href="/join">Apply here</a>.</p>
        </div>
      </div>
    </section>
""",
"""  <script src="/assets/members.js" defer></script>""")

# ---------- Join ----------
page("join.html", "Join the GBA",
 "Apply for Groton Business Association membership. Annual dues are $100 or $200.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>Join the GBA</h1>
        <p class="lede">Membership is open to for-profit and non-profit businesses and organizations in Groton and surrounding towns, including storefronts, farms, corporations, home-based businesses, and individual contributors.</p>
      </div>
    </section>

    <section class="section section-tint">
      <div class="wrap">
        <h2>Membership types</h2>
        <ul class="people">
          <li><strong>For-profit business</strong><span>Up to 3 people attend meetings. $200 a year.</span></li>
          <li><strong>Non-profit organization</strong><span>Up to 3 people attend meetings. $200 a year.</span></li>
          <li><strong>Non-profit organization, single</strong><span>1 person attends meetings. $100 a year.</span></li>
          <li><strong>Individual contributor</strong><span>Only you attend meetings. $100 a year.</span></li>
        </ul>
      </div>
    </section>

    <section class="section">
      <div class="wrap cols cols-2">
        <div>
          <h2>Membership application</h2>
          <form class="form" name="membership" method="POST" action="/thanks" data-netlify="true" netlify-honeypot="company_url">
            <input type="hidden" name="form-name" value="membership">
            <p class="hidden"><label>Leave this empty <input name="company_url"></label></p>
            <div class="field"><label for="m-first">First name <span class="req">*</span></label><input id="m-first" name="first_name" type="text" required autocomplete="given-name"></div>
            <div class="field"><label for="m-last">Last name <span class="req">*</span></label><input id="m-last" name="last_name" type="text" required autocomplete="family-name"></div>
            <div class="field"><label for="m-email">Email <span class="req">*</span></label><input id="m-email" name="email" type="email" required autocomplete="email"></div>
            <div class="field"><label for="m-phone">Cell phone <span class="req">*</span></label><input id="m-phone" name="phone" type="tel" required autocomplete="tel"></div>
            <div class="field"><label for="m-biz">Business or individual contributor name <span class="req">*</span></label><input id="m-biz" name="business_name" type="text" required autocomplete="organization"></div>
            <div class="field"><label for="m-addr">Full address <span class="req">*</span></label><textarea id="m-addr" name="address" required autocomplete="street-address" class="short"></textarea></div>
            <div class="field"><label for="m-web">Website <span class="req">*</span> <span class="hint">(write None if you don't have one)</span></label><input id="m-web" name="website" type="text" required placeholder="www.yourbusiness.com or None" autocomplete="url"></div>
            <fieldset class="field">
              <legend>Membership type <span class="req">*</span></legend>
              <label class="choice"><input type="radio" name="membership_type" value="For-profit business, up to 3 attend, $200" required> For-profit business, up to 3 attend, $200 a year</label>
              <label class="choice"><input type="radio" name="membership_type" value="Non-profit, up to 3 attend, $200"> Non-profit organization, up to 3 attend, $200 a year</label>
              <label class="choice"><input type="radio" name="membership_type" value="Non-profit, 1 attends, $100"> Non-profit organization, 1 attends, $100 a year</label>
              <label class="choice"><input type="radio" name="membership_type" value="Individual contributor, $100"> Individual contributor, $100 a year</label>
            </fieldset>
            <div class="field"><label for="m-about">What does your business do, and why do you want to join? <span class="req">*</span></label><textarea id="m-about" name="about" required></textarea></div>
            <div class="field"><label for="m-listing">Short description for the member directory <span class="req">*</span> <span class="hint">(one or two sentences)</span></label><textarea id="m-listing" name="directory_description" class="short" required></textarea></div>
            <div><button class="btn" type="submit">Send application</button></div>
          </form>
        </div>
        <div>
          <h2>Paying dues</h2>
          <div class="note">
            <p>Dues are paid by check. The website does not take payments.</p>
            <p>After you send the application, either bring your check to the next <a href="/calendar">GBA meeting</a> or mail it.</p>
            <p>Make the check payable to <strong>Groton Business Association</strong> and mail it to:</p>
            <address>Groton Business Association<br>c/o Jeff Gordon, President<br>161 Main Street<br>Groton, MA 01450</address>
          </div>
          <p class="mt-m">Your listing appears in the member directory once dues are received.</p>
        </div>
      </div>
    </section>
""")

# ---------- Contact ----------
page("contact.html", "Contact",
 "Contact the Groton Business Association.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>Contact the GBA</h1>
        <p class="lede">Questions about membership, meetings, sponsorship, or a change to your directory listing.</p>
      </div>
    </section>
    <section class="section">
      <div class="wrap cols cols-2">
        <form class="form" name="contact" method="POST" action="/thanks" data-netlify="true" netlify-honeypot="company_url" enctype="multipart/form-data">
          <input type="hidden" name="form-name" value="contact">
          <p class="hidden"><label>Leave this empty <input name="company_url"></label></p>
          <div class="field"><label for="c-name">Your name <span class="req">*</span></label><input id="c-name" name="name" type="text" required autocomplete="name"></div>
          <div class="field"><label for="c-email">Email <span class="req">*</span></label><input id="c-email" name="email" type="email" required autocomplete="email"></div>
          <div class="field"><label for="c-biz">Business or organization</label><input id="c-biz" name="business" type="text" autocomplete="organization"></div>
          <div class="field">
            <label for="c-topic">Topic</label>
            <select id="c-topic" name="topic">
              <option>General question</option>
              <option>Membership</option>
              <option>Update my directory listing</option>
              <option>Meetings and events</option>
              <option>Sponsorship and GrotonFest</option>
            </select>
          </div>
          <div class="field"><label for="c-msg">Message <span class="req">*</span></label><textarea id="c-msg" name="message" required></textarea></div>
          <div class="field"><label for="c-logo">Logo for your directory listing <span class="hint">(optional, PNG or JPG, under 2 MB)</span></label><input id="c-logo" name="logo" type="file" accept="image/png,image/jpeg"></div>
          <div><button class="btn" type="submit">Send message</button></div>
        </form>
        <div>
          <h2>By mail</h2>
          <address>Groton Business Association<br>c/o Jeff Gordon, President<br>161 Main Street<br>Groton, MA 01450</address>
          <h2 class="mt-m">In person</h2>
          <p>Join us at the next <a href="/calendar">monthly meeting</a>. Your first dinner is on us.</p>
        </div>
      </div>
    </section>
""")

# ---------- Thanks ----------
page("thanks.html", "Message sent",
 "Thank you for contacting the Groton Business Association.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>Sent. Thank you.</h1>
        <p class="lede">A GBA board member will reply by email. If you applied for membership, bring your dues check to the next meeting or mail it to 161 Main Street, Groton, MA 01450.</p>
        <div class="actions"><a class="btn" href="/calendar">See the next meeting</a><a class="btn btn-quiet" href="/">Back to home</a></div>
      </div>
    </section>
""")

# ---------- 404 ----------
page("404.html", "Page not found",
 "Page not found.",
"""    <section class="page-head">
      <div class="wrap">
        <h1>That page isn't here.</h1>
        <p class="lede">The GBA website moved recently and some old addresses changed. Try one of these:</p>
        <div class="actions"><a class="btn" href="/members">Member directory</a><a class="btn btn-quiet" href="/calendar">Calendar</a><a class="btn btn-quiet" href="/">Home</a></div>
      </div>
    </section>
""")
print("built")

# ---------- Make every link relative so pages work opened from a folder and on Netlify ----------
import re, csv as _csv, json as _json
for f in ROOT.glob("*.html"):
    h = f.read_text()
    h = re.sub(r'(href|src)="/(assets|data|docs)/', r'\1="\2/', h)
    h = h.replace('href="/"', 'href="index.html"')
    h = re.sub(r'href="/([a-z0-9-]+)(#[a-z-]+)?"', lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', h)
    h = h.replace('action="/thanks"', 'action="thanks.html"')
    h = h.replace('<script src="assets/members.js" defer></script>', '<script src="data/members-data.js" defer></script>\n  <script src="assets/members.js" defer></script>')
    f.write_text(h)
# Embedded copy of the member list, used when the page is opened straight from a folder.
txt = (ROOT / "data/members.csv").read_text()
cats_txt = (ROOT / "data/categories.csv").read_text()
(ROOT / "data/members-data.js").write_text("window.GBA_MEMBERS_CSV = " + _json.dumps(txt) + ";\nwindow.GBA_CATEGORIES_CSV = " + _json.dumps(cats_txt) + ";\n")
print("relative links done")
