# Pull Request Workflow

## Overview
This workflow ensures code quality and team collaboration through structured pull requests.

## Before Creating a PR

### 1. Branch Preparation
```bash
# Ensure you're on the latest main/master
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Development
- Make focused commits with clear messages
- Write tests for new functionality
- Update documentation as needed
- Run tests locally: `npm test` / `pytest` / etc.

### 3. Self-Review Checklist
- [ ] Code follows team style guidelines
- [ ] All tests pass locally
- [ ] No console.log or debug statements
- [ ] No commented-out code
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] No sensitive data in code

### 4. Pre-PR Commands
```bash
# Run linter
npm run lint  # or equivalent

# Run tests
npm test

# Check for type errors (TypeScript)
npm run type-check

# Format code
npm run format
```

## Creating the Pull Request

### 1. Update Your Branch
```bash
# Rebase on latest main to avoid conflicts
git checkout main
git pull origin main
git checkout your-feature-branch
git rebase main

# Or merge if rebasing is not preferred
git merge main
```

### 2. Push Your Branch
```bash
git push origin your-feature-branch
```

### 3. PR Title Format
```
<type>: <short description>

Examples:
feat: Add user authentication
fix: Resolve memory leak in data processor
docs: Update API documentation
refactor: Simplify payment validation logic
test: Add unit tests for user service
```

### 4. PR Description Template
```markdown
## Summary
Brief description of what this PR does

## Changes
- Bullet point list of main changes
- What was added/modified/removed
- Why these changes were necessary

## Testing
- How to test these changes
- Test cases covered
- Screenshots (if UI changes)

## Related Issues
Closes #123
Relates to #456

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Backwards compatible
- [ ] Migration guide included (if applicable)

## Screenshots (if applicable)
[Add screenshots here]
```

## During Code Review

### For Authors

#### Responding to Feedback
- Be open to suggestions
- Ask for clarification if needed
- Don't take feedback personally
- Respond to all comments
- Mark resolved conversations

#### Making Changes
```bash
# Make requested changes
git add .
git commit -m "Address review feedback"
git push origin your-feature-branch
```

#### Best Practices
- Respond within 24 hours
- Explain your reasoning for decisions
- If disagreeing, provide alternatives
- Thank reviewers for their time
- Update the PR description if scope changes

### For Reviewers

#### Review Checklist
- [ ] Code quality and readability
- [ ] Tests are comprehensive
- [ ] No security vulnerabilities
- [ ] Performance considerations
- [ ] Error handling appropriate
- [ ] Documentation clear
- [ ] Follows team conventions
- [ ] No unnecessary complexity

#### Providing Feedback

**Good Feedback**
```
✅ "Consider extracting this into a separate function for reusability.
   This logic might be useful in other parts of the codebase."

✅ "This could cause a race condition if multiple users access simultaneously.
   Consider adding a mutex lock here."

✅ "Great job on the error handling! The messages are very clear."
```

**Less Helpful Feedback**
```
❌ "This is wrong"
❌ "Why did you do it this way?"
❌ "Just refactor this"
```

#### Comment Types
- **Blocking**: Must be fixed before merge (security, bugs, breaking changes)
- **Non-blocking**: Suggestions for improvement (nits, style preferences)
- **Question**: Asking for clarification
- **Praise**: Acknowledging good work

#### Review Standards
- Review within 24-48 hours
- Be constructive and specific
- Approve if satisfied or minor nits only
- Request changes if blocking issues
- Comment if questions need answering

## Merging Process

### Requirements Before Merge
- [ ] All CI/CD checks passing
- [ ] Minimum required approvals (typically 1-2)
- [ ] No unresolved conversations
- [ ] Branch is up to date with target
- [ ] No merge conflicts

### Merge Options

#### Merge Commit (Default)
```bash
git checkout main
git merge --no-ff feature-branch
```
- Preserves full history
- Shows feature as a unit
- Good for feature tracking

#### Squash and Merge
```bash
git merge --squash feature-branch
git commit -m "feat: Add user authentication

- Implement JWT tokens
- Add login/logout endpoints
- Include password hashing"
```
- Single commit per feature
- Cleaner history
- Good for atomic features

#### Rebase and Merge
```bash
git rebase main
git checkout main
git merge feature-branch
```
- Linear history
- No merge commits
- Good for small changes

### Post-Merge Actions

#### 1. Delete Branch
```bash
# Delete remote branch
git push origin --delete feature-branch

# Delete local branch
git branch -d feature-branch
```

#### 2. Update Related Issues
- Close linked issues
- Update project boards
- Notify stakeholders

#### 3. Monitor Deployment
- Watch CI/CD pipeline
- Monitor error tracking
- Verify in staging/production

## Common Scenarios

### Breaking Changes
1. Document in PR description
2. Update CHANGELOG
3. Provide migration guide
4. Notify team before merge
5. Consider feature flag

### Hotfixes
1. Branch from `main`
2. Name: `hotfix/description`
3. Fast-track review
4. Merge to both `main` and `develop`
5. Tag with version number

### Large Features
1. Break into smaller PRs
2. Use feature flags
3. Merge incrementally
4. Enable when complete
5. Document rollback plan

### Merge Conflicts
```bash
# Update your branch
git checkout main
git pull origin main
git checkout your-feature-branch
git merge main

# Resolve conflicts
# ... edit conflicting files ...

git add .
git commit -m "Resolve merge conflicts"
git push origin your-feature-branch
```

## Best Practices

### PR Size
- Keep PRs small (< 400 lines changed)
- Single purpose per PR
- Break large features into smaller PRs
- Easier to review and less risky

### Commit Quality
```bash
# Good commits
git commit -m "feat: Add email validation to signup form"
git commit -m "test: Add unit tests for email validator"
git commit -m "docs: Update API documentation for new endpoints"

# Avoid
git commit -m "stuff"
git commit -m "work in progress"
git commit -m "fixed"
```

### Communication
- Be responsive to comments
- Use PR for technical discussion
- Take lengthy debates offline
- Tag relevant people with @mentions
- Use GitHub suggestions for small changes

### CI/CD Integration
- All tests must pass
- Linting checks pass
- Security scans pass
- Build succeeds
- Coverage maintained or improved

## Emergency Procedures

### Reverting a PR
```bash
# Revert the merge commit
git revert -m 1 <merge-commit-hash>
git push origin main
```

### Rollback in Production
1. Identify problematic commit
2. Create revert PR
3. Fast-track review
4. Deploy immediately
5. Post-mortem after resolution

## Metrics and Goals

### Team Goals
- Average PR age: < 2 days
- Time to first review: < 24 hours
- Time to merge: < 48 hours
- PR size: < 400 lines

### Quality Metrics
- Test coverage: > 80%
- CI success rate: > 95%
- Escaped defects: < 5%
- Code review participation: 100%

---

**Remember**: The goal is high-quality, maintainable code. Take time to do it right!
