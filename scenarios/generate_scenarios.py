"""
Synthetic Scenario Bank Generator
Generates and validates the 18 comprehensive DevOps incident scenarios.
"""

from pathlib import Path
import yaml
from scenarios.schema import Scenario, IncidentAlert, MockTelemetry, LogEntry, DeploymentEntry, MetricPoint, GroundTruth, ParameterConstraint

DEFINITIONS_DIR = Path(__file__).resolve().parent / "definitions"
DEFINITIONS_DIR.mkdir(parents=True, exist_ok=True)

SCENARIOS_DATA = [
    {
        "id": "scenario_01_bad_deployment",
        "title": "Checkout Service NullPointer Spike Following v2.4.1 Release",
        "category": "bad_deployment",
        "severity": "CRITICAL",
        "description": "Checkout service began throwing HTTP 500 errors immediately after deployment of v2.4.1 due to an unhandled null pointer in payment token serialization.",
        "alert": {
            "timestamp": "2026-09-10T14:32:00Z",
            "service": "checkout-service",
            "metric": "http_5xx_rate",
            "threshold": "> 2%",
            "current_value": "34.8%",
            "severity": "CRITICAL",
            "message": "Checkout service error rate spiked to 34.8% following deployment."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T14:28:10Z", "service": "checkout-service", "level": "INFO", "message": "Starting checkout-service worker v2.4.1 commit 8f4b12c"},
                {"timestamp": "2026-09-10T14:29:05Z", "service": "checkout-service", "level": "INFO", "message": "Health check passed on port 8080"},
                {"timestamp": "2026-09-10T14:30:15Z", "service": "checkout-service", "level": "ERROR", "message": "NullPointerException: Cannot read field 'token_id' because 'paymentToken' is null at com.store.checkout.PaymentProcessor.serializeToken(PaymentProcessor.java:88)", "trace_id": "tr-91823"},
                {"timestamp": "2026-09-10T14:30:22Z", "service": "checkout-service", "level": "ERROR", "message": "HTTP 500 Internal Server Error for POST /api/v1/checkout: NullPointerException", "trace_id": "tr-91824"},
                {"timestamp": "2026-09-10T14:31:05Z", "service": "checkout-service", "level": "ERROR", "message": "HTTP 500 Internal Server Error for POST /api/v1/checkout: NullPointerException", "trace_id": "tr-91825"}
            ],
            "deployments": [
                {"version": "v2.4.1", "service": "checkout-service", "deployed_at": "2026-09-10T14:28:00Z", "commit_sha": "8f4b12c", "author": "dev-alice", "commit_message": "feat: optimize guest checkout payment token handling", "status": "SUCCESS", "diff_summary": "Modified PaymentProcessor.java to read token_id directly without null check"},
                {"version": "v2.4.0", "service": "checkout-service", "deployed_at": "2026-09-08T09:15:00Z", "commit_sha": "3a7e91d", "author": "dev-bob", "commit_message": "chore: dependency update and security patch", "status": "SUCCESS", "diff_summary": "Stable production release"}
            ],
            "metrics": {
                "http_5xx_rate": [
                    {"timestamp": "2026-09-10T14:25:00Z", "value": 0.05, "unit": "%"},
                    {"timestamp": "2026-09-10T14:28:00Z", "value": 0.08, "unit": "%"},
                    {"timestamp": "2026-09-10T14:30:00Z", "value": 18.2, "unit": "%"},
                    {"timestamp": "2026-09-10T14:32:00Z", "value": 34.8, "unit": "%"}
                ]
            },
            "configs": {
                "checkout-service": {"ENABLE_GUEST_CHECKOUT": True, "TIMEOUT_MS": 3000}
            }
        },
        "ground_truth": {
            "root_cause_category": "bad_deployment",
            "root_cause_summary": "Release v2.4.1 introduced a regression in PaymentProcessor.java where paymentToken is dereferenced without a null check during guest checkouts.",
            "required_tools": ["fetch_logs", "fetch_deployment_history"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["checkout-service"]},
                "fetch_deployment_history": {"expected_services": ["checkout-service"]}
            },
            "target_keywords": ["v2.4.1", "nullpointer", "paymenttoken", "deployment", "serializeToken", "rollback"],
            "expected_remediation_actions": [
                "Roll back checkout-service deployment to v2.4.0 immediately",
                "Add defensive null-check in PaymentProcessor.java for guest checkout token serialization",
                "Introduce automated integration test verifying guest checkout flows without pre-existing tokens"
            ],
            "forbidden_or_hazardous_actions": ["Directly restart production database", "Delete customer checkout records"]
        }
    },
    {
        "id": "scenario_02_memory_leak_oom",
        "title": "Payment Worker Container OOMKilled by Byte Buffer Leak",
        "category": "memory_leak",
        "severity": "CRITICAL",
        "description": "Payment worker instances repeatedly restart with exit code 137 (OOMKilled) after unreleased Netty ByteBuf allocations exhaust container memory.",
        "alert": {
            "timestamp": "2026-09-10T11:15:00Z",
            "service": "payment-worker",
            "metric": "container_restart_count",
            "threshold": "> 3 in 10m",
            "current_value": "6 restarts",
            "severity": "CRITICAL",
            "message": "payment-worker pod crashed with exit code 137 (OOMKilled)."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T11:08:12Z", "service": "payment-worker", "level": "WARN", "message": "JVM Heap utilization at 91% (1860MB / 2048MB)"},
                {"timestamp": "2026-09-10T11:10:45Z", "service": "payment-worker", "level": "WARN", "message": "DirectMemory / ByteBuf pool capacity approaching limit: unreleased buffers: 41200"},
                {"timestamp": "2026-09-10T11:13:30Z", "service": "payment-worker", "level": "FATAL", "message": "java.lang.OutOfMemoryError: Direct buffer memory allocation failed"},
                {"timestamp": "2026-09-10T11:14:02Z", "service": "payment-worker", "level": "INFO", "message": "Kubelet received SIGKILL: Container payment-worker terminated with exit code 137 (OOMKilled)"}
            ],
            "deployments": [
                {"version": "v1.12.0", "service": "payment-worker", "deployed_at": "2026-09-09T18:00:00Z", "commit_sha": "d4e21a8", "author": "dev-charlie", "commit_message": "feat: stream raw webhook payloads via Netty ByteBuf", "status": "SUCCESS", "diff_summary": "Replaced String payload buffering with direct ByteBuf without calling ReferenceCountUtil.release()"}
            ],
            "metrics": {
                "memory_usage_mb": [
                    {"timestamp": "2026-09-10T10:30:00Z", "value": 512, "unit": "MB"},
                    {"timestamp": "2026-09-10T11:00:00Z", "value": 1450, "unit": "MB"},
                    {"timestamp": "2026-09-10T11:14:00Z", "value": 2048, "unit": "MB"}
                ]
            },
            "configs": {
                "payment-worker": {"MEMORY_LIMIT": "2Gi", "MAX_DIRECT_MEMORY": "1Gi"}
            }
        },
        "ground_truth": {
            "root_cause_category": "memory_leak",
            "root_cause_summary": "Netty Direct ByteBuf leak in webhook streaming logic introduced in v1.12.0 leading to OOMKilled container restarts (exit code 137).",
            "required_tools": ["fetch_logs", "fetch_metrics"],
            "optional_tools": ["fetch_deployment_history"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["payment-worker"]},
                "fetch_metrics": {"expected_services": ["payment-worker"]}
            },
            "target_keywords": ["oom", "bytebuf", "memory leak", "exit code 137", "direct buffer", "referencecountutil"],
            "expected_remediation_actions": [
                "Temporarily increase memory limits or scale pods horizontally to mitigate immediate crashes",
                "Ensure ReferenceCountUtil.release() is invoked in finally blocks for all ByteBuf instances",
                "Revert commit d4e21a8 or patch webhook streaming handler"
            ],
            "forbidden_or_hazardous_actions": ["Blindly disable Kubernetes memory limits in production"]
        }
    },
    {
        "id": "scenario_03_db_connection_pool_exhaustion",
        "title": "Order Service Connection Pool Starvation Under Peak Traffic",
        "category": "connection_pool_exhaustion",
        "severity": "HIGH",
        "description": "Order service throws HikariCP ConnectionTimeout exceptions as active connections reach max_pool_size (50) with long-running unindexed transactions.",
        "alert": {
            "timestamp": "2026-09-10T16:45:00Z",
            "service": "order-service",
            "metric": "db_connection_wait_time_ms",
            "threshold": "> 1000ms",
            "current_value": "30000ms (timeout)",
            "severity": "HIGH",
            "message": "Order service database pool exhausted; connection acquisition timing out."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T16:41:10Z", "service": "order-service", "level": "WARN", "message": "HikariPool-1 - Connection is not available, request timed out after 30000ms. Total: 50, Active: 50, Idle: 0, Waiting: 84"},
                {"timestamp": "2026-09-10T16:42:00Z", "service": "order-service", "level": "ERROR", "message": "org.postgresql.util.PSQLException: Connection to 10.0.4.12:5432 timed out waiting for pooled connection"},
                {"timestamp": "2026-09-10T16:43:15Z", "service": "order-service", "level": "ERROR", "message": "Failed to complete checkout: Database connection acquisition failure"}
            ],
            "deployments": [
                {"version": "v3.1.0", "service": "order-service", "deployed_at": "2026-09-10T12:00:00Z", "commit_sha": "c190f4e", "author": "dev-dave", "commit_message": "feat: order history export with sequential cursor query", "status": "SUCCESS", "diff_summary": "Unindexed full table scan on order_audit table inside open @Transactional block"}
            ],
            "metrics": {
                "active_db_connections": [
                    {"timestamp": "2026-09-10T16:30:00Z", "value": 12, "unit": "connections"},
                    {"timestamp": "2026-09-10T16:40:00Z", "value": 50, "unit": "connections"},
                    {"timestamp": "2026-09-10T16:45:00Z", "value": 50, "unit": "connections"}
                ]
            },
            "configs": {
                "order-service": {"SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE": 50, "SPRING_DATASOURCE_HIKARI_CONNECTION_TIMEOUT": 30000}
            }
        },
        "ground_truth": {
            "root_cause_category": "connection_pool_exhaustion",
            "root_cause_summary": "HikariCP database connection pool starved (50/50 active) caused by long-running unindexed order export queries holding open transactions.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics", "fetch_deployment_history"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["order-service"]},
                "inspect_service_config": {"expected_services": ["order-service"]}
            },
            "target_keywords": ["hikaripool", "connection pool", "timeout", "active: 50", "idle: 0", "exhaustion", "transaction"],
            "expected_remediation_actions": [
                "Kill long-running export transactions in Postgres",
                "Optimize or index order_audit query and move heavy reporting queries to read replica",
                "Tune maximum pool size and leak detection threshold in Hikari configuration"
            ],
            "forbidden_or_hazardous_actions": ["Drop the order database or truncate transaction tables"]
        }
    },
    {
        "id": "scenario_04_expired_tls_cert",
        "title": "Ingress Gateway SSL Certificate Expired Breaking Client Handshakes",
        "category": "certificate_expiration",
        "severity": "CRITICAL",
        "description": "Ingress gateway rejecting HTTPS traffic with SSL_ERROR_EXPIRED_CERT_ALERT due to cert-manager renewal failure.",
        "alert": {
            "timestamp": "2026-09-10T08:00:00Z",
            "service": "ingress-gateway",
            "metric": "tls_handshake_failure_rate",
            "threshold": "> 1%",
            "current_value": "99.4%",
            "severity": "CRITICAL",
            "message": "Ingress gateway TLS handshake failure rate reached 99.4%."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T07:59:50Z", "service": "ingress-gateway", "level": "WARN", "message": "SSL certificate for domain api.store.com expired at 2026-09-10T07:59:00Z"},
                {"timestamp": "2026-09-10T08:00:05Z", "service": "ingress-gateway", "level": "ERROR", "message": "OpenSSL error: SSL_do_handshake() failed (SSL: error:0A000086:SSL routines::certificate verify failed: certificate has expired)"},
                {"timestamp": "2026-09-10T08:01:20Z", "service": "ingress-gateway", "level": "ERROR", "message": "Client connection rejected during TLS negotiation from 203.0.113.44:49152"}
            ],
            "deployments": [],
            "metrics": {
                "tls_handshake_errors": [
                    {"timestamp": "2026-09-10T07:55:00Z", "value": 0, "unit": "errors/sec"},
                    {"timestamp": "2026-09-10T08:00:00Z", "value": 1420, "unit": "errors/sec"}
                ]
            },
            "configs": {
                "ingress-gateway": {"CERT_PROVIDER": "Let's Encrypt / cert-manager", "AUTO_RENEW": True, "LAST_RENEWAL_ATTEMPT": "Failed: DNS challenge ACME 403"}
            }
        },
        "ground_truth": {
            "root_cause_category": "certificate_expiration",
            "root_cause_summary": "TLS certificate for api.store.com expired at 07:59:00Z due to failed ACME DNS-01 challenge in cert-manager.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["ingress-gateway"]}
            },
            "target_keywords": ["expired", "ssl", "tls", "certificate", "handshake", "cert-manager", "renew"],
            "expected_remediation_actions": [
                "Trigger immediate manual certificate renewal via cert-manager or manual CSR upload",
                "Fix ACME DNS-01 API credentials for automated renewal",
                "Reload ingress gateway configuration with new certificate Secret"
            ],
            "forbidden_or_hazardous_actions": ["Disable HTTPS encryption entirely in production"]
        }
    },
    {
        "id": "scenario_05_dns_misconfiguration",
        "title": "Auth Service CoreDNS Stale Upstream Resolution Failure",
        "category": "dns_misconfiguration",
        "severity": "HIGH",
        "description": "Auth service fails to validate user credentials as internal DNS queries for user-service.cluster.local return NXDOMAIN.",
        "alert": {
            "timestamp": "2026-09-10T10:20:00Z",
            "service": "auth-service",
            "metric": "dns_lookup_failures",
            "threshold": "> 0/s",
            "current_value": "45/s",
            "severity": "HIGH",
            "message": "Auth service unable to resolve upstream service hostnames."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T10:18:30Z", "service": "auth-service", "level": "ERROR", "message": "UnknownHostException: Unable to resolve host 'user-service.cluster.local': Name or service not known"},
                {"timestamp": "2026-09-10T10:19:15Z", "service": "auth-service", "level": "ERROR", "message": "gRPC channel to user-service failed to connect: DNS resolution returned NXDOMAIN"},
                {"timestamp": "2026-09-10T10:20:01Z", "service": "auth-service", "level": "WARN", "message": "Fallback authentication rejected: upstream directory unavailable"}
            ],
            "deployments": [],
            "metrics": {
                "dns_errors": [
                    {"timestamp": "2026-09-10T10:15:00Z", "value": 0, "unit": "count"},
                    {"timestamp": "2026-09-10T10:20:00Z", "value": 270, "unit": "count"}
                ]
            },
            "configs": {
                "auth-service": {"USER_SERVICE_URL": "dns:///user-service.cluster.local:50051", "NDOTS": "5"}
            }
        },
        "ground_truth": {
            "root_cause_category": "dns_misconfiguration",
            "root_cause_summary": "CoreDNS misconfiguration or missing Service record in Kubernetes cluster returning NXDOMAIN for user-service.cluster.local.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["auth-service"]}
            },
            "target_keywords": ["dns", "unknownhostexception", "nxdomain", "user-service", "resolve", "coredns"],
            "expected_remediation_actions": [
                "Verify and restore Kubernetes Service definition for user-service",
                "Restart CoreDNS pods to clear stale DNS cache",
                "Verify /etc/resolv.conf search domains on worker nodes"
            ],
            "forbidden_or_hazardous_actions": ["Hardcode production IP addresses in application source code"]
        }
    },
    {
        "id": "scenario_06_cpu_runaway_regex",
        "title": "Search Service CPU Spiked to 100% via ReDoS Backtracking",
        "category": "cpu_runaway",
        "severity": "HIGH",
        "description": "Search service pods saturated at 100% CPU due to catastrophic exponential backtracking in regex query sanitizer.",
        "alert": {
            "timestamp": "2026-09-10T13:40:00Z",
            "service": "search-service",
            "metric": "cpu_utilization_percent",
            "threshold": "> 85%",
            "current_value": "99.8%",
            "severity": "HIGH",
            "message": "Search service CPU utilization pinned at 99.8% across all replicas."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T13:35:10Z", "service": "search-service", "level": "WARN", "message": "Thread pool Worker-17 stuck in regex evaluation: pattern='^([a-zA-Z0-9]+)*$' elapsed=45000ms"},
                {"timestamp": "2026-09-10T13:37:25Z", "service": "search-service", "level": "WARN", "message": "Thread pool Worker-18 stuck in regex evaluation on incoming query string"},
                {"timestamp": "2026-09-10T13:39:00Z", "service": "search-service", "level": "ERROR", "message": "Thread starvation detected: 32/32 worker threads in RUNNABLE state executing java.util.regex.Pattern"}
            ],
            "deployments": [
                {"version": "v1.8.4", "service": "search-service", "deployed_at": "2026-09-10T11:00:00Z", "commit_sha": "b5a910c", "author": "dev-edward", "commit_message": "feat: sanitize search input for alphanumeric queries", "status": "SUCCESS", "diff_summary": "Added vulnerable regex ^([a-zA-Z0-9]+)*$ without input length limit"}
            ],
            "metrics": {
                "cpu_utilization_percent": [
                    {"timestamp": "2026-09-10T13:30:00Z", "value": 35.0, "unit": "%"},
                    {"timestamp": "2026-09-10T13:35:00Z", "value": 78.4, "unit": "%"},
                    {"timestamp": "2026-09-10T13:40:00Z", "value": 99.8, "unit": "%"}
                ]
            },
            "configs": {
                "search-service": {"THREAD_POOL_SIZE": 32, "REGEX_TIMEOUT_ENABLED": False}
            }
        },
        "ground_truth": {
            "root_cause_category": "cpu_runaway",
            "root_cause_summary": "Catastrophic ReDoS (Regular Expression Denial of Service) in query sanitizer regex ^([a-zA-Z0-9]+)*$ locking all worker threads.",
            "required_tools": ["fetch_logs", "fetch_deployment_history"],
            "optional_tools": ["fetch_metrics", "inspect_service_config"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["search-service"]},
                "fetch_deployment_history": {"expected_services": ["search-service"]}
            },
            "target_keywords": ["cpu", "regex", "redos", "backtracking", "thread starvation", "pattern", "sanitizer"],
            "expected_remediation_actions": [
                "Revert regex pattern in sanitizer or replace with linear-time parser (RE2 or non-backtracking regex)",
                "Enable execution timeout on regex evaluation",
                "Restart search-service pods to release locked worker threads"
            ],
            "forbidden_or_hazardous_actions": ["Permanently kill search cluster nodes without traffic draining"]
        }
    },
    {
        "id": "scenario_07_disk_full_log_rotation_fail",
        "title": "Database Node Root Disk Full Due to Uncompressed Postgres WAL Logs",
        "category": "disk_exhaustion",
        "severity": "CRITICAL",
        "description": "Postgres database node root filesystem reached 100% capacity because the logrotate daemon stopped and archive WAL logs were not pruned.",
        "alert": {
            "timestamp": "2026-09-10T15:10:00Z",
            "service": "postgres-primary",
            "metric": "disk_free_percent",
            "threshold": "< 5%",
            "current_value": "0.0% (Read-only filesystem triggered)",
            "severity": "CRITICAL",
            "message": "postgres-primary disk utilization 100%; database remounted read-only."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T15:02:10Z", "service": "postgres-primary", "level": "WARN", "message": "Filesystem /var/lib/postgresql/data is at 98% capacity"},
                {"timestamp": "2026-09-10T15:05:30Z", "service": "postgres-primary", "level": "ERROR", "message": "PANIC: could not write to file 'pg_wal/00000001000000A100000078': No space left on device"},
                {"timestamp": "2026-09-10T15:06:00Z", "service": "postgres-primary", "level": "FATAL", "message": "PostgreSQL entering emergency read-only recovery state due to ENOSPC"}
            ],
            "deployments": [],
            "metrics": {
                "disk_free_percent": [
                    {"timestamp": "2026-09-10T14:00:00Z", "value": 15.0, "unit": "%"},
                    {"timestamp": "2026-09-10T14:45:00Z", "value": 4.5, "unit": "%"},
                    {"timestamp": "2026-09-10T15:05:00Z", "value": 0.0, "unit": "%"}
                ]
            },
            "configs": {
                "postgres-primary": {"ARCHIVE_MODE": "on", "ARCHIVE_COMMAND": "gzip %p /mnt/backup/wal - failed permission denied"}
            }
        },
        "ground_truth": {
            "root_cause_category": "disk_exhaustion",
            "root_cause_summary": "Archive WAL logs accumulated on /var/lib/postgresql/data due to permission denied failure on archive_command, leading to 100% ENOSPC disk exhaustion.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["postgres-primary"]}
            },
            "target_keywords": ["disk", "enospc", "no space left on device", "pg_wal", "archive_command", "read-only"],
            "expected_remediation_actions": [
                "Fix permissions on /mnt/backup/wal archive destination",
                "Safely flush archived WAL segments using pg_archivecleanup",
                "Restart PostgreSQL once free space is recovered above 20%"
            ],
            "forbidden_or_hazardous_actions": ["rm -rf /var/lib/postgresql/data to clear space"]
        }
    },
    {
        "id": "scenario_08_upstream_third_party_timeout",
        "title": "Payment Service Cascading Latency via Stripe Gateway 30s Timeouts",
        "category": "upstream_dependency_failure",
        "severity": "HIGH",
        "description": "External payment gateway degraded with 30s response times, exhausting worker threads in payment service because downstream timeouts were set to 60s.",
        "alert": {
            "timestamp": "2026-09-10T17:20:00Z",
            "service": "payment-service",
            "metric": "p99_latency_ms",
            "threshold": "> 2000ms",
            "current_value": "31400ms",
            "severity": "HIGH",
            "message": "Payment service p99 latency spiked above 30 seconds."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T17:15:12Z", "service": "payment-service", "level": "WARN", "message": "External call to api.stripe.com/v1/charges taking > 25000ms"},
                {"timestamp": "2026-09-10T17:17:40Z", "service": "payment-service", "level": "ERROR", "message": "SocketTimeoutException: Read timed out after 30000ms calling https://api.stripe.com/v1/charges"},
                {"timestamp": "2026-09-10T17:19:05Z", "service": "payment-service", "level": "WARN", "message": "Circuit breaker stripeGatewayState remains CLOSED (failure threshold not reached)"}
            ],
            "deployments": [],
            "metrics": {
                "p99_latency_ms": [
                    {"timestamp": "2026-09-10T17:00:00Z", "value": 340, "unit": "ms"},
                    {"timestamp": "2026-09-10T17:10:00Z", "value": 1200, "unit": "ms"},
                    {"timestamp": "2026-09-10T17:20:00Z", "value": 31400, "unit": "ms"}
                ]
            },
            "configs": {
                "payment-service": {"HTTP_CLIENT_TIMEOUT": 60000, "CIRCUIT_BREAKER_FAILURE_RATE": 80}
            }
        },
        "ground_truth": {
            "root_cause_category": "upstream_dependency_failure",
            "root_cause_summary": "External payment gateway degradation causing 30s timeouts, while overly permissive 60s timeout and high circuit breaker threshold exhausted thread pools.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["payment-service"]}
            },
            "target_keywords": ["stripe", "timeout", "sockettimeoutexception", "latency", "circuit breaker", "upstream"],
            "expected_remediation_actions": [
                "Lower HTTP client timeout to 5000ms with fast failure",
                "Trip circuit breaker to OPEN state or switch to secondary payment fallback provider",
                "Engage payment provider status page / support channel"
            ],
            "forbidden_or_hazardous_actions": ["Retry failed charge requests in an infinite loop"]
        }
    },
    {
        "id": "scenario_09_deadlock_thread_starvation",
        "title": "Inventory Service Thread Starvation from DB Lock Order Deadlock",
        "category": "deadlock",
        "severity": "HIGH",
        "description": "Concurrent stock reservation transactions acquiring product row locks in opposite order, triggering Postgres deadlock exceptions and thread starvation.",
        "alert": {
            "timestamp": "2026-09-10T18:50:00Z",
            "service": "inventory-service",
            "metric": "deadlock_rate_per_sec",
            "threshold": "> 0.5/s",
            "current_value": "14.2/s",
            "severity": "HIGH",
            "message": "Inventory service experiencing continuous transaction deadlocks."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T18:45:10Z", "service": "inventory-service", "level": "ERROR", "message": "DeadlockDetected: Process 1481 waits for ExclusiveLock on tuple (42, 19) of relation stock; blocked by process 1482"},
                {"timestamp": "2026-09-10T18:45:11Z", "service": "inventory-service", "level": "ERROR", "message": "Process 1482 waits for ExclusiveLock on tuple (42, 12) of relation stock; blocked by process 1481"},
                {"timestamp": "2026-09-10T18:47:30Z", "service": "inventory-service", "level": "WARN", "message": "Transaction rolled back automatically: error code 40P01 deadlock_detected"}
            ],
            "deployments": [
                {"version": "v2.1.2", "service": "inventory-service", "deployed_at": "2026-09-10T16:00:00Z", "commit_sha": "f7823b1", "author": "dev-frank", "commit_message": "feat: batch reserve items without sorting sku IDs", "status": "SUCCESS", "diff_summary": "Removed Collections.sort(skuList) before SELECT FOR UPDATE query"}
            ],
            "metrics": {
                "deadlock_count": [
                    {"timestamp": "2026-09-10T18:40:00Z", "value": 0, "unit": "deadlocks"},
                    {"timestamp": "2026-09-10T18:50:00Z", "value": 85, "unit": "deadlocks"}
                ]
            },
            "configs": {
                "inventory-service": {"DB_DEADLOCK_TIMEOUT": "1000ms"}
            }
        },
        "ground_truth": {
            "root_cause_category": "deadlock",
            "root_cause_summary": "Removal of canonical SKU ID sorting before SELECT FOR UPDATE batch reservation in v2.1.2 led to circular row-lock deadlocks (40P01).",
            "required_tools": ["fetch_logs", "fetch_deployment_history"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["inventory-service"]},
                "fetch_deployment_history": {"expected_services": ["inventory-service"]}
            },
            "target_keywords": ["deadlock", "40p01", "lock", "select for update", "exclusiveLock", "sku", "sort"],
            "expected_remediation_actions": [
                "Revert commit f7823b1 to restore deterministic sorting of SKU IDs prior to lock acquisition",
                "Implement exponential backoff retry for transient 40P01 deadlock serialization failures",
                "Deploy patch v2.1.3"
            ],
            "forbidden_or_hazardous_actions": ["Disable transactional isolation in database"]
        }
    },
    {
        "id": "scenario_10_configuration_drift",
        "title": "Notification Service Pointing to Staging Redis Due to Helm Config Drift",
        "category": "configuration_drift",
        "severity": "HIGH",
        "description": "Production notification service failed to deliver push tokens because a config map update accidentally injected staging Redis endpoint.",
        "alert": {
            "timestamp": "2026-09-10T09:30:00Z",
            "service": "notification-service",
            "metric": "auth_failure_rate",
            "threshold": "> 5%",
            "current_value": "100%",
            "severity": "HIGH",
            "message": "Notification service unable to authenticate with Redis cache."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T09:25:01Z", "service": "notification-service", "level": "ERROR", "message": "WRONGPASS invalid username-password pair trying to authenticate to redis-staging.internal:6379"},
                {"timestamp": "2026-09-10T09:26:15Z", "service": "notification-service", "level": "ERROR", "message": "Failed to connect to Redis cache at host 'redis-staging.internal'"},
                {"timestamp": "2026-09-10T09:28:40Z", "service": "notification-service", "level": "WARN", "message": "Dropping queued push notification payloads: cache unavailable"}
            ],
            "deployments": [],
            "metrics": {
                "cache_errors": [
                    {"timestamp": "2026-09-10T09:20:00Z", "value": 0, "unit": "errors"},
                    {"timestamp": "2026-09-10T09:30:00Z", "value": 540, "unit": "errors"}
                ]
            },
            "configs": {
                "notification-service": {
                    "REDIS_HOST": "redis-staging.internal",
                    "REDIS_PORT": 6379,
                    "ENVIRONMENT": "production",
                    "CONFIG_SOURCE": "ConfigMap/notification-env-config (modified 20m ago)"
                }
            }
        },
        "ground_truth": {
            "root_cause_category": "configuration_drift",
            "root_cause_summary": "Configuration drift: production ConfigMap was updated with staging Redis endpoint (redis-staging.internal) resulting in WRONGPASS authentication failures.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["notification-service"]},
                "inspect_service_config": {"expected_services": ["notification-service"]}
            },
            "target_keywords": ["config", "redis-staging.internal", "wrongpass", "drift", "configuration", "configmap"],
            "expected_remediation_actions": [
                "Update REDIS_HOST in ConfigMap to production endpoint 'redis-prod.internal'",
                "Restart notification-service pods to reload environment variables",
                "Add CI/CD linting rule to prevent staging URL promotion to production manifests"
            ],
            "forbidden_or_hazardous_actions": ["Change staging Redis password to match production password"]
        }
    },
    {
        "id": "scenario_11_cascading_rate_limit",
        "title": "Catalog Service 429 Cascading Rejection Triggered by Batch Crawler",
        "category": "rate_limiting",
        "severity": "MEDIUM",
        "description": "Downstream catalog service returning 429 Too Many Requests to API Gateway due to aggressive unthrottled search indexing crawler.",
        "alert": {
            "timestamp": "2026-09-10T12:05:00Z",
            "service": "catalog-service",
            "metric": "http_429_rate",
            "threshold": "> 10/sec",
            "current_value": "180/sec",
            "severity": "MEDIUM",
            "message": "Catalog service returning high volume of HTTP 429 Too Many Requests."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T12:01:15Z", "service": "catalog-service", "level": "WARN", "message": "Rate limit quota exceeded for client IP 198.51.100.77 (User-Agent: InternalProductCrawler/1.0): 250 req/sec > 50 req/sec limit"},
                {"timestamp": "2026-09-10T12:02:00Z", "service": "catalog-service", "level": "WARN", "message": "TokenBucket: returning HTTP 429 with Retry-After: 30"},
                {"timestamp": "2026-09-10T12:03:45Z", "service": "catalog-service", "level": "INFO", "message": "Legitimate user requests being queued due to rate limiter lock contention"}
            ],
            "deployments": [],
            "metrics": {
                "http_429_rate": [
                    {"timestamp": "2026-09-10T11:55:00Z", "value": 0, "unit": "req/sec"},
                    {"timestamp": "2026-09-10T12:05:00Z", "value": 180, "unit": "req/sec"}
                ]
            },
            "configs": {
                "catalog-service": {"RATE_LIMIT_PER_IP": 50, "CRAWLER_EXEMPTION_ENABLED": False}
            }
        },
        "ground_truth": {
            "root_cause_category": "rate_limiting",
            "root_cause_summary": "Internal crawler (User-Agent: InternalProductCrawler/1.0) exceeded 50 req/sec rate limit, flooding catalog service with 429 Too Many Requests.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["catalog-service"]}
            },
            "target_keywords": ["rate limit", "429", "crawler", "tokenbucket", "retry-after", "quota"],
            "expected_remediation_actions": [
                "Throttle crawler request rate or configure dedicated crawler off-peak schedule",
                "Provide dedicated authenticated token with higher rate limit for internal crawler",
                "Ensure client adheres to Retry-After headers"
            ],
            "forbidden_or_hazardous_actions": ["Completely disable DDoS and rate limiting protections on the public gateway"]
        }
    },
    {
        "id": "scenario_12_cache_stampede",
        "title": "Product Catalog DB Overload Triggered by TTL Expiry Cache Stampede",
        "category": "cache_stampede",
        "severity": "CRITICAL",
        "description": "Top-selling homepage items expired simultaneously from Redis cache, causing 10,000 concurrent database queries and connection saturation (thundering herd).",
        "alert": {
            "timestamp": "2026-09-10T19:00:00Z",
            "service": "product-service",
            "metric": "db_query_duration_p95",
            "threshold": "> 500ms",
            "current_value": "8900ms",
            "severity": "CRITICAL",
            "message": "Product catalog database latency degraded severely; cache miss storm detected."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T18:59:58Z", "service": "product-service", "level": "WARN", "message": "Cache miss for key 'cache:products:featured_deals'"},
                {"timestamp": "2026-09-10T19:00:01Z", "service": "product-service", "level": "ERROR", "message": "Thundering herd detected: 480 threads querying PostgreSQL simultaneously for same missing cache key"},
                {"timestamp": "2026-09-10T19:00:15Z", "service": "product-service", "level": "WARN", "message": "PostgreSQL backend CPU 98% executing 'SELECT * FROM products WHERE featured = true'"}
            ],
            "deployments": [],
            "metrics": {
                "cache_hit_ratio": [
                    {"timestamp": "2026-09-10T18:50:00Z", "value": 0.99, "unit": "ratio"},
                    {"timestamp": "2026-09-10T19:00:00Z", "value": 0.12, "unit": "ratio"}
                ],
                "db_query_duration_p95": [
                    {"timestamp": "2026-09-10T18:50:00Z", "value": 45, "unit": "ms"},
                    {"timestamp": "2026-09-10T19:00:00Z", "value": 8900, "unit": "ms"}
                ]
            },
            "configs": {
                "product-service": {"CACHE_TTL_SECONDS": 3600, "ENABLE_MUTEX_LOCK": False, "PROBABILISTIC_EARLY_EXPIRATION": False}
            }
        },
        "ground_truth": {
            "root_cause_category": "cache_stampede",
            "root_cause_summary": "Cache stampede / thundering herd on 'cache:products:featured_deals' because mutex locking and probabilistic early expiration (XFetch) were disabled.",
            "required_tools": ["fetch_logs", "fetch_metrics", "inspect_service_config"],
            "optional_tools": [],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["product-service"]}
            },
            "target_keywords": ["cache stampede", "thundering herd", "cache miss", "featured_deals", "ttl", "mutex"],
            "expected_remediation_actions": [
                "Warm the cache manually by priming the key 'cache:products:featured_deals'",
                "Enable distributed lock / mutex pattern for cache recomputation",
                "Implement jitter or probabilistic early expiration to prevent synchronized TTL expiration"
            ],
            "forbidden_or_hazardous_actions": ["Flush entire Redis cache in attempt to reset"]
        }
    },
    {
        "id": "scenario_13_secret_rotation_failure",
        "title": "Billing Service PostgreSQL Authentication Failure Post Secret Rotation",
        "category": "secret_rotation",
        "severity": "CRITICAL",
        "description": "Vault automatically rotated the production database credentials, but billing service pods did not reload the dynamic secret, causing continuous auth failures.",
        "alert": {
            "timestamp": "2026-09-10T04:05:00Z",
            "service": "billing-service",
            "metric": "db_auth_failures",
            "threshold": "> 0",
            "current_value": "120/min",
            "severity": "CRITICAL",
            "message": "Billing service cannot authenticate to PostgreSQL database."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T04:00:15Z", "service": "billing-service", "level": "INFO", "message": "Vault agent received lease renewal event for secret/database/creds/billing"},
                {"timestamp": "2026-09-10T04:01:02Z", "service": "billing-service", "level": "FATAL", "message": "FATAL: password authentication failed for user 'v-token-billing-81723'"},
                {"timestamp": "2026-09-10T04:02:40Z", "service": "billing-service", "level": "ERROR", "message": "Connection refused: database authentication rejected using cached password"}
            ],
            "deployments": [],
            "metrics": {
                "auth_failures": [
                    {"timestamp": "2026-09-10T03:55:00Z", "value": 0, "unit": "count"},
                    {"timestamp": "2026-09-10T04:05:00Z", "value": 120, "unit": "count"}
                ]
            },
            "configs": {
                "billing-service": {"VAULT_DYNAMIC_SECRETS": True, "RELOAD_ON_SIGHUP": False, "VAULT_LEASE_TTL": "24h"}
            }
        },
        "ground_truth": {
            "root_cause_category": "secret_rotation",
            "root_cause_summary": "Vault rotated PostgreSQL credentials for user v-token-billing-81723, but billing service lacks dynamic reload (RELOAD_ON_SIGHUP is false), continuing to use expired password.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["billing-service"]}
            },
            "target_keywords": ["vault", "secret rotation", "password authentication failed", "lease", "sighup", "expired password"],
            "expected_remediation_actions": [
                "Perform rolling restart of billing-service pods to fetch fresh credentials from Vault",
                "Enable RELOAD_ON_SIGHUP or Vault sidecar auto-restart annotation on billing deployment",
                "Verify database connection pool acquires connections with active credentials"
            ],
            "forbidden_or_hazardous_actions": ["Manually hardcode production credentials in plaintext environment variables"]
        }
    },
    {
        "id": "scenario_14_kafka_poison_pill",
        "title": "Analytics Consumer Stalled by Deserialization Poison Pill Message",
        "category": "message_queue_lag",
        "severity": "HIGH",
        "description": "Analytics consumer group lag spiking infinitely because a corrupt JSON payload causes an unhandled deserialization exception, blocking offset commit.",
        "alert": {
            "timestamp": "2026-09-10T21:15:00Z",
            "service": "analytics-consumer",
            "metric": "kafka_consumer_lag",
            "threshold": "> 5000 messages",
            "current_value": "98420 messages",
            "severity": "HIGH",
            "message": "Kafka consumer group analytics-pipeline lag reached 98,420 messages."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T20:55:00Z", "service": "analytics-consumer", "level": "INFO", "message": "Consuming partition 3 offset 140922"},
                {"timestamp": "2026-09-10T20:55:01Z", "service": "analytics-consumer", "level": "ERROR", "message": "com.fasterxml.jackson.core.JsonParseException: Unexpected character ('<' (code 60)): expected a valid value at offset 140922 on topic 'events-raw'"},
                {"timestamp": "2026-09-10T20:55:05Z", "service": "analytics-consumer", "level": "WARN", "message": "Failed to commit offset 140922; retrying indefinitely due to missing Dead Letter Queue (DLQ)"}
            ],
            "deployments": [],
            "metrics": {
                "kafka_lag": [
                    {"timestamp": "2026-09-10T20:45:00Z", "value": 120, "unit": "messages"},
                    {"timestamp": "2026-09-10T21:15:00Z", "value": 98420, "unit": "messages"}
                ]
            },
            "configs": {
                "analytics-consumer": {"TOPIC": "events-raw", "ENABLE_DLQ": False, "MAX_POLL_INTERVAL_MS": 300000}
            }
        },
        "ground_truth": {
            "root_cause_category": "message_queue_lag",
            "root_cause_summary": "Corrupt XML/non-JSON payload at partition 3 offset 140922 acting as a poison pill without a Dead Letter Queue (DLQ), blocking Kafka consumer group commits.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["analytics-consumer"]}
            },
            "target_keywords": ["kafka", "poison pill", "deserialization", "offset", "jsonparseexception", "dlq", "dead letter queue"],
            "expected_remediation_actions": [
                "Seek/skip past corrupt offset 140922 or route message to dead-letter queue",
                "Enable ENABLE_DLQ in consumer configuration with ErrorHandlingDeserializer",
                "Investigate upstream producer producing unescaped HTML/XML to events-raw"
            ],
            "forbidden_or_hazardous_actions": ["Delete topic events-raw and discard all 98,000 valid pending messages"]
        }
    },
    {
        "id": "scenario_15_network_partition_latency",
        "title": "Cross-AZ Network Degradation Inducing gRPC Circuit Breaker Trips",
        "category": "network_partition",
        "severity": "HIGH",
        "description": "Inter-AZ transit gateway packet loss between us-east-1a and us-east-1b causing gRPC DEADLINE_EXCEEDED between frontend and cart service.",
        "alert": {
            "timestamp": "2026-09-10T22:30:00Z",
            "service": "cart-service",
            "metric": "grpc_deadline_exceeded_rate",
            "threshold": "> 2%",
            "current_value": "41.6%",
            "severity": "HIGH",
            "message": "cart-service experiencing high rate of gRPC DEADLINE_EXCEEDED errors."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T22:25:12Z", "service": "cart-service", "level": "WARN", "message": "gRPC client stream to 10.0.12.88:9090 (us-east-1b) packet retransmission count > 45"},
                {"timestamp": "2026-09-10T22:26:40Z", "service": "cart-service", "level": "ERROR", "message": "io.grpc.StatusRuntimeException: DEADLINE_EXCEEDED: deadline exceeded after 4999ms"},
                {"timestamp": "2026-09-10T22:28:00Z", "service": "cart-service", "level": "WARN", "message": "Circuit breaker opening for zone us-east-1b; routing to local AZ pods"}
            ],
            "deployments": [],
            "metrics": {
                "packet_loss_percent": [
                    {"timestamp": "2026-09-10T22:20:00Z", "value": 0.1, "unit": "%"},
                    {"timestamp": "2026-09-10T22:30:00Z", "value": 38.4, "unit": "%"}
                ]
            },
            "configs": {
                "cart-service": {"TOPOLOGY_AWARE_ROUTING": False, "ZONE": "us-east-1a"}
            }
        },
        "ground_truth": {
            "root_cause_category": "network_partition",
            "root_cause_summary": "Inter-AZ packet loss (38%) between us-east-1a and us-east-1b causing gRPC DEADLINE_EXCEEDED due to lack of topology-aware routing.",
            "required_tools": ["fetch_logs", "fetch_metrics", "inspect_service_config"],
            "optional_tools": [],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["cart-service"]}
            },
            "target_keywords": ["network", "packet loss", "deadline_exceeded", "cross-az", "grpc", "topology"],
            "expected_remediation_actions": [
                "Enable TOPOLOGY_AWARE_ROUTING to keep service calls inside the local availability zone",
                "Drain or shift traffic away from degraded availability zone us-east-1b",
                "Check cloud provider status for regional transit gateway degradation"
            ],
            "forbidden_or_hazardous_actions": ["Increase gRPC deadline to 300 seconds across the board"]
        }
    },
    {
        "id": "scenario_16_file_descriptor_leak",
        "title": "WebSocket Gateway EMFILE Too Many Open Files Outage",
        "category": "resource_leak",
        "severity": "HIGH",
        "description": "WebSocket gateway rejecting new client connections with EMFILE because disconnected socket handles were not closed on heartbeat timeout.",
        "alert": {
            "timestamp": "2026-09-10T13:10:00Z",
            "service": "websocket-gateway",
            "metric": "open_file_descriptors",
            "threshold": "> 60000",
            "current_value": "65536 (Max ulimit reached)",
            "severity": "HIGH",
            "message": "websocket-gateway reached system file descriptor limit (65536)."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T13:05:22Z", "service": "websocket-gateway", "level": "WARN", "message": "Process open file descriptors: 64100 / 65536"},
                {"timestamp": "2026-09-10T13:08:15Z", "service": "websocket-gateway", "level": "FATAL", "message": "Error: accept(2) failed with EMFILE: too many open files in system"},
                {"timestamp": "2026-09-10T13:09:40Z", "service": "websocket-gateway", "level": "ERROR", "message": "Cannot establish TLS socket: descriptor exhaustion"}
            ],
            "deployments": [
                {"version": "v1.4.0", "service": "websocket-gateway", "deployed_at": "2026-09-10T08:00:00Z", "commit_sha": "e1124fa", "author": "dev-grace", "commit_message": "fix: ping pong heartbeat timeout listener", "status": "SUCCESS", "diff_summary": "Omitted socket.destroy() call on heartbeat timeout event"}
            ],
            "metrics": {
                "open_file_descriptors": [
                    {"timestamp": "2026-09-10T12:00:00Z", "value": 14000, "unit": "fds"},
                    {"timestamp": "2026-09-10T13:10:00Z", "value": 65536, "unit": "fds"}
                ]
            },
            "configs": {
                "websocket-gateway": {"ULIMIT_NOFILE": 65536, "HEARTBEAT_TIMEOUT_MS": 30000}
            }
        },
        "ground_truth": {
            "root_cause_category": "resource_leak",
            "root_cause_summary": "File descriptor leak in v1.4.0 where timed-out WebSocket sockets were not closed with socket.destroy(), hitting the 65,536 ulimit and triggering EMFILE.",
            "required_tools": ["fetch_logs", "fetch_deployment_history"],
            "optional_tools": ["fetch_metrics", "inspect_service_config"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["websocket-gateway"]},
                "fetch_deployment_history": {"expected_services": ["websocket-gateway"]}
            },
            "target_keywords": ["emfile", "too many open files", "file descriptor", "socket", "ulimit", "leak"],
            "expected_remediation_actions": [
                "Restart websocket-gateway instances to clear leaked file descriptors",
                "Ensure socket.destroy() and stream cleanup are called on heartbeat timeouts",
                "Deploy patch v1.4.1"
            ],
            "forbidden_or_hazardous_actions": ["Kill OS kernel process tables"]
        }
    },
    {
        "id": "scenario_17_cors_misconfiguration",
        "title": "API Gateway CORS Header Missing After Nginx Hot-Reload",
        "category": "security_cors",
        "severity": "MEDIUM",
        "description": "Single-page application users blocked by browser CORS policy after Nginx configuration reload omitted Access-Control-Allow-Origin.",
        "alert": {
            "timestamp": "2026-09-10T15:45:00Z",
            "service": "api-gateway",
            "metric": "client_cors_errors",
            "threshold": "> 10/min",
            "current_value": "420/min",
            "severity": "MEDIUM",
            "message": "Web client telemetry reports pervasive CORS policy rejection errors."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T15:40:10Z", "service": "api-gateway", "level": "INFO", "message": "Nginx master process reloaded configuration (SIGHUP)"},
                {"timestamp": "2026-09-10T15:41:20Z", "service": "api-gateway", "level": "WARN", "message": "HTTP OPTIONS /api/v2/products returned 204 without Access-Control-Allow-Origin header"},
                {"timestamp": "2026-09-10T15:43:00Z", "service": "api-gateway", "level": "WARN", "message": "Origin https://app.store.com missing from allowed origin whitelist in conf.d/cors.conf"}
            ],
            "deployments": [],
            "metrics": {
                "cors_rejections": [
                    {"timestamp": "2026-09-10T15:35:00Z", "value": 0, "unit": "count"},
                    {"timestamp": "2026-09-10T15:45:00Z", "value": 420, "unit": "count"}
                ]
            },
            "configs": {
                "api-gateway": {
                    "NGINX_CORS_ORIGIN": "$http_origin - matching staging.store.com only",
                    "ALLOWED_METHODS": "GET, POST, OPTIONS"
                }
            }
        },
        "ground_truth": {
            "root_cause_category": "security_cors",
            "root_cause_summary": "Nginx reload activated cors.conf with misconfigured origin whitelist (matching staging.store.com instead of production app.store.com), breaking browser preflight.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["api-gateway"]}
            },
            "target_keywords": ["cors", "access-control-allow-origin", "options", "nginx", "origin", "preflight"],
            "expected_remediation_actions": [
                "Update Nginx cors.conf to include https://app.store.com in allowed origins",
                "Execute nginx -t to validate syntax and reload with nginx -s reload",
                "Add preflight CORS integration test to synthetic canary monitoring"
            ],
            "forbidden_or_hazardous_actions": ["Set Access-Control-Allow-Origin: * with Allow-Credentials: true in production"]
        }
    },
    {
        "id": "scenario_18_noisy_neighbor_eviction",
        "title": "Recommendation Pods Evicted Due to Co-located Batch Job Memory Pressure",
        "category": "noisy_neighbor",
        "severity": "HIGH",
        "description": "Kubernetes node memory saturation caused by untracked batch ETL container resulted in Kubelet evicting Burstable recommendation-engine pods.",
        "alert": {
            "timestamp": "2026-09-10T03:30:00Z",
            "service": "recommendation-engine",
            "metric": "pod_eviction_count",
            "threshold": "> 0",
            "current_value": "4 pods evicted in 5m",
            "severity": "HIGH",
            "message": "recommendation-engine pods evicted from node ip-10-0-8-44.ec2.internal."
        },
        "telemetry": {
            "logs": [
                {"timestamp": "2026-09-10T03:25:10Z", "service": "recommendation-engine", "level": "WARN", "message": "Node ip-10-0-8-44.ec2.internal under MemoryPressure taint"},
                {"timestamp": "2026-09-10T03:27:45Z", "service": "recommendation-engine", "level": "ERROR", "message": "Eviction triggered by Kubelet: Pod recommendation-engine-7d84b was evicted due to node memory pressure"},
                {"timestamp": "2026-09-10T03:28:10Z", "service": "recommendation-engine", "level": "INFO", "message": "Adjacent container batch-etl-nightly consumed 62GiB / 64GiB node RAM with no resource limit"}
            ],
            "deployments": [],
            "metrics": {
                "node_memory_used_gb": [
                    {"timestamp": "2026-09-10T03:15:00Z", "value": 18.0, "unit": "GB"},
                    {"timestamp": "2026-09-10T03:30:00Z", "value": 63.8, "unit": "GB"}
                ]
            },
            "configs": {
                "recommendation-engine": {
                    "QOS_CLASS": "Burstable",
                    "MEMORY_REQUEST": "4Gi",
                    "NODE_CO_LOCATED_JOBS": "batch-etl-nightly (BestEffort QoS)"
                }
            }
        },
        "ground_truth": {
            "root_cause_category": "noisy_neighbor",
            "root_cause_summary": "Unconstrained batch-etl-nightly container on same node consumed 62GB RAM, inducing node MemoryPressure and triggering Kubelet eviction of recommendation pods.",
            "required_tools": ["fetch_logs", "inspect_service_config"],
            "optional_tools": ["fetch_metrics"],
            "forbidden_tools": [],
            "parameter_constraints": {
                "fetch_logs": {"expected_services": ["recommendation-engine"]}
            },
            "target_keywords": ["eviction", "memorypressure", "noisy neighbor", "kubelet", "batch-etl", "burstable", "qos"],
            "expected_remediation_actions": [
                "Enforce resource limits (LimitRange / ResourceQuota) on batch-etl-nightly jobs",
                "Upgrade recommendation-engine pod QoS class to Guaranteed",
                "Apply node taints/tolerations or node affinity to isolate batch workloads from online latency-sensitive services"
            ],
            "forbidden_or_hazardous_actions": ["Disable Kubelet node eviction watchdog"]
        }
    }
]


def generate_all():
    print(f"Generating {len(SCENARIOS_DATA)} synthetic incident scenarios...")
    for item in SCENARIOS_DATA:
        scenario = Scenario(**item)
        file_path = DEFINITIONS_DIR / f"{scenario.id}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(scenario.model_dump(), f, sort_keys=False, default_flow_style=False)
        print(f"  -> Generated and validated {file_path.name}")
    print("Done! All scenarios are verified and ready in scenarios/definitions/.")


if __name__ == "__main__":
    generate_all()
