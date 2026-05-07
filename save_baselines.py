"""Save drift baselines for all 3 collections."""

from dotenv import load_dotenv
from evaluation.drift_monitor import update_baseline

load_dotenv()

print("Saving drift baselines...")

update_baseline('mechanical_collection')
print("✓ mechanical_collection baseline saved")

update_baseline('software_collection')
print("✓ software_collection baseline saved")

update_baseline('support_collection')
print("✓ support_collection baseline saved")

print("\nAll baselines saved to evaluation/baselines/")
