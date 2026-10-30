# Changelog

## [2.1.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v2.0.0...v2.1.0) (2026-10-30)


### Features

* **api:** catalog content for seven sectors (RS-97) ([#206](https://github.com/SebastianLazarte/ai-process-discovery/issues/206)) ([ceb4a25](https://github.com/SebastianLazarte/ai-process-discovery/commit/ceb4a257ae2cad8713176eb1b9639865e72a5dd8))
* **api:** process template catalog served by the API (RS-95) ([#198](https://github.com/SebastianLazarte/ai-process-discovery/issues/198)) ([dc3250e](https://github.com/SebastianLazarte/ai-process-discovery/commit/dc3250e95bed4cd582299a5a623515c480154486))
* **ui:** start a process from a sector template (RS-96) ([#212](https://github.com/SebastianLazarte/ai-process-discovery/issues/212)) ([a7cff6f](https://github.com/SebastianLazarte/ai-process-discovery/commit/a7cff6fb0cfaa4dba65490c92f9c10be587fe37d))


### Bug Fixes

* route the old /docs, /redoc and /openapi.json to the API ([#185](https://github.com/SebastianLazarte/ai-process-discovery/issues/185)) ([4ab0419](https://github.com/SebastianLazarte/ai-process-discovery/commit/4ab0419527a36dc655a494a10090c3f00ad89789))


### Documentation

* align the decision records with what is built ([#203](https://github.com/SebastianLazarte/ai-process-discovery/issues/203)) ([b1a65de](https://github.com/SebastianLazarte/ai-process-discovery/commit/b1a65deae3ca219f659e226233baae8d259b0174))
* guardrail decisions for AI drafts (RS-98, RS-100, RS-101) ([#199](https://github.com/SebastianLazarte/ai-process-discovery/issues/199)) ([44f5d6f](https://github.com/SebastianLazarte/ai-process-discovery/commit/44f5d6f217527c9bd6c8cc5b53c1766b54faf796))
* guided process capture backlog (B14, RS-95 to RS-101) ([#188](https://github.com/SebastianLazarte/ai-process-discovery/issues/188)) ([2ce0ee6](https://github.com/SebastianLazarte/ai-process-discovery/commit/2ce0ee6b171c24faf955d048e1cf9eec99beee32))
* link the live demo from the README ([#204](https://github.com/SebastianLazarte/ai-process-discovery/issues/204)) ([4992cc6](https://github.com/SebastianLazarte/ai-process-discovery/commit/4992cc68f17c55e5e4238770115cf39265c1df2b))
* record the first restore rehearsal and the 2.0.0 switch (RS-68) ([#187](https://github.com/SebastianLazarte/ai-process-discovery/issues/187)) ([4e5d711](https://github.com/SebastianLazarte/ai-process-discovery/commit/4e5d71110c09a03a676c5af65a735717cbb168a5))

## [2.0.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.5.0...v2.0.0) (2026-10-21)


### ⚠ BREAKING CHANGES

* **ui:** retire the vanilla client and the root API routes; Next.js serves / (RS-80) ([#182](https://github.com/SebastianLazarte/ai-process-discovery/issues/182))

### Features

* production routes for 2.0.0 and one version per service (RS-79) ([#172](https://github.com/SebastianLazarte/ai-process-discovery/issues/172)) ([a0e1fa4](https://github.com/SebastianLazarte/ai-process-discovery/commit/a0e1fa44ac187ec57c26906585aa00771ee92b78))
* **ui:** analyse form with assumptions and an honest LLM wait (RS-75) ([#177](https://github.com/SebastianLazarte/ai-process-discovery/issues/177)) ([495839d](https://github.com/SebastianLazarte/ai-process-discovery/commit/495839db8014ba9fc20970c522d4ed2a35617dbe))
* **ui:** analysis history in the new client (RS-93) ([#174](https://github.com/SebastianLazarte/ai-process-discovery/issues/174)) ([4260a9b](https://github.com/SebastianLazarte/ai-process-discovery/commit/4260a9baddb167c2027dd9bb7d91ebdf3d272ddd))
* **ui:** blueprint with a Markdown download in the new client (RS-94) ([#173](https://github.com/SebastianLazarte/ai-process-discovery/issues/173)) ([aac05ae](https://github.com/SebastianLazarte/ai-process-discovery/commit/aac05aef17cdb6f4103c36c2b64232b4d5dabdbd))
* **ui:** override a recommendation with a required reason in the new client (RS-76) ([#179](https://github.com/SebastianLazarte/ai-process-discovery/issues/179)) ([e1bf4b2](https://github.com/SebastianLazarte/ai-process-discovery/commit/e1bf4b24fd9b4fd82a226b568cc625904629db29))
* **ui:** reorder and delete steps in the new client (RS-91) ([#178](https://github.com/SebastianLazarte/ai-process-discovery/issues/178)) ([78fb364](https://github.com/SebastianLazarte/ai-process-discovery/commit/78fb36446ef01c314ee038fc5b5cb5e88b6cb76e))
* **ui:** results in four panels with the language of trust (RS-92) ([#175](https://github.com/SebastianLazarte/ai-process-discovery/issues/175)) ([6f05ae6](https://github.com/SebastianLazarte/ai-process-discovery/commit/6f05ae671d69b42b724e8c5a04b2865bfe52e1ef))
* **ui:** retire the vanilla client and the root API routes; Next.js serves / (RS-80) ([#182](https://github.com/SebastianLazarte/ai-process-discovery/issues/182)) ([ec3b411](https://github.com/SebastianLazarte/ai-process-discovery/commit/ec3b411271ee07aaef09cac8ea49f2bd3315cb76))
* **ui:** steps list, step form and process settings in the new client (RS-74) ([#176](https://github.com/SebastianLazarte/ai-process-discovery/issues/176)) ([249f853](https://github.com/SebastianLazarte/ai-process-discovery/commit/249f85392a2353fe68b5378c7cfe87113dd3dda2))
* **ui:** strict security headers with a per-request CSP nonce (RS-72) ([#169](https://github.com/SebastianLazarte/ai-process-discovery/issues/169)) ([c362e2d](https://github.com/SebastianLazarte/ai-process-discovery/commit/c362e2d54e7c681193381cba9f4e3b4d170adc74))

## [1.5.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.4.0...v1.5.0) (2026-10-20)


### Features

* deploy each release over SSH with an HTTPS smoke test (RS-67) ([#155](https://github.com/SebastianLazarte/ai-process-discovery/issues/155)) ([e7a74bf](https://github.com/SebastianLazarte/ai-process-discovery/commit/e7a74bfe7c01bc93963518f748b5d02f0e8b838e))
* nightly backup and purge timers with a restore rehearsal (RS-68) ([#157](https://github.com/SebastianLazarte/ai-process-discovery/issues/157)) ([eb5f5dc](https://github.com/SebastianLazarte/ai-process-discovery/commit/eb5f5dcaaba0e993a6a5b36a87aca83f951b2218))
* **ui:** ship the Next.js client as a read-only image with every release (RS-77) ([#159](https://github.com/SebastianLazarte/ai-process-discovery/issues/159)) ([f8a897c](https://github.com/SebastianLazarte/ai-process-discovery/commit/f8a897c3f0c900d2e232e8f2d0a6aa5e1f01639b))


### Documentation

* adopt a test quality standard (ADR 0012) ([#152](https://github.com/SebastianLazarte/ai-process-discovery/issues/152)) ([f8b2b4f](https://github.com/SebastianLazarte/ai-process-discovery/commit/f8b2b4f84ba1875a106ece6502de1523667e11e8))
* record the parity spec (ADR 0015) and Next.js at the root from 2.0.0 (ADR 0016) ([#168](https://github.com/SebastianLazarte/ai-process-discovery/issues/168)) ([364d844](https://github.com/SebastianLazarte/ai-process-discovery/commit/364d84454e8ce36cfa055e32aa0600e9b24a1aac))
* refine RS-74 to RS-80 to the Definition of Ready and split out RS-91 to RS-94 ([#158](https://github.com/SebastianLazarte/ai-process-discovery/issues/158)) ([f0b5cbe](https://github.com/SebastianLazarte/ai-process-discovery/commit/f0b5cbef0d0425ef46984c4fbe8b5cd73a2e8dbd))

## [1.4.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.3.1...v1.4.0) (2026-10-19)


### Features

* **api:** HVAC manufacturer demos with preset assumptions and a first analysis (RS-89) ([#108](https://github.com/SebastianLazarte/ai-process-discovery/issues/108)) ([9b41504](https://github.com/SebastianLazarte/ai-process-discovery/commit/9b41504d995b6d50bd079eba0e4f8931deab76be))
* **api:** serve the API under /api with a committed OpenAPI contract (RS-69) ([#116](https://github.com/SebastianLazarte/ai-process-discovery/issues/116)) ([6921cd5](https://github.com/SebastianLazarte/ai-process-discovery/commit/6921cd5d6813ce6b79342df341759da4630165f2))
* deploy script with backup, migration and automatic rollback (RS-66) ([#154](https://github.com/SebastianLazarte/ai-process-discovery/issues/154)) ([183cb30](https://github.com/SebastianLazarte/ai-process-discovery/commit/183cb30ec5c94bfb792d776ba251ddf02c79814f))
* **persistence:** ship schema changes as Alembic migrations (RS-59) ([#119](https://github.com/SebastianLazarte/ai-process-discovery/issues/119)) ([46959d4](https://github.com/SebastianLazarte/ai-process-discovery/commit/46959d4388acc9fd9414024382bc72334f9649e2))
* **ui:** dark theme tokens and the sidebar of the vanilla client (RS-90) ([#120](https://github.com/SebastianLazarte/ai-process-discovery/issues/120)) ([b52d4c0](https://github.com/SebastianLazarte/ai-process-discovery/commit/b52d4c04d3c5478e2e60aeeb11befdf76888f13d))
* **ui:** Next.js project with lint, types and tests in CI (RS-70) ([#109](https://github.com/SebastianLazarte/ai-process-discovery/issues/109)) ([a2859ba](https://github.com/SebastianLazarte/ai-process-discovery/commit/a2859bac0b255a23bb8c192d3ee8fdc552ee7dcf))
* **ui:** process list, demo loading, creation and deletion in the new client (RS-73) ([#118](https://github.com/SebastianLazarte/ai-process-discovery/issues/118)) ([f626b70](https://github.com/SebastianLazarte/ai-process-discovery/commit/f626b70c0cbc1ecb210a7f1431750115fdccd4c3))
* **ui:** typed API client generated from OpenAPI, with TanStack Query (RS-71) ([#117](https://github.com/SebastianLazarte/ai-process-discovery/issues/117)) ([f5d3e70](https://github.com/SebastianLazarte/ai-process-discovery/commit/f5d3e702c13c419f33c5af7fbd5afdf3b8f016ef))


### Bug Fixes

* **api:** keep the release version out of the committed OpenAPI contract ([#121](https://github.com/SebastianLazarte/ai-process-discovery/issues/121)) ([2e7700b](https://github.com/SebastianLazarte/ai-process-discovery/commit/2e7700b3c90709a79cc28c598facde3c69728339))

## [1.3.1](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.3.0...v1.3.1) (2026-10-16)


### Documentation

* design brief and design system decisions (ADR 0013) ([#107](https://github.com/SebastianLazarte/ai-process-discovery/issues/107)) ([bdf5e12](https://github.com/SebastianLazarte/ai-process-discovery/commit/bdf5e12c2efe596b036904f2fd2f1fd967cbb978))
* put the go-live items first and rewrite the README for visitors ([#105](https://github.com/SebastianLazarte/ai-process-discovery/issues/105)) ([1ceca43](https://github.com/SebastianLazarte/ai-process-discovery/commit/1ceca436f85ed68250b33575f6b13ec4a4c6bd5a))

## [1.3.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.2.1...v1.3.0) (2026-10-15)


### Features

* purge command for expired demo data (RS-63) ([#100](https://github.com/SebastianLazarte/ai-process-discovery/issues/100)) ([e4c1560](https://github.com/SebastianLazarte/ai-process-discovery/commit/e4c1560ab6ab4f4e4128dc332aea6a9ab47a2008))


### Documentation

* replace vanilla web client with Next.js (ADR 0009) ([#87](https://github.com/SebastianLazarte/ai-process-discovery/issues/87)) ([e996f24](https://github.com/SebastianLazarte/ai-process-discovery/commit/e996f24af9f9f9daf6d69a6df70c58644717a08b))
* run the demo as its own apd user ([#99](https://github.com/SebastianLazarte/ai-process-discovery/issues/99)) ([36e3b5c](https://github.com/SebastianLazarte/ai-process-discovery/commit/36e3b5cdddf27fdd889b702fbba8735d70be0e6f))
* Scrum product backlog with the PO-approved stories (PDR 002) ([#88](https://github.com/SebastianLazarte/ai-process-discovery/issues/88)) ([a4584d8](https://github.com/SebastianLazarte/ai-process-discovery/commit/a4584d88504901120c9ee82e03469cb3c6f366cb))

## [1.2.1](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.2.0...v1.2.1) (2026-10-14)


### Documentation

* layered CLAUDE.md context per area ([#81](https://github.com/SebastianLazarte/ai-process-discovery/issues/81)) ([fcd56dc](https://github.com/SebastianLazarte/ai-process-discovery/commit/fcd56dc3341933fe0ddd20aa5b4ffcae78883a0e))
* review agent instruction files like code ([#83](https://github.com/SebastianLazarte/ai-process-discovery/issues/83)) ([40980c2](https://github.com/SebastianLazarte/ai-process-discovery/commit/40980c2744b1d99f5e358d576bf65e81b3dbf6f3))

## [1.2.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.1.0...v1.2.0) (2026-10-13)


### Features

* **api:** size limits on processes, steps and assumptions ([#74](https://github.com/SebastianLazarte/ai-process-discovery/issues/74)) ([18d7906](https://github.com/SebastianLazarte/ai-process-discovery/commit/18d790675719e742ed7ce420c723e1cb99c61de8))
* **llm:** daily quota on analyses that call the LLM ([#75](https://github.com/SebastianLazarte/ai-process-discovery/issues/75)) ([35be0b5](https://github.com/SebastianLazarte/ai-process-discovery/commit/35be0b5a43ce4aa044a9ca65391188220f90ca85))
* Nginx site with TLS, rate limits and body limit ([#78](https://github.com/SebastianLazarte/ai-process-discovery/issues/78)) ([ee8d849](https://github.com/SebastianLazarte/ai-process-discovery/commit/ee8d849a0a8f1ece648474a5a3ad7929a26c19f0))
* production compose for the public demo ([#77](https://github.com/SebastianLazarte/ai-process-discovery/issues/77)) ([8fd4061](https://github.com/SebastianLazarte/ai-process-discovery/commit/8fd40616b958d376b835ab38990b1a67f0ab9e98))
* **web:** public demo banner driven by a /meta endpoint ([#76](https://github.com/SebastianLazarte/ai-process-discovery/issues/76)) ([d3b6caf](https://github.com/SebastianLazarte/ai-process-discovery/commit/d3b6caf1aa6f83e1c85eb54788f87cb592c24366))


### Documentation

* production deployment plan (ADR 0008, B11 requirements, runbook) ([#73](https://github.com/SebastianLazarte/ai-process-discovery/issues/73)) ([442f2d4](https://github.com/SebastianLazarte/ai-process-discovery/commit/442f2d4c5c4becb32b6fe8dfc84f81e32a32e407))

## [1.1.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.0.0...v1.1.0) (2026-10-12)


### Features

* **web:** vanilla web client served by FastAPI at /ui/ ([#71](https://github.com/SebastianLazarte/ai-process-discovery/issues/71)) ([8f253f9](https://github.com/SebastianLazarte/ai-process-discovery/commit/8f253f97573cc9f8a63ad3a4c4df8a3b4b21c03a))

## [1.0.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v0.1.0...v1.0.0) (2026-10-07)


### Features

* **api:** persistence, analysis service and REST API ([#53](https://github.com/SebastianLazarte/ai-process-discovery/issues/53)) ([a97e92c](https://github.com/SebastianLazarte/ai-process-discovery/commit/a97e92c310c18094d879e639aa3a7026a5736b23))
* **blueprint:** eight-section blueprint with Markdown export ([#54](https://github.com/SebastianLazarte/ai-process-discovery/issues/54)) ([9e3e6ae](https://github.com/SebastianLazarte/ai-process-discovery/commit/9e3e6ae36f7d6a54c442d4edf68a94d9a33cbb42))
* **business-case:** savings, payback and ROI from user assumptions ([#50](https://github.com/SebastianLazarte/ai-process-discovery/issues/50)) ([4e36a58](https://github.com/SebastianLazarte/ai-process-discovery/commit/4e36a58a5bcdcdf443d049ec59012eb6fd52bdba))
* **domain:** process model and current-state metrics ([#46](https://github.com/SebastianLazarte/ai-process-discovery/issues/46)) ([d8daec4](https://github.com/SebastianLazarte/ai-process-discovery/commit/d8daec40d3a91ba9ab663853b1620049c99558d4))
* **llm:** provider-agnostic LLM layer with structured output ([#52](https://github.com/SebastianLazarte/ai-process-discovery/issues/52)) ([7666fea](https://github.com/SebastianLazarte/ai-process-discovery/commit/7666feacccc00efe6c882656c90f19f3faffa680))
* **reconciliation:** rules and AI reconciliation with safeguards ([#51](https://github.com/SebastianLazarte/ai-process-discovery/issues/51)) ([463fb13](https://github.com/SebastianLazarte/ai-process-discovery/commit/463fb13775f1311d04ce019d33351e8575017b82))
* **release:** Docker image, compose stack and project documentation ([#56](https://github.com/SebastianLazarte/ai-process-discovery/issues/56)) ([2491900](https://github.com/SebastianLazarte/ai-process-discovery/commit/249190022b83b498da3dc7af71ffa5a49f396568))
* **scoring:** deterministic suitability scoring and classification ([#48](https://github.com/SebastianLazarte/ai-process-discovery/issues/48)) ([f4d156c](https://github.com/SebastianLazarte/ai-process-discovery/commit/f4d156cdbaeebcaca77b033852b02dc838c30839))
* **ui:** Streamlit client over the REST API ([#55](https://github.com/SebastianLazarte/ai-process-discovery/issues/55)) ([e94e037](https://github.com/SebastianLazarte/ai-process-discovery/commit/e94e0375a0ef773af47f6e1bcb5a8e49e5ff4751))
