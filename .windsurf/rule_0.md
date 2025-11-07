---
trigger: always_on
description: Guidelines for using Windsurf Cascade AI features
---

# Windsurf Cascade AI Guidelines

## Overview
These guidelines help you work effectively with Windsurf's Cascade AI assistant.


## Communication Best Practices

### Be Specific and Clear
- Provide context about what you're trying to achieve
- Include relevant file paths or function names
- Specify the programming language if not obvious

### Use Natural Language
- Write requests as you would to a colleague
- Don't worry about perfect syntax or formatting
- Ask follow-up questions to clarify

### Leverage Context
- Cascade can see your open files and workspace
- Reference code by saying "in the current file" or "the function above"
- Use @mentions for specific files: `@filename.ts`

## Code Generation

### Request Complete Solutions
- Ask for full implementations, not just snippets
- Request error handling and edge cases
- Specify dependencies or frameworks to use

### Iterative Development
- Start with a basic implementation
- Request improvements or refactoring in follow-up prompts
- Ask for explanations of complex logic

### Testing
- Request unit tests alongside implementations
- Ask for test cases covering edge cases
- Request integration or E2E tests when appropriate

## Code Review and Refactoring

### Review Assistance
- Ask Cascade to review your code for:
  - Potential bugs
  - Performance issues
  - Security vulnerabilities
  - Code style improvements

### Refactoring Requests
- "Refactor this to use async/await"
- "Make this code more modular"
- "Extract this into reusable functions"
- "Simplify this complex logic"

## Documentation

### Code Documentation
- Request JSDoc/TSDoc comments
- Ask for README sections
- Request inline comments for complex logic

### API Documentation
- Request OpenAPI/Swagger specs
- Ask for API usage examples
- Request endpoint descriptions

## Debugging

### Problem Description
- Describe the expected vs actual behavior
- Include error messages or stack traces
- Mention recent changes that might be related

### Debugging Strategies
- Ask Cascade to identify potential causes
- Request debugging steps or logging suggestions
- Ask for explanations of error messages

## Best Practices

### File Operations
- Be explicit about file paths
- Confirm before large file operations
- Review changes before applying

### Multi-File Changes
- Break large changes into smaller steps
- Review each file change individually
- Test incrementally

### Version Control
- Commit working code before major refactors
- Review Cascade's changes before committing
- Use meaningful commit messages

## Cascade-Specific Features

### Flow Mode
- Use for longer, complex tasks
- Let Cascade work through multiple steps
- Review the plan before execution

### Chat Mode
- Use for quick questions
- Request explanations
- Get code suggestions

### Commands
- `/explain` - Understand code functionality
- `/fix` - Address issues or bugs
- `/test` - Generate tests
- `/refactor` - Improve code structure

## Security Considerations

### Never Commit
- API keys or secrets
- Passwords or tokens
- Personal information
- Internal URLs or endpoints

### Always Review
- External dependencies being added
- File permission changes
- Network operations
- Database queries

## Examples

### Good Requests
```
"Create a React component for a user profile card that displays name, 
email, and avatar. Include TypeScript types and handle loading states."

"Review the authentication logic in @auth.ts for potential security issues."

"Add unit tests for the calculateTotal function covering edge cases 
like empty arrays and negative numbers."
```

### Vague Requests (Avoid)
```
"Make it better"
"Fix the bug"
"Add tests"
```

## Tips for Success

1. **Start Simple**: Begin with a clear, focused request
2. **Iterate**: Refine the solution through follow-up questions
3. **Verify**: Always review and test generated code
4. **Learn**: Ask Cascade to explain its decisions
5. **Context**: Provide relevant background information
6. **Feedback**: Tell Cascade if something isn't right

## Common Pitfalls

- Being too vague in requests
- Not reviewing generated code
- Accepting solutions without understanding
- Not testing changes before committing
- Requesting changes to too many files at once

## Integration with Team Workflow

- Use Cascade for initial implementations
- Have human code review before merging
- Document Cascade-assisted changes in commits
- Share useful prompts with the team
- Establish team guidelines for AI assistance

---

Remember: Cascade is a powerful tool, but you remain responsible for the code. 
Always review, understand, and test before committing changes.
