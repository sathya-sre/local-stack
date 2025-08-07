#!/usr/bin/env python3
"""
🚀 LocalStack Complete Demo
Comprehensive demonstration of AWS services in LocalStack

Services demonstrated:
- S3: Object storage with versioning
- SQS: Message queuing with attributes
- DynamoDB: NoSQL database
- SNS: Pub/Sub messaging
- Lambda: Serverless functions
- API Gateway: REST API endpoints

Run: python3 demo.py
"""

import boto3
import json
import time
import zipfile
import io
from botocore.config import Config

# 🔧 Configuration
LOCALSTACK_ENDPOINT = "http://localhost:4566"
AWS_REGION = "us-east-1"
AWS_ACCOUNT_ID = "000000000000"

config = Config(region_name=AWS_REGION, retries={'max_attempts': 0})

# 🎨 Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def check_localstack():
    """Check if LocalStack is running"""
    try:
        import requests
        response = requests.get(f"{LOCALSTACK_ENDPOINT}/_localstack/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print_success("LocalStack is running!")
            services = health_data.get('services', {})
            available_services = [s for s, status in services.items() if status == 'available']
            print_info(f"Available services: {', '.join(available_services)}")
            return True
        else:
            print_error("LocalStack health check failed")
            return False
    except Exception as e:
        print_error("LocalStack is not running")
        print_info("Start with: docker-compose up -d")
        return False

def create_client(service):
    """Create AWS service client"""
    return boto3.client(
        service,
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        config=config
    )

def demo_s3():
    """Demonstrate S3 operations"""
    print_header("S3 Object Storage Demo")
    s3 = create_client('s3')
    
    bucket_name = 'complete-demo-bucket'
    
    # Create bucket
    try:
        s3.create_bucket(Bucket=bucket_name)
        print_success(f"Created bucket: {bucket_name}")
    except Exception as e:
        if "BucketAlreadyExists" in str(e) or "BucketAlreadyOwnedByYou" in str(e):
            print_info(f"Using existing bucket: {bucket_name}")
        else:
            print_warning(f"Bucket issue: {e}")
    
    # Upload files
    files_to_upload = [
        ('demo.txt', 'Hello from LocalStack S3!', 'text/plain'),
        ('config.json', json.dumps({'app': 'demo', 'version': '1.0'}), 'application/json'),
        ('data.csv', 'name,age,city\nJohn,30,NYC\nJane,25,LA', 'text/csv')
    ]
    
    for filename, content, content_type in files_to_upload:
        s3.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=content,
            ContentType=content_type
        )
        print_success(f"Uploaded: {filename}")
    
    # List objects
    try:
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            print_info("Files in bucket:")
            for obj in response['Contents']:
                print(f"  📄 {obj['Key']} ({obj['Size']} bytes)")
    except Exception as e:
        print_warning(f"Could not list objects: {e}")
    
    # Enable versioning
    try:
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print_success("Enabled S3 versioning")
    except Exception as e:
        print_warning(f"Versioning issue: {e}")
    
    return bucket_name

def demo_sqs():
    """Demonstrate SQS operations"""
    print_header("SQS Message Queuing Demo")
    sqs = create_client('sqs')
    
    queue_name = 'complete-demo-queue'
    queue_url = None
    
    # Create queue - with improved error handling
    try:
        response = sqs.create_queue(QueueName=queue_name)
        queue_url = response['QueueUrl']
        print_success(f"Created queue: {queue_name}")
    except Exception as e:
        try:
            # Try to get existing queue
            response = sqs.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            print_info(f"Using existing queue: {queue_name}")
        except Exception as e2:
            print_error(f"Queue error: {e2}")
            return None
    
    if not queue_url:
        print_error("No queue URL available")
        return None
    
    # Send messages
    messages = [
        {'type': 'user_signup', 'user_id': '12345'},
        {'type': 'order_placed', 'order_id': 'ORD-001', 'amount': 99.99},
        {'type': 'notification', 'message': 'Demo notification'}
    ]
    
    for message_data in messages:
        try:
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message_data)
            )
            print_success(f"Sent message: {message_data['type']}")
        except Exception as e:
            print_warning(f"Failed to send message: {e}")
    
    # Receive messages
    print_info("Processing messages...")
    processed = 0
    for _ in range(5):  # Try up to 5 times
        try:
            response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
            if 'Messages' in response:
                message = response['Messages'][0]
                body = json.loads(message['Body'])
                print_info(f"Received: {body['type']}")
                
                # Delete message
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                print_success(f"Processed {body['type']}")
                processed += 1
            else:
                break
        except Exception as e:
            print_warning(f"Message processing error: {e}")
            break
    
    print_info(f"Successfully processed {processed} messages")
    return queue_url

