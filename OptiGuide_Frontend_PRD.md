# OptiGuide Frontend Product Requirements Document (PRD)

**Version:** 1.0\
**Date:** 2 November 2026\
**Status:** Frontend development specification\
**Product:** OptiGuide

------------------------------------------------------------------------

## 1. Product Overview

OptiGuide is a digital vision-screening and eyewear-recommendation
platform. It provides accessible preliminary vision screening through
smartphones and computers, generates understandable screening summaries,
assists with eyewear recommendations, and helps connect users with
optical shops and eye-care professionals.

The frontend serves three main audiences:

1.  Individuals who need accessible vision screening.
2.  Optical shopkeepers who manage customers and eyewear
    recommendations.
3.  Administrators and eye-care professionals who review screening
    results and referrals.

The product must work across desktop, tablet, and mobile devices, with a
consistent experience across web and mobile platforms.

### Core Product Capabilities

-   Voice-guided symptom questionnaire.
-   Multilingual user interface.
-   Distance vision screening.
-   Near vision screening.
-   Astigmatism screening.
-   Colour vision screening.
-   Pupillary distance (PD) estimation using a selfie and reference
    card.
-   Rule-based screening result interpretation.
-   Eyewear and lens recommendations.
-   Optical shop management dashboard.
-   Customer screening history.
-   Ophthalmologist referral workflow.
-   Downloadable screening reports.

**Medical limitation:** OptiGuide is a preliminary screening platform.
It must never represent screening results as a confirmed diagnosis or
prescription, or replace a professional eye examination.

------------------------------------------------------------------------

## 2. Design Vision and Visual Identity

The approved visual direction is a deep forest green, warm ivory, and
editorial-style interface.

### 2.1 Visual Design Specification

  Design element     Specification
  ------------------ ----------------------------------------------------
  Primary colour     Deep forest green
  Secondary colour   Muted teal
  Background         Warm ivory
  Surface            Soft stone and warm neutral
  Typography         Editorial serif headings, readable sans-serif body
  Borders            Thin, subtle neutral borders
  Corners            Moderate, consistent corner radius
  Shadows            Minimal, only when needed
  Photography        Authentic people and rural Indian settings
  Layout             Spacious, structured, editorial

### 2.2 Suggested Colour Tokens

These are initial design tokens, not mandatory final production values.

  Token            Hex
  ---------------- -----------
  Forest green     `#073F35`
  Deep green       `#092D28`
  Muted teal       `#4F8278`
  Warm ivory       `#F7F4EC`
  Stone            `#E9E5DA`
  Charcoal         `#202823`
  Secondary text   `#686F69`
  Success          `#28734F`
  Warning          `#B77932`
  Error            `#A9473E`

Use colours consistently. Status colours must remain distinguishable
without relying on colour alone.

### 2.3 Typography

Use a distinctive editorial heading font and a highly readable body
font.

Suggested pairings:

-   Lora + Source Sans 3.
-   DM Serif Display + IBM Plex Sans.
-   Newsreader + Public Sans.

Avoid the font families specifically listed in the design restrictions
in Section 11.

------------------------------------------------------------------------

## 3. Frontend Application Structure

OptiGuide contains three connected application areas:

1.  **Public website:** Introduction, features, and screening entry
    point.
2.  **User application:** Screening, results, and eyewear guidance.
3.  **Shop dashboard:** Customers, reports, referrals, and orders.

These applications connect to a FastAPI backend responsible for
authentication, screening, recommendations, reports, and persistent
data.

### 3.1 Application Roles

  -----------------------------------------------------------------------
  Role                                Permissions
  ----------------------------------- -----------------------------------
  Guest                               Browse website and access screening
                                      introduction

  Individual                          Complete screening and access
                                      personal reports

  Shopkeeper                          Manage customers, screenings, and
                                      eyewear recommendations

  Administrator                       Manage users, shops, system
                                      configuration, and reports

  Eye-care professional               Review referred cases and relevant
                                      screening information
  -----------------------------------------------------------------------

Access must be controlled by role-based authorization. Hiding a button
in the frontend is not sufficient to protect restricted functionality.

------------------------------------------------------------------------

## 4. Frontend Pages and Requirements

### 4.1 Public Landing Page

**Priority: P0**

**Purpose:** Explain OptiGuide and encourage visitors to begin vision
screening.

#### Required sections

1.  **Navigation bar**
    -   OptiGuide logo.
    -   Home.
    -   How It Works.
    -   Screening.
    -   For Shops.
    -   About.
    -   Language selector.
    -   Start Screening button.
2.  **Hero section**
    -   Main headline: "Accessible Vision Care for Everyone".
    -   Short product explanation.
    -   Authentic Indian rural photography.
    -   Start Vision Screening CTA.
    -   See How It Works CTA.
    -   Small visual demonstration of screening capabilities.
