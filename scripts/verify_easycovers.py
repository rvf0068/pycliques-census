"""Replay every positive order-10 easy-cover witness, without searching."""
from staged import census, checked_records
from easy_cover_certificates import verify_record

def main():
    _, source, _ = census(10)
    records = checked_records(10, "easycovers", source)
    proved = 0
    for i, record in sorted(records.items()):
        if record["status"] != "DIVERGENT":
            continue
        print(f"Checking original index {i}", flush=True)
        if not verify_record(record):
            raise SystemExit(f"INVALID certificate for original index {i}")
        proved += 1
    print(f"Verified {proved} positive records of {len(records)} total")

if __name__ == "__main__":
    main()
