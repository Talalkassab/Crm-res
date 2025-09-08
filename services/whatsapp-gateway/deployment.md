# WhatsApp Gateway Deployment Guide

## Production Deployment

### AWS ECS Fargate Deployment

1. **Build and Push Docker Image**
```bash
# Build for production
docker build -t whatsapp-gateway:latest .

# Tag for ECR
docker tag whatsapp-gateway:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/whatsapp-gateway:latest

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/whatsapp-gateway:latest
```

2. **ECS Task Definition**
```json
{
  "family": "whatsapp-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "whatsapp-gateway",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/whatsapp-gateway:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "WHATSAPP_API_VERSION", "value": "v19.0"}
      ],
      "secrets": [
        {"name": "WHATSAPP_WEBHOOK_SECRET", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:whatsapp-webhook-secret"},
        {"name": "WHATSAPP_VERIFY_TOKEN", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:whatsapp-verify-token"},
        {"name": "WHATSAPP_ACCESS_TOKEN", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:whatsapp-access-token"},
        {"name": "WHATSAPP_PHONE_NUMBER_ID", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:whatsapp-phone-id"},
        {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:redis-url"},
        {"name": "SUPABASE_URL", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:supabase-url"},
        {"name": "SUPABASE_ANON_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:supabase-key"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/whatsapp-gateway",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    },
    {
      "name": "celery-worker",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/whatsapp-gateway:latest",
      "command": ["celery", "-A", "src.services.queue", "worker", "--loglevel=info"],
      "secrets": [
        {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:redis-url"},
        {"name": "SUPABASE_URL", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:supabase-url"},
        {"name": "SUPABASE_ANON_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:supabase-key"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/whatsapp-gateway-worker",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **ECS Service Configuration**
```json
{
  "serviceName": "whatsapp-gateway",
  "cluster": "production",
  "taskDefinition": "whatsapp-gateway:1",
  "desiredCount": 2,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-12345", "subnet-67890"],
      "securityGroups": ["sg-whatsapp"],
      "assignPublicIp": "ENABLED"
    }
  },
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/whatsapp-gateway",
      "containerName": "whatsapp-gateway",
      "containerPort": 8000
    }
  ]
}
```

### Infrastructure Requirements

1. **Redis Cluster**
   - AWS ElastiCache Redis cluster
   - Multi-AZ for high availability
   - Minimum 1GB memory

2. **Load Balancer**
   - Application Load Balancer
   - Health check on `/health`
   - SSL termination

3. **Security Groups**
   - Inbound: Port 8000 from ALB
   - Outbound: HTTPS (443) to Meta APIs
   - Outbound: Redis port to ElastiCache

4. **Secrets Management**
   - AWS Secrets Manager for sensitive values
   - IAM roles with least privilege access

## Monitoring and Observability

### CloudWatch Dashboards

Create dashboards monitoring:
- Request rates and latencies
- Error rates by endpoint
- Queue depth and processing times
- Rate limit violations
- Circuit breaker state changes

### Alerts

Set up CloudWatch alarms for:
- High error rates (>5%)
- Queue depth > 1000
- Memory usage > 80%
- CPU usage > 70%
- Health check failures

### Log Analysis

- Structured JSON logs to CloudWatch Logs
- Correlation IDs for request tracing
- Log retention set to 30 days minimum

## Scaling Configuration

### Auto Scaling

```json
{
  "AutoScalingGroupName": "whatsapp-gateway-asg",
  "TargetCapacity": {
    "Min": 2,
    "Max": 10,
    "Desired": 2
  },
  "ScalingPolicies": [
    {
      "PolicyName": "CPUScaleUp",
      "TargetValue": 70.0,
      "ScaleOutCooldown": 300,
      "MetricType": "CPUUtilization"
    },
    {
      "PolicyName": "QueueDepthScaleUp", 
      "TargetValue": 500.0,
      "ScaleOutCooldown": 300,
      "MetricType": "Custom:QueueDepth"
    }
  ]
}
```

### Celery Worker Scaling

- Separate ECS service for Celery workers
- Scale based on queue depth metrics
- Use spot instances for cost optimization

## Disaster Recovery

### Backup Strategy
- Redis persistence enabled
- Supabase automatic backups
- ECS task definitions versioned

### Recovery Procedures
1. Restore Redis from snapshot
2. Deploy previous task definition version
3. Monitor health endpoints
4. Gradually increase traffic

### Testing
- Monthly DR drills
- Automated failover testing
- Performance impact assessment