from pathlib import Path
from typing import List, Optional, Any, Dict
import pandas as pd
import requests

BASE_URL = "https://api.fda.gov/drug/event.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
# DATA_DIR is the directory where raw data will be stored, two parent folders up from this file

def build_query(generic_name:str, brand_name:str) -> str:
    gen = generic_name.upper().strip() # Converts generic name to uppercase and removes leading/trailing whitespace
    brand = brand_name.upper().strip()
    query_parts = [
        f'patient.drug.openfda.generic_name.exact:"{gen}"',
        f'patient.drug.openfda.brand_name.exact:"{brand}"',
        f'patient.drug.medicinalproduct.exact:"{gen}"',
        f'patient.drug.medicinalproduct.exact:"{brand}"',
    ]
    return f"({' + '.join(query_parts)})"
# Builds a query string for the FDA API based on generic and brand names inputted by user

def fetch_data(query: str, limit: int = 1000, skip: int = 0) -> List[Dict[str, Any]]:
    param = {"search": query, "limit": min(limit, 1000), "skip": skip}
    try:
        response = requests.get(BASE_URL, params=param, timeout=15)
        # Sends a GET request to the FDA API with the specified query and pagination parameters
        if response.status_code == 404:
            return []
        response.raise_for_status()
        # Raises an exception if the response status code indicates an error
        payload = response.json()
        return payload.get("results", [])
    # Returns the list of results from the API response after parsing the JSON payload into python-readable format
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        # Prints an error message and re-raises the exception
        raise

def age_normalization(age_val: Optional[str], unit_code: Optional[str]) -> Optional[float]:
    if not age_val:
        return None
    try:
        age = float(age_val)
        #801=years, 802=months, 803=weeks, 804=days
        if unit_code == "801" or unit_code is None:
            return age
        if unit_code == "802":
            return round(age / 12.0, 2)
        if unit_code == "803":
            return round(age / 52.14, 2)
        if unit_code == "804":
            return round(age / 364.25, 2)
        #rounds and return the age in years based on the unit code
    except ValueError:
        return None
    # Returns None if the age value cannot be converted to a float

def parse_records(raw_records: List[Dict[str, Any]], target_generic: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    sex_map = {"1": "Male", "2": "Female", "0": "Unknown"}
    for record in raw_records:
        # Extracts the safety report ID, receive date, and seriousness status
        report_id = record.get("safetyreportid")
        receive_date = record.get("recieveddate")
        is_serious = True if record.get("serious") == "1" else False

        patient = record.get("patient", {})
        raw_age = patient.get("patientonsetage")
        age_unit = patient.get("patientonsetageunit")
        patient_age = age_normalization(raw_age, age_unit)
        patient_sex = sex_map.get(patient.get("patientsex", ""), "Unknown")
        # Extracts the patient's age and sex from the patient data
        drugs = record.get("drug", [])
        is_suspect = False
        reported_drug_names = None
        for drug in drugs:
            char_code = str(drug.get("characterization"))
            med_name = drug.get("medicinalproduct", "").upper()

            openfda_dict = drug.get("openfda", {})
            generic_list = [g.upper() for g in openfda_dict.get("generic_name", [])]
            # Checks if the target generic matches the drug's generic name or medicinal product name
            if (target_generic.upper() in generic_list or target_generic.upper() in med_name):
                reported_drug_names = med_name
                if char_code == "1":
                    is_suspect = True
                    break
                # Stops checking drugs once a suspect drug is found
        if not is_suspect:
            continue

        reactions = patient.get("reaction", [])
        for rx in reactions:
            reaction_name = rx.get("reactionmeddrapt")
            if reaction_name:
                rows.append({
                    "safety_report_id": str(report_id),
                    "receive_date": pd.to_datetime(receive_date, format = "%Y%m%d", errors = "coerce"),
                    "patient_age_yrs": patient_age,
                    "patient_sex": patient_sex,
                    "is_serious": is_serious,
                    "reported_drug_names": reported_drug_names,
                    "standard_generic": target_generic,
                    "adverse_event_pt": reaction_name.upper().strip()
                })
                # Adds each reaction to the results for the suspect drug report
    return pd.DataFrame(rows)