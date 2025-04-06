import requests
from django.conf import settings
import time

class BetterContactAPI:
    def __init__(self):
        self.api_key = settings.BETTER_CONTACT_API_KEY
        self.base_url = "https://app.bettercontact.rocks/api/v2"
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key 
        }

    def enrich_single_contact(self, email):
        """
        Enrich a single contact using Better Contact API
        """
        try:
            enrich_url = f"{self.base_url}/async"

            payload = {
                "data": [
                    {
                        "email": email,
                        "custom_fields": {
                            "uuid": str(time.time()),
                            "list_name": "single_enrichment"
                        }
                    }
                ],
                "enrich_email_address": True,
                "enrich_phone_number": True
            }

            response = requests.post(enrich_url, json=payload, headers=self.headers)
            print("API Response:", response.text)

            response.raise_for_status()
            request_id = response.json().get('id')

            if not request_id:
                raise Exception("No request ID received from API")
            max_attempts = 10
            attempt = 0
            while attempt < max_attempts:
                result_url = f"{self.base_url}/async/{request_id}"
                result_response = requests.get(result_url, headers=self.headers)
                result_response.raise_for_status()
                result_data = result_response.json()
                if result_data.get('status') == 'terminated':
                    if result_data.get('data') and len(result_data['data']) > 0:
                        enriched_data = result_data['data'][0]
                        return {
                            'first_name': enriched_data.get('contact_first_name'),
                            'last_name': enriched_data.get('contact_last_name'),
                            'email': enriched_data.get('contact_email_address'),
                            'phone_number': enriched_data.get('contact_phone_number'),
                            'job_title': enriched_data.get('contact_job_title'),
                            'company_name': enriched_data.get('company_name'),
                            'linkedin_url': enriched_data.get('linkedin_url')
                        }
                    else:
                        raise Exception("No enriched data found")

                time.sleep(2)
                attempt += 1

            raise Exception("Enrichment timeout - took too long to process")

        except requests.exceptions.RequestException as e:
            print("Error details:", str(e))
            print("Response content:", e.response.text if hasattr(e, 'response') else "No response content")
            raise Exception(f"API request failed: {str(e)}")

import requests
from django.conf import settings

