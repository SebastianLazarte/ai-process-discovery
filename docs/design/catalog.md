# Process template catalog

What the template catalog of block B14 holds and where each process comes from (RS-97). The catalog lives in `src/app/catalog/`, one JSON file per sector, and `GET /api/process-templates` serves it (RS-95). The screen that offers it is RS-96.

## What a template holds

Each template has a name, a short description and four to seven steps. A step carries only qualitative traits: the role, the tools, its input and output, the five levels (repetitiveness, rule clarity, input type, integration readiness, criticality), the three flags (human judgement, human approval, sensitive data) and its typical problems. A template never carries minutes, rates, executions or an hourly cost, because the person types every number for their company (ADR 0001, hard rule 2). Roles, tools and data are generic and never name a real company or product brand.

The traits are chosen so the rules give a realistic mix rather than one answer for every step:

- Intake from email, paper and portals is `MIXED`, so the rules ask an analyst to review it.
- Reading documents (invoices, claims evidence, trade documents) is `DIGITAL_UNSTRUCTURED` without judgement, so it becomes an AI candidate.
- Clear checks on structured data (three-way match, sanctions screening, policy cover) have high rule clarity, so they become rule based once the person types a low exception rate.
- Steps in systems that already integrate well become API integration, and physical work without integration (counting stock, inspecting a return, scanning cards) stays manual.
- Approvals, credit and claims decisions, fraud referrals and clinical priorities keep a person in control. KYC, loans, claims, health records and payment details are flagged as sensitive data.

## The screen (RS-96)

New process (`/processes/new`) asks for a sector, then one of its processes. Each list ends with Other, which opens the blank process form instead. A chosen template opens a review: the process name and description come from the template, and every step shows its traits read only. The person types the executions per month and, for each step, the minutes per execution, plus the hourly cost, occurrence and exception rates when they know them. The screen sends nothing until the minutes of every step and the executions per month are there, then creates the process with its steps in one request and opens its Steps page, where any trait can be changed.

## How to read the sources

The processes come from public lists of the use cases most often automated in each sector. Most of these lists are published by automation vendors and consultancies, so they are a guide to what is common and say nothing about how often each process is automated in practice. They are not a measured ranking. The Product Owner chose three processes per sector from them.

| Source | What it gives |
|---|---|
| [Blue Prism, RPA use cases](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/) | Use cases by industry and by department (vendor) |
| [AIMultiple, RPA use cases](https://aimultiple.com/robotic-process-automation-use-cases) | Use cases by industry and by function (industry analyst) |
| [Itransition, RPA use cases](https://www.itransition.com/rpa/use-cases) | Use cases by industry (consultancy) |
| [Damco, industry-specific RPA use cases](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) | Use cases by industry (consultancy) |
| Pipefy, 2024 automation trends | Share of automations by area: customer support 48 %, finance and procurement 26.7 % (vendor survey) |
| Controllers Council, 2025 Finance Leader Outlook | Accounts payable is the most automated finance area (survey of finance leaders) |

## Manufacturing

| Process | Where it comes from |
|---|---|
| Supplier invoice processing | Invoice and purchase order processing and accounts payable in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); invoice processing in [Itransition](https://www.itransition.com/rpa/use-cases) and [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases). The Controllers Council outlook names accounts payable as the most automated finance area |
| Purchase orders to suppliers | Invoice and purchase order processing and supply chain management in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); procure-to-pay in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases). Pipefy puts finance and procurement at 26.7 % of automations |
| Customer order entry | Contract and order management in [Itransition](https://www.itransition.com/rpa/use-cases); order processing with data entry into the business system in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |

## Retail and e-commerce

| Process | Where it comes from |
|---|---|
| Returns and refunds | Returns and exchange processing in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); automated returns in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) |
| Inventory reconciliation | Inventory management in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/), [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) and [Itransition](https://www.itransition.com/rpa/use-cases); inventory updates in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |
| Customer support requests | Customer support in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/) and [Itransition](https://www.itransition.com/rpa/use-cases); customer service team support in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases). Pipefy puts customer support at 48 % of automations. This version follows orders and deliveries, where the any-sector one is general |

## Logistics

| Process | Where it comes from |
|---|---|
| Freight invoice audit | Invoice processing under supply chain and logistics in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); supply chain and freight management in [Itransition](https://www.itransition.com/rpa/use-cases) and [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases). The sources name invoice processing; the audit against agreed rates is how it applies to carrier invoices |
| Shipment status updates | Shipment scheduling and tracking in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); proof of delivery tracking in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) |
| Customs documentation | Trade documents in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) and packing slips and shipping labels in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases). None of the sources names customs declarations directly; the Product Owner chose them as the document-heavy part of cross-border shipping |

## Banking and financial services

| Process | Where it comes from |
|---|---|
| Customer onboarding and KYC | Customer onboarding and know your customer in [Itransition](https://www.itransition.com/rpa/use-cases) and [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases); sanction screening for onboarding in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) |
| Account reconciliation | Reconciliations in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); bank statement reconciliation in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases); general ledger reconciliation in [Itransition](https://www.itransition.com/rpa/use-cases) |
| Loan application processing | Loan application handling and credit checks in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); loan processing in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases), [Itransition](https://www.itransition.com/rpa/use-cases) and [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |

## Insurance

| Process | Where it comes from |
|---|---|
| Claims intake (first notice of loss) | Claims registration and processing in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/) and [Itransition](https://www.itransition.com/rpa/use-cases); claims processing in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) and [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |
| Policy changes | Policy servicing and administration in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/) and [Itransition](https://www.itransition.com/rpa/use-cases); policy administration with renewals, updates and cancellations in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |
| Quote preparation | Underwriting in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/) and [Itransition](https://www.itransition.com/rpa/use-cases); underwriting data gathering in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases); answering broker queries in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) |

## Healthcare administration

| Process | Where it comes from |
|---|---|
| Patient intake and registration | Patient registration and insurance eligibility verification in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases); self-service check-in in [Itransition](https://www.itransition.com/rpa/use-cases) |
| Appointment scheduling | Appointment scheduling in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/), [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases), [Itransition](https://www.itransition.com/rpa/use-cases) and [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |
| Insurance claims submission | Claims and billing accuracy in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); claims administration in [Itransition](https://www.itransition.com/rpa/use-cases); claims management and processing in [Damco](https://www.damcogroup.com/blogs/industry-specific-rpa-use-cases) |

## Any sector

| Process | Where it comes from |
|---|---|
| Employee onboarding | New-starter onboarding in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); employee onboarding in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) and [Itransition](https://www.itransition.com/rpa/use-cases) |
| Expense reports | Expense reimbursement and travel and expense management in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/); expense management in [AIMultiple](https://aimultiple.com/robotic-process-automation-use-cases) and [Itransition](https://www.itransition.com/rpa/use-cases). Pipefy puts finance and procurement at 26.7 % of automations |
| Customer support requests | Customer support and complaint handling in [Blue Prism](https://www.blueprism.com/automation-journey/robotic-process-automation-rpa-use-cases/). Pipefy puts customer support at 48 % of automations, the largest area in its survey |
