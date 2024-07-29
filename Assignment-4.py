import boto3
from datetime import datetime, timedelta
from dateutil.tz import gettz

def list_ebs_volumes(region_name):
    ec2 = boto3.client('ec2', region_name)

    try:
        response = ec2.describe_volumes()
        volumes = response.get('Volumes', [])

        if volumes:
            print("EBS Volumes:")
            for volume in volumes:
                volume_id = volume['VolumeId']
                size = volume['Size']
                state = volume['State']
                print(f"Volume ID: {volume_id}, Size: {size} GiB, State: {state}")
                return volume_id
        else:
            print("No EBS volumes found.")
            size_gb = 10
            availability_zone = 'eu-north-1a'
            return create_ebs_volume(size_gb, availability_zone,region_name)

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def create_ebs_volume(size_gb, availability_zone, region_name):
    ec2 = boto3.client('ec2', region_name)

    try:
        response = ec2.create_volume(
            Size=size_gb,
            AvailabilityZone=availability_zone,
            VolumeType='gp2'
        )
        volume_id = response['VolumeId']
        print(f"Created EBS Volume with ID: {volume_id}")

        return volume_id

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def create_snapshot(ec2_client, volume_id, description='Snapshot created by boto3 script'):
    try:
        response = ec2_client.create_snapshot(
            VolumeId=volume_id,
            Description=description
        )
        snapshot_id = response['SnapshotId']
        print(f"Created snapshot with ID: {snapshot_id}")
        return snapshot_id
    except Exception as e:
        print(f"An error occurred while creating snapshot: {e}")
        return None

def list_and_delete_old_snapshots(ec2_client, days_old=30):
    cutoff_date = datetime.now(gettz('UTC')).isoformat() - timedelta(days=days_old)
    
    try:
        response = ec2_client.describe_snapshots(OwnerIds=['self'])
        snapshots = response.get('Snapshots', [])

        deleted_snapshots = []

        for snapshot in snapshots:
            snapshot_id = snapshot['SnapshotId']
            start_time = snapshot['StartTime']

            if start_time < cutoff_date:
                ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                print(f"Deleted snapshot with ID: {snapshot_id}")
                deleted_snapshots.append(snapshot_id)

        return deleted_snapshots
    except Exception as e:
        print(f"An error occurred while listing or deleting snapshots: {e}")
        return []
    
def lambda_handler(event, context):
    ec2_client = boto3.client('ec2', region_name='eu-north-1')
    volume_id = 'vol-0a3ab0aa93aa2239e'
    snapshot_id = create_snapshot(ec2_client, volume_id)
    
    if snapshot_id:
        deleted_snapshots = list_and_delete_old_snapshots(ec2_client, days_old=30)
        
        print(f"Snapshot created: {snapshot_id}")
        print(f"Snapshots deleted: {', '.join(deleted_snapshots)}")

    return {
        'statusCode': 200,
        'body': {
            'created_snapshot': snapshot_id,
            'deleted_snapshots': deleted_snapshots
        }
    }

if __name__ == "__main__":
    region_name='eu-north-1'
    volume_id=list_ebs_volumes(region_name)
    ec2_client =boto3.client('ec2', region_name)
    snapshot_id = create_snapshot(ec2_client, volume_id)
    
    if snapshot_id:
        deleted_snapshots = list_and_delete_old_snapshots(ec2_client, days_old=30)
        
        print(f"Snapshot created: {snapshot_id}")
        print(f"Snapshots deleted: {', '.join(deleted_snapshots)}")
