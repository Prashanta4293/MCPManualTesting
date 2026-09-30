# Odisha homepage exploratory execution

Executed **28–29 September 2026** using Playwright MCP against https://apptourlfr-stg.estpl.net/home.

**Total: 100 | Passed: 71 | Failed: 26 | Blocked: 1 | Not tested: 2**

**Coverage:** 75 primary header navigation items: 53 mega-menu destinations, 17 hamburger links, Book Now, and four social links. Returned to home between items. Home branding/title/favicon asset, logo, language, search, profile views, hamburger, accessibility panel, announcement controls and keyboard skip were also assessed. No registration, login, booking, payment, contact, feedback or OTP form was submitted.

Primary navigation ran on 28 September. Follow-up home, image, announcement and keyboard checks ran on 29 September; this is not a full rerun of every destination on the second day. Desktop viewport started at 1366×577 and was enlarged to 1366×900 to complete links clipped by the mega-menu.

The home page loads. No tested internal destination was a confirmed blank page or page-level 404/500. Tourist Map is an image viewer, not blank. X content verification was blocked by a certificate interstitial. Some otherwise reachable pages failed their combined test because of content, JavaScript or resource errors.

## Defect summary

| ID | Finding | Severity / Priority | Tests | Evidence |
|---|---|---|---|---|
| D01 | Hidden home background resource blocked — Remove/repair loremflickr background request; visible video background still works. | Low / P3 | HOME-003 | [Screenshot](odisha_evidence/home-final.png) |
| D02 | Conflicting coastline lengths on same page — Overview says nearly 480 km; geography section says nearly 574 km. Confirm authoritative content. | Low / P3 | NAV-001 | [Screenshot](odisha_evidence/nav-01.png) |
| D03 | Editorial instruction exposed in public content — Remove author instruction beneath Ancient & Medieval Monuments. | Low / P3 | NAV-003 | [Screenshot](odisha_evidence/nav-03.png) |
| D04 | Coastal template heading on inland regional pages — Central and West Odisha use DISTRICTS THAT SHAPE THE COAST. Content review needed. | Low / P3 | NAV-018, NAV-020 | [Screenshot](odisha_evidence/nav-18.png) |
| D05 | Tourist Map logs missing-elements error — Map renders as image viewer. Console error exists; absence of heading/breadcrumb may be intentional viewer design, not a blank-page failure. | Medium / P2 | NAV-029 | [Screenshot](odisha_evidence/nav-29.png) |
| D06 | Swiper initialization error on five destinations — Swiper is not defined. Carousel functional impact was not separately tested. | Medium / P2 | NAV-034, NAV-044, NAV-046, NAV-047, NAV-048 | [Screenshot](odisha_evidence/nav-34.png) |
| D07 | Heritage Properties video thumbnail HTTP 404 — https://img.youtube.com/vi/-aPINUood2M/maxresdefault.jpg fails; fallback visual impact not established. | Low / P3 | NAV-034 | [Screenshot](odisha_evidence/nav-34.png) |
| D08 | Tour Operators content labelled Tour Guides — Heading and introduction refer to guides while table lists tour operators/travel agents. | Low / P3 | NAV-036 | [Screenshot](odisha_evidence/nav-36.png) |
| D09 | Odisha Parab mixes Varanasi and Ahmedabad — Venue/intro say Varanasi; About text says Ahmedabad edition. | Medium / P2 | NAV-049 | [Screenshot](odisha_evidence/nav-49.png) |
| D10 | Four cuisine pages request missing pattern image — /patter-1.png returns 404 on Mahaprasad, Rasagola, Chhenapoda and Sarsatia. | Low / P3 | NAV-050, NAV-051, NAV-052, NAV-053 | [Screenshot](odisha_evidence/nav-50.png) |
| D11 | Mahaprasad has sweet-category label — LEGENDARY SWEET conflicts with page description of a sacred meal of rice, lentils and vegetables. | Low / P3 | NAV-050 | [Screenshot](odisha_evidence/nav-50.png) |
| D12 | Plan Your Trip menu overflows short desktop viewport — At 1366×577 bottom links fall below viewport; no internal menu scrolling; click times out. | Medium / P2 | HDR-004 | [Screenshot](odisha_evidence/menu-overflow.png) |
| D13 | Hindi and Odia selection has no visible effect — Both leave EN, en-US and English content unchanged. | Medium / P2 | LANG-Hi, LANG-Od | [Screenshot](odisha_evidence/language-Hi.png) |
| D14 | Search opener throws null-value TypeError — Search overlay opens but inline onclick accesses missing searchKeyword element. | Medium / P2 | SEARCH-001 | [Screenshot](odisha_evidence/search-console-error.png) |
| D15 | Skip link does not bypass header keyboard focus — After activation the next Tab goes to header logo, not main content. | Medium / P2 | A11Y-001 | [Screenshot](odisha_evidence/skip-link-focus.png) |
| EXT01 | Book Odisha third-party script failures — External ownership: Clarity CSP and Google tag failures; booking home still renders. | Low / P3 | NAV-071 | [Screenshot](odisha_evidence/external-71.png) |
| EXT02 | Department site runtime/resource failures — External ownership: 404 script/MIME errors and embedded media certificate errors. | Medium / P2 | NAV-055 | [Screenshot](odisha_evidence/external-55.png) |
| EXT03 | Facebook runtime error — External ownership: Action bar is null on Comet; official profile visible. | Low / P3 | NAV-072 | [Screenshot](odisha_evidence/external-72.png) |
| EXT04 | YouTube passive sign-in request unauthorized — External ownership: HTTP 401 in passive sign-in flow; intended channel content visible. | Low / P3 | NAV-075 | [Screenshot](odisha_evidence/external-75.png) |

