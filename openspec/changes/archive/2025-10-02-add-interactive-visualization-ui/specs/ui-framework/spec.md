# UI Framework Specification

## ADDED Requirements

### Requirement: Dash Application Structure

The system SHALL implement a web-based UI using the Dash framework with modular architecture.

#### Scenario: Application initialization

- **WHEN** application starts
- **THEN** Dash app SHALL be initialized with Bootstrap theme
- **AND** application SHALL load configuration from environment variables
- **AND** health check endpoint `/health` SHALL return 200 OK

#### Scenario: Multi-page routing

- **WHEN** user navigates within application
- **THEN** available pages SHALL include:
  - Home/Dashboard (overview, quick stats)
  - Map View (interactive heat maps)
  - Comparison (side-by-side analysis)
  - Data Management (cache, jobs, exports)
  - Settings (parameters, preferences)
- **AND** URL routing SHALL work (e.g., `/map`, `/comparison`)
- **AND** browser back/forward buttons SHALL work correctly

#### Scenario: Navigation sidebar

- **WHEN** viewing any page
- **THEN** sidebar SHALL display navigation links with icons
- **AND** current page SHALL be highlighted
- **AND** sidebar SHALL be collapsible (desktop) or drawer (mobile)
- **AND** user SHALL navigate without full page reload

---

### Requirement: Interactive Filtering and Controls

The system SHALL provide comprehensive filtering and parameter adjustment controls.

#### Scenario: Filter panel

- **WHEN** user opens filter panel
- **THEN** filters SHALL include:
  - State selector (multi-select: CO, UT, ID)
  - Metro area selector (multi-select with search)
  - County selector (searchable dropdown)
  - Score range slider (min-max, 0-100)
  - Land use category (urban, suburban, rural)
- **AND** "Apply Filters" button SHALL trigger filter application
- **AND** "Clear Filters" button SHALL reset to defaults
- **AND** filtered hex count SHALL be displayed

#### Scenario: Parameter adjustment panel

- **WHEN** user opens "Advanced Settings"
- **THEN** adjustable parameters SHALL include:
  - Subscore weights (7 sliders, constrained to sum=100)
  - Decay parameters (alpha per mode)
  - Value of time (VOT, weekday/weekend)
  - CES elasticity (rho per category)
  - Satiation kappa (per category)
- **AND** parameter validation SHALL occur in real-time
- **AND** "Recalculate" button SHALL trigger score recomputation job
- **AND** "Reset to Defaults" button SHALL restore original parameter values

#### Scenario: Filter persistence

- **WHEN** user applies filters
- **THEN** filter state SHALL be encoded in URL query parameters
- **AND** URL SHALL be shareable (others can view same filtered view)
- **AND** browser refresh SHALL preserve filters

---

### Requirement: Dash Callback System

The system SHALL use Dash callbacks for reactive interactivity without full page reloads.

#### Scenario: Callback registration

- **WHEN** defining UI interactions
- **THEN** callbacks SHALL be registered with @app.callback decorator
- **AND** inputs SHALL be clearly defined (e.g., dropdown value, slider value)
- **AND** outputs SHALL be specified (e.g., update graph, update table)
- **AND** state SHALL be preserved across callbacks when needed

#### Scenario: Callback performance

- **WHEN** callback is triggered
- **THEN** execution SHALL complete in <1 second for simple callbacks
- **AND** execution SHALL complete in <5 seconds for complex callbacks (aggregation, filtering)
- **AND** long-running operations SHALL be offloaded to background jobs
- **AND** loading spinners SHALL appear during callback execution

#### Scenario: Error handling in callbacks

- **WHEN** callback encounters error
- **THEN** error SHALL be caught and logged
- **AND** user-friendly error message SHALL be displayed in UI
- **AND** application SHALL NOT crash or freeze
- **AND** user SHALL be able to retry or return to previous state

#### Scenario: Debouncing rapid interactions

- **WHEN** user rapidly adjusts slider or types in input
- **THEN** callbacks SHALL be debounced (wait 200ms after last change)
- **AND** excessive callback firing SHALL be prevented
- **AND** UI SHALL remain responsive during debounce period

---

### Requirement: CLI Integration via Job Queue

The system SHALL enable CLI command execution from UI with progress tracking.

#### Scenario: Job submission form

- **WHEN** user submits pipeline job
- **THEN** form SHALL include:
  - Job type (data refresh, score recomputation, export)
  - Parameters (config file, region, output format)
  - Resource limits (max memory, timeout)
- **AND** form validation SHALL occur before submission
- **AND** job SHALL be assigned unique ID (UUID)

#### Scenario: Job execution

