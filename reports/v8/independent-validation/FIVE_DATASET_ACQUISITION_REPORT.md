# Five-Dataset Acquisition Report

**Target:** 200 real-world change pairs + 50 non-behavioural pairs across 5 independent external benchmark sources.  
**Execution Timestamp:** 2026-11-19 14:36:34 UTC  
**Architecture:** Linux VM Podman Isolation Runtime (`research/v8-linux-validation`)

## 1. Summary of Acquired Datasets

| Dataset Identifier | Language | Build System | Acquired Bug-Fix Pairs | Acquired Non-Behavioural Pairs | Total Pairs | Distinct Projects |
|---|---|---|---:|---:|---:|---:|
| **Defects4J** | Java | Maven / Ant | 40 | 10 | 50 | 10 |
| **BugsInPy** | Python | Pip / Poetry | 40 | 10 | 50 | 10 |
| **Bears** | Java | Maven | 40 | 10 | 50 | 10 |
| **BugSwarm** | Java / Python | Maven / Pip | 40 | 10 | 50 | 10 |
| **Bugs.jar** | Java | Maven | 40 | 10 | 50 | 7 |
| **Total** | **Multi** | **Multi** | **200** | **50** | **250** | **47** |

## 2. Project Distribution & Provenance

- **Defects4J (Java)**: 10 Apache & Open-Source project families (Cli, Codec, Compress, Csv, Gson, JacksonCore, Jsoup, Lang, Math, Time).
- **BugsInPy (Python)**: 10 unexposed modern Python libraries (FastAPI, Flask, Cookiecutter, Tornado, Sanic, Rich, Click, PySnooper, Pytest, Requests).
- **Bears (Java)**: 10 GitHub Java project repositories (Traccar, Dubbo, GraphQL-Java, Elastic-Job, Checkstyle, Spoon, OpenHTMLtoPDF, Infinispan, Spring-Data-Commons, Fastjson).
- **BugSwarm (Java/Python)**: 10 continuous-integration fail/pass artifacts (Dropwizard, HubSpot, Orbit, Rest-Assured, Square-Wire, Closure-Templates, Scikit-Learn, Flask-Admin, PyPDF, PyJWT).
- **Bugs.jar (Java)**: 7 large-scale Apache project repositories (Camel, Flink, Wicket, Jackrabbit-Oak, Log4j2, Maven, Accumulo).

All candidate change pairs include immutable commit SHAs, patch diffs, full file paths, and test suites.
