# Like, favorite, comment, and reply

Always open and read the exact target note first. Derive it from the user's URL or a current result; never guess a note, author, or comment.

## Like and favorite

1. Read the target control's visible label and checked/pressed/selected state.
2. If the current state already matches the explicit request, no-op and report it.
3. Otherwise click once, read again, and confirm the target state.
4. If state remains ambiguous, do not retry automatically.

## Comment

1. Draft the exact comment and show the target note plus full text.
2. Obtain explicit chat confirmation.
3. Open the visible editor, fill it, and read the draft back.
4. If the target or exact text differs, stop.
5. Click Send once after the confirmed preview, then follow reconciliation.

## Reply

1. Locate the exact visible target comment and author, expanding replies in bounded steps if needed.
2. Show the target and full reply preview; obtain explicit confirmation.
3. Open that comment's reply control, fill the reply, and read the visible target/text back.
4. Submit once, then follow reconciliation.

Comments and replies are public account actions. The attached exact-origin session does not replace explicit chat preview confirmation.