- **WHEN** job is submitted
- **THEN** CLI command SHALL execute as background subprocess
- **AND** stdout/stderr SHALL be captured and logged
- **AND** job status SHALL be tracked (pending, running, completed, failed, cancelled)
- **AND** job metadata SHALL be stored (command, parameters, timestamps)

#### Scenario: Job progress tracking

- **WHEN** job is running
- **THEN** UI SHALL display progress bar (0-100%)
- **AND** progress SHALL be parsed from CLI log output
- **AND** ETA SHALL be estimated based on current throughput
- **AND** user SHALL be able to view real-time logs (streaming)

#### Scenario: Job completion

- **WHEN** job completes successfully
- **THEN** toast notification SHALL appear
- **AND** output files SHALL be available for download or viewing
- **AND** if data changed, visualization SHALL auto-refresh
- **AND** job result SHALL be stored for 30 days

#### Scenario: Job failure

- **WHEN** job fails
- **THEN** error message SHALL be displayed
- **AND** full logs SHALL be accessible for debugging
- **AND** user SHALL be able to retry with modified parameters
- **AND** failure SHALL be logged for monitoring

#### Scenario: Job cancellation

- **WHEN** user cancels running job
- **THEN** subprocess SHALL be terminated gracefully (SIGTERM)
- **AND** partial outputs SHALL be preserved
- **AND** job status SHALL be marked as cancelled
- **AND** resources SHALL be cleaned up

---

### Requirement: Comparison and Analysis Tools

The system SHALL provide tools for comparing runs, regions, and subscores.

#### Scenario: Side-by-side map comparison

- **WHEN** user activates comparison mode
- **THEN** layout SHALL show two map panels (left and right)
- **AND** each panel SHALL have independent controls (subscore, filters)
- **AND** zoom and pan SHALL be synchronized (toggle on/off)

#### Scenario: Comparison configuration

- **WHEN** configuring comparison
- **THEN** comparison types SHALL include:
  - Run-to-run (different parameter sets)
  - Region-to-region (Denver vs SLC)
  - Subscore-to-subscore (EA vs LCA)
  - Temporal (before/after)
- **AND** user SHALL select data source for left and right panels
- **AND** comparison SHALL load data for both selections

#### Scenario: Difference heat map

- **WHEN** viewing comparison
- **THEN** third panel SHALL show difference (run2 - run1)
- **AND** diverging color scale SHALL be used (red=run1 better, blue=run2 better)
- **AND** hexes with large differences (>10 points) SHALL be highlighted

#### Scenario: Comparison statistics

- **WHEN** comparison is active
- **THEN** summary table SHALL display:
  - Mean, median, std for both runs
  - Correlation coefficient (R²)
  - Mean absolute difference (MAD)
  - % of hexes with >10-point change
- **AND** scatter plot SHALL show: X=run1 scores, Y=run2 scores
- **AND** export button SHALL save comparison report (PDF or HTML)

---

### Requirement: Data Loading and Management

The system SHALL efficiently load and manage AUCS output data.

#### Scenario: Parquet data loading

- **WHEN** application starts
- **THEN** system SHALL load latest AUCS outputs from Parquet files
- **AND** schema validation SHALL occur (check required columns)
- **AND** data summary SHALL be computed (row count, score statistics)
- **AND** load time SHALL be <30 seconds for 1M hexes

#### Scenario: Run selection

- **WHEN** multiple runs exist
- **THEN** user SHALL select which run to visualize (dropdown)
- **AND** run metadata SHALL be displayed (date, parameter hash, version)
- **AND** switching runs SHALL reload data without restart

#### Scenario: Data refresh

- **WHEN** new pipeline run completes
- **THEN** system SHALL detect new output files
- **AND** notification SHALL appear: "New data available, click to refresh"
- **AND** refresh SHALL reload Parquet files and update visualizations
- **AND** previous data SHALL be preserved (allow switching back)

#### Scenario: Lazy data loading

- **WHEN** loading large datasets
- **THEN** only metadata SHALL load initially (bounding boxes, statistics)
- **AND** hex data SHALL be loaded on-demand per viewport
- **AND** spatial index SHALL be built for fast queries
- **AND** memory usage SHALL be optimized (load only needed columns)

---

### Requirement: User Experience and Design

The system SHALL provide a polished, intuitive user interface.

#### Scenario: Consistent styling

- **WHEN** viewing any page
- **THEN** consistent color scheme SHALL be applied (brand colors)
- **AND** consistent typography SHALL be used (font family, sizes, weights)
- **AND** consistent spacing SHALL be maintained (margins, padding)
- **AND** all interactive elements SHALL have hover states

#### Scenario: Loading indicators

- **WHEN** data is being fetched or processed
- **THEN** spinner or progress bar SHALL appear
- **AND** loading message SHALL explain what is happening
- **AND** user SHALL be able to cancel long operations