class DataEnrichmentService:
    def __init__(self):
        self.api_keys = {
            "datagma": settings.DATAGMA_API_KEY,
            "snov": settings.SNOV_API_KEY,
            "findthatlead": settings.FINDTHATLEAD_API_KEY,
            "hunter": settings.HUNTER_API_KEY,
            "apollo": settings.APOLLO_API_KEY,
            "societeinfo": settings.SOCIETEINFO_API_KEY,
            "prospeo": settings.PROSPEO_API_KEY,
            "contactout": settings.CONTACTOUT_API_KEY,
            "icypeas": settings.ICYPEAS_API_KEY,
            "enrow": settings.ENROW_API_KEY,
            "anymailfinder": settings.ANYMAILFINDER_API_KEY,
            "rocketreach": settings.ROCKETREACH_API_KEY,
            "people_data_labs": settings.PEOPLE_DATA_LABS_API_KEY,
            "enrichso": settings.ENRICHSO_API_KEY,
            "kendo": settings.KENDO_API_KEY,
            "nimbler": settings.NIMBLER_API_KEY,
            "tomba": settings.TOMBA_API_KEY,
            "trueinbox": settings.TRUEINBOX_API_KEY,
            "forager": settings.FORAGER_API_KEY,
            "usebouncer": settings.USEBOUNCER_API_KEY,
            "cleon1": settings.CLEON1_API_KEY,
        }

    def call_api(self, tool_name, endpoint, payload=None, method="GET"):
        """
        Generic method to call APIs for different tools.
        """
        api_key = self.api_keys.get(tool_name.lower())
        if not api_key:
            raise Exception(f"API key for {tool_name} is not configured.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = requests.get(endpoint, headers=headers, params=payload)
            elif method == "POST":
                response = requests.post(endpoint, headers=headers, json=payload)
            else:
                raise Exception("Unsupported HTTP method.")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request to {tool_name} failed: {str(e)}")

    def enrich_email(self, tool_name, email):
        """
        Enrich email using the specified tool.
        """
        if tool_name.lower() == "hunter":
            endpoint = "https://api.hunter.io/v2/email-finder"
            payload = {"email": email}
            return self.call_api(tool_name, endpoint, payload)

        elif tool_name.lower() == "snov":
            endpoint = "https://api.snov.io/v1/get-emails-from-names"
            payload = {"email": email}
            return self.call_api(tool_name, endpoint, payload)


        else:
            raise Exception(f"Tool {tool_name} is not supported for email enrichment.")

    def enrich_phone(self, tool_name, phone_number):
        """
        Enrich phone number using the specified tool.
        """
        if tool_name.lower() == "apollo":
            endpoint = "https://api.apollo.io/v1/phone-enrichment"
            payload = {"phone_number": phone_number}
            return self.call_api(tool_name, endpoint, payload)


        else:
            raise Exception(f"Tool {tool_name} is not supported for phone enrichment.")


import requests
from django.conf import settings

class DataEnrichmentService:
    def __init__(self):
        self.api_keys = {
            "datagma": settings.DATAGMA_API_KEY,
            "snov": settings.SNOV_API_KEY,
            "findthatlead": settings.FINDTHATLEAD_API_KEY,
            "hunter": settings.HUNTER_API_KEY,
            "apollo": settings.APOLLO_API_KEY,
            "societeinfo": settings.SOCIETEINFO_API_KEY,
            "prospeo": settings.PROSPEO_API_KEY,
            "contactout": settings.CONTACTOUT_API_KEY,
            "icypeas": settings.ICYPEAS_API_KEY,
            "enrow": settings.ENROW_API_KEY,
            "anymailfinder": settings.ANYMAILFINDER_API_KEY,
            "rocketreach": settings.ROCKETREACH_API_KEY,
            "people_data_labs": settings.PEOPLE_DATA_LABS_API_KEY,
            "enrichso": settings.ENRICHSO_API_KEY,
            "kendo": settings.KENDO_API_KEY,
            "nimbler": settings.NIMBLER_API_KEY,
            "tomba": settings.TOMBA_API_KEY,
            "trueinbox": settings.TRUEINBOX_API_KEY,
            "forager": settings.FORAGER_API_KEY,
            "usebouncer": settings.USEBOUNCER_API_KEY,
            "cleon1": settings.CLEON1_API_KEY,
        }

    def call_api(self, tool_name, endpoint, payload=None, method="GET"):
        """
        Generic method to call APIs for different tools.
        """
        api_key = self.api_keys.get(tool_name.lower())
        if not api_key:
            raise Exception(f"API key for {tool_name} is not configured.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = requests.get(endpoint, headers=headers, params=payload)
            elif method == "POST":
                response = requests.post(endpoint, headers=headers, json=payload)
            else:
                raise Exception("Unsupported HTTP method.")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request to {tool_name} failed: {str(e)}")

    def enrich_email(self, tool_name, email):
        """
        Enrich email using the specified tool.
        """
        if tool_name.lower() == "hunter":
            endpoint = f"https://api.hunter.io/v2/people/find"
            params = {
                "email": email,
                "api_key": self.api_keys["hunter"]  
            }

            try:
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()

                if "data" in data:
                    person_data = data["data"]
                    return {
                        "activity": "Email enrichment and qualification",
                        "tool": "⚡ Hunter",
                        "status": "Email found",
                        "details": {
                            "full_name": person_data.get("name", {}).get("fullName"),
                            "first_name": person_data.get("name", {}).get("givenName"),
                            "last_name": person_data.get("name", {}).get("familyName"),
                            "email": person_data.get("email"),
                            "location": person_data.get("location"),
                            "company": person_data.get("employment", {}).get("name"),
                            "position": person_data.get("employment", {}).get("title"),
                            "linkedin": person_data.get("linkedin", {}).get("handle"),
                            "twitter": person_data.get("twitter", {}).get("handle"),
                            "phone": person_data.get("phone")
                        }
                    }
                else:
                    return {
                        "activity": "Email enrichment and qualification",
                        "tool": "⚡ Hunter",
                        "status": "Email not found"
                    }

            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response.status_code == 404:
                    return {
                        "activity": "Email enrichment and qualification",
                        "tool": "⚡ Hunter",
                        "status": "Email not found"
                    }
                else:
                    raise Exception(f"Hunter API request failed: {str(e)}")


        else:
            raise Exception(f"Tool {tool_name} is not supported for email enrichment.")

    def enrich_phone(self, tool_name, phone_number):
        """
        Enrich phone number using the specified tool.
        """
        if tool_name.lower() == "apollo":
            endpoint = "https://api.apollo.io/v1/phone-enrichment"
            payload = {"phone_number": phone_number}
            return self.call_api(tool_name, endpoint, payload)



        else:
            raise Exception(f"Tool {tool_name} is not supported for phone enrichment.")