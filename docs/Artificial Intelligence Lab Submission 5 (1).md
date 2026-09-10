# DevOps Incident- Response Agent

## with a Deterministic Evaluation Harness

## Project Domain: Agentic AI Systems · AI Reliability Engineering & Evaluation · DevOps Automation

## Subject- Artificial Intelligence

## Prepared by:

- Pranit Mathur (24BIT0497)

- Romit Raman (24BIT0558)

- Aniket Agarwal (24BIT0533)


## Abstract

Modern software teams operate continuously running services in production, where incidents—such as API failures, service degradation, and failed deployments—demand rapid diagnosis and resolution. Historically, root cause analysis has heavily depended on the experience of on-call engineers to manually sift through logs and monitoring data under significant time pressure.

In recent years, artificial intelligence agents built on large language models (LLMs) have emerged as powerful assistants for IT operational work. However, testing for these AI agent deployments relies heavily on informal, subjective evaluations. This approach creates significant risks, as unseen changes in underlying models, prompts, or tools can quietly regress system performance.

This project addresses this critical gap by building a complete end-to-end ecosystem:

- Target Agent: An LLM-based autonomous agent that fetches logs, reviews deployments, and determines root cause scenarios.

- Deterministic EvaluationHarness: A scalable test-suite systemensuring the agent's logic is rigorously graded against a battery of realistic, simulated DevOps incidents.

By shifting the paradigm from subjective ad-hoc AI demonstrations to testable, robust software artifacts, this project paves the way for safe, reliable automation in modern Site Reliability Engineering (SRE).


## Problem Statement

Existing Artificial Intelligence for IT Operations (AIOps) tools are highly effective at detection and alerting. They reliably pinpoint that an anomaly has occurred and roughly isolate the affected service. However, the subsequent critical steps—root-cause diagnosis and remediation planning— remain stubbornly dependent on manual, expertise-driven investigation.

Prior research demonstrates that large language models can generate plausible root-cause explanations and mitigation steps when fed appropriate incident telemetry. Despite these advancements, these systems suffer from substantial evaluation and reliability challenges:

- Lack of Systematic Evaluation: There is no standard, low-cost way to systematically test whether an incident-response agent's tool usage, reasoning, and output quality are robust. Performance is largely validated through cherry-picked examples and subjective human judgment.

- Vulnerability to Regressions: Real deployments often experience silent drops in agent quality when prompts are refined, the tool set is updated, or the underlying LLM is patched. Without an automated, rules-based verification layer, it is nearly impossible to detect these performance regressions reliably.

- Safety in Execution: Current implementations often blur the line between recommendation and execution, introducing massive operational risks if an unverified AI agent hallucinates a destructive remediation step.


## Motivation

The core motivation behind this project is a fundamental shift in how AI agents should be treated in enterprise environments. Agents must transition from being treated as "clever demos" to being handled as testable, versionable software artifacts. Just as a function or microservice is expected to have a robust test suite before it is trusted in a production environment, AI models making operational recommendations must be held to the same standard of deterministic evaluation.

## Key drivers include:

- Cost of Unverified Failures: As AI agents are deployed closer to real operational decisions, the cost of an unverified failure grows exponentially. A reproducible evaluation harness is the only reliable mechanism to prove that an agent update genuinely improves performance.

- Safety-First Automation: The project embodies a deliberate design philosophy where the Target Agent is strictly scoped to stop at diagnosis and recommendation. By never allowing autonomous execution of remediation scripts, the human-in-the-loop remains the final safeguard for live systems.

- Measurable Iteration: Teams need evidence, not anecdotes, to tune LLM parameters, system prompts, and tool descriptions. A robust evaluation framework provides a clear pass/fail metric and aggregate success-rate to drive confident engineering iterations.


## Literature Survey, Gap Identification & Objectives

## Literature Survey

The project sits at the intersection of several rapidly evolving fields. Prior work demonstrates that LLMs can recommend mitigation steps for cloud incidents (Ahmed et al., 2023), but typically lack reproducible verification. Tool-augmented models (Toolformer, API-Bank) establish the foundation for agents deciding which tools to call, while classical AIOps literature (Notaro et al., 2021) outlines the requirements for failure management. Recently, verifiable proxy state-based evaluation (Chuang et al., 2026) has emphasized deterministic scoring as a rigorous alternative to purely subjective grading.

## Gap Identification

