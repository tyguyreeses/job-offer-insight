# Frontend `src`

Core UI logic and data flow.

## Key Files

- `App.tsx`: main state and mutation/query lifecycle
- `api.ts`: fetch wrapper and endpoint definitions
- `types.ts`: TypeScript models for API data
- `styles.css`: global styles and layout rules

## Key Behavior

- Compare query key: `["offers", sortBy]`
- Mutations refresh data via `invalidateQueries({ queryKey: ["offers"] })`
