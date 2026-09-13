pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io/your-dockerhub-user'
        NAMESPACE = 'event-monitoring'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Syntax Check') {
            steps {
                sh '''
                python -m compileall applications/event-ingestor
                python -m compileall applications/event-processor
                python -m compileall applications/event-query-api
                python -m compileall applications/notification-service
                python -m compileall applications/dashboard
                '''
            }
        }

        stage('Build Images') {
            steps {
                script {
                    def services = [
                        'event-ingestor',
                        'event-processor',
                        'event-query-api',
                        'notification-service',
                        'dashboard'
                    ]

                    for (service in services) {
                        sh """
                        docker build \
                          -t ${DOCKER_REGISTRY}/${service}:${BUILD_NUMBER} \
                          -t ${DOCKER_REGISTRY}/${service}:latest \
                          applications/${service}
                        """
                    }
                }
            }
        }

        stage('Push Images') {
            steps {
                script {
                    def services = [
                        'event-ingestor',
                        'event-processor',
                        'event-query-api',
                        'notification-service',
                        'dashboard'
                    ]

                    for (service in services) {
                        sh """
                        docker push ${DOCKER_REGISTRY}/${service}:${BUILD_NUMBER}
                        docker push ${DOCKER_REGISTRY}/${service}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                bash scripts/set-image-registry.sh "${DOCKER_REGISTRY}"
                bash scripts/deploy.sh

                kubectl set image deployment/event-ingestor \
                  event-ingestor=${DOCKER_REGISTRY}/event-ingestor:${BUILD_NUMBER} \
                  -n ${NAMESPACE}
                kubectl set image deployment/event-processor \
                  event-processor=${DOCKER_REGISTRY}/event-processor:${BUILD_NUMBER} \
                  -n ${NAMESPACE}
                kubectl set image deployment/event-query-api \
                  event-query-api=${DOCKER_REGISTRY}/event-query-api:${BUILD_NUMBER} \
                  -n ${NAMESPACE}
                kubectl set image deployment/notification-service \
                  notification-service=${DOCKER_REGISTRY}/notification-service:${BUILD_NUMBER} \
                  -n ${NAMESPACE}
                kubectl set image deployment/dashboard \
                  dashboard=${DOCKER_REGISTRY}/dashboard:${BUILD_NUMBER} \
                  -n ${NAMESPACE}

                kubectl rollout status deployment/event-ingestor -n ${NAMESPACE}
                kubectl rollout status deployment/event-processor -n ${NAMESPACE}
                kubectl rollout status deployment/event-query-api -n ${NAMESPACE}
                kubectl rollout status deployment/notification-service -n ${NAMESPACE}
                kubectl rollout status deployment/dashboard -n ${NAMESPACE}
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                kubectl run smoke-test-${BUILD_NUMBER} \
                  --rm -i --restart=Never \
                  --namespace ${NAMESPACE} \
                  --image=curlimages/curl:8.8.0 \
                  -- http://event-ingestor-service/health
                '''
            }
        }
    }

    post {
        failure {
            sh '''
            kubectl rollout undo deployment/event-ingestor -n ${NAMESPACE} || true
            kubectl rollout undo deployment/event-processor -n ${NAMESPACE} || true
            kubectl rollout undo deployment/event-query-api -n ${NAMESPACE} || true
            kubectl rollout undo deployment/notification-service -n ${NAMESPACE} || true
            kubectl rollout undo deployment/dashboard -n ${NAMESPACE} || true
            '''
        }
    }
}