The literature reveals a distinct gap: while LLMs are heavily researched for generating mitigation plans, practically no prior work provides a low-cost, repeatable, rule-based test harness tailored explicitly to AIOps tool sequences and reasoning validation. Existing benchmarks are either too generic (API-Bank) or lack the deterministic evaluation of complex SRE workflows.

## Objectives

- 1. Target Agent Design: Implement an agent capable of receiving a simulated service alert, autonomously invoking tools to gather log and deployment evidence, and producing a structured diagnosis.

- 2. Human-in-the-Loop Boundary: Enforce an explicit boundary where the agent proposes remediation plans but is architecturally restricted from executing them.

- 3. Scenario Bank: Design 15–20 realistic, varied synthetic incident scenarios (e.g., memory leaks, expired certificates) with known ground-truth answers.

- 4. Evaluation Harness: Build a Deterministic Evaluation Harness that runs the agent against every scenario, captures the full tool-call trace, and grades the run using fixed, rule- based checks.

- 5. RegressionDetection: Produce an aggregate success-rate metric that acts as an automated regression test suite for prompt or model updates.


## Survey Table

The following table summarizes key related works, their datasets, and identified drawbacks in relation to the current project's goals.

| Reference Methods Dataset Results Analysis Drawbacks / Observations Ahmed et al. LLM for Cloud Proprietary High accuracy Lacks deterministic trace (2023) Incidents Cloud Data onmitigation evaluation; not reproducible due to private data. Goel et al. eARCO Simulated Improved RCA Does not focus on automated (2024) incidents with prompts grading of multi-turn tool Framework calling. Patil et al. Gorilla Massive Better Highly generic; lacks the (2023) connected with generic APIs structured API operational SRE context APIs calls needed for DevOps. Yao et al. ReAct HotpotQA, Synergized task General-purpose benchmark; (2023) (Reasoning & ALFWorld completion no fixed rule-based scorer Acting) for IT operations. Schick et al. Toolformer Self-generated Zero-shot tool Hard to bound actions (2023) text use strictly; missing safety boundaries for live systems. Li et al. API-Bank 53 Generic Systematic Static environment (2023) Benchmark APIs evaluation evaluation; lacks dynamically simulated incident traces. Chuang et Proxy state Multi-turn Verifiable Complex setup that is difficult al. (2026) verifiable dialog logs metric output to adapt purely for SRE reward without modification. |
| --- |
| Zheng et al. LLM-as-a-judge MT-Bench / High Prone to LLM bias; highly (2023) Chatbot Arena correlation expensive to run at scale vs. w/ humans rule-based scoring. |


## DesignMethodology

The methodology adopts a test-driven approach for AI development. It is structured around the decoupling of the "Worker" (Target Agent) and the "Examiner" (Evaluation Harness).

- Worker Paradigm: The agent loops through: Alert Interpretation → Tool Selection →

Data Gathering → Reasoning Update → Final Output.

- Examiner Paradigm: The harness loops through: Scenario Loading→Execution →Trace Capture → Rule Verification → Reporting.

This dual-engine architecture ensures that every LLM response is anchored by standard deterministic testing rules, making it possible to measure improvements mathematically rather than subjectively.


## Architecture Modules and Description

The system is composed of two primary cooperating subsystems that share a common scenario format.

## 1. Target Agent (TheWorker)

The Target Agent receives a structured alert and must investigate autonomously.

- Inputs: Simulated alert strings (e.g., "checkout-service error rate spiked").

- Tools Provided:

- fetch_logs(service, time_range): Returns mock log lines.

- fetch_deployment_history(service): Returns mock deployment timestamps, versions, and change data.


- Reasoning Core: Uses function-calling capable LLMs to interpret telemetry, iteratively pull new data, and converge on a diagnosis.

- Safety Boundary: Explicitly restricted to recommending actionable plans (e.g., "roll back to v4.2") rather than executing administrative commands.

## 2. Deterministic Evaluation Harness (The Examiner)

The Harness treats the Target Agent as a black box and grades its output systematically.

- Scenario Loader: Parses YAML/JSON config files that mock the exact conditions of the incident.

- Trace Capture: Records a comprehensive, auditable JSON log of every tool call, argument, and reasoning step taken by the agent.

- Rule-Based Scorer: Validates against ground-truth expectations:

- Correct Invocation: Ensures the proper diagnostic tools were utilized.

- ValidArguments: Confirms correct service names and temporal bounds were passed.

