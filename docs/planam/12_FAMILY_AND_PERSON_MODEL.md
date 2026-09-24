# Family And Person Model

`Account` is authentication. `Person` is a human. `Membership` links a Person to a Household with relationship and scoped permission. These are distinct concepts. Dependents may exist without an Account, and one account may belong to multiple households even when the active UI shows one.

CorePerson is the canonical identity reference. New canonical IDs use UUIDv7. Birth date is restricted Core data. FoodProfile is person-scoped and owned by the food domain. Household summaries are derived only after person-level policy, participation, portions, and uncertainty are resolved.

Wave 02 creates the physical Core roots and idempotently maps legacy `users`, `families`, and `family_members` into Account/AuthIdentity/Person/Household/Membership plus legacy mappings. A dependent FamilyMember can map to a Person without creating an Account.
