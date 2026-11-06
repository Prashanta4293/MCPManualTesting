# TSP login access failure

One Login click followed explicit manual CAPTCHA confirmation. The browser reached `/en/tsp-dashboard`, but showed **Destination Unknown** and remained unsigned-in after a 15-second wait. No visible login-field error was present.

Login/access: **Fail**. Eight application sections: **Blocked / Not Tested**. Root cause is not confirmed. Verify that the configured account is active and provisioned for TSP dashboard access before another authorized attempt.

Evidence: destination-unknown.png and inventory.json. No repeated login, pytest, automation development, draft saves, uploads, application submission or workflow changes.
