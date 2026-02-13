pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.io'
        AWS_REGION = 'us-east-1'
        KUBE_CONFIG = credentials('kubeconfig')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                        cd applications/event-ingestor
                        python -m pytest tests/ --cov=app --cov-report=xml
                        '''
                    }
                }
                stage('Security Scan') {
                    steps {
                        sh '''
                        docker scan your-registry/event-ingestor:latest
                        trivy image your-registry/event-ingestor:latest
                        '''
                    }
                }
            }
        }
        
        stage('Build & Push Docker') {
            steps {
                script {
                    def services = ['event-ingestor', 'event-processor', 'dashboard']
                    for (service in services) {
                        sh """
                        docker build -t ${DOCKER_REGISTRY}/${service}:${BUILD_NUMBER} \
                                     -t ${DOCKER_REGISTRY}/${service}:latest \
                                     applications/${service}/
                        docker push ${DOCKER_REGISTRY}/${service}:${BUILD_NUMBER}
                        docker push ${DOCKER_REGISTRY}/${service}:latest
                        """
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                # Update image tags in Kubernetes manifests
                sed -i "s|image:.*event-ingestor.*|image: ${DOCKER_REGISTRY}/event-ingestor:${BUILD_NUMBER}|g" \
                    infrastructure/kubernetes/deployments/event-ingestor-deployment.yaml
                
                # Apply manifests
                kubectl apply -f infrastructure/kubernetes/ --recursive
                
                # Wait for rollout
                kubectl rollout status deployment/event-ingestor -n event-monitoring
                kubectl rollout status deployment/event-processor -n event-monitoring
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                # Run integration tests
                cd tests/integration
                python -m pytest test_api_integration.py -v
                
                # Load test
                locust -f load_test.py --host=http://events.kollurinikhil.2bd.net --users 100 --spawn-rate 10 --run-time 1m
                '''
            }
        }
        
        stage('Monitoring') {
            steps {
                sh '''
                # Check application health
                curl -f http://events.kollurinikhil.2bd.net/health || exit 1
                
                # Check metrics endpoint
                curl http://events.kollurinikhil.2bd.net/metrics | jq .
                '''
            }
        }
    }
    
    post {
        success {
            slackSend(
                color: 'good',
                message: "Deployment Successful: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "Deployment Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
            sh '''
            # Rollback to previous version
            kubectl rollout undo deployment/event-ingestor -n event-monitoring
            kubectl rollout undo deployment/event-processor -n event-monitoring
            '''
        }
    }
}