def demo_dynamodb():
    """Demonstrate DynamoDB operations"""
    print_header("DynamoDB NoSQL Database Demo")
    dynamodb = create_client('dynamodb')
    
    table_name = 'complete-demo-table'
    
    # Create table
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'pk', 'KeyType': 'HASH'},
                {'AttributeName': 'sk', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'pk', 'AttributeType': 'S'},
                {'AttributeName': 'sk', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print_success(f"Created DynamoDB table: {table_name}")
    except Exception as e:
        if "ResourceInUseException" in str(e) or "already exists" in str(e):
            print_info(f"Using existing table: {table_name}")
        else:
            print_warning(f"Table creation issue: {e}")
    
    # Insert sample data
    sample_items = [
        {
            'pk': {'S': 'USER#12345'},
            'sk': {'S': 'PROFILE'},
            'name': {'S': 'John Doe'},
            'email': {'S': 'john@example.com'},
            'age': {'N': '30'}
        },
        {
            'pk': {'S': 'USER#12345'},
            'sk': {'S': 'ORDER#001'},
            'order_id': {'S': 'ORD-001'},
            'amount': {'N': '99.99'},
            'status': {'S': 'completed'}
        }
    ]
    
    for item in sample_items:
        try:
            dynamodb.put_item(TableName=table_name, Item=item)
            print_success(f"Added item: {item['sk']['S']}")
        except Exception as e:
            print_warning(f"Item insertion error: {e}")
    
    # Query data
    try:
        response = dynamodb.query(
            TableName=table_name,
            KeyConditionExpression='pk = :pk',
            ExpressionAttributeValues={':pk': {'S': 'USER#12345'}}
        )
        print_info(f"Found {response['Count']} items for user 12345")
        for item in response['Items']:
            sk = item['sk']['S']
            if sk == 'PROFILE':
                print(f"  👤 Profile: {item['name']['S']}")
            elif sk.startswith('ORDER#'):
                print(f"  🛒 Order: {item['order_id']['S']} - ${item['amount']['N']}")
    except Exception as e:
        print_warning(f"Query error: {e}")
    
    return table_name

def demo_sns():
    """Demonstrate SNS operations"""
    print_header("SNS Pub/Sub Messaging Demo")
    sns = create_client('sns')
    
    topic_name = 'complete-demo-topic'
    
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        print_success(f"Created SNS topic: {topic_name}")
        
        # Publish messages
        messages = [
            {'subject': 'Welcome!', 'message': 'Welcome to our demo!'},
            {'subject': 'Order Update', 'message': 'Your order has been processed.'},
            {'subject': 'System Alert', 'message': 'Demo completed successfully.'}
        ]
        
        for msg in messages:
            sns.publish(
                TopicArn=topic_arn,
                Subject=msg['subject'],
                Message=msg['message']
            )
            print_success(f"Published: {msg['subject']}")
        
        return topic_arn
        
    except Exception as e:
        print_warning(f"SNS demo error: {e}")
        return None

def demo_lambda():
    """Demonstrate Lambda operations"""
    print_header("Lambda Serverless Functions Demo")
    lambda_client = create_client('lambda')
    iam = create_client('iam')
    
    function_name = 'complete-demo-function'
    role_name = 'complete-demo-lambda-role'
    
    # Create IAM role
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        print_success(f"Created IAM role: {role_name}")
    except Exception as e:
        if "EntityAlreadyExists" in str(e):
            print_info(f"Using existing role: {role_name}")
        else:
            print_warning(f"Role creation issue: {e}")
    
    role_arn = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/{role_name}"
    
    # Lambda function code
    lambda_code = '''
import json
import time

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Hello from LocalStack Lambda!",
            'input': event,
            'timestamp': int(time.time())
        })
    }
'''
    
    # Create Lambda function
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('lambda_function.py', lambda_code)
        zip_buffer.seek(0)
        
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_buffer.read()},
            Description='Complete demo Lambda function'
        )
        print_success(f"Created Lambda function: {function_name}")
    except Exception as e:
        if "ResourceConflictException" in str(e):
            print_info(f"Using existing function: {function_name}")
        else:
            print_warning(f"Lambda creation issue: {e}")
    
    # Wait for Lambda function to be ready
    print_info("Waiting for Lambda function to be ready...")
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            state = response.get('Configuration', {}).get('State', 'Unknown')
            
            if state == 'Active':
                print_success("Lambda function is ready!")
                break
            elif state == 'Pending':
                print_info(f"Lambda function state: {state}, waiting... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print_warning(f"Lambda function in unexpected state: {state}")
                break
        except Exception as e:
            print_warning(f"Error checking Lambda state: {e}")
            time.sleep(1)
    
    # Test Lambda function
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps({'test': 'data', 'demo': True})
        )
        result = json.loads(response['Payload'].read().decode('utf-8'))
        print_success(f"Lambda invoked successfully!")
        print_info(f"Response: {result.get('body', 'No body')}")
    except Exception as e:
        if "Pending" in str(e):
            print_warning("Lambda function still not ready, skipping invocation test")
        else:
            print_warning(f"Lambda invocation error: {e}")
    
    return function_name

