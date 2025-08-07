#!/bin/bash

# LocalStack Demo Setup Script
echo "Setting up LocalStack demo environment..."

# AWS CLI endpoint for LocalStack
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"
LOCALSTACK_ENDPOINT="http://localhost:4566"

# Create S3 bucket
echo "Creating S3 bucket..."
aws --endpoint-url=$LOCALSTACK_ENDPOINT s3 mb s3://my-test-bucket

# List S3 buckets
echo "Listing S3 buckets..."
aws --endpoint-url=$LOCALSTACK_ENDPOINT s3 ls

# Upload a test file
echo "Test file content" > test-file.txt
aws --endpoint-url=$LOCALSTACK_ENDPOINT s3 cp test-file.txt s3://my-test-bucket/

# List objects in bucket
echo "Listing objects in bucket..."
aws --endpoint-url=$LOCALSTACK_ENDPOINT s3 ls s3://my-test-bucket/

# Create SQS queue
echo "Creating SQS queue..."
aws --endpoint-url=$LOCALSTACK_ENDPOINT sqs create-queue --queue-name my-test-queue

# List SQS queues
echo "Listing SQS queues..."
aws --endpoint-url=$LOCALSTACK_ENDPOINT sqs list-queues

# Send message to queue
echo "Sending message to SQS queue..."
QUEUE_URL=$(aws --endpoint-url=$LOCALSTACK_ENDPOINT sqs get-queue-url --queue-name my-test-queue --output text --query 'QueueUrl')
aws --endpoint-url=$LOCALSTACK_ENDPOINT sqs send-message --queue-url $QUEUE_URL --message-body "Hello from LocalStack!"

# Receive message from queue
echo "Receiving message from SQS queue..."
aws --endpoint-url=$LOCALSTACK_ENDPOINT sqs receive-message --queue-url $QUEUE_URL

echo "LocalStack demo setup complete!"
