---
trigger: always_on
glob: *.{js,ts,jsx,tsx,py,go,java}
description: General code quality standards for all languages
---

# Code Quality Standards

## General Principles

### Readability First
- Code is read more often than written
- Use descriptive names for variables, functions, and classes
- Keep functions small and focused (single responsibility)
- Add comments for complex logic, not obvious code

### Consistency
- Follow project conventions and style guides
- Use consistent naming conventions
- Maintain consistent indentation and formatting
- Follow language-specific idioms

### Simplicity
- Prefer simple solutions over clever ones
- Avoid premature optimization
- Don't repeat yourself (DRY)
- Keep it simple, stupid (KISS)

## Naming Conventions

### Variables
- Use descriptive names: `userCount` not `uc`
- Boolean variables: `isActive`, `hasPermission`, `canEdit`
- Arrays/Collections: Use plural names: `users`, `items`
- Constants: Use UPPER_SNAKE_CASE: `MAX_RETRIES`, `API_BASE_URL`

### Functions/Methods
- Use verbs: `getUser()`, `calculateTotal()`, `validateInput()`
- Be specific: `fetchUserById()` not `getData()`
- Boolean returns: `isValid()`, `hasAccess()`, `canPerform()`

### Classes
- Use nouns: `UserManager`, `PaymentProcessor`
- Be descriptive: `OrderValidator` not `Validator`
- Avoid generic names: `Handler`, `Manager`, `Processor` (add specificity)

## Function Design

### Size and Complexity
- Functions should be small (< 50 lines ideally)
- Maximum 3-4 parameters (use objects for more)
- Single responsibility - do one thing well
- Cyclomatic complexity < 10

### Error Handling
- Handle errors explicitly, don't ignore them
- Use specific error types
- Provide meaningful error messages
- Clean up resources in finally blocks

### Pure Functions When Possible
- Prefer pure functions (no side effects)
- Make side effects explicit and isolated
- Avoid global state modification

## Code Structure

### File Organization
- One class/component per file
- Related code together
- Logical grouping of functions
- Imports at the top, organized by type

### Module Organization
```
src/
├── components/     # UI components
├── services/       # Business logic
├── utils/          # Helper functions
├── models/         # Data models/types
├── config/         # Configuration
└── tests/          # Test files
```

### Layered Architecture
- Presentation layer (UI)
- Business logic layer (services)
- Data access layer (repositories)
- Clear separation of concerns

## Documentation

### Code Comments
- Explain **why**, not **what**
- Document complex algorithms
- Note non-obvious behavior
- Keep comments up to date

### Function Documentation
```javascript
/**
 * Calculates the total price including tax and discounts
 * 
 * @param {number} basePrice - The original price before adjustments
 * @param {number} taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @param {number} discount - Discount amount to subtract
 * @returns {number} Final price after tax and discount
 * @throws {Error} If basePrice is negative
 */
function calculateTotal(basePrice, taxRate, discount) {
  // implementation
}
```

### README Files
- Purpose and overview
- Setup instructions
- Usage examples
- API documentation
- Contributing guidelines

## Testing

### Test Coverage
- Aim for > 80% code coverage
- Test critical paths thoroughly
- Include edge cases and error conditions
- Test both happy path and failure scenarios

### Test Organization
- One test file per source file
- Descriptive test names
- Arrange-Act-Assert pattern
- Independent tests (no shared state)

### Test Naming
```javascript
describe('UserValidator', () => {
  it('should accept valid email addresses', () => {})
  it('should reject emails without @ symbol', () => {})
  it('should throw error for null input', () => {})
})
```

## Performance

### Do
- Profile before optimizing
- Cache expensive computations
- Use appropriate data structures
- Lazy load when appropriate
- Implement pagination for large datasets

### Don't
- Optimize prematurely
- Sacrifice readability for minor gains
- Ignore algorithmic complexity
- Load entire datasets into memory

## Security

### Input Validation
- Validate all user input
- Sanitize before database queries
- Escape output in templates
- Use parameterized queries

### Authentication/Authorization
- Never store passwords in plain text
- Use established libraries (don't roll your own crypto)
- Implement proper session management
- Follow principle of least privilege

### Sensitive Data
- Never commit secrets to version control
- Use environment variables for config
- Log carefully (no sensitive data)
- Encrypt data at rest and in transit

## Version Control

### Commits
- Make small, logical commits
- Write clear commit messages
- Reference issue/ticket numbers
- Don't commit commented-out code

### Commit Messages
```
feat: Add user authentication module

- Implement JWT token generation
- Add login/logout endpoints
- Include password hashing

Closes #123
```

### Branches
- Feature branches: `feature/user-auth`
- Bug fixes: `fix/login-error`
- Hotfixes: `hotfix/security-patch`
- Keep branches short-lived

## Code Review

### Before Submitting
- Self-review your changes
- Run tests locally
- Update documentation
- Remove debug code
- Check for console.log statements

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate

## Language-Specific Guidelines

### JavaScript/TypeScript
- Use `const` by default, `let` when needed, avoid `var`
- Prefer async/await over callbacks
- Use TypeScript strict mode
- Leverage type inference
- Use optional chaining: `user?.address?.city`

### Python
- Follow PEP 8
- Use type hints
- Leverage list comprehensions appropriately
- Use context managers for resources
- Prefer f-strings for formatting

### Go
- Follow effective Go guidelines
- Use gofmt
- Handle errors explicitly
- Use defer for cleanup
- Keep interfaces small

## Anti-Patterns to Avoid

### God Objects
- Classes that do too much
- Break into smaller, focused classes

### Spaghetti Code
- Tangled, difficult-to-follow logic
- Refactor into clear, structured code

### Magic Numbers
- Unexplained numeric constants
- Use named constants with explanations

### Premature Abstraction
- Over-engineering simple solutions
- Add abstraction when needed, not "just in case"

## Continuous Improvement

- Refactor as you go
- Pay down technical debt regularly
- Learn from code reviews
- Stay updated with best practices
- Share knowledge with the team

---

**Remember**: These are guidelines, not rigid rules. Use judgment based on context, 
but be consistent within your project.
