#!/usr/bin/env python3

import csv
import requests
import uuid
from datetime import datetime
from typing import Dict, Any

# Configuration
CONFIG = {
    "CPFQDN": "cloudpath.my.domain",  # Cloudpath FQDN or IP address
    "CPUSER": "your Cloudpath admin username/email",
    "CPPASSWORD": "password",
    "SZKEYFILE": "nameofyourdpskexportfile.csv",  # CSV file with DPSKs exported from SZ
    "CPDPSKGUID": "yourDPSKpoolGuid"  # Cloudpath DPSK Pool Guid
}

class CloudpathDPSKMigration:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.timestamp = datetime.now().strftime("%m-%d-%Y")

    def read_csv_file(self) -> Dict[str, Dict[str, str]]:
        """Read the CSV file and process its contents."""
        print("Reading CSV file", end="")
        result = {}
        with open(self.config["SZKEYFILE"], mode="r", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = row.pop("Passphrase")
                row["uuid"] = f"SZ2CP-{self.timestamp}-{uuid.uuid4()}"
                result[key] = row
                print(".", end="")
        print()
        return result

    def get_cp_token(self) -> str:
        """Get API token from Cloudpath."""
        url = f"https://{self.config['CPFQDN']}/admin/publicApi/token"
        body = {"userName": self.config["CPUSER"], "password": self.config["CPPASSWORD"]}
        response = requests.post(url, json=body)
        return response.json()['token']

    def create_dpsks(self, old_dpsks: Dict[str, Dict[str, str]]):
        """Create DPSKs in Cloudpath."""
        url = f"https://{self.config['CPFQDN']}/admin/publicApi/dpskPools/{self.config['CPDPSKGUID']}/dpsks"
        for key, value in old_dpsks.items():
            token = self.get_cp_token()
            print(f'Creating EDPSK {key} ', end="")
            
            headers = {"Content-Type": "application/json", "Authorization": token}
            body = {
                "name": value["uuid"],
                "passphrase": key,
                "vlanid": value["VLAN ID"],
                "thirdPartyId": value["User Name"]
            }
            response = requests.post(url, headers=headers, json=body)
            print(response)
        print()

    def run(self):
        """Main execution method."""
        sz_keys = self.read_csv_file()
        self.create_dpsks(sz_keys)

def main():
    migration = CloudpathDPSKMigration(CONFIG)
    migration.run()

if __name__ == "__main__":
    main()
