"""Task 7: verify do_release is imported from utils in dokima."""
import os


def test_do_release_in_import():
    """RED: do_release must appear in the from-utils import block."""
    panel_path = os.path.join(os.path.dirname(__file__), "..", "dokima")
    with open(panel_path, "r") as f:
        lines = f.readlines()

    # Locate the from-utils import block — it spans lines containing
    # 'from utils import (' through to the matching closing paren.
    in_import = False
    found = False
    for line in lines:
        if "from utils import (" in line:
            in_import = True
        if in_import:
            if "do_release" in line:
                found = True
                break
            if ")" in line and not "(" in line.replace("from utils import (", ""):
                # Closing paren reached — end of block
                break

    assert found, "do_release missing from from-utils import block in dokima"
