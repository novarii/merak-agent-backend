# Next.js ChatKit Frontend (Custom Backend Integration)

## Background
- We need a production-ready Next.js + React client for the Merak agent that streams via ChatKit while delegating orchestration to our FastAPI service. The merged `repomix-output-openai-openai-chatkit-starter-app.xml` provides a working reference UI we can tailor to our stack.
- The backend already runs on the OpenAI Agents SDK (`backend/app/integrations/chatkit_server.py`) and mirrors the patterns in `example_implementation.xml` (see `app/chat.py` and `app/main.py`), so we must keep workflow state, tool calls, and memory server-side.
- Because we bypass Agent Builder workflows, we cannot rely on hosted workflow IDs; instead we expose a custom ChatKit API endpoint and authenticate through our own domain using a custom fetch implementation (`useChatKit({ api: { fetch } })` per ChatKit docs).

## Goals
- Deliver a Next.js 14 App Router frontend (`frontend/`) that renders ChatKit with Merak branding, light/dark theme parity, starter prompts, and attachment support mirroring the starter app.
- Implement a custom `useChatKit` configuration that points to our backend domain, injects Merak auth headers, configures `uploadStrategy`, and reuses backend-issued client secrets without exposing raw tokens.
- Provide environment-driven configuration (`NEXT_PUBLIC_CHATKIT_API_URL`, `NEXT_PUBLIC_CHATKIT_DOMAIN_KEY`, `NEXT_PUBLIC_CHATKIT_UPLOAD_URL`) with documentation and `.env.example` alignment.
- Surface backend errors (e.g., missing agents SDK, auth failures) through explicit UI messaging so support can debug without browser consoles.

## Non-Goals
- Creating or maintaining hosted Agent Builder workflows (we remain fully on the Agents SDK).
- Rewriting backend orchestration, tool catalog, or memory strategies beyond the API endpoints required for the frontend.
- Building an authenticated web shell or dashboard beyond the ChatKit conversation view.

## Acceptance Criteria
- Visiting the Next.js app shows a responsive ChatKit panel that pulls client secrets from the Merak backend and streams responses over SSE without manual refreshes.
- The `useChatKit` configuration wraps requests with a custom fetch that injects Merak auth (e.g., session cookie, JWT) and targets `NEXT_PUBLIC_CHATKIT_API_URL`, including a `domainKey` consistent with the security allowlist.
- Attachments are enabled via `uploadStrategy: { type: "direct", uploadUrl: NEXT_PUBLIC_CHATKIT_UPLOAD_URL }`, and uploads are proxied through the backend without exposing OpenAI API keys.
- Theme switching and starter prompts mirror backend-driven tool events (`switch_theme`, `save_fact`), ensuring tool callbacks observed in `example_implementation.xml` continue to function.
- Frontend environment docs and `.agent/System/project_architecture.md` are updated with any new variables, and the `.env.example` in `frontend/` lists required settings.

## Rollout Plan
- **Dev Preview:** Scaffold Next.js app locally, point at a staging instance of the FastAPI backend, and validate streaming plus file upload in Chrome and Safari.
- **Staging:** Deploy the frontend to the staging environment with domain allowlisting, run manual regression follows from `SOP/manual_testing.md`, and capture curl/browser HAR snippets for the release notes.
- **Production:** Flip DNS or Vercel project to production targets after confirming observability dashboards (request volume, error rates) reflect the new ChatKit traffic; announce availability to the team and monitor for 24 hours.

## Implementation Plan
- **Project Setup:** Bootstrap the Next.js 14 app router structure inside `frontend/`, reusing layout, global styles, and ESLint configuration from the starter app in `repomix-output-openai-openai-chatkit-starter-app.xml`.
- **Shared Configuration:** Add `frontend/lib/config.ts` to centralize environment reads (mirroring starter constants) and ensure we fail fast if `NEXT_PUBLIC_CHATKIT_API_URL` or domain settings are missing.
- **Chat Module:** Port `components/ChatKitPanel.tsx` and supporting hooks, adapting the `getClientSecret` flow to hit new backend endpoints (`/api/chatkit/session`, `/api/chatkit/refresh`) that proxy to `MerakChatKitServer`. Inject the custom fetch described in the ChatKit docs (Context7 `/openai/chatkit-js`, Custom Backends guide) to add Merak auth.
- **API Routes:** Implement Next.js API routes (`app/api/chatkit/session/route.ts`, `.../refresh/route.ts`, `.../upload/route.ts`) that call the FastAPI backend, handling cookies and error translation similar to the starter `create-session` route.
- **Theming & UX:** Wire the `useColorScheme` hook to persist user preference, provide helpful error overlays for missing backend configuration, and ensure tool-driven theme changes from the backend propagate to the UI.
- **Docs & Tooling:** Update `.env.example`, `.agent/System/project_architecture.md`, and `SOP/manual_testing.md` with new environment variables, security guidance (domain allowlist, auth headers), and runbooks for validating uploads.

## Related Docs
- `.agent/System/project_architecture.md` — backend topology and integration points.
- `example_implementation.xml` — reference ChatKit server built on the Agents SDK (see `app/chat.py`).
- `repomix-output-openai-openai-chatkit-starter-app.xml` — baseline Next.js ChatKit UI to adapt.