3.  **Capability introduction**
    -   Phone or web accessibility.
    -   Voice-guided experience.
    -   Eyewear guidance.
    -   Optical shop integration.
4.  **How OptiGuide works**
    -   Answer questions.
    -   Complete vision tests.
    -   Receive screening results.
    -   Explore eyewear guidance.
5.  **Actual product demonstration**
    -   Embedded interactive screening preview.
    -   Demonstrate the visual acuity test.
    -   Show a sample screening report.
    -   Allow visitors to experience the workflow without creating a
        real medical record.
6.  **Eyewear guidance section**
    -   Pupillary distance estimation.
    -   Frame selection.
    -   Lens recommendations.
    -   Virtual try-on demonstration, if supported.
7.  **Rural accessibility section**
    -   Mobile-first access.
    -   Voice instructions.
    -   Local-language support.
    -   Affordable access to preliminary screening.
8.  **Audience introduction**
    -   Individuals.
    -   Optical shops.
    -   Eye-care professionals.
9.  **Footer**
    -   About.
    -   Contact.
    -   Privacy Policy.
    -   Terms of Service.
    -   Disclaimer.

#### Landing page interactions

-   Navigation links must work.
-   Language selector must change supported interface language.
-   Start Screening must open the screening flow.
-   Demo must be interactive, not a static decorative image.
-   Responsive navigation must work on small screens.

### 4.2 Authentication and Onboarding

**Priority: P0**

Required pages:

-   Login.
-   Registration.
-   Forgot password.
-   Password reset.
-   Role selection where applicable.
-   Language selection.
-   Basic onboarding.

#### Functional requirements

-   Email or phone-based authentication, depending on backend support.
-   Form validation.
-   Password visibility toggle.
-   Clear authentication errors.
-   Session persistence.
-   Protected routes.
-   Logout.
-   Accessible labels and instructions.

For individual users, avoid unnecessary registration barriers before
preliminary screening. Allow guest screening where the backend and
privacy model permit it.

### 4.3 Vision Screening Introduction

**Priority: P0**

Before the actual test, users must understand:

-   What the screening does.
-   Which tests will be performed.
-   How much time the process may take.
-   How to position the device.
-   Whether a camera is required.
-   Why accurate screen distance matters.
-   That the results are preliminary.

#### Device readiness checks

-   Camera permission.
-   Camera availability.
-   Screen orientation.
-   Display size and scaling.
-   Screen brightness instructions.
-   Internet connection.
-   Reference-card availability when required.

The application must not claim accurate distance vision measurement if
the display size, viewing distance, or testing calibration requirements
are not satisfied.

### 4.4 Symptom Questionnaire

**Priority: P0**

Collect relevant information about:

-   Blurred vision.
-   Difficulty reading nearby text.
-   Difficulty seeing distant objects.
-   Eye strain.
-   Headaches associated with visual tasks.
-   Existing eyewear.
-   Duration of symptoms.
-   Relevant eye-care history.

#### Functional requirements

-   One question at a time.
-   Voice playback for questions.
-   Audio replay.
-   Multiple-language support.
-   Large selectable answer areas.
-   Previous and next navigation.
-   Progress indication.
-   Save and resume where supported.

Provide a clear route to urgent professional care when users report
potentially serious symptoms. Do not attempt to diagnose them through
the questionnaire.

### 4.5 Distance Vision Test

**Priority: P0**

Requirements:

-   Display calibrated optotypes.
-   Support appropriate test orientations.
-   Record user responses.
-   Provide instructions for covering one eye.
-   Test both eyes separately where supported.
-   Record viewing distance.
-   Validate device and display conditions.
-   Show test progress.
-   Handle incorrect and missing responses.

The test must use an evidence-based, validated protocol before
presenting clinically meaningful acuity estimates.

### 4.6 Near Vision Test

**Priority: P0**

Features:

-   Display near-reading text.
-   Provide prescribed viewing-distance instructions.
-   Support both eyes where appropriate.
-   Record reading performance.
-   Provide clear visual instructions.
-   Handle incomplete tests.

### 4.7 Astigmatism Screening

**Priority: P0**

Features:

-   Radial-line test.
-   Clear viewing instructions.
-   User response collection.
-   Results stored as screening observations.
-   Appropriate caution regarding false positives.

### 4.8 Colour Vision Test

**Priority: P0**

Features:

-   Colour plate presentation.
-   User answer collection.
-   Plate navigation.
-   Accessibility instructions.
-   Results summary.

Colour display calibration is important. Results must be marked
unreliable when display conditions prevent meaningful interpretation.

### 4.9 Pupillary Distance Estimation

**Priority: P0**

This module uses a smartphone camera and reference card to estimate
pupillary distance.

#### Functional requirements

1.  Explain the measurement process.
2.  Request camera permission.
3.  Display face positioning instructions.
4.  Guide the user to position the reference card.
5.  Capture the selfie.
6.  Detect facial landmarks.
7.  Estimate pupil positions.
8.  Calculate estimated PD.
9.  Display measurement and confidence.
10. Allow recapture when quality is insufficient.

