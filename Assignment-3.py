import boto3
import os
import uuid
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_s3_bucket(s3,region_name, bucket_name, encryption_type=None):
    
    try:
        if region_name:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': region_name
                }
            )
        else:
            s3.create_bucket(Bucket=bucket_name)
        
        print(f'Bucket {bucket_name} created.')

        if encryption_type:
            s3.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': encryption_type
                            }
                        }
                    ]
                }
            )
            print(f'Server-side encryption {encryption_type} enabled for bucket {bucket_name}.')
        else:
            print(f'No server-side encryption set for bucket {bucket_name}.')
            remove_default_encryption(bucket_name)

    except NoCredentialsError:
        print("AWS credentials not found.")
    except PartialCredentialsError:
        print("Incomplete AWS credentials.")
    except ClientError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def remove_default_encryption(bucket_name):
    s3 = boto3.client('s3')

    try:
        s3.delete_bucket_encryption(Bucket=bucket_name)
        print(f"Default encryption removed from bucket: {bucket_name}")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
            print(f"No server-side encryption configuration found for bucket: {bucket_name}")
        else:
            print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def lambda_handler(event, context):
    s3 = boto3.client('s3')

    try:
        response = s3.list_buckets()
        buckets = response['Buckets']
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        return {
            'statusCode': 500,
            'body': 'Error listing buckets'
        }
    
    unencrypted_buckets = []
    
    for bucket in buckets:
        bucket_name = bucket['Name']
        try:
            encryption = s3.get_bucket_encryption(Bucket=bucket_name)
            if not encryption.get('ServerSideEncryptionConfiguration'):
                unencrypted_buckets.append(bucket_name)
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                unencrypted_buckets.append(bucket_name)
            else:
                logger.error(f"Error checking encryption for bucket {bucket_name}: {e}")

    if unencrypted_buckets:
        logger.info("Unencrypted buckets:")
        for bucket in unencrypted_buckets:
            logger.info(bucket)
    else:
        logger.info("All buckets have server-side encryption enabled.")

    return {
        'statusCode': 200,
        'body': 'Process completed successfully'
    }

def get_bucket_encryption(bucket_name):
    s3 = boto3.client('s3')

    try:
        response = s3.get_bucket_encryption(Bucket=bucket_name)
        encryption_config = response.get('ServerSideEncryptionConfiguration', None)
        
        if encryption_config:
            print(f"Encryption is enabled: {encryption_config}")
        else:
            print("No encryption configuration found.")

    except s3.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
            print("No encryption configuration found.")
        else:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    region_name='eu-north-1'
    session = boto3.Session(
    aws_access_key_id=os.getenv('Access_Key'),
    aws_secret_access_key=os.getenv('Secret_Key'),
    region_name=region_name
    )
    s3_client = session.client('s3')
    
    buckets = [
        {"name": 's3-'+str(uuid.uuid4())[:5], "encryption": "AES256"},
        {"name": 's3-'+str(uuid.uuid4())[:5], "encryption": None},
        {"name": 's3-'+str(uuid.uuid4())[:5], "encryption": "aws:kms"}
    ]
    
    for bucket in buckets:
        create_s3_bucket(s3_client,region_name,bucket['name'], bucket['encryption'])