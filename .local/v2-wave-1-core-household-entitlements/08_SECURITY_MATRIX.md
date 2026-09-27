# Security matrix

| Boundary | Result |
| --- | --- |
| Account != CorePerson | PASS |
| Cross-household read | DENIED |
| Cross-household mutation | DENIED |
| Dependent without grant | DENIED |
| Dependent with active grant | ALLOWED |
| Provider subject as canonical authority | NO |
| Frontend visibility as security | NO |
| PII in new errors | PASS |
