# LOGIN DELIVERY ABSTRACTION

OTP and magic-link generation are separated from delivery.
The system now:
1. creates a challenge
2. records a delivery attempt
3. returns preview data in development
4. can later swap in SMS/email providers without changing core flows
