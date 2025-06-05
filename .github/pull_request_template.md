# Pull Request

## Description
<!-- Provide a clear and concise description of what this PR accomplishes -->


## Related Issues/Stories
<!-- Link to relevant Issue / Jira story/task-->
Related to [Jira number]\
Fixes #issue

## Type of Change
<!-- Select the category that best describes what type of change your PR introduces. -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 🔧 Refactoring (code change that neither fixes a bug nor adds a feature)
- [ ] 📚 Documentation (changes to documentation only)
- [ ] 🧪 Tests (adding missing tests or correcting existing tests)
- [ ] 🎨 Style (formatting, missing semi colons, etc; no production code change)
- [ ] ⚡ Performance (changes that improve performance)
- [ ] 🔒 Security (changes that improve security)

## Components Modified
<!-- Check all that apply -->
- [ ] Frontend (React/TypeScript)
- [ ] Backend (FastAPI/Python)
- [ ] Database (PostgreSQL/Alembic migrations)
- [ ] LlamaStack Integration
- [ ] Chat functionality
- [ ] Virtual Agents
- [ ] Knowledge Bases
- [ ] MCP Servers
- [ ] Guardrails
- [ ] Authentication/Authorization
- [ ] Infrastructure
- [ ] Documentation

## Changes Made
<!-- Check all that apply. -->
### Backend Changes
- [ ] Added/Modified API endpoints
- [ ] Database schema changes (migrations included)
- [ ] Modified business logic
- [ ] Updated dependencies

### Frontend Changes
- [ ] Added/Modified UI components
- [ ] Updated hooks/services
- [ ] Modified routing
- [ ] Updated state management
- [ ] Style/UX improvements
- [ ] Updated dependencies

### Infrastructure Changes
- [ ] Updated Docker/Podman configuration
- [ ] Modified environment variables
- [ ] Updated deployment scripts
- [ ] Changed build process

> [!TIP]
> Use `~~text~~` to strikethrough items that don't apply to your changes. This is not needed for sections already marked "Select all that apply" or if you have checked the box indicating that the whole section does not apply.

## Testing
<!-- Describe the tests you ran and provide instructions to reproduce -->

### Automated Tests
- [ ] ~~Unit tests pass~~ *(No unit tests yet)*
- [ ] ~~Integration tests pass~~ *(No integration tests yet)*
- [ ] ~~E2E tests pass~~ *(No E2E tests yet)*
- [ ] New tests added for changes

### Manual Testing
#### LlamaStack Integration Testing
- [ ] Agent creation/retrieval works correctly
- [ ] Knowledge base ingestion works end-to-end (upload → processing → ready status)
- [ ] Knowledge base retrieval works in chat (RAG pipeline functions)
- [ ] Chat streaming responses work as expected

### Test Environment
<!-- Select all that apply -->
- [ ] Local environment
- [ ] Development cluster
- [ ] Staging cluster
- [ ] Production cluster

## Screenshots/Videos
<!-- If applicable, add screenshots or videos to help explain your changes -->

## Database Changes
<!-- If your PR includes database changes -->
- [ ] No database changes were made
### otherwise:
- [ ] Alembic migration files included
- [ ] Migration tested on clean database
- [ ] Migration tested on existing data
- [ ] Rollback migration tested
- [ ] Database schema documented
- [ ] Backward compatibility maintained

## API Changes
<!-- If your PR includes API changes -->
- [ ] No API changes were made
### otherwise:
- [ ] ~~Swagger documentation updated~~ *(No Swagger docs yet)*
- [ ] Frontend updated to match API changes
- [ ] Backward compatibility maintained
- [ ] API versioning considered if breaking change

## Security Considerations
<!-- Address any security implications -->
- [ ] **Database**: Used SQLAlchemy ORM (no raw SQL)
- [ ] **API**: Input validation with Pydantic models
- [ ] **Frontend**: No `dangerouslySetInnerHTML` with user content. Input is sanitized
- [ ] **Secrets**: No API keys or credentials in code
- [ ] **Logging**: No sensitive data (tokens, passwords) in logs

## Performance Considerations
**If applicable to your changes:**
- [ ] **Database**: Queries use appropriate indexes and filters
- [ ] **API**: Endpoints don't fetch unnecessary data
- [ ] **Frontend**: No large unnecessary dependencies bundled
- [ ] **LlamaStack**: Calls are efficient (correct endpoints used, not called in loops, etc.)
- [ ] **File operations**: Handled appropriately (size limits, chunked processing, cleanup, background tasks)

## Breaking Change Impact
- [ ] No breaking changes were made
### otherwise:
- [ ] Migration guide provided for existing users
- [ ] Deprecation notices added where appropriate
- [ ] Rollback strategy documented

## Deployment Notes
<!-- Any special deployment considerations -->
- [ ] Environment variables added/changed
- [ ] Configuration changes needed
- [ ] Other (explain):

## Code Quality
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is properly commented
- [ ] No debugging code left in place
- [ ] Error handling implemented appropriately

## Documentation
- [ ] Code is self-documenting or comments added
- [ ] README updated if needed
- [ ] API documentation updated if needed
- [ ] Inline documentation updated if needed

## Dependencies
- [ ] No unnecessary dependencies added
- [ ] Package versions pinned appropriately
- [ ] Requirements files updated (requirements.txt, package.json)
- [ ] License compatibility verified

## Git Hygiene
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts
- [ ] Branch is up to date with target branch
- [ ] Commits are logically organized

## Additional Notes
<!-- Any additional information that reviewers should know -->
Is there any additional info that the reviewers should know?

---

## For Reviewers
- [ ] Code review completed
- [ ] Architecture and design approved
- [ ] Security implications reviewed
- [ ] Performance impact assessed
- [ ] Documentation reviewed
- [ ] Testing strategy approved
