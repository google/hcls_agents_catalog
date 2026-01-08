import requests
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_spelling_suggestion(drug_name):
    """
    Fetches spelling suggestions for a drug name from the RxNav API.

    Args:
        drug_name (str): The potentially misspelled drug name.

    Returns:
        str: The first spelling suggestion, or None if no suggestion is found
             or an error occurs.
    """
    if not drug_name:
        return None

    url = f"https://rxnav.nlm.nih.gov/REST/spellingsuggestions.json?name={drug_name}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        suggestion_group = data.get("suggestionGroup")
        if suggestion_group:
            suggestion_list = suggestion_group.get("suggestionList")
            if suggestion_list and "suggestion" in suggestion_list:
                suggestions = suggestion_list["suggestion"]
                if suggestions and isinstance(suggestions, list) and len(suggestions) > 0:
                    return suggestions[0]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during spelling suggestion API request for '{drug_name}': {e}")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing spelling suggestion response for '{drug_name}': {e}")
    return None

# Helper function to parse clinical drug name into components
KNOWN_DOSE_FORMS = sorted([
    "Extended Release Tablet", "Delayed Release Tablet", "Orally Disintegrating Tablet", "Chewable Tablet", "Effervescent Tablet", "Buccal Tablet", "Sublingual Tablet", "Oral Tablet", "Tablet",
    "Extended Release Capsule", "Delayed Release Capsule", "Oral Capsule", "Capsule",
    "Oral Solution", "Oral Suspension", "Oral Syrup", "Oral Elixir", "Oral Powder for Solution", "Oral Powder for Suspension", "Powder for Oral Solution", "Powder for Oral Suspension",
    "Injectable Solution", "Injectable Suspension", "Powder for Injectable Solution", "Injection", "Solution for Injection",
    "Topical Cream", "Cream", "Topical Ointment", "Ointment", "Topical Gel", "Gel", "Topical Lotion", "Lotion", "Topical Patch", "Transdermal Patch", "Patch", "Topical Solution", "Topical Suspension", "Topical Spray",
    "Nasal Spray", "Nasal Solution", "Nasal Suspension",
    "Inhalation Solution", "Inhalation Suspension", "Inhalation Aerosol", "Metered Dose Inhaler", "Powder for Inhalation",
    "Ophthalmic Solution", "Ophthalmic Ointment", "Ophthalmic Gel", "Ophthalmic Suspension", "Eye Drops",
    "Otic Solution", "Otic Suspension", "Ear Drops", "Rectal Suppository", "Vaginal Cream", "Vaginal Tablet", "Vaginal Suppository", "Vaginal Ring"
], key=len, reverse=True)

COMMON_UNITS_REGEX = r"(?:MG|MCG|G|ML|L|%|U|IU|MEQ|ACTUAT|HR|UNT|DOSE|PUFF|SPRAY|DROP|APPL|KIT|VIAL|SYRINGE|CARTRIDGE|PEN|AMPUL|BTL|BAG|PATCH|UL|MCL|MOL|MMOL|UMOL|NMOL|PMOL|GM|KG|OZ|LB|FL OZ|PT|QT|GAL|CC|TSP|TBSP)"