#### Technical requirements

-   Camera integration.
-   MediaPipe-based facial landmark detection, if compatible with the
    selected implementation.
-   Image-quality checks.
-   Reference-card detection.
-   Measurement calculation.
-   Error handling.
-   Explicit user consent.

PD estimation must not be presented as clinically verified or used as a
substitute for professional fitting without validation.

### 4.10 Screening Results Page

**Priority: P0**

#### Required sections

**A. Screening overview** - Screening date. - Completion status. -
Overall screening summary. - Important limitations.

**B. Individual test results** - Distance vision. - Near vision. -
Astigmatism. - Colour vision.

**C. PD estimate** - Estimated value. - Measurement confidence. -
Measurement limitations.

**D. Recommendations** - Preliminary eyewear guidance. - Suggested
professional follow-up. - Referral indication where applicable.

**E. Report actions** - Download PDF. - Print report. - View screening
history. - Share securely where authorized.

Use understandable language. Avoid making unsupported claims such as
"You have myopia" or "Your prescription is confirmed."

### 4.11 Eyewear Recommendation Page

**Priority: P1**

#### Features

-   Suggested frame categories.
-   Frame shape selection.
-   Lens category guidance.
-   Estimated PD information.
-   Product catalogue.
-   Frame images.
-   Price information supplied by the shop.
-   Availability status.
-   Shop contact information.

#### Virtual try-on

If supported by the camera and face-tracking implementation:

-   Enable camera preview.
-   Detect face position.
-   Overlay selected frames.
-   Change frame selection.
-   Adjust frame placement.
-   Remove camera preview.

The interface must explain that virtual try-on is an appearance preview,
not a professional fitting.

### 4.12 Individual User Dashboard

**Priority: P1**

Required features:

-   Personal profile.
-   Start new screening.
-   Previous screening sessions.
-   Screening reports.
-   Eyewear recommendations.
-   Referral status.
-   Language preferences.
-   Account settings.
-   Privacy controls.

### 4.13 Optical Shop Dashboard

**Priority: P0**

#### Dashboard overview

Display:

-   Total customers.
-   Completed screenings.
-   Pending follow-ups.
-   Eyewear orders.
-   Referrals.

These must be real backend-derived values, not fabricated statistics.

#### Customer management

-   Register customers.
-   Search customers.
-   View customer details.
-   View screening history.
-   Start a new screening.
-   Access authorized reports.

#### Screening management

-   View screening sessions.
-   Review results.
-   Track incomplete screenings.
-   Access referral information.

#### Eyewear management

-   Browse catalogue.
-   Add eyewear products.
-   Edit product information.
-   Manage prices and stock where supported.
-   View customer recommendations.
-   Manage orders.

#### Referral management

-   View referred cases.
-   Track referral status.
-   Record follow-up status.
-   Access authorized clinical information.

#### Shop settings

-   Shop profile.
-   Contact details.
-   Staff accounts.
-   Language preferences.
-   Account settings.

### 4.14 Administrator Dashboard

**Priority: P1**

Required modules:

-   User management.
-   Shop management.
-   Role management.
-   Screening activity.
-   Referral monitoring.
-   Platform configuration.
-   Audit information.
-   System health and error reporting.

Administrative access must be protected and audited.

### 4.15 Legal and Support Pages

**Priority: P0**

Required pages:

-   About OptiGuide.
-   Contact.
-   Help and FAQ.
-   Privacy Policy.
-   Terms of Service.
-   Medical disclaimer.
-   Camera and data consent information.

The Privacy Policy must clearly explain what data is collected, why it
is collected, how it is stored, who can access it, and how users can
exercise their rights.

The Terms of Service must explain acceptable use, limitations, and
responsibilities.

------------------------------------------------------------------------

## 5. User Journeys and Navigation

### 5.1 Individual Screening Journey

1.  Landing Page.
2.  Start Screening.
3.  Language Selection.
4.  Screening Introduction.
5.  Device Readiness.
6.  Symptom Questionnaire.
7.  Distance Vision.
8.  Near Vision.
9.  Astigmatism.
10. Colour Vision.
11. PD Estimation.
12. Screening Processing.
13. Results Report.
14. Eyewear Guidance or Professional Referral.

Each screening step must support:

-   Previous and next navigation.
-   Clear progress indication.
-   Instructions before testing.
-   Recovery from temporary errors.
-   Safe handling of interrupted sessions.
-   Accessible text and audio instructions.

The application should not force users to complete an unsafe or invalid
test merely to reach the results page.

### 5.2 Shopkeeper Journey

1.  Shop Login.
2.  Shop Dashboard.
3.  Register Customer.
4.  Start Screening.
5.  Complete Screening.
6.  Review Report.
7.  View Eyewear Guidance.
8.  Select Suitable Frames.
9.  Manage Order.

