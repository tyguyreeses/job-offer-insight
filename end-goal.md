# End-Goal - job offer reviewer website called Job Offer Insight

## Pages and Main Functions

### Main Page

- add a job - large text
- Two buttons
    - Audio input
    - Text input
- AI parses audio into text
- AI extracts job information to fulfill a standardized format
- Prompts user (in big soft text) with further questions and information to fill out json schema
- Currency standard: USD only
- JSON schema:
    - Annual salary (converts hourly wages and hours/week into annual salary when needed)
    - Various benefits (monetary)
        - Insurance
        - Retirement contributions
        - Signing bonus
        - Stock options
        - Etc.
    - Other things you’re excited about (non-monetary)
        - Doing good in the world
        - Good company culture
        - Gym
        - Etc.
    - Convert that into a JSON schema and store it in a database (SQLite)
- Example offer schema (starting point):

```json
{
  "id": "uuid",
  "company_name": "Acme Robotics",
  "role_title": "Software Engineer II",
  "location": "Denver, CO",
  "employment_type": "full_time",
  "work_model": "hybrid",
  "compensation": {
    "annual_base_salary_usd": 145000,
    "hourly_rate_usd": null,
    "hours_per_week": null,
    "annualized_total_cash_usd": 157000,
    "signing_bonus_usd": 12000,
    "target_bonus_percent": 10
  },
  "monetary_benefits": {
    "retirement_match_percent": 4,
    "retirement_match_cap_usd": null,
    "health_insurance_employer_monthly_usd": 650,
    "hsa_employer_annual_usd": 1000,
    "equity_grant_usd": 40000,
    "equity_vesting_schedule": "4 years, 1-year cliff",
    "other_monetary_benefits": [
      "Annual wellness stipend",
      "Commuter reimbursement"
    ]
  },
  "non_monetary_benefits": {
    "mission_alignment_notes": "Strong climate impact mission",
    "culture_notes": "Collaborative and low-ego",
    "growth_notes": "Clear promotion rubric",
    "wellness_notes": "Gym reimbursement",
    "pto_days": 20,
    "remote_flexibility_notes": "2 days in office",
    "other_non_monetary_benefits": [
      "Strong mentorship culture",
      "Interesting technical domain"
    ]
  },
  "offer_meta": {
    "status": "active",
    "source_input_type": "audio",
    "created_at": "2026-04-07T20:00:00Z",
    "updated_at": "2026-04-07T20:00:00Z"
  }
}
```

- Required fields to save an offer (my recommended minimum):
    - `company_name`
    - `role_title`
    - At least one base pay path:
        - either `compensation.annual_base_salary_usd`
        - or both `compensation.hourly_rate_usd` and `compensation.hours_per_week`
- Annualization rule:
    - If hourly compensation is provided, default annual base salary calculation is:
      `hourly_rate_usd * hours_per_week * 52`

- Missing information flow:
    - If a field is missing, the agent must explicitly ask the user whether to add that information or confirm it is not
      part of the offer.
    - If the user confirms it is not part of the offer, store the field as blank (`null`, empty string, or empty array
      as appropriate).
    - Backend behavior for blank values: treat blank values as "benefit/field not included in the offer", not as an
      error.
    - Validation approach:
        - Soft warnings for all non-required fields
        - Hard blocking validation only for required fields listed above
- Editing existing offer flow:
    - Editing must be supported
    - Editing uses a structured form pre-filled with existing values
    - Editing does not return the user to the initial open-ended AI input page

### Dashboard to display job entries

- Cards side by side with a side scroll left to right, sorted by a changeable option
- Each card has the following information from the json schema displayed vertically in this order
    - Salary
    - Monetary benefits
    - Non-monetary benefits (AI bullet point summary - generated once and then stored)
    - Date created (mm-dd-yyyy)
- Can select cards from this view and press a compare button (can compare one-to-all and one-to-one)
- Selection rule:
    - Maximum of two selected cards at one time
    - If a third card is selected, automatically deselect the earliest selected card

### Ability to run a comparison between two entries

- New page, separate from the dashboard and job creation pages
- Leave comparison logic/ranking blank for now
- One-to-one comparison behavior:
    - Show selected offer card on the left
    - Show selected offer card on the right
    - Show an empty middle comparison summary area with a placeholder
- One-to-all comparison behavior (inferred by how many offers are selected):
    - Show selected base offer card on the left
    - Keep the middle comparison summary area empty with a placeholder
    - Keep the right area empty with a placeholder
- Ability to compare one entry to all other entries (UI flow only for now)
- Saved comparison storage:
    - Store selected offer IDs
    - Store comparison summary text (placeholder for now)
    - Support optional user note
    - If note exists, display it below everything else on the comparison page
- Ability to store saved comparison or return back to dashboard with a button

## General Principles

### Styling

- Custom CSS styling
- Large, centered text
- Clean, minimal style
- Soft, blue glow when hovering over selectable items (also centered)
- Smooth loading animations - fade in top to bottom, left to right
- Elegant navbar
    - Dashboard (default when at least one entry exists)
    - Add Entry (default when no entries exist)
        - selecting entries displayed here and clicking on the compare button navigates to the compare screen
    - Compare
        - If not coming from the compare button on the entry page, if previous comparisons have been saved, a list of
          those should be displayed
        - if not coming from the compare button on the entry page, displays a list of potential offers to select for a
          comparison (only displaying company name)

