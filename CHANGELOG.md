# Changelog

## [1.4.0](https://github.com/SebastianLazarte/ai-process-discovery/compare/v1.3.1...v1.4.0) (2026-10-16)


### Features

* **api:** HVAC manufacturer demos with preset assumptions and a first analysis (RS-89) ([#108](https://github.com/SebastianLazarte/ai-process-discovery/issues/108)) ([9b41504](https://github.com/SebastianLazarte/ai-process-discovery/commit/9b41504d995b6d50bd079eba0e4f8931deab76be))
* **api:** serve the API under /api with a committed OpenAPI contract (RS-69) ([#116](https://github.com/SebastianLazarte/ai-process-discovery/issues/116)) ([6921cd5](https://github.com/SebastianLazarte/ai-process-discovery/commit/6921cd5d6813ce6b79342df341759da4630165f2))
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