A referral can also be initiated when required.

### 5.3 Navigation Hierarchy

  -----------------------------------------------------------------------
  Application                         Main navigation
  ----------------------------------- -----------------------------------
  Public website                      Home, How It Works, Screening, For
                                      Shops, About

  Individual                          Home, New Screening, Reports,
                                      Eyewear, Profile

  Shopkeeper                          Dashboard, Customers, Screenings,
                                      Catalogue, Orders, Referrals,
                                      Settings

  Administrator                       Overview, Users, Shops, Screenings,
                                      Referrals, Reports, Settings
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 6. Functional Requirements

  ID      Requirement                           Priority
  ------- ------------------------------------- ----------
  FR-01   Responsive navigation                 P0
  FR-02   Authentication and protected routes   P0
  FR-03   Language selection                    P0
  FR-04   Voice-assisted questionnaire          P0
  FR-05   Distance vision test interface        P0
  FR-06   Near vision test interface            P0
  FR-07   Astigmatism test interface            P0
  FR-08   Colour vision test interface          P0
  FR-09   Camera and PD estimation interface    P0
  FR-10   Screening results page                P0
  FR-11   PDF report interface                  P0
  FR-12   Shopkeeper dashboard                  P0
  FR-13   Customer management                   P0
  FR-14   Referral management                   P1
  FR-15   Eyewear catalogue                     P1
  FR-16   Virtual try-on                        P1
  FR-17   Individual dashboard                  P1
  FR-18   Administrator dashboard               P1
  FR-19   Screening history                     P1
  FR-20   Help, privacy and terms pages         P0

P0 requirements must be completed for the first functional release. P1
requirements may follow after the core screening workflow is stable.

------------------------------------------------------------------------

## 7. Frontend Technical Requirements

### 7.1 Proposed Technology Stack

The frontend should align with the previously selected React Native and
FastAPI architecture.

  Layer                    Technology
  ------------------------ -------------------------------------------------------
  Language                 TypeScript
  Mobile application       React Native
  Cross-platform tooling   Expo
  Web support              React Native Web or a dedicated React web application
  Styling                  Shared design tokens and platform-appropriate styling
  Navigation               React Navigation / web routing
  API communication        Fetch or Axios
  Server state             TanStack Query
  Local form state         React Hook Form
  Validation               Zod
  Camera                   Expo Camera / browser camera APIs
  Computer vision          MediaPipe
  Charts                   Accessible charting library, where needed
  PDF viewing              PDF viewer or browser-native PDF support
  Backend                  FastAPI
  API documentation        OpenAPI

**Architecture recommendation:** Keep shared TypeScript types,
validation schemas, design tokens, and business logic in reusable
packages. The marketing website, screening application, and shop
dashboard may use different route shells while sharing the same visual
system.

Do not force identical layouts across phone and desktop when their
interaction requirements differ.

### 7.2 API Integration

The frontend must communicate with the FastAPI backend through
documented API endpoints.

Expected integration areas:

-   Authentication.
-   User profiles.
-   Language preferences.
-   Screening sessions.
-   Questionnaire responses.
-   Vision test responses.
-   PD measurement results.
-   Screening reports.
-   Eyewear recommendations.
-   Customer records.
-   Shop records.
-   Orders.
-   Referrals.

#### API integration rules

-   Use environment variables for API base URLs.
-   Do not hardcode production credentials.
-   Validate API responses.
-   Handle network failures.
-   Prevent duplicate form submissions.
-   Handle expired sessions.
-   Implement appropriate authorization checks.
-   Never fabricate successful screening results when an API request
    fails.

The backend remains responsible for authoritative screening
calculations, recommendation rules, access control, and persistent
records.

### 7.3 Camera and Browser Requirements

-   Request permissions only when required.
-   Explain why camera access is needed.
-   Provide an alternative path when camera access is unavailable.
-   Handle camera denial gracefully.
-   Stop camera streams when leaving camera-dependent screens.
-   Avoid storing selfies unnecessarily.
-   Obtain explicit consent before image capture.
-   Use secure transmission for any image that must be uploaded.

### 7.4 Performance Requirements

  -----------------------------------------------------------------------
  Metric                              Target
  ----------------------------------- -----------------------------------
  Initial page load                   Under 3 seconds on a typical
                                      broadband connection

  Main navigation response            Under 200 ms

  Local interaction response          Under 100 ms

  Layout stability                    Minimal unexpected layout movement

  Image optimisation                  Responsive images and modern
                                      formats

  API loading                         Clear progress indication

  Mobile responsiveness               Support small phones through large
                                      screens
  -----------------------------------------------------------------------

These are engineering targets, not guarantees. Test on realistic
low-bandwidth connections and lower-end Android devices.

------------------------------------------------------------------------

## 8. Design System and Reusable Components

