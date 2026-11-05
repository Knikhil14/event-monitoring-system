Directory structure:
└── knikhil14-event-monitoring-system/
    ├── README.md
    ├── ')
    ├── --- -name .py -print0
    ├── chat.json
    ├── Data_tracking
    ├── Initial_application_code_check
    ├── tatus --short --branch
    ├── applications/
    │   ├── dashboard/
    │   │   ├── app.py
    │   │   ├── Dockerfile
    │   │   └── requirements.txt
    │   ├── event-ingestor/
    │   │   ├── app.py
    │   │   ├── Dockerfile
    │   │   └── requirements.txt
    │   ├── event-processor/
    │   │   ├── Dockerfile
    │   │   ├── main.py
    │   │   └── requirements.txt
    │   ├── event-query-api/
    │   │   ├── Dockerfile
    │   │   ├── main.py
    │   │   └── requirements.txt
    │   └── notification-service/
    │       ├── Dockerfile
    │       ├── main.py
    │       └── requirements.txt
    ├── cicd/
    │   └── Jenkinsfile.groovy
    ├── docs/
    │   ├── event-monitoring-system-project-documentation.docx
    │   ├── generate_project_documents.py
    │   └── render_workflow_png.py
    ├── infrastructure/
    │   ├── kubernetes/
    │   │   ├── configmaps/
    │   │   │   ├── dashboard-config.yaml
    │   │   │   ├── db-config.yaml
    │   │   │   ├── processor-config.yaml
    │   │   │   ├── rabbitmq-config.yaml
    │   │   │   └── redis-config.yaml
    │   │   ├── deployments/
    │   │   │   ├── dashboard-deployment.yaml
    │   │   │   ├── event-ingestor-deployment.yaml
    │   │   │   ├── event-processor-deployment.yaml
    │   │   │   ├── event-query-api-deployment.yaml
    │   │   │   ├── notification-service-deployment.yaml
    │   │   │   ├── postgresql-statefulset.yaml
    │   │   │   ├── rabbitmq-deployment.yaml
    │   │   │   └── redis-deployment.yaml
    │   │   ├── ingress/
    │   │   │   └── ingress.yaml
    │   │   ├── jobs/
    │   │   │   └── db-init-job.yaml
    │   │   └── namespaces/
    │   │       └── event-namespace.yaml
    │   └── terraform/
    │       ├── main.tf
    │       ├── provider.tf
    │       ├── tfplan
    │       ├── variables.tf
    │       └── modules/
    │           ├── eks/
    │           │   ├── main.tf
    │           │   └── variables.tf
    │           ├── rds/
    │           │   ├── main.tf
    │           │   └── variables.tf
    │           ├── redis/
    │           │   ├── main.tf
    │           │   └── variables.tf
    │           └── vpc/
    │               ├── main.tf
    │               ├── outputs.tf
    │               └── variables.tf
    ├── monitoring/
    │   ├── grafana/
    │   │   └── dashboard.json
    │   └── prometheus/
    │       └── prometheus-config.yaml
    └── scripts/
        ├── build-and-push.sh
        ├── deploy.sh
        ├── monitor.sh
        ├── set-image-registry.sh
        ├── setup.sh
        └── test-events.sh
