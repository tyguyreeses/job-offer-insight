# Frontend

React UI for creating and comparing job offers.

## Key Files

- `src/App.tsx`: page flow, query/mutation wiring, edit mode
- `src/api.ts`: backend calls and error handling
- `src/types.ts`: shared data contracts
- `src/components/OfferForm.tsx`: create/edit form behavior
- `src/components/OfferTable.tsx`: ranking table and actions
- `src/components/OfferChart.tsx`: metric chart
- `src/styles.css`: layout and styles

## Change Areas

- UI state and flow are managed in `src/App.tsx`.
- API transport and endpoint paths are defined in `src/api.ts`.
- Shared client-side data types are in `src/types.ts`.
- Styling and layout rules are in `src/styles.css`.