Build reusable components rather than independently styling every page.

### Core Components

  Component            Purpose
  -------------------- --------------------------------
  Header               Navigation
  Footer               Legal and contact navigation
  Primary button       Main actions
  Secondary button     Supporting actions
  Form field           Consistent input styling
  Language selector    Language switching
  Progress indicator   Screening progression
  Instruction panel    Test instructions
  Audio control        Voice playback
  Test display         Vision test content
  Result summary       Screening outcomes
  Report section       Structured reports
  Data table           Shop and admin management
  Filter bar           Search and filtering
  Modal                Confirmation and focused tasks
  Toast                Short action feedback
  Skeleton loader      Loading state
  Empty state          No-data experience
  Error state          Recovery and error information

### Component Design Rules

-   Use consistent spacing tokens.
-   Maintain readable text sizes.
-   Ensure keyboard accessibility.
-   Support touch targets of approximately 44 × 44 CSS pixels or larger.
-   Use visible focus indicators.
-   Do not communicate status through colour alone.
-   Use meaningful accessible names.
-   Support reduced-motion preferences.
-   Avoid unnecessary animation.
-   Use real content and meaningful sample data in demonstrations.

------------------------------------------------------------------------

## 9. Accessibility Requirements

Accessibility is a core product requirement, not an optional design
improvement.

### Visual Accessibility

-   Large readable typography.
-   High text contrast.
-   Clear instructions.
-   Responsive content.
-   No information communicated exclusively through colour.

### Voice Accessibility

-   Audio question playback.
-   Replay control.
-   Clear voice guidance.
-   Language-specific audio where available.
-   Written alternative to all audio instructions.

### Interaction Accessibility

-   Large touch targets.
-   Simple navigation.
-   Clear form validation.
-   Keyboard navigation.
-   Screen-reader support.
-   Avoid unnecessarily complex interactions.

### Language Accessibility

Initially plan for:

-   English.
-   Hindi.
-   Odia.

Additional languages should be configurable through the localization
system.

All interface text, test instructions, errors, and audio prompts should
be localization-ready.

------------------------------------------------------------------------

## 10. Loading, Error, and Empty States

Every API-connected screen must account for different states.

  State                Expected behaviour
  -------------------- -------------------------------------------------
  Loading              Skeletons or suitable progress indicators
  Success              Display confirmed data
  Empty                Explain why no data exists and what to do
  Error                Explain the issue and offer recovery
  Offline              Show connection status and protect unsaved work
  Unauthorized         Redirect or request authentication
  Expired session      Offer reauthentication
  Camera unavailable   Explain the issue and provide an alternative

Avoid displaying fabricated dashboard data or fake successful results to
hide backend integration problems.

------------------------------------------------------------------------

## 11. Mandatory Design Restrictions: 30 Things to Avoid

These constraints are based on the supplied visual reference images and
must be followed throughout OptiGuide frontend development.

  ------------------------------------------------------------------------
                           No. Avoid                 Implementation rule
  ---------------------------- --------------------- ---------------------
                             1 Harsh gradients       Use solid colours and
                                                     subtle tonal
                                                     transitions.

                             2 Lucide icons          Do not use the Lucide
                                                     icon library. Use a
                                                     consistent
                                                     alternative icon set
                                                     or custom SVGs.

                             3 Pure white            Use warm ivory and
                               backgrounds           neutral surfaces.

                             4 Rainbow colouring     Keep the palette
                                                     controlled and
                                                     consistent.

                             5 Drop shadows          Avoid decorative
                                                     shadows; use borders
                                                     and contrast for
                                                     separation.

                             6 Three feature cards   Use varied editorial
                               in a row              layouts and
                                                     appropriately sized
                                                     sections.

                             7 Emojis                Use professional
                                                     visual assets and
                                                     icons.

                             8 Liquid glass          Avoid glassmorphism
                                                     and frosted-glass
                                                     interfaces.

                             9 Em dashes             Do not use the em
                                                     dash character in
                                                     website copy.

                            10 Inter, Geist, Space   Select a different
                               Grotesk               typography pairing.

                            11 Coloured left stripe  Do not use decorative
                                                     coloured vertical
                                                     stripes on cards or
                                                     sections.

                            12 Fake testimonials     Use verified feedback
                                                     only, or omit
                                                     testimonials.

                            13 Bento grids           Avoid the bento-grid
                                                     visual pattern.

                            14 Terminal windows      Do not add fake
                                                     terminal or
                                                     command-line
                                                     decorations.

                            15 "It's not X, it's Y"  Avoid this cliché
                                                     copywriting
                                                     structure.

                            16 Checkmark bullets     Use descriptive text,
                                                     numbered processes,
                                                     or meaningful visual
                                                     explanations.

                            17 Three pricing tiers   Do not add a generic
                                                     three-tier pricing
                                                     section.

                            18 No real product demo  Do not omit the
                                                     actual interactive
                                                     OptiGuide
                                                     demonstration.

                            19 Soft corner radius    Avoid overly rounded,
                                                     pill-like cards and
                                                     controls. Use
                                                     restrained geometry.

                            20 Purple and black      Do not use this
                                                     combination as the
                                                     brand palette.

                            21 No skeleton loaders   Do not omit loading
                                                     states. Implement
                                                     suitable skeleton
                                                     loaders where
                                                     appropriate.

                            22 Radial orbs           Avoid decorative
                                                     floating circular
                                                     gradients and orb
                                                     effects.

                            23 Dot grids             Do not use decorative
                                                     dotted-grid
                                                     backgrounds.

                            24 Sparkle icons         Avoid decorative AI
                                                     sparkle symbols.

                            25 Animated arrows       Do not use decorative
                                                     animated directional
                                                     arrows.

                            26 No Terms of Service   Include a proper
                                                     Terms of Service
                                                     page.

                            27 No Privacy Policy     Include a proper
                                                     Privacy Policy page.

                            28 Hover animations      Avoid hover-driven
                                                     decorative animations
                                                     and movement.

                            29 Neon colours          Avoid fluorescent and
                                                     glowing colour
                                                     treatments.

                            30 Basic pastel colours  Avoid generic pastel
                                                     palettes. Use the
                                                     approved deeper, more
                                                     grounded colour
                                                     identity.
  ------------------------------------------------------------------------