15 staging-site defect groups and 4 external-site diagnostic groups. These are distinct from the number of failed test cases; one shared defect can affect multiple cases. Severity and priority are provisional QA assessments.

## Blocked and not verified

- **Blocked:** X opens Chrome’s `NET::ERR_CERT_AUTHORITY_INVALID` privacy warning. No bypass; profile content, images and normal URL completion are unverified.
- **Not tested by instruction:** form submissions and authentication/booking/payment completion.
- **Not tested:** mobile menus, exhaustive offscreen/carousel/CSS-background images, media playback, accessibility option effects and native screen-reader audio.
- **Favicon limitation:** configured PNG was fetched with HTTP 200 and decoded at 136×146; actual browser-tab chrome appearance is not visible to Playwright page screenshots.
- Supplemental account views and event-alias breadcrumb were checked on 29 September. No authenticated profile state or form completion was verified.
- No approved specification was supplied. Destination URLs were compared to clicked link targets; factual/legal accuracy, inner-page forms, filters, pagination and downloadable documents were outside this header smoke execution.
- Analytics `ERR_ABORTED` entries alone were not counted as functional failures. External popup diagnostics can miss the earliest response because listeners were installed after the popup appeared.
- Some lazy carousel images remain pending outside the viewed state. No blanket claim that every image/media state passed is made.

## Test results

