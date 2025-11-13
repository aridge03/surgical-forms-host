def data_sanity_check(data: dict) -> list:
    """
    Deterministic data sanity validation.
    Returns a list of error messages.
    If everything passes, returns ["PASS"].
    """

    errors = []

    # Required program name
    required_program_name = "Edmonton Zone FAST Program Facilitated Access to Surgical Treatment"
    program_name = data.get("Program name")

    if program_name is None or str(program_name).strip() != required_program_name:
        errors.append("Wrong form: Program name does not match required value.")

    # Helpers
    def is_yes(value):
        return str(value).strip().upper() == "YES"

    def is_no(value):
        return str(value).strip().upper() == "NO"

    def has_text(value):
        return value is not None and str(value).strip() != ""

    # Extract fields
    next_available = data.get("Refer to Next Available Surgeon")
    surgeon_name = data.get("Refer to Specific Hospital or Surgeon")

    positive_fit = data.get("Positive FIT")
    reason_ineligibility = data.get("Reason for Ineligibility")

    other_condition_flag = data.get("Other Condition Check")
    other_condition_text = data.get("Other Condition")

    # --- Surgeon Routing Logic ---
    if is_yes(next_available) and not has_text(surgeon_name):
        pass  # OK
    elif is_no(next_available) and has_text(surgeon_name):
        pass  # OK
    elif is_yes(next_available) and has_text(surgeon_name):
        errors.append("Invalid surgeon routing: cannot have both next available and a specific surgeon selected.")
    else:
        errors.append("Invalid surgeon routing: must have either a next available or a specific surgeon selected.")


    # --- Positive FIT Logic ---
    if is_yes(positive_fit) and has_text(reason_ineligibility):
        pass
    elif is_no(positive_fit) and not has_text(reason_ineligibility):
        pass
    elif is_no(positive_fit) and has_text(reason_ineligibility):
        errors.append("Invalid FIT section: check Positive FIT with your Ineligibility.")
    else:
        errors.append("Invalid FIT section: please provide Ineligibility reason with check Positive FIT result.")


    # --- Other Condition Logic ---
    if is_yes(other_condition_flag) and has_text(other_condition_text):
        pass
    elif is_no(other_condition_flag) and not has_text(other_condition_text):
        pass
    elif is_no(other_condition_flag) and  has_text(other_condition_text):
        errors.append("Invalid Other Condition section: Please check the other condition box since you provided other condition description.")
    else:
        errors.append("Invalid Other Condition section: Please provide other condition descritption since you checked off the other condition option.")


    # Final result
    if errors:
        return errors
    return ["PASS"]