### Enforcement Rules

These restrictions apply to:

-   Landing page.
-   Screening interface.
-   Results pages.
-   Shopkeeper dashboard.
-   Administrator dashboard.
-   Authentication screens.
-   Mobile application.
-   All reusable components.

A developer must not introduce a prohibited visual pattern simply
because a UI library provides it by default.

**Important interpretation:** Items 18, 21, 26, and 27 are requirements
to implement the positive behaviour, not features to remove. OptiGuide
must have a real product demo, skeleton loaders, Terms of Service, and
Privacy Policy.

------------------------------------------------------------------------

## 12. Responsive Design Requirements

The same product must work across different screen sizes.

### Desktop

-   Full navigation.
-   Spacious editorial layouts.
-   Dashboard side navigation.
-   Wider report layouts.
-   Camera and screening content with appropriate sizing.

### Tablet

-   Adapted navigation.
-   Reorganized dashboard sections.
-   Appropriate touch targets.
-   Flexible test layouts.

### Mobile

-   Compact navigation.
-   Single-column reading flow.
-   Full-width screening controls.
-   Camera-first PD estimation.
-   Large accessible test instructions.
-   Bottom navigation where appropriate.
-   No horizontal scrolling for normal content.

------------------------------------------------------------------------

## 13. Frontend Security and Privacy

The frontend must follow privacy-by-design principles.

Required measures:

1.  Obtain consent before collecting personal or camera-related data.
2.  Do not expose API secrets in client code.
3.  Protect authenticated routes.
4.  Avoid storing sensitive screening information in insecure local
    storage.
5.  Prevent unauthorized access to customer reports.
6.  Clear sensitive information on logout where appropriate.
7.  Avoid unnecessary image uploads.
8.  Display privacy information before data collection.
9.  Support account and data management workflows.
10. Use HTTPS in production.
11. Avoid logging personally identifiable information.
12. Provide appropriate session expiration handling.

Camera permissions must never be requested simply on opening the
homepage.

------------------------------------------------------------------------

## 14. Testing and Quality Assurance

The frontend must be tested before deployment.

### 14.1 Unit Testing

Test:

-   Form validation.
-   Navigation logic.
-   Screening progress.
-   Result presentation.
-   Language switching.
-   Role-based interface rendering.
-   Component behaviour.

Suggested tools: Jest and React Native Testing Library.

### 14.2 Integration Testing

Test:

-   Login and registration.
-   API communication.
-   Screening session creation.
-   Questionnaire submission.
-   Vision test responses.
-   PD estimation integration.
-   Report retrieval.
-   Customer creation.
-   Referral updates.

### 14.3 End-to-End Testing

Suggested tool: Playwright for web and an appropriate React Native
end-to-end framework for mobile.

Required scenarios:

  Test                     Expected outcome
  ------------------------ -----------------------------------------
  Open homepage            All sections render correctly
  Start screening          Screening introduction opens
  Select language          Supported interface language changes
  Complete questionnaire   Responses are saved
  Complete eye tests       Test responses are submitted
  Deny camera permission   Alternative instructions appear
  Capture reference card   Measurement workflow responds correctly
  View results             Correct backend results appear
  Download report          Valid report is generated
  Shop login               Shop dashboard opens
  Register customer        Customer record is created
  Unauthorized access      Protected page is inaccessible

### 14.4 Visual Testing

Verify:

