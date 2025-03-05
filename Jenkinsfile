pipeline {
    agent any

    environment {
        DOCKER_REPOSITORY = 'gloticker/ticker-scrap'
        REGISTRY_CREDENTIAL = 'gloticker-docker-hub'
        dockerImage = ''
        DEPLOY_URL = 'https://scrap.gloticker.live'
    }

    parameters {
        string(name: 'DOCKER_NETWORK', defaultValue: 'proxy-network', description: 'docker network name')
        string(name: 'IMAGE_NAME', defaultValue: 'ticker-scrap', description: 'docker image name')
        choice(name: 'ENV_TYPE', choices: ['dev', 'prod'], description: 'Choose the environment type')
    }

    stages {
        stage('environment setup') {
            steps {
                script {
                    env.BRANCH_NAME = params.ENV_TYPE == 'prod' ? 'main' : 'dev'
                }
            }
        }

        stage('git clone') {
            steps {
                git branch: "${env.BRANCH_NAME}",
                    credentialsId: 'github-token',
                    url: 'https://github.com/gloticker/ticker-scrap'
            }
        }

        stage('image build & docker-hub push') {
            steps {
                script {
                    docker.withRegistry('', REGISTRY_CREDENTIAL) {
                        sh 'docker buildx create --use --name mybuilder'
                        sh "docker buildx build --platform linux/amd64 -t $DOCKER_REPOSITORY:$BUILD_NUMBER --push ."
                        sh "docker buildx build --platform linux/amd64 -t $DOCKER_REPOSITORY:latest --push ."
                    }
                }
            }
        }

        stage('previous docker rm') {
            steps {
                sshagent(credentials: ['deepeet-ubuntu', 'gloticker-ubuntu']) {
                    sh """
                        ssh -o ProxyCommand="ssh -W %h:%p -p ${PROXMOX_SSH_PORT} ${PROXMOX_SERVER_ACCOUNT}@${PROXMOX_SERVER_URI}" \
                        -o StrictHostKeyChecking=no ${GLOTICKER_SERVER_ACCOUNT}@${GLOTICKER_SERVER_IP} \
                        '
                        docker ps -q --filter "name=ticker-scrap" | xargs -r docker stop
                        docker ps -aq --filter "name=ticker-scrap" | xargs -r docker rm -f
                        docker images ${DOCKER_REPOSITORY}:${env.IMAGE_NAME}-latest -q | xargs -r docker rmi
                        '
                    """
                }
            }
        }

        stage('docker-hub pull') {
            steps {
                sshagent(credentials: ['deepeet-ubuntu', 'gloticker-ubuntu']) {
                    sh """
                        ssh -o ProxyCommand="ssh -W %h:%p -p ${PROXMOX_SSH_PORT} ${PROXMOX_SERVER_ACCOUNT}@${PROXMOX_SERVER_URI}" \
                        -o StrictHostKeyChecking=no ${GLOTICKER_SERVER_ACCOUNT}@${GLOTICKER_SERVER_IP} 'docker pull ${DOCKER_REPOSITORY}:latest'
                    """
                }
            }
        }

        stage('service start') {
            steps {
                withCredentials([file(credentialsId: 'gloticker-ticker-scrap-credentials', variable: 'ENV_CREDENTIALS')]) {
                    sshagent(credentials: ['deepeet-ubuntu', 'gloticker-ubuntu']) {
                        sh """
                            scp -o ProxyCommand="ssh -W %h:%p -p ${PROXMOX_SSH_PORT} \
                            ${PROXMOX_SERVER_ACCOUNT}@${PROXMOX_SERVER_URI}" \
                            -o StrictHostKeyChecking=no $ENV_CREDENTIALS ${GLOTICKER_SERVER_ACCOUNT}@${GLOTICKER_SERVER_IP}:~/gloticker-ticker-scrap-credentials
                        """

                        sh """
                            ssh -o ProxyCommand="ssh -W %h:%p -p ${PROXMOX_SSH_PORT} \
                            ${PROXMOX_SERVER_ACCOUNT}@${PROXMOX_SERVER_URI}" \
                            -o StrictHostKeyChecking=no ${GLOTICKER_SERVER_ACCOUNT}@${GLOTICKER_SERVER_IP} \
                            '
                            echo "===== 📌 .env 📌 ====="
                            cat ~/gloticker-ticker-scrap-credentials
                            echo "==================================="

                            SERVER_PORT=\$(grep SERVER_PORT ~/gloticker-ticker-scrap-credentials | cut -d "=" -f2)

                            echo "===== 📌 SERVER_PORT 📌 ====="
                            echo "Extracted SERVER_PORT: \$SERVER_PORT"
                            echo "===================================="

                            docker run -i -e TZ=America/New_York --env-file ~/gloticker-ticker-scrap-credentials \\
                            --name ${params.IMAGE_NAME} --network ${params.DOCKER_NETWORK} \\
                            -p \${SERVER_PORT}:\${SERVER_PORT} \\
                            --restart unless-stopped \\
                            -d ${DOCKER_REPOSITORY}:latest

                            rm -f ~/gloticker-ticker-scrap-credentials
                            '
                        """
                    }
                }
            }
        }

        stage('service test & alert send') {
            steps {
                sh """
                    #!/bin/bash

                    for retry_count in \$(seq 20)
                    do
                        if curl -s "${DEPLOY_URL}/ping" > /dev/null
                        then
                            echo "Build Success!"
                            curl -d '{"title":"ticker-scrap ${env.BRANCH_NAME} release:$BUILD_NUMBER","body":"Deployment Succeeded🚀"}' -H "Content-Type: application/json" -X POST ${PUSH_ALERT}
                            exit 0
                        fi

                        if [ \$retry_count -eq 20 ]
                        then
                            echo "Build Failed!"
                            curl -d '{"title":"ticker-scrap ${env.BRANCH_NAME} release:$BUILD_NUMBER","body":"Deployment Failed😢"}' -H "Content-Type: application/json" -X POST ${PUSH_ALERT}
                            exit 1
                        fi

                        echo "The server is not alive yet. Retry health check in 5 seconds..."
                        sleep 5
                    done
                """
            }
        }
    }
}
