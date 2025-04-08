import requests
from django.conf import settings
import time
from decouple import config

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
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from datetime import datetime, timezone
import hmac, hashlib

def gen_signature(url: str, method: str, secret: str, timestamp: str = datetime.now(timezone.utc).isoformat()) -> str:
    '''
    Generate the signature for an API call
    url: The URL to be called 
    method: HTTP method (GET, POST, PUT, DELETE)
    secret: API secret
    timestamp: ISO 8601 UTC formatted timestamp
    '''
    endpoint = urlparse(url).path
    payload = f"{method}{endpoint}{timestamp}".lower()
    sign = hmac.new(secret.encode(), payload.encode(), hashlib.sha1).hexdigest()
    return sign

class DataEnrichmentService:
    def __init__(self):
        self.api_keys = {
            "datagma": settings.DATAGMA_API_KEY,
            "hunter": settings.HUNTER_API_KEY,
            "apollo": settings.APOLLO_API_KEY,
            "prospeo": settings.PROSPEO_API_KEY,
            "contactout": settings.CONTACTOUT_API_KEY,
            "icypeas": settings.ICYPEAS_API_KEY,
            "anymailfinder": settings.ICYPEAS_API_KEY,
            "enrichso": settings.ENRICHSO_API_KEY,
            "tomba":settings.TOMBA_API_KEY,
        }

        self.api_secrets = {
            "tomba":config("TOMBA_secret")
        }

        self.tool_configs = {
            "hunter": {
                "icon": "🦊",
                "name": "Hunter",
                "endpoint": "https://api.hunter.io/v2/email-finder",
                "method": "GET",
                "requires_auth": True,
                "auth_type": "param",
                "auth_param": "api_key",
                "timeout": 30,
                "retry_count": 2
            },
            "datagma": {
                "icon": "⚡",
                "name": "Datagma",
                "endpoint": "https://gateway.datagma.net/api/ingress/v8/findEmail",
                "method": "GET",
                "requires_auth": True,
                "auth_type": "param",
                "auth_param": "apiId",
                "timeout": 30,
                "retry_count": 2
            },
            "apollo": {
                "icon": "🚀",
                "name": "Apollo",
                "endpoint": "https://api.apollo.io/api/v1/contacts",
                "method": "POST",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "x-api-key",
                "timeout": 30,
                "retry_count": 2
            },
            "prospeo": {
                "icon": "🎯",
                "name": "Prospeo",
                "endpoint_email": "https://api.prospeo.io/email-finder",
                "endpoint_mobile": "https://api.prospeo.io/mobile-finder",
                "method": "POST",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "X-KEY",
                "timeout": 30,
                "retry_count": 2
            },
            "contactout": {
                "icon": "👥",
                "name": "ContactOut",
                "endpoint": "https://api.contactout.com/v1/people/linkedin",
                "method": "GET",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "token",
                "timeout": 30,
                "retry_count": 2
            },
            "icypeas": {
                "icon": "🌱",
                "name": "Icypeas",
                "endpoint": "https://app.icypeas.com/api/email-search",
                "method": "POST",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "Authorization",
                "timeout": 30,
                "retry_count": 2
            },
            "anymailfinder": {
                "icon": "📧",
                "name": "Anymailfinder",
                "endpoint": "https://api.anymailfinder.com/v5.0/search/person.json",
                "method": "POST",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "Authorization",
                "timeout": 30,
                "retry_count": 2
            },
            "enrichso": {
                "icon": "🔍",
                "name": "Enrich.so",
                "endpoint": "https://api.enrich.so/v1/api/find-email",
                "method": "GET",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "Authorization",
                "timeout": 30,
                "retry_count": 2
            },
            "tomba": {
                "icon": "📬",
                "name": "Tomba",
                "endpoint": "https://api.tomba.io/v1/email-finder",
                "method": "GET",
                "requires_auth": True,
                "auth_type": "header",
                "auth_param": "Authorization",
                "timeout": 30,
                "retry_count": 2
            }
        }

    def format_response(self, tool: str, status: str, details: Optional[Dict] = None, error: Optional[str] = None) -> Dict:
        response = {
            "activity": "Email enrichment and qualification",
            "tool": f"{self.tool_configs[tool]['icon']} {self.tool_configs[tool]['name']}",
            "status": status
        }
        if details:
            response["details"] = details
        if error:
            response["error"] = error
        return response

    def make_request(self, tool: str, endpoint: str, params: Dict = None, headers: Dict = None, timeout: int = 30, method: str = None) -> Dict:
        headers = headers or {"accept": "application/json"}
        retry_count = self.tool_configs[tool].get("retry_count", 1)
        method = method or self.tool_configs[tool].get("method", "GET")
        if self.tool_configs[tool].get("requires_auth"):
            auth_type = self.tool_configs[tool].get("auth_type")
            auth_param = self.tool_configs[tool].get("auth_param")

            if auth_type == "header" and "Authorization" in auth_param:
                headers["Authorization"] = f"Bearer {self.api_keys[tool]}"

        for attempt in range(retry_count):
            try:
                if method == "GET":
                    response = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
                elif method == "POST":
                    response = requests.post(endpoint, json=params, headers=headers, timeout=timeout)

                print(f"Response from {tool} (Attempt {attempt + 1}): Status={response.status_code}")
                print(f"Response content: {response.text[:500]}")

                if response.status_code == 404:
                    return {"status": "not_found"}

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == retry_count - 1:
                    error_msg = str(e)
                    if hasattr(e, 'response') and e.response:
                        error_msg = f"{error_msg} - Response: {e.response.text}"
                    raise Exception(error_msg)
                time.sleep(1)

    def find_email(self, tool_name: str, contact_details: Dict) -> Dict:
        tool_name = tool_name.lower()

        if tool_name not in self.tool_configs:
            raise Exception(f"Tool {tool_name} is not supported for email lookup.")

        if tool_name == "hunter":
            try:
                params = {
                    "api_key": self.api_keys["hunter"],
                    "first_name": contact_details.get("first_name"),
                    "last_name": contact_details.get("last_name"),
                    "domain": contact_details.get("company_domain")
                }

                data = self.make_request("hunter", self.tool_configs["hunter"]["endpoint"], params)

                if data.get("data", {}).get("email"):
                    phone_numbers = []
                    if data["data"].get("phone"):
                        phone_numbers.append(data["data"]["phone"])
                    if data["data"].get("mobile"):
                        phone_numbers.append(data["data"]["mobile"])
                    if data["data"].get("direct_phone"):
                        phone_numbers.append(data["data"]["direct_phone"])

                    details = {
                        "full_name": f"{contact_details.get('first_name')} {contact_details.get('last_name')}",
                        "first_name": contact_details.get("first_name"),
                        "last_name": contact_details.get("last_name"),
                        "email": data["data"]["email"],
                        "location": data["data"].get("location"),
                        "company": contact_details.get("company_name"),
                        "position": data["data"].get("position"),
                        "linkedin": contact_details.get("linkedin_profile", "").split("/")[-1],
                        "twitter": data["data"].get("twitter"),
                        "phone_numbers": phone_numbers if phone_numbers else None,
                        "direct_phone": data["data"].get("direct_phone"),
                        "mobile_phone": data["data"].get("mobile"),
                        "confidence_score": data["data"].get("score", 0)
                    }
                    return self.format_response("hunter", "Email found", details)

                return self.format_response("hunter", "Email not found")

            except Exception as e:
                return self.format_response("hunter", "Error", error=str(e))

        elif tool_name == "datagma":
            try:
                params = {
                    "apiId": self.api_keys["datagma"],
                    "firstName": contact_details.get("first_name"),
                    "lastName": contact_details.get("last_name"),
                    "company": contact_details.get("company_domain")
                }

                if contact_details.get("linkedin_profile"):
                    params["linkedinUrl"] = contact_details["linkedin_profile"]

                data = self.make_request("datagma", self.tool_configs["datagma"]["endpoint"], params)

                if data.get("email"):
                    phone_numbers = []
                    if data.get("phone"):
                        phone_numbers.append(data["phone"])
                    if data.get("mobile"):
                        phone_numbers.append(data["mobile"])
                    if data.get("directPhone"):
                        phone_numbers.append(data["directPhone"])

                    details = {
                        "email": data["email"],
                        "first_name": data.get("firstName"),
                        "last_name": data.get("lastName", ""),
                        "full_name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
                        "company": data.get("company"),
                        "phone_numbers": phone_numbers if phone_numbers else None,
                        "direct_phone": data.get("directPhone"),
                        "mobile_phone": data.get("mobile"),
                        "confidence_score": data.get("confidenceScore"),
                        "source": data.get("source")
                    }
                    return self.format_response("datagma", "Email found", details)

                return self.format_response("datagma", "Email not found")

            except Exception as e:
                return self.format_response("datagma", "Error", error=str(e))

        elif tool_name == "apollo":
            try:
                headers = {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "x-api-key": self.api_keys["apollo"]
                }

                params = {
                    "first_name": contact_details.get("first_name"),
                    "last_name": contact_details.get("last_name"),
                    "organization_name": contact_details.get("company_name"),
                    "website_url": f"https://www.{contact_details.get('company_domain')}"
                }

                data = self.make_request(
                    "apollo",
                    self.tool_configs["apollo"]["endpoint"],
                    params=params,
                    headers=headers,
                    method="POST"
                )

                if data.get("contact", {}).get("email"):
                    phone_numbers = []
                    if data["contact"].get("phone_number"):
                        phone_numbers.append(data["contact"]["phone_number"])
                    if data["contact"].get("mobile_phone"):
                        phone_numbers.append(data["contact"]["mobile_phone"])
                    if data["contact"].get("direct_phone"):
                        phone_numbers.append(data["contact"]["direct_phone"])

                    details = {
                        "full_name": f"{contact_details.get('first_name')} {contact_details.get('last_name')}",
                        "first_name": data["contact"].get("first_name"),
                        "last_name": data["contact"].get("last_name"),
                        "email": data["contact"]["email"],
                        "location": data["contact"].get("location"),
                        "company": data["contact"].get("organization_name"),
                        "position": data["contact"].get("title"),
                        "linkedin": data["contact"].get("linkedin_url", "").split("/")[-1],
                        "phone_numbers": phone_numbers if phone_numbers else None,
                        "direct_phone": data["contact"].get("direct_phone"),
                        "mobile_phone": data["contact"].get("mobile_phone"),
                        "confidence_score": data["contact"].get("email_confidence", 0)
                    }
                    return self.format_response("apollo", "Email found", details)

                return self.format_response("apollo", "Email not found")

            except Exception as e:
                return self.format_response("apollo", "Error", error=str(e))

        elif tool_name == "prospeo":
            try:
                headers = {
                    "Content-Type": "application/json",
                    "X-KEY": self.api_keys["prospeo"]
                }

                email_params = {
                    "first_name": contact_details.get("first_name"),
                    "last_name": contact_details.get("last_name"),
                    "company": contact_details.get("company_domain")
                }

                print(f"Making email request to Prospeo with params: {email_params}")

                email_data = self.make_request(
                    "prospeo",
                    self.tool_configs["prospeo"]["endpoint_email"],
                    params=email_params,
                    headers=headers,
                    method="POST"
                )

                phone_numbers = []
                mobile_data = {}
                linkedin_url = contact_details.get("linkedin_profile")

                if linkedin_url:
                    if not linkedin_url.startswith("http"):
                        linkedin_url = f"https://linkedin.com/in/{linkedin_url}"

                    mobile_params = {
                        "url": linkedin_url
                    }

                    print(f"Making mobile request to Prospeo with params: {mobile_params}")

                    try:
                        mobile_data = self.make_request(
                            "prospeo",
                            self.tool_configs["prospeo"]["endpoint_mobile"],
                            params=mobile_params,
                            headers=headers,
                            method="POST"
                        )

                        if mobile_data.get("mobile"):
                            phone_numbers.append(mobile_data["mobile"])
                        if mobile_data.get("phone"):
                            phone_numbers.append(mobile_data["phone"])
                        if mobile_data.get("direct_phone"):
                            phone_numbers.append(mobile_data["direct_phone"])

                    except Exception as mobile_error:
                        print(f"Error fetching mobile data from Prospeo: {str(mobile_error)}")

                if email_data.get("email"):
                    details = {
                        "full_name": f"{contact_details.get('first_name')} {contact_details.get('last_name')}",
                        "first_name": contact_details.get("first_name"),
                        "last_name": contact_details.get("last_name"),
                        "email": email_data["email"],
                        "location": email_data.get("location"),
                        "company": contact_details.get("company_name"),
                        "position": email_data.get("position"),
                        "linkedin": linkedin_url.split("/")[-1] if linkedin_url else None,
                        "phone_numbers": phone_numbers if phone_numbers else None,
                        "direct_phone": mobile_data.get("direct_phone"),
                        "mobile_phone": mobile_data.get("mobile"),
                        "confidence_score": email_data.get("confidence", 0)
                    }
                    return self.format_response("prospeo", "Email found", details)

                return self.format_response("prospeo", "Email not found")

            except Exception as e:
                print(f"Error in Prospeo service: {str(e)}")
                return self.format_response("prospeo", "Error", error=str(e))

        elif tool_name == "contactout":
            try:
                headers = {
                    "authorization": "basic",
                    "token": self.api_keys["contactout"]
                }

                linkedin_url = contact_details.get("linkedin_profile")
                if not linkedin_url:
                    return self.format_response("contactout", "Error", error="LinkedIn profile URL is required")

                if not linkedin_url.startswith("http"):
                    linkedin_url = f"https://linkedin.com/in/{linkedin_url}"

                params = {
                    "profile": linkedin_url,
                    "include_phone": "true"
                }

                print(f"Making request to ContactOut with params: {params}")

                data = self.make_request(
                    "contactout",
                    self.tool_configs["contactout"]["endpoint"],
                    params=params,
                    headers=headers,
                    method="GET"
                )

                if data and isinstance(data, list) and len(data) > 0:
                    person = data[0]  

                    phone_numbers = []
                    if person.get("phone_numbers"):
                        phone_numbers.extend(person["phone_numbers"])
                    if person.get("mobile_phone"):
                        phone_numbers.append(person["mobile_phone"])
                    if person.get("direct_phone"):
                        phone_numbers.append(person["direct_phone"])

                    email = None
                    if person.get("emails"):
                        email = person["emails"][0] if person["emails"] else None

                    details = {
                        "full_name": person.get("full_name"),
                        "first_name": person.get("first_name"),
                        "last_name": person.get("last_name"),
                        "email": email,
                        "location": person.get("location"),
                        "company": person.get("current_company"),
                        "position": person.get("current_title"),
                        "linkedin": linkedin_url.split("/")[-1],
                        "phone_numbers": phone_numbers if phone_numbers else None,
                        "direct_phone": person.get("direct_phone"),
                        "mobile_phone": person.get("mobile_phone"),
                        "confidence_score": person.get("email_confidence", 0)
                    }
                    return self.format_response("contactout", "Email found", details)

                return self.format_response("contactout", "Email not found")

            except Exception as e:
                print(f"Error in ContactOut service: {str(e)}")
                return self.format_response("contactout", "Error", error=str(e))

        elif tool_name == "icypeas":
            try:
                timestamp = datetime.now(timezone.utc).isoformat()
                signature = gen_signature(
                    self.tool_configs["icypeas"]["endpoint"],
                    "POST",
                    self.api_keys["icypeas"],
                    timestamp
                )

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self.api_keys["icypeas"],
                    "X-Signature": signature,
                    "X-Timestamp": timestamp
                }

                params = {
                    "firstname": contact_details.get("first_name"),
                    "lastname": contact_details.get("last_name"),
                    "domainOrCompany": contact_details.get("company_domain") or contact_details.get("company_name")
                }

                if contact_details.get("linkedin_profile"):
                    linkedin_url = contact_details["linkedin_profile"]
                    if not linkedin_url.startswith("http"):
                        linkedin_url = f"https://linkedin.com/in/{linkedin_url}"
                    params["linkedinUrl"] = linkedin_url

                print(f"Making request to Icypeas with params: {params}")
                print(f"Headers: {headers}")

                data = self.make_request(
                    "icypeas",
                    self.tool_configs["icypeas"]["endpoint"],
                    params=params,
                    headers=headers,
                    method="POST"
                )

                if data.get("email"):
                    phone_numbers = []
                    if data.get("phoneNumbers"):
                        phone_numbers.extend(data["phoneNumbers"])
                    if data.get("mobilePhone"):
                        phone_numbers.append(data["mobilePhone"])
                    if data.get("directPhone"):
                        phone_numbers.append(data["directPhone"])

                    details = {
                        "full_name": f"{contact_details.get('first_name')} {contact_details.get('last_name')}",
                        "first_name": contact_details.get("first_name"),
                        "last_name": contact_details.get("last_name"),
                        "email": data["email"],
                        "location": data.get("location"),
                        "company": data.get("company"),
                        "position": data.get("position"),
                        "linkedin": contact_details.get("linkedin_profile", "").split("/")[-1],
                        "phone_numbers": phone_numbers if phone_numbers else None,
                        "direct_phone": data.get("directPhone"),
                        "mobile_phone": data.get("mobilePhone"),
                        "confidence_score": data.get("confidence", 0),
                        "source": "icypeas"
                    }
                    return self.format_response("icypeas", "Email found", details)

                return self.format_response("icypeas", "Email not found")

            except Exception as e:
                print(f"Error in Icypeas service: {str(e)}")
                return self.format_response("icypeas", "Error", error=str(e))

        elif tool_name == "anymailfinder":
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_keys['anymailfinder']}"
                }

                params = {
                    "domain": contact_details.get("company_domain"),
                    "first_name": contact_details.get("first_name"),
                    "last_name": contact_details.get("last_name"),
                    "company_name": contact_details.get("company_name"),
                    "full_name": f"{contact_details.get('first_name', '')} {contact_details.get('last_name', '')}".strip()
                }

                print(f"Making request to Anymailfinder with params: {params}")

                data = self.make_request(
                    "anymailfinder",
                    self.tool_configs["anymailfinder"]["endpoint"],
                    params=params,
                    headers=headers,
                    method="POST"
                )

                if data.get("results", {}).get("email"):
                    details = {
                        "full_name": params["full_name"],
                        "first_name": contact_details.get("first_name"),
                        "last_name": contact_details.get("last_name"),
                        "email": data["results"]["email"],
                        "company": contact_details.get("company_name"),
                        "validation": data["results"].get("validation"),
                        "phone_numbers": None,
                        "confidence_score": 100 if data["results"].get("validation") == "valid" else 0
                    }
                    return self.format_response("anymailfinder", "Email found", details)

                return self.format_response("anymailfinder", "Email not found")

            except Exception as e:
                print(f"Error in Anymailfinder service: {str(e)}")
                return self.format_response("anymailfinder", "Error", error=str(e))

        elif tool_name == "enrichso":
            try:
                headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {self.api_keys['enrichso']}"
                }

                full_name = f"{contact_details.get('first_name', '')} {contact_details.get('last_name', '')}".strip()
                if not full_name or not contact_details.get("company_domain"):
                    return self.format_response("enrichso", "Error", error="Full name and company domain are required for Enrich.so")

                params = {
                    "fullName": full_name,
                    "companyDomain": contact_details.get("company_domain")
                }

                print(f"Making request to Enrich.so with params: {params}")

                data = self.make_request(
                    "enrichso",
                    self.tool_configs["enrichso"]["endpoint"],
                    params=params,
                    headers=headers,
                    method="GET"
                )

                if data.get("email"):
                    details = {
                        "full_name": full_name,
                        "first_name": contact_details.get("first_name"),
                        "last_name": contact_details.get("last_name"),
                        "email": data["email"],
                        "company": contact_details.get("company_name"),
                        "phone_numbers": None,
                        "confidence_score": data.get("confidence", 0)
                    }
                    return self.format_response("enrichso", "Email found", details)

                return self.format_response("enrichso", "Email not found")

            except Exception as e:
                print(f"Error in Enrich.so service: {str(e)}")
                return self.format_response("enrichso", "Error", error=str(e))

        elif tool_name == "tomba":
            try:
                headers = {
                    "accept": "application/json",
                    "Authorization": f"Bearer {self.api_keys['tomba']}"
                }

                full_name = f"{contact_details.get('first_name', '')} {contact_details.get('last_name', '')}".strip()
                if not full_name or not contact_details.get("company_domain"):
                    return self.format_response("tomba", "Error", error="Full name and company domain are required for Tomba")

                params = {
                    "domain": contact_details.get("company_domain"),
                    "full_name": full_name,
                    "first_name": contact_details.get("first_name"),
                    "last_name": contact_details.get("last_name")
                }

                print(f"Making request to Tomba with params: {params}")

                data = self.make_request(
                    "tomba",
                    self.tool_configs["tomba"]["endpoint"],
                    params=params,
                    headers=headers,
                    method="GET"
                )

                if data.get("data", {}).get("email"):
                    details = {
                        "full_name": full_name,
                        "first_name": contact_details.get("first_name"),
                        "last_name": contact_details.get("last_name"),
                        "email": data["data"]["email"],
                        "company": contact_details.get("company_name"),
                        "phone_numbers": None,  
                        "confidence_score": data["data"].get("score", 0)
                    }
                    return self.format_response("tomba", "Email found", details)

                return self.format_response("tomba", "Email not found")

            except Exception as e:
                print(f"Error in Tomba service: {str(e)}")
                return self.format_response("tomba", "Error", error=str(e))

    def get_email_data(self, contact_details: Dict) -> Dict:
        results = []
        tools = ["hunter", "datagma", "apollo", "prospeo", "contactout", "icypeas", "anymailfinder", "enrichso", "tomba"]  # Added Tomba
        start_time = time.time()
        successful_tools = 0
        found_emails = 0
        catch_all_domains = 0
        found_email = None
        found_phones = []

        for tool in tools:
            try:
                result = self.find_email(tool, contact_details)
                if result["status"] == "Email found" and result.get("details", {}).get("email"):
                    successful_tools += 1
                    found_emails += 1
                    if not found_email:
                        found_email = result["details"]["email"]

                    
                    if result["details"].get("phone_numbers"):
                        found_phones.extend(result["details"]["phone_numbers"])
                    if result["details"].get("direct_phone"):
                        found_phones.append(result["details"]["direct_phone"])
                    if result["details"].get("mobile_phone"):
                        found_phones.append(result["details"]["mobile_phone"])

                elif result["status"] == "CatchAll domain":
                    successful_tools += 1
                    catch_all_domains += 1
                results.append(result)
            except Exception as e:
                results.append(self.format_response(
                    tool,
                    "Error",
                    error=str(e)
                ))

        found_phones = list(dict.fromkeys([phone for phone in found_phones if phone]))

        execution_time = time.time() - start_time

        return {
            "activity": "Email enrichment and qualification",
            "email": found_email,
            "phone_numbers": found_phones if found_phones else None,
            "input_data": contact_details,
            "total_tools_used": len(tools),
            "successful_tools": successful_tools,
            "found_emails": found_emails,
            "catch_all_domains": catch_all_domains,
            "execution_time": f"{execution_time:.2f} seconds",
            "results": results
        }