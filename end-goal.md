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
- Json Schema:
    - Annual salary (converts wages and hours to annual salary)
    - Various benefits (monetary)
        - Insurance
        - Retirement contributions
        - Signing bonus
        - Stock options
        - Etc.
    - Other things you’re excited about (non monetary)
        - Doing good in the world
        - Good company culture
        - Gym?
        - Etc.
    - Convert that into a json schema and stores it in a database (SQLite)

### Dashboard to display job entries

- Cards side by side with a side scroll left to right, sorted by a changeable option
- Each card has the following information from the json schema displayed vertically in this order
    - Salary
    - Monetary benefits
    - Non-monetary benefits
    - Date created (mm-dd-yyyy)
    - Etc.
- Can select cards from this view and press a compare button (can compare one-to-all, one-to-one, or even one-to-many)

### Ability to run a comparison between two entries

- New page, separate from the dashboard and job creation pages
- Entries on the left and right with comparison of each section of the entry
- Ability to compare one entry to all other entries
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
        - if not coming from the compare button on the entry page, displays a list of potential offers to select for a
          comparison (only displaying company name)

### Code

- Python backend, FastAPI, Vite-React frontend
- The code should always follow "injection dependency first" and framework-oriented design" principles.
- `config.yaml` does all the decision-making and `main.py` does all the setup work.
- add a logger (debug vs info configured at runtime in `main.py` using `--debug`)
- Use OpenAI's python library and client for all AI services
- Use `reference-audio-material/README.md` to explore that folder for guidance on how the audio system should be designed.