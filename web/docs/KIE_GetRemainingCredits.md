# KIE Get Remaining Credits

Check remaining KIE account credits using the API key from `config/kie_key.txt`.

## Inputs
- `log` (BOOLEAN, optional): Enable console logging (default: `true`).

## Outputs
- `data` (STRING): Raw JSON response from the credits endpoint.
- `credits_remaining` (INT): Parsed remaining credit balance.

## Notes
- This node is useful as a first smoke test after setup.
- If the API key is missing or invalid, the node raises an error.
