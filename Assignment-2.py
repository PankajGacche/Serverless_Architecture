import boto3
import os
import uuid
from datetime import datetime, timedelta
from datetime import datetime, timezone, timedelta

def Create_S3_Bucket(s3_client,region_name):
    bucket_name = 's3-'+str(uuid.uuid4())[:5] 

    s3_client.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={
        'LocationConstraint': region_name
        },
        ObjectOwnership='BucketOwnerEnforced',
    )

    s3_client.put_bucket_website(
    Bucket=bucket_name,
    WebsiteConfiguration={
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    }
    )

    print(f'Created S3 bucket for web app static files: {bucket_name}')
    return bucket_name

def create_old_files(file_paths, days_old):
    old_time = datetime.now() - timedelta(days=days_old)
    for file_path in file_paths:
        os.utime(file_path, (old_time.timestamp(), old_time.timestamp()))

def upload_files(s3_client,file_paths, bucket_name):
    for file_path in file_paths:
        s3_key = os.path.basename(file_path)

        last_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

        try:
            s3_client.upload_file(
                file_path, 
                bucket_name, 
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'original-modification-date': last_modified_time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
            )
            print(f"Successfully uploaded {file_path} to {bucket_name}/{s3_key} with original modification date")
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

def delete_old_objects_based_on_metadata(s3_client,bucket_name, days_old):
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(days=days_old)
    continuation_token = None
    deleted_objects = []

    while True:
        list_params = {'Bucket': bucket_name}
        if continuation_token:
            list_params['ContinuationToken'] = continuation_token
        
        response = s3_client.list_objects_v2(**list_params)
        
        if 'Contents' not in response:
            print("No objects found in the bucket.")
            break
        
        for obj in response['Contents']:
            object_key = obj['Key']

            head_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
            metadata = head_response.get('Metadata', {})
            original_modification_date_str = metadata.get('original-modification-date', None)
            
            if original_modification_date_str:
                original_modification_date = datetime.strptime(original_modification_date_str, '%Y-%m-%d %H:%M:%S')

                if original_modification_date.tzinfo is None:
                    original_modification_date = original_modification_date.replace(tzinfo=timezone.utc)
                
                print(f"Object found: {object_key} (Original Modification Date: {original_modification_date})")

                if original_modification_date < cutoff_time:
                    s3_client.delete_object(Bucket=bucket_name, Key=object_key)
                    deleted_objects.append(object_key)
                    print(f"Deleted: {object_key}")
        
        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    if not deleted_objects:
        print("No objects older than 30 days were found.")
    else:
        print("Deleted objects:")
        for key in deleted_objects:
            print(f" - {key}")

def lambda_handler(event, context):
    bucket_name = 's3-bb797'
    days_old = 30
    
    now = datetime.now(timezone.utc)
    cutoff_time = now - timedelta(days=days_old)
    continuation_token = None
    deleted_objects = []

    while True:
        list_params = {'Bucket': bucket_name}
        if continuation_token:
            list_params['ContinuationToken'] = continuation_token
        
        response = s3_client.list_objects_v2(**list_params)
        
        if 'Contents' not in response:
            print("No objects found in the bucket.")
            break
        
        for obj in response['Contents']:
            object_key = obj['Key']

            head_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
            metadata = head_response.get('Metadata', {})
            original_modification_date_str = metadata.get('original-modification-date', None)
            
            if original_modification_date_str:
                original_modification_date = datetime.strptime(original_modification_date_str, '%Y-%m-%d %H:%M:%S')
                
                if original_modification_date.tzinfo is None:
                    original_modification_date = original_modification_date.replace(tzinfo=timezone.utc)
                
                print(f"Object found: {object_key} (Original Modification Date: {original_modification_date})")
                
                if original_modification_date < cutoff_time:
                    s3_client.delete_object(Bucket=bucket_name, Key=object_key)
                    deleted_objects.append(object_key)
                    print(f"Deleted: {object_key}")
        
        if response.get('IsTruncated'):
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    if not deleted_objects:
        print("No objects older than 30 days were found.")
    else:
        print("Deleted objects:")
        for key in deleted_objects:
            print(f" - {key}")

    return {
        'statusCode': 200,
        'body': f"Deleted objects: {', '.join(deleted_objects) if deleted_objects else 'None'}"
    }

if __name__ == "__main__":
    region_name='eu-north-1'
    file_paths = ['D:/Pankaj/Study/Hero_Vired/Lambda Function/Assignement-2/file1.txt', 'D:/Pankaj/Study/Hero_Vired/Lambda Function/Assignement-2/file2.txt', 'D:/Pankaj/Study/Hero_Vired/Lambda Function/Assignement-2/file3.txt']
    session = boto3.Session(
    aws_access_key_id=os.getenv('Access_Key'),
    aws_secret_access_key=os.getenv('Secret_Key'),
    region_name=region_name
    )
    s3_client = session.client('s3')
    
    bucket_name=Create_S3_Bucket(s3_client,region_name)
    create_old_files(file_paths[:2], 30)  
    upload_files(s3_client,file_paths, bucket_name)