#### Scenario: Toast notifications

- **WHEN** action completes (job finish, export complete, error)
- **THEN** toast notification SHALL appear in corner
- **AND** notification SHALL auto-dismiss after 5 seconds (or be dismissible)
- **AND** notification SHALL have appropriate icon (success, error, info, warning)

#### Scenario: Tooltips and help text

- **WHEN** user hovers over UI element
- **THEN** tooltip SHALL explain element purpose (if not obvious)
- **AND** complex controls SHALL have "?" icon with help text
- **AND** help text SHALL be concise (<50 words)

#### Scenario: Keyboard navigation

- **WHEN** using keyboard
- **THEN** Tab key SHALL move focus through interactive elements
- **AND** Enter key SHALL activate buttons and submit forms
- **AND** Escape key SHALL close modals and drawers
- **AND** focus indicators SHALL be visible

---

### Requirement: Security and Authentication

The system SHALL implement security measures appropriate for deployment context.

#### Scenario: Optional authentication

- **WHEN** authentication is enabled (configurable)
- **THEN** login page SHALL appear on first visit
- **AND** supported auth methods SHALL include: basic auth, OAuth2, SAML
- **AND** session SHALL persist across browser restarts (remember me)
- **AND** logout button SHALL clear session

#### Scenario: Input validation

- **WHEN** user provides input (filters, parameters, file uploads)
- **THEN** input SHALL be validated (type, range, format)
- **AND** malicious input SHALL be rejected (prevent XSS, injection)
- **AND** validation errors SHALL be displayed clearly

#### Scenario: Rate limiting

- **WHEN** user makes requests
- **THEN** rate limit SHALL be enforced (max 100 req/min per user)
- **AND** excessive requests SHALL be rejected with 429 status
- **AND** user SHALL see rate limit error message

#### Scenario: Secure API endpoints

- **WHEN** accessing API endpoints
- **THEN** authentication token SHALL be required (if auth enabled)
- **AND** HTTPS SHALL be enforced in production
- **AND** CSRF protection SHALL be enabled

---

### Requirement: Deployment and Operations

The system SHALL be deployable to production with operational monitoring.

#### Scenario: Production deployment

- **WHEN** deploying to production
- **THEN** Gunicorn or Uvicorn SHALL be used as WSGI server
- **AND** worker count SHALL be set to (2 × CPU cores + 1)
- **AND** worker timeout SHALL be 300 seconds (for long callbacks)
- **AND** environment variables SHALL configure all settings (12-factor app)

#### Scenario: Health checks

- **WHEN** monitoring application health
- **THEN** `/health` endpoint SHALL return 200 if healthy
- **AND** health check SHALL verify: data files exist, cache accessible, routing services reachable
- **AND** unhealthy status SHALL trigger restart (if orchestrated)

#### Scenario: Logging

- **WHEN** application is running
- **THEN** logs SHALL be written to stdout (container-friendly)
- **AND** logs SHALL be structured JSON (parseable)
- **AND** log level SHALL be configurable (DEBUG, INFO, WARNING, ERROR)
- **AND** sensitive data SHALL be sanitized from logs

#### Scenario: Error reporting

- **WHEN** error occurs
- **THEN** error SHALL be logged with full context (traceback, user action, request ID)
- **AND** error SHALL be reported to monitoring service (Sentry, optional)
- **AND** user SHALL see generic error message (not technical details)

---

### Requirement: Documentation and Help

The system SHALL provide in-app documentation and external user guides.

#### Scenario: In-app help

- **WHEN** user needs help
- **THEN** "Help" button SHALL open sidebar with context-sensitive tips
- **AND** tooltips SHALL appear on hover for all controls
- **AND** "Getting Started" tutorial SHALL guide first-time users

#### Scenario: User guide

- **WHEN** user accesses documentation
- **THEN** comprehensive user guide SHALL be available (docs/UI_USER_GUIDE.md)
- **AND** guide SHALL include: navigation, filtering, parameter adjustment, export
- **AND** screenshots SHALL illustrate key features
- **AND** video tutorial (5-minute walkthrough) SHALL be linked

#### Scenario: FAQ

- **WHEN** user has common question
- **THEN** FAQ page SHALL answer common questions:
  - "What is AUCS?"
  - "How do I interpret scores?"
  - "Why is my hex score low?"
  - "How often is data updated?"
  - "How do I export data?"
- **AND** FAQ SHALL be searchable

#### Scenario: Contact support

- **WHEN** user needs help not covered by docs
- **THEN** "Contact Support" link SHALL provide email or form
- **AND** support request SHALL include: user ID, current page, error logs (if applicable)
