# import requests
# import pandas as pd
# from django.conf import settings

# class BetterContactAPI:
#     def __init__(self):
#         self.api_key = settings.BETTER_CONTACT_API_KEY
#         self.base_url = "https://api.bettercontact.com/v1"
#         self.headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }

#     def enrich_single_contact(self, email):
#         """
#         Enrich a single contact using Better Contact API
#         """
#         endpoint = f"{self.base_url}/person-enrichment"
#         payload = {
#             "email": email
#         }

#         try:
#             response = requests.post(endpoint, headers=self.headers, json=payload)
#             response.raise_for_status()
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             raise Exception(f"API request failed: {str(e)}")

#     def enrich_bulk_contacts(self, file_path):
#         """
#         Enrich multiple contacts using Better Contact API
#         """
#         endpoint = f"{self.base_url}/bulk-enrichment"

#         try:
#             with open(file_path, 'rb') as file:
#                 files = {
#                     'file': file
#                 }
#                 response = requests.post(endpoint, headers=self.headers, files=files)
#                 response.raise_for_status()
#                 return response.json()
#         except requests.exceptions.RequestException as e:
#             raise Exception(f"Bulk API request failed: {str(e)}")