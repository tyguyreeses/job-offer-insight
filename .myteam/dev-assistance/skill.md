---
name: Developer Assistance
description: This skill provides specific instructions for implementing **non-myteam** related features. When implementing any new non-myteam feature, you MUST use this skill.
---

1. Call `Frontend` and/or `Backend` depending on feature requirements. 

2. Read relevant `DOCS.md` files before scanning many code files.

    - Use `DOCS.md` as the map of ownership, data flow, and key files, then read source files for implementation details.

4. Ask the user questions, one at a time, to gather the necessary information to implement the feature. 

    - Do not ask for all the information at once. Wait for the user's response after each question before asking the next one.

5. Implement the feature based on the gathered information.

    - Prioritize injection dependencies and modular design to ensure the new feature is maintainable and testable. Follow existing code patterns and best practices observed in the codebase.

6. Review the implementation to ensure it meets the requirements and does not introduce any bugs or issues.

    - Does the implementation meet the requirements?
    - Are there any duplicated code or opportunities for refactoring?
    - Are there any potential edge cases or error handling that needs to be addressed?
    - Implement changes as needed based on the review.

7. Update documentation to reflect the new feature and its implementation details.

    - README.md, CHANGELOG.md, DOCS.md, and any relevant code comments should be updated to provide brief and clear information about the new feature.
