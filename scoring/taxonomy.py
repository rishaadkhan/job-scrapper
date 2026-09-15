"""Curated backend engineering skills taxonomy and canonical aliases"""
from typing import Dict, List, Set

# Categorized taxonomy of backend engineering skills
BACKEND_TAXONOMY: Dict[str, List[str]] = {
    "Languages": [
        "Python", "Java", "Go", "Golang", "C++", "C#", ".NET", "TypeScript",
        "JavaScript", "Rust", "Scala", "Kotlin", "Ruby", "PHP", "SQL"
    ],
    "Frameworks & Runtimes": [
        "Spring", "Spring Boot", "Django", "FastAPI", "Flask", "Node.js",
        "Express", "NestJS", "Gin", "ASP.NET", "Ruby on Rails", "React",
        "Next.js", "Hibernate", "JPA"
    ],
    "Databases & Caching": [
        "PostgreSQL", "Postgres", "MySQL", "Redis", "MongoDB", "Cassandra",
        "DynamoDB", "Elasticsearch", "Kafka", "RabbitMQ", "SQLite", "Oracle",
        "Snowflake", "Memcached", "ClickHouse", "Neo4j"
    ],
    "Cloud & Infrastructure": [
        "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud",
        "Docker", "Kubernetes", "K8s", "Terraform", "CI/CD", "GitHub Actions",
        "Linux", "Helm", "Prometheus", "Grafana", "CloudFormation", "Lambda",
        "Serverless", "ECS", "EKS"
    ],
    "Architecture & Concepts": [
        "Microservices", "REST", "RESTful", "REST API", "GraphQL", "gRPC",
        "Distributed Systems", "Event-Driven", "Event Driven Architecture",
        "OOP", "Design Patterns", "System Design", "Concurrency",
        "Multithreading", "Data Structures", "Algorithms", "High Availability",
        "Scalability", "Low Latency", "API Design", "Unit Testing", "TDD",
        "Agile", "Scrum"
    ],
    "Data & Analytics": [
        "Apache Spark", "Spark", "Flink", "Airflow", "Hadoop", "Pandas",
        "NumPy", "ETL", "Data Pipelines", "BigQuery"
    ]
}

# Mapping of lowercase variations / aliases to clean canonical display name
CANONICAL_SKILL_MAP: Dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "go": "Go",
    "golang": "Go",
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "rust": "Rust",
    "scala": "Scala",
    "kotlin": "Kotlin",
    "ruby": "Ruby",
    "php": "PHP",
    "sql": "SQL",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node": "Node.js",
    "express": "Express",
    "nestjs": "NestJS",
    "gin": "Gin",
    "asp.net": "ASP.NET",
    "rails": "Ruby on Rails",
    "ruby on rails": "Ruby on Rails",
    "react": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "hibernate": "Hibernate",
    "jpa": "JPA",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "redis": "Redis",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch",
    "kafka": "Kafka",
    "apache kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "snowflake": "Snowflake",
    "memcached": "Memcached",
    "clickhouse": "ClickHouse",
    "aws": "AWS",
    "amazon web services": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "GitHub Actions",
    "linux": "Linux",
    "helm": "Helm",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "lambda": "AWS Lambda",
    "serverless": "Serverless",
    "microservices": "Microservices",
    "rest": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "distributed systems": "Distributed Systems",
    "event-driven": "Event-Driven Architecture",
    "event driven": "Event-Driven Architecture",
    "oop": "OOP",
    "design patterns": "Design Patterns",
    "system design": "System Design",
    "concurrency": "Concurrency",
    "multithreading": "Multithreading",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "high availability": "High Availability",
    "scalability": "Scalability",
    "low latency": "Low Latency",
    "api design": "API Design",
    "unit testing": "Unit Testing",
    "tdd": "TDD",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "flink": "Apache Flink",
    "airflow": "Apache Airflow",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "etl": "ETL",
    "data pipelines": "Data Pipelines",
    "bigquery": "BigQuery"
}


def get_all_taxonomy_terms() -> List[str]:
    """Returns all searchable terms sorted by descending length to match multi-word phrases first."""
    terms = list(CANONICAL_SKILL_MAP.keys())
    terms.sort(key=len, reverse=True)
    return terms
