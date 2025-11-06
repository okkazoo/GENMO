#!/usr/bin/env python3
"""
GENMO Vast.ai Deployment Script
Automates deployment of GENMO web app to Vast.ai GPU instances
"""

import argparse
import json
import os
import subprocess
import sys
import time
import requests
from typing import Dict, List, Optional


class VastAIDeployer:
    """Vast.ai deployment manager"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://console.vast.ai/api/v0"
        self.headers = {
            "Accept": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make API request to Vast.ai"""
        url = f"{self.base_url}{endpoint}?api_key={self.api_key}"

        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            sys.exit(1)

    def search_offers(
        self,
        min_gpu_ram: int = 16,
        max_price: float = 0.50,
        gpu_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for available GPU instances

        Args:
            min_gpu_ram: Minimum GPU RAM in GB
            max_price: Maximum price per hour in USD
            gpu_name: Specific GPU name filter (e.g., "RTX 4090")
        """
        print(f"\n🔍 Searching for GPU instances...")
        print(f"   - Min GPU RAM: {min_gpu_ram} GB")
        print(f"   - Max price: ${max_price}/hr")
        if gpu_name:
            print(f"   - GPU filter: {gpu_name}")

        # Make search request - use correct Vast.ai API endpoint
        response = self._make_request(
            "GET",
            "/search/asks"
        )

        offers = response.get("offers", [])

        if not offers:
            print("❌ No instances found")
            return []

        # Filter offers based on criteria
        filtered_offers = []
        for offer in offers:
            # Check if rentable
            if not offer.get("rentable", False):
                continue

            # Check GPU RAM (in MB)
            gpu_ram_mb = offer.get("gpu_ram", 0)
            if gpu_ram_mb < min_gpu_ram * 1024:
                continue

            # Check price
            price = offer.get("dph_total", 999)
            if price > max_price:
                continue

            # Check GPU name if specified
            if gpu_name:
                offer_gpu = offer.get("gpu_name", "")
                if gpu_name.lower() not in offer_gpu.lower():
                    continue

            filtered_offers.append(offer)

        if not filtered_offers:
            print("❌ No instances found matching criteria")
            return []

        # Sort by price
        filtered_offers.sort(key=lambda x: x.get("dph_total", 999))

        print(f"\n✓ Found {len(filtered_offers)} matching instances (from {len(offers)} total)")
        return filtered_offers

    def display_offers(self, offers: List[Dict], limit: int = 5):
        """Display available offers"""
        print(f"\n📋 Top {min(limit, len(offers))} Offers:")
        print("-" * 100)
        print(f"{'ID':<10} {'GPU':<25} {'RAM':<8} {'Price/hr':<10} {'Location':<20}")
        print("-" * 100)

        for offer in offers[:limit]:
            print(
                f"{offer['id']:<10} "
                f"{offer.get('gpu_name', 'Unknown'):<25} "
                f"{offer.get('gpu_ram', 0) / 1024:.1f} GB  "
                f"${offer.get('dph_total', 0):<9.3f} "
                f"{offer.get('geolocation', 'Unknown'):<20}"
            )

    def create_instance(
        self,
        offer_id: int,
        docker_image: str = "genmo-webapp:latest",
        disk_space: int = 50
    ) -> Dict:
        """
        Create a new instance

        Args:
            offer_id: Offer ID from search results
            docker_image: Docker image to use
            disk_space: Disk space in GB
        """
        print(f"\n🚀 Creating instance from offer {offer_id}...")

        payload = {
            "client_id": "me",
            "image": docker_image,
            "disk": disk_space,
            "label": "genmo-webapp",
            "onstart": (
                "cd /workspace/GENMO && "
                "git pull && "
                "/workspace/docker-entrypoint.sh"
            ),
            "runtype": "ssh",
            "env": {
                "GENMO_MODE": "webapp"
            }
        }

        response = self._make_request(
            "PUT",
            f"/asks/{offer_id}/",
            json=payload
        )

        instance_id = response.get("new_contract")

        if not instance_id:
            print("❌ Failed to create instance")
            print(f"Response: {response}")
            sys.exit(1)

        print(f"✓ Instance created: {instance_id}")
        return response

    def get_instance_info(self, instance_id: int) -> Dict:
        """Get instance information"""
        response = self._make_request("GET", f"/instances/{instance_id}/")
        return response

    def wait_for_instance(self, instance_id: int, timeout: int = 300) -> Dict:
        """Wait for instance to be ready"""
        print(f"\n⏳ Waiting for instance {instance_id} to be ready...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            info = self.get_instance_info(instance_id)

            status = info.get("actual_status", "unknown")
            print(f"   Status: {status}", end="\r")

            if status == "running":
                print(f"\n✓ Instance is running!")
                return info

            time.sleep(5)

        print(f"\n❌ Timeout waiting for instance to start")
        sys.exit(1)

    def stop_instance(self, instance_id: int):
        """Stop an instance"""
        print(f"\n🛑 Stopping instance {instance_id}...")

        response = self._make_request(
            "DELETE",
            f"/instances/{instance_id}/"
        )

        print("✓ Instance stopped")
        return response

    def list_instances(self) -> List[Dict]:
        """List all active instances"""
        response = self._make_request("GET", "/instances/")
        return response.get("instances", [])


def deploy_to_vastai(
    api_key: str,
    min_gpu_ram: int = 16,
    max_price: float = 0.50,
    gpu_name: Optional[str] = None,
    auto_select: bool = False
):
    """
    Deploy GENMO to Vast.ai

    Args:
        api_key: Vast.ai API key
        min_gpu_ram: Minimum GPU RAM in GB
        max_price: Maximum price per hour
        gpu_name: Preferred GPU name
        auto_select: Automatically select cheapest option
    """
    deployer = VastAIDeployer(api_key)

    # Search for offers
    offers = deployer.search_offers(min_gpu_ram, max_price, gpu_name)

    if not offers:
        print("❌ No suitable instances found. Try adjusting search criteria.")
        sys.exit(1)

    # Display offers
    deployer.display_offers(offers)

    # Select offer
    if auto_select:
        selected_offer = offers[0]
        print(f"\n🎯 Auto-selected cheapest offer: {selected_offer['id']}")
    else:
        print("\n" + "=" * 100)
        offer_id = input("Enter offer ID to rent (or 'q' to quit): ").strip()

        if offer_id.lower() == 'q':
            print("Deployment cancelled")
            sys.exit(0)

        try:
            offer_id = int(offer_id)
            selected_offer = next(o for o in offers if o['id'] == offer_id)
        except (ValueError, StopIteration):
            print("❌ Invalid offer ID")
            sys.exit(1)

    # Create instance
    result = deployer.create_instance(selected_offer['id'])
    instance_id = result.get('new_contract')

    # Wait for instance to be ready
    info = deployer.wait_for_instance(instance_id)

    # Display connection info
    ssh_host = info.get('ssh_host')
    ssh_port = info.get('ssh_port')
    web_port = info.get('ports', {}).get('5000/tcp')

    print("\n" + "=" * 100)
    print("🎉 DEPLOYMENT SUCCESSFUL!")
    print("=" * 100)
    print(f"\n📊 Instance ID: {instance_id}")
    print(f"🖥️  GPU: {selected_offer.get('gpu_name')}")
    print(f"💰 Cost: ${selected_offer.get('dph_total'):.3f}/hour")
    print(f"\n🌐 Web Interface: http://{ssh_host}:{web_port or 5000}")
    print(f"🔐 SSH Access: ssh -p {ssh_port} root@{ssh_host}")
    print(f"\n💡 To stop the instance and avoid charges:")
    print(f"   python deploy_vastai.py --stop {instance_id}")
    print("=" * 100)

    return instance_id


def list_instances(api_key: str):
    """List all running instances"""
    deployer = VastAIDeployer(api_key)
    instances = deployer.list_instances()

    if not instances:
        print("No active instances")
        return

    print("\n📋 Active Instances:")
    print("-" * 100)
    print(f"{'ID':<10} {'Status':<15} {'GPU':<25} {'Cost/hr':<10}")
    print("-" * 100)

    for inst in instances:
        print(
            f"{inst['id']:<10} "
            f"{inst.get('actual_status', 'unknown'):<15} "
            f"{inst.get('gpu_name', 'Unknown'):<25} "
            f"${inst.get('dph_total', 0):<9.3f}"
        )


def stop_instance(api_key: str, instance_id: int):
    """Stop a running instance"""
    deployer = VastAIDeployer(api_key)
    deployer.stop_instance(instance_id)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy GENMO Video-to-3D to Vast.ai"
    )

    parser.add_argument(
        "--api-key",
        help="Vast.ai API key (or set VASTAI_API_KEY env var)"
    )

    parser.add_argument(
        "--min-gpu-ram",
        type=int,
        default=16,
        help="Minimum GPU RAM in GB (default: 16)"
    )

    parser.add_argument(
        "--max-price",
        type=float,
        default=0.50,
        help="Maximum price per hour in USD (default: 0.50)"
    )

    parser.add_argument(
        "--gpu",
        help="Preferred GPU name (e.g., 'RTX 4090', 'A6000')"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically select cheapest option"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List active instances"
    )

    parser.add_argument(
        "--stop",
        type=int,
        metavar="INSTANCE_ID",
        help="Stop an instance by ID"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("VASTAI_API_KEY")

    if not api_key:
        print("❌ Error: Vast.ai API key required")
        print("   Set via --api-key or VASTAI_API_KEY environment variable")
        print("\n   Get your API key from: https://console.vast.ai/account/")
        sys.exit(1)

    # Execute command
    if args.list:
        list_instances(api_key)
    elif args.stop:
        stop_instance(api_key, args.stop)
    else:
        deploy_to_vastai(
            api_key,
            min_gpu_ram=args.min_gpu_ram,
            max_price=args.max_price,
            gpu_name=args.gpu,
            auto_select=args.auto
        )


if __name__ == "__main__":
    main()