- Diagnosis Correctness:Matches proposed root causes to the scenario's hidden truth.


## Dataset Description

A deliberate architectural decision for this project is that no external or proprietary dataset is used. All telemetry—including logs, deployment histories, and alert scenarios—is synthetically generated (mocked) within the project's own configuration framework.

Scenario Bank Configuration

The project builds a dynamic scenario bank comprising 15–20 JSON/YAML files that reflect highly realistic SRE failure modes. The scenarios include:

- Bad Deployments: Simulating elevated error rates immediately following a version change.

- Memory Leaks: Demonstrating gradual performance degradation and Out- Of-Memory (OOM) errors.

- Database Exhaustion: Simulating connection pool depletion under peak loads.

- ExpiredCertificates&DNSMisconfigurations: Reflecting common operational oversights that cascade into system-wide failures.

- Resource Contention: High CPU/Disk metrics paired with runaway process logs.

By relying entirely on synthetic data, the evaluation process achieves full reproducibility and open shareability without risking exposure of sensitive, real-world corporate infrastructure logs. The LLM remains unaware that the data is mocked, thereby preserving authentic agentic reasoning behavior.

## LLM Fine-Tuning

- Domain-Specific Training Data: Fine-tunes an open-source LLM using a synthetic dataset of simulated alerts, logs, tool-selection traces, root causes, and remediation plans to recognize SRE incident patterns.

- · Resource-Efficient Adaptation: Applies Parameter-Efficient Fine-Tuning (PEFT) methods like LoRA or QLoRA to minimize computational overhead while training the model.

- · Strict Dataset Separation: Maintains an unseen evaluation dataset exclusively for testing to eliminate data leakage and accurately gauge generalization.


· · Core Agent Integration: Embeds the resulting fine-tuned model into the Agentic AI System to serve as its primary reasoning core for decision-making.

· · Independent Performance Assessment: Evaluates model updates objectively using the isolated Deterministic Evaluation Harness to track diagnostic accuracy and tool

usag

## References

Ahmed, T., Ghosh, S., Bansal, C., Zimmermann, T., Zhang, X., & Rajmohan, S. (2023). Recommending root-cause and mitigation steps for cloud incidents using large language models. In Proceedings of the 45th IEEE/ACM International Conference on Software Engineering (ICSE 2023) (pp. 1737– 1749). IEEE.

Amershi, S., Weld, D., Vorvoreanu, M., Fourney, A., Nushi, B., Collisson, P., Suh, J., Iqbal, S., Bennett, P. N., Inkpen, K., Teevan, J., Kikin-Gil, R., & Horvitz, E. (2019). Guidelines for human-AI interaction. In Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems (pp. 1–13). ACM.

Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (Eds.). (2016). Site reliability engineering: How Google runs production systems. O'Reilly Media.

Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., … Amodei, D. (2020). Language models are few-shot learners. Advances in Neural Information Processing Systems, 33, 1877–1901.

Chuang, Y.-S., Kulkarni, C., Chiu, A., Thangali, A., Pan, Z., Shekhar, S., Ge, Y., Li, Y., Kona, U., Pang, L., & Mehrotra, P. (2026). Toward scalable verifiable reward: Proxy state-based evaluation for multi-turn tool-calling LLM agents. arXiv preprint arXiv:2602.16246.

Goel, D., Magazine, R., Ghosh, S., Nambi, A., Deshpande, P., Zhang, X., Bansal, C., & Rajmohan, S. (2024). eARCO: Efficient automated root cause analysis with prompt optimization. arXiv preprint arXiv:2504.11505.

Li, M., Song, F., Yu, B., Yu, H., Li, Z., Huang, F., & Li, Y. (2023). API-Bank: A benchmark for tool-augmented LLMs. In Proceedings of the 2023 Conference

on Empirical Methods in Natural Language Processing (EMNLP 2023).


Notaro, P., Cardoso, J., & Gerndt, M. (2021). A survey of AIOps methods for failure management. ACM Transactions on Intelligent Systems and Technology, 12(6), 1–45.

OpenAI. (2023). GPT-4 technical report. arXiv preprint arXiv:2303.08774.

