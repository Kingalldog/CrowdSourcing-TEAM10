import json


def make_view_spec(view: dict) -> dict:
    return {
        "lock": {
            "core": "1.7.0",
            "view.list": "1.0.5",
            "view.text": "1.0.0",
            "field.radio-group": "1.1.10",
            "view.image": "1.2.0",
            "helper.if": "1.0.0",
            "condition.required": "1.1.5",
            "plugin.hotkeys": "1.0.0",
            "condition.equals": "1.0.0",
            "field.image-annotation": "1.0.0",
            "field.checkbox": "1.0.0",
            "plugin.field.image-annotation.hotkeys": "1.0.0",
            "action.set": "1.0.0",
            "plugin.toloka": "1.1.8",
            "condition.any": "1.0.0",
            "condition.not": "1.0.0",
        },
        "type": "tb",
        "config": json.dumps(view, ensure_ascii=False),
        "settings": {
            "showSkip": True,
            "showTimer": True,
            "showTitle": True,
            "showFinish": True,
            "showSubmit": True,
            "showMessage": True,
            "showFullscreen": True,
            "showInstructions": True,
        },
    }
