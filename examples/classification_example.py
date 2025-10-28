"""
Example: Get Call Classification with Pretty-Printed Tag Names

This example demonstrates how to retrieve a call classification with
human-readable tag names using the get_call_classification_pretty() method.

The method returns the classification with an additional 'TagsPretty' field
that contains a dictionary mapping group names to tag names.
"""

import os
from enreachvoice import Client

# Initialize client
USERNAME = os.getenv('ENREACH_USERNAME', 'your-username')
PASSWORD = os.getenv('ENREACH_PASSWORD', 'your-secret-key')

client = Client(
    username=USERNAME,
    password=PASSWORD,
    discovery_url='https://qas-discovery.enreachvoice.com'  # Optional: for test environments
)

# Example call ID (replace with your actual call ID)
call_id = '48c1222c-88ab-40c0-8693-a76d05b33814'

# Get classification with pretty-printed tags
classification = client.get_call_classification_pretty(call_id)

if classification:
    print("=" * 70)
    print("CLASSIFICATION DETAILS")
    print("=" * 70)
    
    print(f"\nClassification ID: {classification['Id']}")
    print(f"Schema ID: {classification['TagSchemaId']}")
    print(f"Modified: {classification['Modified']}")
    print(f"Created by: {classification['CreatedBy']}")
    
    if classification.get('Note'):
        print(f"Note: {classification['Note']}")
    
    print("\n" + "=" * 70)
    print("TAGS (Pretty-Printed)")
    print("=" * 70)
    
    # Display the pretty-printed tags
    for group_name, value in classification['TagsPretty'].items():
        if isinstance(value, list):
            # Multi-selection group
            print(f"\n{group_name}:")
            for tag in value:
                print(f"  • {tag}")
        else:
            # Single-selection group
            print(f"\n{group_name}: {value}")
    
    print("\n" + "=" * 70)
    print("RAW DATA (for comparison)")
    print("=" * 70)
    print("\nRaw TagSelections:")
    for selection in classification['TagSelections']:
        print(f"  TagId: {selection['TagId']}")
    
else:
    print(f"No classification found for call {call_id}")

# Example output:
# ======================================================================
# CLASSIFICATION DETAILS
# ======================================================================
#
# Classification ID: f1590ff9-05b4-f011-9949-00505689303a
# Schema ID: d045db9b-28a7-4b49-b5d8-fd4b4469c148
# Modified: 2025-10-28T13:57:03.4Z
# Created by: 83ea47cd-d58e-f011-9949-00505689303a
#
# ======================================================================
# TAGS (Pretty-Printed)
# ======================================================================
#
# Reason for call: Sales demo
#
# Customer type: Prospect
#
# Products:
#   • Hammers
#   • Screwdrivers
#
# ======================================================================
# RAW DATA (for comparison)
# ======================================================================
#
# Raw TagSelections:
#   TagId: 2556
#   TagId: 2560
#   TagId: 2563
#   TagId: 2569