-   No prohibited design patterns.
-   Correct colour tokens.
-   Consistent typography.
-   Responsive layouts.
-   No overflowing text.
-   No broken images.
-   No unexpected layout shifts.
-   Accessible focus states.
-   Correct loading and error states.

### 14.5 Real-Device Testing

Test on:

-   Low-end Android phones.
-   Mid-range Android phones.
-   iPhones.
-   Desktop Chrome.
-   Desktop Firefox.
-   Desktop Safari.
-   Tablet browsers.

Pay particular attention to screen scaling, browser zoom, camera
permissions, audio playback, and internet interruptions.

------------------------------------------------------------------------

## 15. Acceptance Criteria

The frontend will be considered ready for release only when the
following conditions are satisfied.

  -----------------------------------------------------------------------
  Area                                Acceptance criteria
  ----------------------------------- -----------------------------------
  Landing page                        All required sections and working
                                      navigation

  Design                              All 30 design restrictions followed

  Responsiveness                      Works on phone, tablet, and desktop

  Accessibility                       Keyboard, screen reader, and voice
                                      support tested

  Authentication                      Login, registration, and protected
                                      routes work

  Screening                           All four vision tests are
                                      integrated

  Questionnaire                       Responses are saved and recoverable

  PD estimation                       Camera and measurement workflow
                                      integrated and validated

  Results                             Real screening data displayed
                                      correctly

  Eyewear                             Recommendations and catalogue
                                      integration work

  Shop dashboard                      Customer and screening management
                                      work

  Admin                               Protected administrative routes
                                      work

  API                                 FastAPI integration works without
                                      fabricated data

  Loading                             Appropriate loading states are
                                      implemented

  Errors                              Network and validation errors are
                                      handled

  Legal                               Privacy Policy, Terms of Service,
                                      and disclaimer exist

  Security                            Sensitive data is protected

  Testing                             Critical user journeys pass
                                      automated and manual tests
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 16. Four-Person Frontend Development Division

The frontend work is divided among four people.

### Person 1: Public Website and Design System

Responsibilities:

-   Landing page.
-   Navbar and footer.
-   About and How It Works.
-   Responsive design.
-   Design tokens and reusable components.
-   Privacy and Terms pages.

**Deliverable:** Complete public-facing OptiGuide website.

### Person 2: Vision Screening Application

Responsibilities:

-   Screening introduction.
-   Symptom questionnaire.
-   Voice assistance.
-   Distance vision test.
-   Near vision test.
-   Astigmatism test.
-   Colour vision test.
-   Screening progress and error handling.

**Deliverable:** Complete individual screening workflow.

### Person 3: Camera, Results, and Eyewear

Responsibilities:

-   Camera integration.
-   MediaPipe facial landmark detection.
-   Reference-card-based PD estimation.
-   Screening results page.
-   PDF reports.
-   Eyewear recommendation interface.
-   Virtual try-on.

**Deliverable:** Measurement, results, and eyewear experience.

### Person 4: Shopkeeper and Admin Dashboard

Responsibilities:

-   Shopkeeper authentication.
-   Shop dashboard.
-   Customer management.
-   Screening history.
-   Eyewear catalogue.
-   Orders.
-   Referrals.
-   Administrator dashboard.

**Deliverable:** Complete shop and administration experience.

### Shared Responsibilities

All four developers must:

-   Follow the same design system.
-   Use shared TypeScript types.
-   Follow agreed API contracts.
-   Use consistent naming conventions.
-   Write tests for their modules.
-   Avoid introducing prohibited design patterns.
-   Review each other's pull requests.

The project lead should own integration, routing, shared state, and
final visual quality assurance.

------------------------------------------------------------------------

## 17. Recommended Frontend Folder Structure

``` text
optiguide/
│
├── apps/
│   ├── web/
│   │   ├── public/
│   │   └── src/
│   │       ├── app/
│   │       ├── components/
│   │       ├── pages/
│   │       └── styles/
│   │
│   └── mobile/
│       ├── app/
│       └── src/
│           ├── components/
│           ├── screens/
│           └── navigation/
│
├── packages/
│   ├── ui/
│   ├── design-system/
│   ├── api-client/
│   ├── types/
│   ├── validation/
│   ├── localization/
│   └── utilities/
│
├── backend/
│   └── app/
│
├── docs/
│   ├── frontend-prd.md
│   ├── api-contracts.md
│   ├── design-system.md
│   └── testing.md
│
├── tests/
│   ├── integration/
│   └── e2e/
│
├── .env.example
├── package.json
└── README.md
```

This is a proposed monorepo structure. The team should confirm the React
Native Web versus dedicated web implementation decision before creating
the final project scaffolding.

------------------------------------------------------------------------

