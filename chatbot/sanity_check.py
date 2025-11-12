def data_sanity_check(data: dict) -> str:
    """
    Basic deterministic data sanity validation.
    Returns PASS or FAIL only.
    Assumes fields are normalized to YES/NO/None or text.
    """

    # ✅ Require correct program name
    required_program_name = "Edmonton Zone FAST Program Facilitated Access to Surgical Treatment"
    program_name = data.get("Program name")

    # if field missing OR does not match exactly → fail as wrong form
    if program_name is None or str(program_name).strip() != required_program_name:
        return "FAIL wrong form"

    def is_yes(value):
        return str(value).strip().upper() == "YES"

    def is_no(value):
        return str(value).strip().upper() == "NO"

    def has_text(value):
        return value is not None and str(value).strip() != ""

    next_available = data.get("Refer to Next Available Surgeon")
    surgeon_name = data.get("Refer to Specific Hospital or Surgeon")

    positive_fit = data.get("Positive FIT")
    reason_ineligibility = data.get("Reason for Ineligibility")

    other_condition_flag = data.get("Other Condition Check")
    other_condition_text = data.get("Other Condition")

    # --- Surgeon Routing Logic ---
    if is_yes(next_available) and not has_text(surgeon_name):
        pass_surgeon = True
    elif is_no(next_available) and has_text(surgeon_name):
        pass_surgeon = True
    else:
        return "FAIL please check your next available surgeon data"

    # --- Positive FIT Logic ---
    if is_yes(positive_fit) and has_text(reason_ineligibility):
        pass_fit = True
    elif is_no(positive_fit) and not has_text(reason_ineligibility):
        pass_fit = True
    else:
        return "FAIL please check your positive fit input"

    # --- Other Condition Logic ---
    if is_yes(other_condition_flag) and has_text(other_condition_text):
        pass_other = True
    elif is_no(other_condition_flag) and not has_text(other_condition_text):
        pass_other = True
    else:
        return "FAIL please check your other condition data"

    return "PASS"
