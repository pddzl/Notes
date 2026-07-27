
**`/v1/chat/completions`** is the **older, chat-focused API**.

**`/v1/responses`** (sometimes proxied as `/api/v3/responses` by some providers) is the **new unified API** that OpenAI recommends for new projects.

| Feature                   | Chat Completions       | Responses                      |
| ------------------------- | ---------------------- | ------------------------------ |
| Primary input             | `messages`             | `input`                        |
| Chat                      | ✅                      | ✅                              |
| Images                    | ✅                      | ✅                              |
| Audio                     | Partial                | ✅                              |
| PDF                       | Limited                | ✅                              |
| Tool calling              | ✅                      | ✅ (more capable)               |
| Built-in tools            | Limited                | ✅                              |
| Structured output         | ✅                      | Better support                 |
| Conversation continuation | Client-managed history | Can use `previous_response_id` |
| Streaming                 | Text-focused           | Rich event stream              |
| Recommended for new apps  | No                     | Yes                            |
