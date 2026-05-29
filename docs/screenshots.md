# Screenshots (for the portfolio / README)

Capture these once the stack is running locally. Store images under
`docs/images/` and embed them in the README.

## Suggested shots

1. **Swagger UI overview** — http://localhost:8000/docs
   Shows the full API surface (auth, uploads, jobs, webhooks, exports, audit).
   _Filename:_ `docs/images/swagger-overview.png`

2. **Authorize + a successful upload** — expand `POST /uploads`, run it, show the
   `201` response with batch status `validated`.
   _Filename:_ `docs/images/upload-success.png`

3. **Validation errors** — upload a file with bad rows and show
   `GET /uploads/{id}/errors` returning structured error codes.
   _Filename:_ `docs/images/validation-errors.png`

4. **Job result** — `GET /jobs/{id}` showing `status: succeeded` and the
   `result` summary.
   _Filename:_ `docs/images/job-result.png`

5. **Audit log** — `GET /audit-logs` (as admin) showing the recorded events.
   _Filename:_ `docs/images/audit-log.png`

## Tips

- Use a clean browser window (no extensions/toolbars) at ~1280px wide.
- Mask any real tokens before publishing.
- Optionally record a short GIF of the upload → job → export flow.

## Embedding in the README

```markdown
![Swagger UI](docs/images/swagger-overview.png)
```
