"""Execute an Athena SQL file and save query execution metadata/results via AWS CLI credentials."""
import argparse, time
from pathlib import Path
import boto3


def main():
    p=argparse.ArgumentParser()
    p.add_argument("sql_file")
    p.add_argument("--database", default="supply_chain_canonical")
    p.add_argument("--workgroup", default="primary")
    p.add_argument("--region", default="ap-south-1")
    p.add_argument("--results", default="s3://smart-supply-chain-data-2026/athena-results/")
    args=p.parse_args()
    sql=Path(args.sql_file).read_text(encoding="utf-8")
    athena=boto3.client("athena",region_name=args.region)
    statements=[part.strip() for part in sql.split(";") if part.strip()]
    for index, statement in enumerate(statements, start=1):
        response=athena.start_query_execution(
            QueryString=statement,
            QueryExecutionContext={"Database":args.database},
            WorkGroup=args.workgroup,
            ResultConfiguration={"OutputLocation":args.results},
        )
        qid=response["QueryExecutionId"]
        print(f"Statement {index}/{len(statements)} QueryExecutionId: {qid}")
        while True:
            status=athena.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
            state=status["State"]
            if state in {"SUCCEEDED","FAILED","CANCELLED"}:
                print("State:",state)
                if state != "SUCCEEDED": print("Reason:",status.get("StateChangeReason"))
                break
            time.sleep(2)
        if state != "SUCCEEDED": raise SystemExit(1)
        result=athena.get_query_results(QueryExecutionId=qid,MaxResults=1000)
        print("Rows returned (first page):",len(result.get("ResultSet",{}).get("Rows",[])))

if __name__ == "__main__":
    main()
