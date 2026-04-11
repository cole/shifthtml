# Goals
- simple and clean wins
- think in types first
- modern deps & toolchain (3.14+)
- DOM APIs are our inspiration; the browser knows how to build HTML
- On top of that, we aim for a concise but pythonic and readable DSL
- core concern: tree builder for rendering HTML
- loosely coupled higher layers: template compilation, low JS tooling for dynamic content
- our main use case is getting content to the browser as soon as it's ready with no upfront delays

# Guidelines
- jj for version control
- commits have a leading emoji (relevant to the commit) and < 70 char summary line; body of commit can provide detail
- full test coverage, but not verbose
- no docstrings on tests; the test name should be descriptive enough
- format, lint and typecheck (using ruff and ty) before committing
- never use inline imports; import at the top of the file
- avoid type ignores and casts, and prefer straighforward types over duck typing
- simplify where possible
