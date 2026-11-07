"""Upload local raw and curated directories to S3 using the caller's AWS CLI/role credentials."""
import argparse
from pathlib import Path
import boto3
from config.settings import ROOT


def upload_tree(client, local_dir: Path, bucket: str, prefix: str):
    if not local_dir.exists():
        raise FileNotFoundError(local_dir)
    count=0
    for path in local_dir.rglob("*"):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel=path.relative_to(local_dir).as_posix()
        key=f"{prefix.rstrip('/')}/{rel}"
        client.upload_file(str(path), bucket, key)
        count += 1
        print(f"s3://{bucket}/{key}")
    return count


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bucket", default="smart-supply-chain-data-2026")
    p.add_argument("--region", default="ap-south-1")
    args=p.parse_args()
    s3=boto3.client("s3", region_name=args.region)
    for source in ["m5", "olist", "scms"]:
        n=upload_tree(s3, ROOT/"data"/"raw"/source, args.bucket, f"raw/{source}")
        print(f"Uploaded {n} raw files for {source}")
    for source in ["m5", "olist", "scms"]:
        n=upload_tree(s3, ROOT/"data"/"curated"/source, args.bucket, f"curated/{source}")
        print(f"Uploaded {n} curated files for {source}")

if __name__ == "__main__":
    main()
