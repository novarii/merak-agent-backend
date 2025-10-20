# ChatKit Thread Item Conversion SOP

## Purpose
Document the remediation steps for `MerakChatKitServer._to_agent_input` whenever it bypasses `ThreadItemConverter.to_agent_input`. Following this SOP ensures streamed runs align with the ChatKit server guide (https://openai.github.io/chatkit-python/server) and prevents `Runner.run_streamed` from receiving unsupported payloads.

## Preconditions
- Local environment bootstrapped per `.agent/SOP/manual_testing.md`.
- `openai-chatkit` and `openai-agents` installed in the active virtualenv.
- Ability to edit `backend/app/integrations/chatkit_server.py`.

## Implementation Steps
1. **Open the converter helper**  
   Navigate to `backend/app/integrations/chatkit_server.py` and locate the `_to_agent_input` method inside `MerakChatKitServer`.

2. **Prioritise `to_agent_input`**  
   Inside the loop that probes converter methods, add a branch that checks for `to_agent_input` (the canonical API exposed by `ThreadItemConverter`). Example pattern:
   ```python
   for attr in ("to_agent_input", "to_input_item", "convert", ...):
       method = getattr(converter, attr, None)
       ...
   ```
   Alternatively, call `await converter.to_agent_input(item, thread=thread, store=self.store)` before the loop and fall back only when it raises `AttributeError`.

3. **Maintain compatibility arguments**  
   Preserve the existing signature inspection so the converter receives `(item, thread, store=self.store)` when supported. This keeps backward compatibility with SDK releases that still expect auxiliary parameters.

4. **Return converted payload**  
   Ensure the method returns the result of `to_agent_input` (or, if absent, the first successful conversion method). Only fall back to `item` when every candidate method raises `TypeError` or is missing.

5. **Lint for regressions**  
   From `backend/`, run:
   ```
   ruff check app/integrations/chatkit_server.py
   black app/integrations/chatkit_server.py
   ```
   Resolve any formatting issues introduced during the edit.

## Validation
1. Run the FastAPI server (`uvicorn app.main:app --reload`) with valid OpenAI credentials.
2. Initiate a ChatKit session (CLI or script) and send a user message.
3. Confirm the server streams assistant tokens without raising `TypeError`. If logging is enabled, the converter should now emit `ResponseInput*` payloads rather than raw `ThreadItem` objects.

## Rollback
Revert the changes to `_to_agent_input` (e.g., `git checkout -- app/integrations/chatkit_server.py`) if streaming breaks after the edit, then investigate agent/converter compatibility before reapplying the fix.

## Related References
- ChatKit server documentation: https://openai.github.io/chatkit-python/server
- `MerakChatKitServer` implementation: `backend/app/integrations/chatkit_server.py`