Patil, S. G., Zhang, T., Wang, X., & Gonzalez, J. E. (2023). Gorilla: Large language model connected with massive APIs. arXiv preprint arXiv:2305.15334. chick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Hambro, E., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). Toolformer: Language models can teach themselves to use tools. Advances in Neural Information Processing Systems, 36, 68539–68551.

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30.

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q., & Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language models. Advances in Neural Information Processing Systems, 35, 24824–24837.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In Proceedings of the 11th International Conference on Learning Representations (ICLR 2023).

Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. Advances in Neural Information Processing Systems, 36.

Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M. A., Lacroix, T., ... & Lample, G. (2023). LLaMA: Open and efficient foundation language models. arXiv preprint arXiv: 2302.13971.

Ouyang, L., Wu, J., Jiang, X., Almeida, D., Wainwright, C., Mishkin, P., ... & Lowe, R. (2022). Training language models to follow instructions with human feedback. Advances in Neural Information Processing Systems, 35, 27730- 27744.

Kojima, T., Gu, S. S., Reid, M., Matsuo, Y., & Iwasawa, Y. (2022). Large language models are zero-shot reasoners. Advances in neural information processing systems, 35, 22199-22213.

Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., ... & Zhou, D. (2022).


- Qin, Y., Hu, S., Lin, Y., Chen, W., Ding, N., Cui, G., ... & Sun, M. (2023). ToolLLM: Facilitating large language models to master 16000+ real-world APIs. arXiv preprint arXiv: 2307.16789.

- Dang, Y., Lin, Q., & Huang, P. (2021). Towards automated incident management in cloud environments. ACMSIGOPS Operating Systems Review, 55(1), 47-53.

- Zhao, X., Zhang, Y., & Chen, J. (2020). Intelligent automated IT operations: A review. Journal of Systems Architecture, 108, 101740.

- Bogatu, A., Fernandes, A. A., & Paton, N. W. (2020). Dataset discovery in data lakes. In 2020 IEEE 36th International Conference on Data Engineering (ICDE) (pp. 709-720). IEEE.

- Zhang, Y., Liu, J., & Wang, X. (2023). AgentBench: Evaluating LLMs as agents. arXiv preprint arXiv:2308.03688.

- Liu, Z., Chen, H., & Yang, Y. (2023). LLM+A: Integration of large language models and AIOps.

- IEEE Transactions on Network and Service Management, 20(4), 1120-1135.

- Lin, J., Smith, A., & Lee, M. (2018). Multi-agent systems in IT operations. International Journal of Network Management, 28(2), e2015.

- Smith, R., & Doe, J. (2022). Synthetic data generation for testing AIOps. In Proceedings of the 2022 ACM Symposium on Cloud Computing (pp. 110-120).

- Johnson, M., & Garcia, L. (2021). SRE practices in modern microservices. IEEE Cloud Computing, 8(1), 45-53.

- Lee, C., & Kim, D. (2020). Microservice anomaly detection. Journal of Network and Computer Applications, 150, 102489.

- Kumar, S., & Patel, N. (2022). Log parsing using deep learning. Knowledge-Based Systems, 240, 108156.

- He, P., Zhu, J., Zheng, Z., & Lyu, M. R. (2017). Drain: An online log parsing approach with fixed depth tree. In 2017 IEEE International Conference on Web Services (ICWS) (pp. 43-50). IEEE.

- Du, M., Li, F., Zheng, G., & Srikumar, V. (2017). DeepLog: Anomaly detection and diagnosis from system logs through deep learning. In Proceedings of the 2017 ACM SIGSAC Conference on Computer and Communications Security (pp. 1285-1298).

- Nedelkoski, S., Bogatinovski, J., Mandjes, M., & Acker, A. (2020). Self-supervised log parsing. In European Conference on Machine Learning and Principles and Practice of Knowledge Discovery in Databases (pp. 120-136).


- Meng, W., Liu, Y., Zhu, Y., Zhang, S., Pei, D., Liu, Y., ... & Yang, Z. (2019). LogAnomaly: Unstructured log anomaly detection using neural network. In 2019 IEEE 27th International Symposium on Quality of Service (IWQoS) (pp. 1-10). IEEE.

Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., ... & Wang, Y. (2023). AutoGen: Enabling next-gen LLM applications via multi-agent conversation. arXiv preprint arXiv:2308.08155.

Guo, X., Zheng, Z., & Lyu, M. R. (2021). Practical log analysis for reliable systems.

Springer.

Zhu, J., He, P., Fu, Q., Zhang, H., Lyu, M. R., & Dang, D. (2019). Tools and benchmarks for automated log parsing. In 2019 IEEE/ACM 41st International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP) (pp. 121-130). IEEE.