## 18. Development Milestones

  -----------------------------------------------------------------------
  Phase                   Work                    Owner
  ----------------------- ----------------------- -----------------------
  Phase 1                 Repository setup,       Person 1 + lead
                          design system, shared   
                          components              

  Phase 2                 Public website and      Person 1
                          authentication          

  Phase 3                 Vision screening        Person 2
                          workflow                

  Phase 4                 PD, reports, and        Person 3
                          eyewear                 

  Phase 5                 Shop and admin          Person 4
                          dashboards              

  Phase 6                 API integration and     All
                          cross-module testing    

  Phase 7                 Responsive QA,          All
                          accessibility, and      
                          deployment              
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 19. Final Definition of Done

-   [ ] The website matches the approved OptiGuide design direction.
-   [ ] All 30 visual restrictions are respected.
-   [ ] The public website is fully responsive.
-   [ ] The product demonstration is functional.
-   [ ] All four screening tests are integrated.
-   [ ] Voice and multilingual functionality work.
-   [ ] PD estimation is integrated and validated.
-   [ ] Screening reports display real backend data.
-   [ ] Eyewear recommendations are connected.
-   [ ] Shopkeeper dashboard is functional.
-   [ ] Admin dashboard is protected.
-   [ ] Privacy Policy and Terms of Service are available.
-   [ ] Loading, error, and empty states are implemented.
-   [ ] Critical tests pass.
-   [ ] No placeholder data is presented as real customer or clinical
    data.
-   [ ] The web and mobile experiences have been tested.

------------------------------------------------------------------------

## 20. Instructions for the Antigravity Implementation Agent

### OptiGuide Frontend Implementation Instructions

You are implementing the frontend of OptiGuide, a digital
vision-screening and eyewear recommendation platform.

#### Primary Objective

Build a polished, production-oriented frontend that follows the approved
OptiGuide visual concept and this PRD.

#### Mandatory Instructions

1.  Inspect the existing repository before making changes.
2.  Preserve existing working functionality.
3.  Do not overwrite existing project architecture without
    justification.
4.  Establish shared design tokens before implementing pages.
5.  Build reusable components.
6.  Implement responsive web and mobile experiences.
7.  Integrate with the FastAPI backend using documented API contracts.
8.  Use actual API data wherever backend functionality exists.
9.  Clearly distinguish demonstration data from real data.
10. Implement all applicable accessibility requirements.
11. Implement all 30 design restrictions listed in this PRD.
12. Do not invent clinical results or confirmed prescriptions.
13. Test every major user journey.
14. Document setup, environment variables, and implementation decisions.

#### Design Requirements

Follow the approved OptiGuide aesthetic:

-   Deep forest green.
-   Warm ivory.
-   Muted teal.
-   Stone and charcoal neutrals.
-   Editorial serif headings.
-   Readable sans-serif body typography.
-   Restrained geometry.
-   Minimal decorative effects.
-   Authentic vision-care imagery.
-   Clear, accessible layouts.

Do not introduce any of the prohibited design patterns listed in Section
11.

#### Repository Inspection

Before implementation:

1.  Inspect the repository tree.
2.  Identify existing frameworks, dependencies, and scripts.
3.  Identify existing routes and components.
4.  Inspect current API integration.
5.  Identify reusable code.
6.  Review environment configuration.
7.  Identify existing tests.
8.  Document gaps and implementation risks.

Do not assume the repository is empty.

#### Architecture and Setup

1.  Confirm the web and mobile application architecture.
2.  Confirm shared package boundaries.
3.  Define routing and authentication strategy.
4.  Define API client conventions.
5.  Define shared TypeScript types.
6.  Configure environment variables.
7.  Set up linting, formatting, and testing.
8.  Document local development commands.

#### Implementation Order

1.  Design tokens and shared components.
2.  Public website and navigation.
3.  Authentication and onboarding.
4.  Screening introduction and questionnaire.
5.  Four vision test interfaces.
6.  Camera and PD estimation.
7.  Results and PDF reports.
8.  Eyewear recommendation experience.
9.  Shopkeeper dashboard.
10. Administrator dashboard.
11. Legal and support pages.
12. Responsive and accessibility improvements.

#### Testing Requirements

-   Add unit tests for reusable components and important logic.
-   Add integration tests for API-connected workflows.
-   Add end-to-end tests for critical user journeys.
-   Test responsive layouts.
-   Test camera permissions and failure paths.
-   Test loading, error, and offline states.
-   Verify that protected routes enforce authorization.
-   Verify that no fake clinical results are displayed as real results.

#### Completion Requirements

At completion, provide:

1.  Repository changes and implemented features.
2.  Final folder structure.
3.  Setup and run instructions.
4.  Environment variable documentation.
5.  API endpoints integrated.
6.  Tests executed and their results.
7.  Known limitations and unresolved issues.
8.  Screenshots of major pages.
9.  A checklist showing which PRD requirements are complete.

Do not claim a feature is complete if it is only a static mockup or
placeholder.

**Final objective:** Deliver a cohesive, accessible, responsive
OptiGuide frontend that is ready for integration with the FastAPI
backend and supports the four-person development workflow.