### Code

- Python backend, FastAPI, Vite-React frontend
- The code should always follow "injection dependency first" and framework-oriented design" principles.
- `config.yaml` does all the decision-making and `main.py` does all the setup work.
- add a logger (debug vs info configured at runtime in `main.py` using `--debug`)
- Use OpenAI's python library and client for all AI services
- Use `reference-audio-material/README.md` to explore that folder for guidance on how the audio system should be
  designed.

## Suggested Project Directory Tree

```text
job-offer-insight/
├── AGENTS.md
├── README.md
├── PLAN.md
├── end-goal.md
├── reference-audio-material/                     # Existing reference only, not runtime code
├── src/
│   ├── config.yaml                               # Runtime configuration source of truth
│   ├── backend/
│   │   ├── main.py                               # FastAPI app setup, DI wiring, logger, startup/shutdown
│   │   ├── api/
│   │   │   ├── router.py                         # Top-level API router composition
│   │   │   └── v1/
│   │   │       ├── offers.py                     # Create/read/update offer endpoints
│   │   │       ├── comparisons.py                # Compare endpoint + saved comparisons CRUD
│   │   │       └── health.py                     # Health/readiness endpoints
│   │   ├── domain/
│   │   │   ├── models/
│   │   │   │   ├── offer.py                      # Domain offer model
│   │   │   │   └── comparison.py                 # Domain comparison model
│   │   │   ├── services/
│   │   │   │   ├── offer_service.py              # Offer orchestration + validation rules
│   │   │   │   ├── compare_service.py            # Compare-mode orchestration + placeholder summary
│   │   │   │   └── ai_intake_service.py          # Transcript extraction + missing-info Q flow
│   │   │   └── rules/
│   │   │       ├── required_fields.py            # Hard required field checks
│   │   │       └── annualization.py              # hourly_rate * hours_per_week * 52
│   │   ├── gen_ai/
│   │   │   ├── client.py                         # OpenAI client factory
│   │   │   ├── prompts/
│   │   │   │   ├── extract_offer.md              # Extract structured offer JSON
│   │   │   │   ├── ask_missing_fields.md         # Clarifying questions prompt
│   │   │   │   └── summarize_non_monetary.md     # Bullet-point summary prompt
│   │   │   └── mappers/
│   │   │       └── offer_mapper.py               # LLM output -> typed schema mapping
│   │   ├── prompts/                              # Keep for compatibility if needed
│   │   ├── storage/
│   │   │   ├── db.py                             # SQLite engine/session setup
│   │   │   ├── schema.sql                        # Initial schema DDL
│   │   │   ├── repositories/
│   │   │   │   ├── offer_repository.py
│   │   │   │   └── comparison_repository.py
│   │   │   └── migrations/
│   │   │       └── 0001_init.sql
│   │   ├── schemas/
│   │   │   ├── offer.py                          # Pydantic API schemas
│   │   │   └── comparison.py
│   │   └── utils/
│   │       ├── config_loader.py                  # Load + validate config.yaml
│   │       ├── config_types.py                   # Typed config models
│   │       └── logging.py                        # Logger configuration
│   ├── frontend/
│   │   ├── index.html
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx
│   │       ├── styles/
│   │       │   ├── tokens.css                    # Typography/colors/spacing/motion tokens
│   │       │   └── global.css                    # Global style + layout
│   │       ├── pages/
│   │       │   ├── AddEntryPage.tsx              # Audio/text intake + missing-field form flow
│   │       │   ├── DashboardPage.tsx             # Card list + max-two selection behavior
│   │       │   ├── ComparePage.tsx               # Left/right cards + placeholder summary region
│   │       │   └── SavedComparisonsPage.tsx      # List/view saved comparisons
│   │       ├── components/
│   │       │   ├── Navbar.tsx
│   │       │   ├── OfferCard.tsx
│   │       │   ├── ComparisonPlaceholder.tsx
│   │       │   ├── OfferForm.tsx                 # Edit existing offer in structured form
│   │       │   ├── AudioInputPanel.tsx
│   │       │   └── WarningBanner.tsx             # Soft validation warnings
│   │       ├── services/
│   │       │   ├── apiClient.ts
│   │       │   ├── offersApi.ts
│   │       │   └── comparisonsApi.ts
│   │       ├── state/
│   │       │   ├── selectionStore.ts             # Deselect oldest when selecting a third
│   │       │   └── offersStore.ts
│   │       └── types/
│   │           ├── offer.ts
│   │           └── comparison.ts
│   └── docs/
│       ├── application_interface.md              # Black-box contract, request/response behavior
│       ├── plans/
│       │   └── <feature-branch>.md
│       └── decisions/
│           └── 0001-offer-schema.md              # Optional architecture decision records
└── tests/
    ├── backend/
    │   ├── api/
    │   ├── domain/
    │   └── storage/
    ├── frontend/
    │   ├── pages/
    │   └── components/
    └── e2e/
```
