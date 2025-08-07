#!/bin/bash

# CloudFormation Demo Script for LocalStack
echo "🚀 Deploying CloudFormation Stack to LocalStack..."

# Configuration
STACK_NAME="localstack-demo-stack"
TEMPLATE_FILE="cloudformation-template.yaml"
REGION="us-east-1"
LOCALSTACK_ENDPOINT="http://localhost:4566"

# AWS CLI configuration for LocalStack
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"

# Check if LocalStack is running
echo "📡 Checking LocalStack status..."
if ! curl -s "$LOCALSTACK_ENDPOINT/_localstack/health" > /dev/null; then
    echo "❌ LocalStack is not running. Please start it with: docker-compose up -d"
    exit 1
fi
echo "✅ LocalStack is running"

# Deploy CloudFormation stack
echo "📦 Deploying CloudFormation stack..."
aws cloudformation deploy \
    --endpoint-url "$LOCALSTACK_ENDPOINT" \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment=dev

if [ $? -eq 0 ]; then
    echo "✅ Stack deployed successfully!"
    
    # Get stack outputs
    echo "📋 Stack Outputs:"
    aws cloudformation describe-stacks \
        --endpoint-url "$LOCALSTACK_ENDPOINT" \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
    
    # Test the deployed resources
    echo "🧪 Testing deployed resources..."
    
    # Get bucket name from stack output
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --endpoint-url "$LOCALSTACK_ENDPOINT" \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
        --output text)
    
    # Upload test file to S3
    echo "Testing S3 bucket: $BUCKET_NAME"
    echo "Hello from CloudFormation!" > cf-test-file.txt
    aws s3 cp cf-test-file.txt "s3://$BUCKET_NAME/" --endpoint-url "$LOCALSTACK_ENDPOINT"
    
    # List S3 objects
    aws s3 ls "s3://$BUCKET_NAME/" --endpoint-url "$LOCALSTACK_ENDPOINT"
    
    # Clean up test file
    rm cf-test-file.txt
    
    echo "🎉 CloudFormation demo completed successfully!"
else
    echo "❌ Stack deployment failed"
    exit 1
fi
