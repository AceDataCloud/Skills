# Like, favorite, comment, and reply

Always open and read the exact target note first. Derive it from the user's URL or a current result; never guess a note, author, or comment.

## Like and favorite

1. Read the target control's visible label and checked/pressed/selected state.
2. If the current state already matches the explicit request, no-op and report it.
3. Otherwise click once, poll the fresh state every 500 ms for at most 4 seconds, and confirm the exact target state.
4. If the state is readable and clearly unchanged, one retry is allowed because the action is reversible; never exceed two total clicks. If state cannot be read, do not retry.

## Comment

1. Draft the exact comment and show the target note plus full text.
2. Obtain explicit chat confirmation.
3. Open the visible comment placeholder, then fill the visible contenteditable comment input and read the draft back.
4. If the target or exact text differs, stop.
5. Click the visible submit button once after the confirmed preview. Poll the visible comments for the exact text every 300 ms for at most 4 seconds; absence is an unknown/failed result, not success.

## Reply

1. Locate the exact visible target comment and author. Prefer an exact comment ID when visible; otherwise match the explicitly confirmed user. Expand/scroll in bounded steps, stop at the end marker, and never search more than 100 rounds.
2. Show the target and full reply preview; obtain explicit confirmation.
3. Open that comment's reply control, fill the reply, and read the visible target/text back.
4. Submit once, then require the exact reply text to appear within 4 seconds before reporting success.

Comments and replies are public account actions. The allowed-origin BrowserSession does not replace explicit chat preview confirmation.