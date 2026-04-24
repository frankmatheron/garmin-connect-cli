from __future__ import annotations

import json


def emit(data: object, pretty: bool) -> None:
    """JSON by default; with --pretty, indent dicts/lists and stringify scalars.

    The per-command modules override this with a table-shaped pretty form
    when the payload has an obvious row structure.
    """
    if pretty:
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)
    else:
        print(json.dumps(data, ensure_ascii=False))
