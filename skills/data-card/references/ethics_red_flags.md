# Ethics red flags — escalation triggers

If ANY of these apply, surface to user before producing the data
card. These are common causes of desk reject at venues with ethics
review:

## Sensitive data

- PHI (protected health information): MIMIC, eICU, any clinical EHR.
  Requires IRB or DUA acknowledgment in data availability statement.
- Genomic / biometric data
- Mental-health-related text
- Children's data (any subject <18)
- Faces of identifiable individuals (consent required)
- User-level data scraped from social media (most platforms' TOS
  forbid redistribution; flag explicitly)

## Collection method risks

- Crowdsourcing without IRB review
- Wages below platform minimum / regional minimum wage
- Hidden / dark-pattern participant recruitment
- No informed consent

## Use risks

- Surveillance / law-enforcement applications
- Lethal-autonomous-weapons-adjacent
- Disinformation / influence-operation tooling
- Discrimination amplification (e.g., predictive policing)

## Reporting requirements per venue

- NeurIPS / ICML / ICLR: ethics review panel — flag in checklist
- ACL ARR: required Limitations + Ethics Statement
- SIGMOD / VLDB / KDD: generally lighter, but PHI still requires DUA
  acknowledgment

## Action when red flag detected

1. Stop auto-fill of the data card.
2. Surface to user with explicit description of the flag.
3. Recommend explicit text in the paper acknowledging the constraint
   AND in the data availability statement.
4. If no acknowledgment can be made (e.g., scraped data without
   consent and no replacement), recommend not releasing the dataset
   and weakening the claim accordingly.