def parse_clinical_drug_name(name_str_to_parse):
    name_str = name_str_to_parse.strip()

    parsed_ingredient = "N/A"
    parsed_strength = "N/A"
    parsed_dose_form = "N/A"

    text_before_dose_form = name_str
    for df in KNOWN_DOSE_FORMS:
        # Case-insensitive match for dose form at the end of the string, ensuring word boundary
        df_match_obj = re.search(r"\b" + re.escape(df) + r"$", name_str, re.IGNORECASE)
        if df_match_obj:
            parsed_dose_form = df_match_obj.group(0) # Preserve original casing
            text_before_dose_form = name_str[:df_match_obj.start()].strip()
            break

    if not text_before_dose_form:
        parsed_ingredient = name_str if parsed_dose_form == "N/A" else "N/A"
    else:
        # Regex for strength: (value unit (/ value unit)*) at the end of text_before_dose_form
        strength_pattern_str = r"((?:\d+(?:\.\d+)?)\s*" + COMMON_UNITS_REGEX + r"(?:\s*[/]\s*(?:\d+(?:\.\d+)?)\s*" + COMMON_UNITS_REGEX + r")*)$"
        strength_match = re.search(strength_pattern_str, text_before_dose_form, re.IGNORECASE)

        if strength_match:
            parsed_strength = strength_match.group(1).strip()
            parsed_ingredient = text_before_dose_form[:strength_match.start()].strip()
            if not parsed_ingredient:
                 parsed_ingredient = "N/A"
        else:
            parsed_ingredient = text_before_dose_form.strip()

    if parsed_ingredient == "" and (parsed_strength != "N/A" or parsed_dose_form != "N/A"):
        parsed_ingredient = "N/A"
    elif not parsed_ingredient and parsed_strength == "N/A" and parsed_dose_form == "N/A":
        parsed_ingredient = name_str # Default to full name if nothing else worked

    return parsed_ingredient, parsed_strength, parsed_dose_form

def get_drug_info(drug_name):
    """
    Fetches drug information from the RxNav API and parses name and synonym.

    Args:
        drug_name (str): The name of the drug to search for.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              detailed information for each clinical drug.
              Returns an empty list if the request fails or no data is found.
    """
    if not drug_name:
        return []

    url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={drug_name}"
    drug_data = []

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        drug_group = data.get("drugGroup")
        if drug_group and drug_group.get("conceptGroup"):
            for concept_g in drug_group.get("conceptGroup", []):
                tty = concept_g.get("tty")
                # We are interested in Semantic Clinical Drugs (SCD) and Semantic Brand Drugs (SBD)
                if tty in ["SCD", "SBD"]:
                    for concept_prop in concept_g.get("conceptProperties", []):
                        name_api = concept_prop.get("name")
                        rxcui = concept_prop.get("rxcui")

                        if name_api and rxcui:
                            standardized_name_for_display = name_api

                            name_to_parse = name_api
                            bracket_start = name_api.find('[')
                            if bracket_start != -1:
                                name_to_parse = name_api[:bracket_start].strip()

                            ingredient, strength, dose_form = parse_clinical_drug_name(name_to_parse)
                            drug_data.append({
                                'standardized_name': standardized_name_for_display,
                                'rxcui': rxcui,
                                'active_ingredient': ingredient if ingredient else "N/A",
                                'strength': strength if strength else "N/A",
                                'dose_form': dose_form if dose_form else "N/A"
                            })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during drug info API request for '{drug_name}': {e}")
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing drug info response for '{drug_name}': {e}")

    return drug_data

if __name__ == "__main__":
    # drug_name_to_check = "atorvastation" # Potentially misspelled "lipitir"
    drug_name_to_check = "morphine sulfate" # Potentially misspelled "lipitir"

    print(f"Checking spelling for: '{drug_name_to_check}'")

    corrected_name = get_spelling_suggestion(drug_name_to_check)

    if corrected_name and corrected_name.lower() != drug_name_to_check.lower():
        print(f"Did you mean '{corrected_name}'? Using this suggestion.")
        drug_name_to_use = corrected_name
    elif corrected_name:
        print(f"Spelling appears correct: '{corrected_name}'")
        drug_name_to_use = corrected_name
    else:
        print(f"No spelling suggestion found for '{drug_name_to_check}'. Using original input.")
        drug_name_to_use = drug_name_to_check

    if drug_name_to_use:
        extracted_info = get_drug_info(drug_name_to_use)

        if extracted_info:
            print(f"\nInformation for '{drug_name_to_use}':")
            print("-" * 20)
            for item in extracted_info:
                print(f"{item['standardized_name']} ({item['rxcui']}): {item['active_ingredient']}, {item['strength']}, {item['dose_form']}")
        else:
            print(f"No information found for '{drug_name_to_use}' or an error occurred.")