| ID | Module | Scenario | Status |
|---|---|---|---|
| NAV-001 | Discover | Open Odisha At A Glance | Failed |
| NAV-002 | Discover | Open Iconic Odisha | Passed |
| NAV-003 | Discover | Open Heritage & Architecture | Failed |
| NAV-004 | Discover | Open Spiritual & Sacred Odisha | Passed |
| NAV-005 | Discover | Open Wildlife Sanctuaries of Odisha | Passed |
| NAV-006 | Discover | Open Coastal Getaway | Passed |
| NAV-007 | Discover | Open Tribal Odisha | Passed |
| NAV-008 | Discover | Open Arts, Crafts & Handloom | Passed |
| NAV-009 | Experience | Open Festival & Celebrations | Passed |
| NAV-010 | Experience | Open Cuisine & Culinary Trails | Passed |
| NAV-011 | Experience | Open Ecotourism | Passed |
| NAV-012 | Experience | Open Tribal, Village & Rural Life | Passed |
| NAV-013 | Experience | Open Adventure & Outdoors | Passed |
| NAV-014 | Experience | Open Culture, Music & Dance | Passed |
| NAV-015 | Experience | Open Odisha Walks | Passed |
| NAV-016 | Experience | Open Sports Tourism | Passed |
| NAV-017 | Plan Your Trip / Where to go | Open East Odisha (Coastal) | Passed |
| NAV-018 | Plan Your Trip / Where to go | Open Central Odisha | Failed |
| NAV-019 | Plan Your Trip / Where to go | Open Northern Odisha | Passed |
| NAV-020 | Plan Your Trip / Where to go | Open Western Odisha | Failed |
| NAV-021 | Plan Your Trip / Where to go | Open Southern Odisha | Passed |
| NAV-022 | Plan Your Trip / Where to go | Open Tourist Destinations | Passed |
| NAV-023 | Plan Your Trip / Where to go | Open Tourist Places | Passed |
| NAV-024 | Plan Your Trip / Travel Essentials | Open Best Time to Visit | Passed |
| NAV-025 | Plan Your Trip / Travel Essentials | Open Weather & Climate | Passed |
| NAV-026 | Plan Your Trip / Travel Essentials | Open How to Reach Odisha | Passed |
| NAV-027 | Plan Your Trip / Travel Essentials | Open Getting Around Odisha | Passed |
| NAV-028 | Plan Your Trip / Travel Essentials | Open Currency Converter | Passed |
| NAV-029 | Plan Your Trip / Travel Essentials | Open Odisha Tourist Map | Failed |
| NAV-030 | Plan Your Trip / Accommodations | Open OTDC Panthanivas | Passed |
| NAV-031 | Plan Your Trip / Accommodations | Open Eco Retreats | Passed |
| NAV-032 | Plan Your Trip / Accommodations | Open Nature Camps | Passed |
| NAV-033 | Plan Your Trip / Accommodations | Open Hotels | Passed |
| NAV-034 | Plan Your Trip / Accommodations | Open Heritage Properties | Failed |
| NAV-035 | Plan Your Trip / Tourist Services & Safety | Open Tourist Offices | Passed |
| NAV-036 | Plan Your Trip / Tourist Services & Safety | Open Tour Operators | Failed |
| NAV-037 | Plan Your Trip / Tourist Services & Safety | Open Hospitals List | Passed |
| NAV-038 | Plan Your Trip / Tourist Services & Safety | Open Feedback and Suggestions | Passed |
| NAV-039 | Plan Your Trip / Tourist Services & Safety | Open Wayside Amenities | Passed |
| NAV-040 | Plan Your Trip / Travel Tips & Guidelines | Open Do’s & Don’ts | Passed |
| NAV-041 | Plan Your Trip / Travel Tips & Guidelines | Open Responsible Tourism Guidelines | Passed |
| NAV-042 | Plan Your Trip / Travel Tips & Guidelines | Open Safety Advisories | Passed |
| NAV-043 | Plan Your Trip / Unique Experiences | Open Light & Sound Shows | Passed |
| NAV-044 | Plan Your Trip / Highlighted Events | Open Mahendragiri Eco-Adventure Fest 2026 | Failed |
| NAV-045 | Plan Your Trip / Highlighted Events | Open Ratha Jatra 2026 | Passed |
| NAV-046 | Plan Your Trip / Highlighted Events | Open Konark Festival 2026 | Failed |
| NAV-047 | Plan Your Trip / Highlighted Events | Open National Chilika Bird Festival 2026 | Failed |
| NAV-048 | Plan Your Trip / Highlighted Events | Open International Sand Art Festival 2026 | Failed |
| NAV-049 | Plan Your Trip / Highlighted Events | Open Odisha Parab | Failed |
| NAV-050 | Plan Your Trip / Cuisines of Odisha | Open Mahaprasad | Failed |
| NAV-051 | Plan Your Trip / Cuisines of Odisha | Open Rasagola | Failed |
| NAV-052 | Plan Your Trip / Cuisines of Odisha | Open Chhenapoda | Failed |
| NAV-053 | Plan Your Trip / Cuisines of Odisha | Open Sarsatia | Failed |
| NAV-054 | Hamburger / About Odisha Tourism | Open About Us | Passed |
| NAV-056 | Hamburger / About Odisha Tourism | Open Vision, Mission & Objectives | Passed |
| NAV-057 | Hamburger / About Odisha Tourism | Open Odisha Tourism Policy | Passed |
| NAV-058 | Hamburger / About Odisha Tourism | Open Operational Guidelines | Passed |
| NAV-059 | Hamburger / About Odisha Tourism | Open Tenders and Notices | Passed |
| NAV-060 | Hamburger / Media & Updates | Open Newsletter | Passed |
| NAV-061 | Hamburger / Media & Updates | Open Brochure | Passed |
| NAV-062 | Hamburger / Media & Updates | Open Photo Gallery | Passed |
| NAV-063 | Hamburger / Media & Updates | Open Video Gallery | Passed |
| NAV-064 | Hamburger / Media & Updates | Open Traveller Blogs | Passed |
| NAV-065 | Hamburger / Media & Updates | Open Festival & Events | Passed |
| NAV-066 | Hamburger / Policies & Legal | Open Privacy Policy | Passed |
| NAV-067 | Hamburger / Policies & Legal | Open Disclaimer | Passed |
| NAV-068 | Hamburger / Help & Support | Open Contact Us | Passed |
| NAV-069 | Hamburger / Help & Support | Open Site Map | Passed |
| NAV-070 | Hamburger / Help & Support | Open FAQs | Passed |
| NAV-055 | Header / External | Department of Tourism, Government of Odisha | Failed |
| NAV-071 | Header / External | Book Now | Failed |
| NAV-072 | Header / External | Facebook | Failed |
| NAV-073 | Header / External | X | Blocked |
| NAV-074 | Header / External | Instagram | Passed |
| NAV-075 | Header / External | YouTube | Failed |
| HOME-001 | Home | Home URL, title and visible sections | Passed |
| HOME-002 | Home | Favicon asset | Passed |
| HOME-003 | Home | Home image and network health | Failed |
| HDR-001 | Header | Logo image and navigation | Passed |
| HDR-002 | Header | Discover menu reveal | Passed |
| HDR-003 | Header | Experience menu reveal | Passed |
| HDR-004 | Header | Plan Your Trip menu fits viewport | Failed |
| HDR-005 | Header | Hamburger opens and closes | Passed |
| LANG-Hi | Header / Language | Select Hindi | Failed |
| LANG-Od | Header / Language | Select Odia | Failed |
| LANG-En | Header / Language | Select English | Passed |
| SEARCH-001 | Header / Search | Open search overlay without runtime error | Failed |
| SEARCH-002 | Header / Search | Search Puri | Passed |
| ACCOUNT-001 | Header / Profile | Login dialog display and close | Passed |
| ACCOUNT-ForgotPassword | Header / Profile | Forgot Password? opens | Passed |
| ACCOUNT-SignUp | Header / Profile | Sign Up opens | Passed |
| ACCOUNT-OfficialLogin | Header / Profile | Official Login opens | Passed |
| ACC-001 | Header / Accessibility | Accessibility panel opens and closes | Passed |
| TOP-001 | Header / Announcements | Collapse and restore announcement bar | Passed |
| TOP-002 | Header / Announcements | Events Of Odisha destination | Passed |
| A11Y-001 | Header / Keyboard | Skip to Main Content focus transfer | Failed |
| LIMIT-001 | Scope limitations | Prohibited form submissions | Not Tested |
| LIMIT-002 | Scope limitations | Deep accessibility, mobile and media coverage | Not Tested |
| SEARCH-003 | Header / Search | Close search overlay | Passed |
| HDR-006 | Header / External | Cancel external navigation | Passed |

## Artifacts

- [Excel execution report](odisha_homepage_execution.xlsx): all 16 requested columns, summary, defects and limitations.
- [Evidence directory](odisha_evidence/): screenshots, detailed JSON observations and home console/network logs.

Passed means the assertions stated in that row were actually executed and observed. It does not imply untested destination features or external integrations were verified.