def demo_api_gateway():
    """Demonstrate API Gateway operations"""
    print_header("API Gateway REST API Demo")
    apigateway = create_client('apigateway')
    
    api_name = 'complete-demo-api'
    
    try:
        # Create REST API
        api_response = apigateway.create_rest_api(
            name=api_name,
            description='Complete Demo REST API'
        )
        api_id = api_response['id']
        print_success(f"Created API: {api_name}")
        
        # Get root resource
        resources = apigateway.get_resources(restApiId=api_id)
        root_resource_id = resources['items'][0]['id']
        
        # Create /health endpoint
        health_resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='health'
        )
        
        # Create GET method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=health_resource['id'],
            httpMethod='GET',
            authorizationType='NONE'
        )
        
        # Mock integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=health_resource['id'],
            httpMethod='GET',
            type='MOCK',
            requestTemplates={'application/json': '{"statusCode": 200}'}
        )
        
        # Method response
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=health_resource['id'],
            httpMethod='GET',
            statusCode='200'
        )
        
        # Integration response
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=health_resource['id'],
            httpMethod='GET',
            statusCode='200',
            responseTemplates={
                'application/json': '{"status": "healthy", "service": "complete-demo"}'
            }
        )
        
        # Deploy API
        apigateway.create_deployment(restApiId=api_id, stageName='dev')
        
        api_url = f"http://localhost:4566/restapis/{api_id}/dev/_user_request_"
        print_success(f"API deployed at: {api_url}")
        print_info(f"Health endpoint: {api_url}/health")
        
        return api_id
        
    except Exception as e:
        print_warning(f"API Gateway demo error: {e}")
        return None

if __name__ == "__main__":
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("🚀 LocalStack Complete Demo")
    print("=" * 50)
    print("Comprehensive AWS Services Demonstration")
    print(f"{Colors.END}")
    
    if not check_localstack():
        exit(1)
    
    try:
        # Run all demos
        bucket_name = demo_s3()
        queue_url = demo_sqs()
        table_name = demo_dynamodb()
        topic_arn = demo_sns()
        lambda_function = demo_lambda()
        api_id = demo_api_gateway()
        
        # Summary
        print_header("Demo Summary")
        print_success("LocalStack demo completed!")
        
        print(f"\n{Colors.BOLD}📋 Resources Created:{Colors.END}")
        print(f"  🪣 S3 Bucket: {bucket_name}")
        print(f"  📨 SQS Queue: {queue_url.split('/')[-1] if queue_url else 'Failed'}")
        print(f"  🗄️ DynamoDB Table: {table_name}")
        print(f"  📢 SNS Topic: {topic_arn.split(':')[-1] if topic_arn else 'Failed'}")
        print(f"  ⚡ Lambda Function: {lambda_function}")
        print(f"  🌐 API Gateway: {api_id if api_id else 'Failed'}")
        
        print(f"\n{Colors.BOLD}🔗 Next Steps:{Colors.END}")
        print(f"  📊 Start dashboard: python3 server.py")
        print(f"  ☁️  Deploy CloudFormation: make cf-deploy")
        print(f"  🏥 Check health: curl {LOCALSTACK_ENDPOINT}/_localstack/health")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Demo completed successfully!{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.END}")
    except Exception as e:
        print_error(f"Demo failed: {e}")
        print_warning("Make sure LocalStack is running: docker-compose up -d")
