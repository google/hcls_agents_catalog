# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import base_tool
from google.adk.tools import ToolContext
from google.genai import types

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["ADK_ENABLE_PROGRESSIVE_SSE_STREAMING"] = "False"


BaseTool = base_tool.BaseTool

# --- A2UI Components Schema ---
AGENT_A2UI_COMPONENTS = {
    "type": "ARRAY",
    "description": "A list containing all UI components for the surface.",
    "items": {
        "type": "OBJECT",
        "description": "Represents a *single* component in a UI widget tree. This component could be one of many supported types.",
        "properties": {
            "id": {
                "type": "STRING",
                "description": "The unique identifier for this component. This MUST match a component ID that was previously created, such as the 'root' argument in a previous call to beginRendering."
            },
            "weight": {
                "type": "NUMBER",
                "description": "The relative weight of this component within a Row or Column. This corresponds to the CSS 'flex-grow' property. Note: this may ONLY be set when the component is a direct descendant of a Row or Column."
            },
            "component": {
                "type": "OBJECT",
                "description": "A wrapper object that MUST contain exactly one key, which is the name of the component type (e.g., 'Heading'). The value is an object containing the properties for that specific component.",
                "properties": {
                    "Text": {
                        "type": "OBJECT",
                        "properties": {
                            "text": {
                                "type": "OBJECT",
                                "description": "The text content to display. This can be a literal string or a reference to a value in the data model ('path', e.g., '/doc/title').",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "usageHint": {
                                "type": "STRING",
                                "description": "A hint for the base text style. One of: h1, h2, h3, h4, h5, caption, body.",
                                "enum": ["h1", "h2", "h3", "h4", "h5", "caption", "body"]
                            }
                        },
                        "required": ["text"]
                    },
                    "Image": {
                        "type": "OBJECT",
                        "properties": {
                            "url": {
                                "type": "OBJECT",
                                "description": "The URL of the image to display.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "fit": {
                                "type": "STRING",
                                "description": "Specifies how the image should be resized.",
                                "enum": ["contain", "cover", "fill", "none", "scale-down"]
                            },
                            "usageHint": {
                                "type": "STRING",
                                "description": "A hint for the image size and style.",
                                "enum": ["icon", "avatar", "smallFeature", "mediumFeature", "largeFeature", "header"]
                            }
                        },
                        "required": ["url"]
                    },
                    "Icon": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {
                                "type": "OBJECT",
                                "description": "The name of the icon to display.",
                                "properties": {
                                    "literalString": {
                                        "type": "STRING",
                                        "enum": [
                                            "accountCircle", "add", "arrowBack", "arrowForward", "attachFile", "calendarToday",
                                            "call", "camera", "check", "close", "delete", "download", "edit", "event", "error",
                                            "favorite", "favoriteOff", "folder", "help", "home", "info", "locationOn", "lock",
                                            "lockOpen", "mail", "menu", "moreVert", "moreHoriz", "notificationsOff", "notifications",
                                            "payment", "person", "phone", "photo", "print", "refresh", "search", "send", "settings",
                                            "share", "shoppingCart", "star", "starHalf", "starOff", "upload", "visibility",
                                            "visibilityOff", "warning"
                                        ]
                                    },
                                    "path": {"type": "STRING"}
                                }
                            }
                        },
                        "required": ["name"]
                    },
                    "Video": {
                        "type": "OBJECT",
                        "properties": {
                            "url": {
                                "type": "OBJECT",
                                "description": "The URL of the video to display.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            }
                        },
                        "required": ["url"]
                    },
                    "AudioPlayer": {
                        "type": "OBJECT",
                        "properties": {
                            "url": {
                                "type": "OBJECT",
                                "description": "The URL of the audio to be played.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "description": {
                                "type": "OBJECT",
                                "description": "A description of the audio.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            }
                        },
                        "required": ["url"]
                    },
                    "Row": {
                        "type": "OBJECT",
                        "properties": {
                            "children": {
                                "type": "OBJECT",
                                "description": "Defines the children.",
                                "properties": {
                                    "explicitList": {
                                        "type": "ARRAY",
                                        "items": {"type": "STRING"}
                                    },
                                    "template": {
                                        "type": "OBJECT",
                                        "description": "A template for generating a dynamic list of children.",
                                        "properties": {
                                            "componentId": {"type": "STRING"},
                                            "dataBinding": {"type": "STRING"}
                                        },
                                        "required": ["componentId", "dataBinding"]
                                    }
                                }
                            },
                            "distribution": {
                                "type": "STRING",
                                "description": "Defines the arrangement of children along the main axis.",
                                "enum": ["center", "end", "spaceAround", "spaceBetween", "spaceEvenly", "start"]
                            },
                            "alignment": {
                                "type": "STRING",
                                "description": "Defines the alignment of children along the cross axis.",
                                "enum": ["start", "center", "end", "stretch"]
                            }
                        },
                        "required": ["children"]
                    },
                    "Column": {
                        "type": "OBJECT",
                        "properties": {
                            "children": {
                                "type": "OBJECT",
                                "description": "Defines the children.",
                                "properties": {
                                    "explicitList": {
                                        "type": "ARRAY",
                                        "items": {"type": "STRING"}
                                    },
                                    "template": {
                                        "type": "OBJECT",
                                        "description": "A template for generating a dynamic list of children.",
                                        "properties": {
                                            "componentId": {"type": "STRING"},
                                            "dataBinding": {"type": "STRING"}
                                        },
                                        "required": ["componentId", "dataBinding"]
                                    }
                                }
                            },
                            "distribution": {
                                "type": "STRING",
                                "description": "Defines the arrangement of children along the main axis.",
                                "enum": ["start", "center", "end", "spaceBetween", "spaceAround", "spaceEvenly"]
                            },
                            "alignment": {
                                "type": "STRING",
                                "description": "Defines the alignment of children along the cross axis.",
                                "enum": ["center", "end", "start", "stretch"]
                            }
                        },
                        "required": ["children"]
                    },
                    "List": {
                        "type": "OBJECT",
                        "properties": {
                            "children": {
                                "type": "OBJECT",
                                "description": "Defines the children.",
                                "properties": {
                                    "explicitList": {
                                        "type": "ARRAY",
                                        "items": {"type": "STRING"}
                                    },
                                    "template": {
                                        "type": "OBJECT",
                                        "description": "A template for generating a dynamic list of children.",
                                        "properties": {
                                            "componentId": {"type": "STRING"},
                                            "dataBinding": {"type": "STRING"}
                                        },
                                        "required": ["componentId", "dataBinding"]
                                    }
                                }
                            },
                            "direction": {
                                "type": "STRING",
                                "description": "The direction in which the list items are laid out.",
                                "enum": ["vertical", "horizontal"]
                            },
                            "alignment": {
                                "type": "STRING",
                                "description": "Defines the alignment of children along the cross axis.",
                                "enum": ["start", "center", "end", "stretch"]
                            }
                        },
                        "required": ["children"]
                    },
                    "Card": {
                        "type": "OBJECT",
                        "properties": {
                            "child": {
                                "type": "STRING",
                                "description": "The ID of the component to be rendered inside the card."
                            }
                        },
                        "required": ["child"]
                    },
                    "Tabs": {
                        "type": "OBJECT",
                        "properties": {
                            "tabItems": {
                                "type": "ARRAY",
                                "description": "An array of objects defining tabs.",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "title": {
                                            "type": "OBJECT",
                                            "description": "The tab title.",
                                            "properties": {
                                                "literalString": {"type": "STRING"},
                                                "path": {"type": "STRING"}
                                            }
                                        },
                                        "child": {"type": "STRING"}
                                    },
                                    "required": ["title", "child"]
                                }
                            }
                        },
                        "required": ["tabItems"]
                    },
                    "Divider": {
                        "type": "OBJECT",
                        "properties": {
                            "axis": {
                                "type": "STRING",
                                "description": "The orientation of the divider.",
                                "enum": ["horizontal", "vertical"]
                            }
                        }
                    },
                    "Modal": {
                        "type": "OBJECT",
                        "properties": {
                            "entryPointChild": {
                                "type": "STRING",
                                "description": "The ID of the component that opens the modal."
                            },
                            "contentChild": {
                                "type": "STRING",
                                "description": "The ID of the component to be displayed inside the modal."
                            }
                        },
                        "required": ["entryPointChild", "contentChild"]
                    },
                    "Button": {
                        "type": "OBJECT",
                        "properties": {
                            "child": {
                                "type": "STRING",
                                "description": "The ID of the component to display in the button."
                            },
                            "primary": {
                                "type": "BOOLEAN",
                                "description": "Indicates if this button should be styled as the primary action."
                            },
                            "action": {
                                "type": "OBJECT",
                                "description": "The client-side action to be dispatched.",
                                "properties": {
                                    "name": {"type": "STRING"},
                                    "context": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "key": {"type": "STRING"},
                                                "value": {
                                                    "type": "OBJECT",
                                                    "properties": {
                                                        "path": {"type": "STRING"},
                                                        "literalString": {"type": "STRING"},
                                                        "literalNumber": {"type": "NUMBER"},
                                                        "literalBoolean": {"type": "BOOLEAN"}
                                                    }
                                                }
                                            },
                                            "required": ["key", "value"]
                                        }
                                    }
                                },
                                "required": ["name"]
                            }
                        },
                        "required": ["child", "action"]
                    },
                    "CheckBox": {
                        "type": "OBJECT",
                        "properties": {
                            "label": {
                                "type": "OBJECT",
                                "description": "The text to display next to the checkbox.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "value": {
                                "type": "OBJECT",
                                "description": "The current state of the checkbox.",
                                "properties": {
                                    "literalBoolean": {"type": "BOOLEAN"},
                                    "path": {"type": "STRING"}
                                }
                            }
                        },
                        "required": ["label", "value"]
                    },
                    "TextField": {
                        "type": "OBJECT",
                        "properties": {
                            "label": {
                                "type": "OBJECT",
                                "description": "The text label for the input field.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "text": {
                                "type": "OBJECT",
                                "description": "The value of the text field.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "textFieldType": {
                                "type": "STRING",
                                "description": "The type of input field to display.",
                                "enum": ["date", "longText", "number", "shortText", "obscured"]
                            },
                            "validationRegexp": {
                                "type": "STRING",
                                "description": "A regular expression used for client-side validation."
                            }
                        },
                        "required": ["label"]
                    },
                    "DateTimeInput": {
                        "type": "OBJECT",
                        "properties": {
                            "value": {
                                "type": "OBJECT",
                                "description": "The selected date and/or time value.",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "enableDate": {
                                "type": "BOOLEAN",
                                "description": "If true, allows the user to select a date."
                            },
                            "enableTime": {
                                "type": "BOOLEAN",
                                "description": "If true, allows the user to select a time."
                            },
                            "outputFormat": {
                                "type": "STRING",
                                "description": "The desired format for the output string."
                            }
                        },
                        "required": ["value"]
                    },
                    "MultipleChoice": {
                        "type": "OBJECT",
                        "properties": {
                            "selections": {
                                "type": "OBJECT",
                                "description": "The currently selected values for the component.",
                                "properties": {
                                    "literalArray": {
                                        "type": "ARRAY",
                                        "items": {"type": "STRING"}
                                    },
                                    "path": {"type": "STRING"}
                                }
                            },
                            "options": {
                                "type": "ARRAY",
                                "description": "An array of available options.",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "label": {
                                            "type": "OBJECT",
                                            "description": "The text to display for this option.",
                                            "properties": {
                                                "literalString": {"type": "STRING"},
                                                "path": {"type": "STRING"}
                                            }
                                        },
                                        "value": {
                                            "type": "STRING",
                                            "description": "The value to be associated with this option."
                                        }
                                    },
                                    "required": ["label", "value"]
                                }
                            },
                            "maxAllowedSelections": {
                                "type": "NUMBER",
                                "description": "The maximum number of options that the user is allowed to select."
                            }
                        },
                        "required": ["selections", "options"]
                    },
                    "Slider": {
                        "type": "OBJECT",
                        "properties": {
                            "value": {
                                "type": "OBJECT",
                                "description": "The current value of the slider.",
                                "properties": {
                                    "literalNumber": {"type": "NUMBER"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "minValue": {
                                "type": "NUMBER",
                                "description": "The minimum value of the slider."
                            },
                            "maxValue": {
                                "type": "NUMBER",
                                "description": "The maximum value of the slider."
                            }
                        },
                        "required": ["value"]
                    },
                    "WebFrameSrcdoc": {
                        "type": "OBJECT",
                        "description": "Renders a specific application view or raw HTML.",
                        "properties": {
                            "view_type": {
                                "type": "STRING",
                                "description": "The name of the UI component to render.",
                                "enum": ["IssueTracker", "UserProfile", "AnalyticsChart", "HtmlViewer"]
                            },
                            "height": {
                                "type": "NUMBER"
                            }
                        },
                        "required": ["view_type"]
                    },
                    'WebFrameUrl': {
                        'type': 'OBJECT',
                        'description': 'Renders a specific webpage in an iframe',
                        'properties': {
                            'url': {
                                'type': 'OBJECT',
                                'description': (
                                    'The URL to render. Use literalString for a fixed URL'
                                    ' or path for data-binding.'
                                ),
                                'properties': {
                                    'literalString': {
                                        'type': 'STRING',
                                        'description': 'The hardcoded URL string',
                                    },
                                    'path': {
                                        'type': 'STRING',
                                        'description': (
                                            'A path to a value in the data model (e.g.'
                                            ' /results/0/url)'
                                        ),
                                    },
                                },
                            },
                            'height': {'type': 'NUMBER'},
                        },
                        'required': ['url'],
                    }
                }
            }
        },
        "required": ["id", "component"]
    }
}

# --- Hydration Handlers & Html Manager ---
class HtmlRenderManager(Protocol):
    async def render_html(
        self,
        view_type: str,
        data: dict[str, Any],
        context: ToolContext
    ) -> str:
        ...

class AppHtmlManager:
    async def render_html(
        self,
        view_type: str,
        data: dict[str, Any],
        context: ToolContext
    ) -> str:
        return "<div style='padding:20px;'>No HTML template matches this request.</div>"

class BaseA2UIComponentHandler:
    @classmethod
    def get_name(cls) -> str:
        raise NotImplementedError

    async def hydrate(self, llm_args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        return llm_args

class WebFrameSrcdocHandler(BaseA2UIComponentHandler):
    def __init__(self, html_manager: HtmlRenderManager):
        self._html_manager = html_manager

    @classmethod
    def get_name(cls) -> str:
        return "WebFrameSrcdoc"

    async def hydrate(self, llm_args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        view_type = llm_args.get("view_type")
        if not view_type:
            return llm_args
        data_args = llm_args.get("data", {})
        try:
            html_content = await self._html_manager.render_html(view_type, data_args, tool_context)
        except Exception as e:
            html_content = f"<div class='error'>Failed to load {view_type}</div>"
        return {
            "htmlContent": {"literalString": html_content},
            "interactionMode": "readOnly"
        }

class WebFrameUrlHandler(BaseA2UIComponentHandler):
    @classmethod
    def get_name(cls) -> str:
        return "WebFrameUrl"

    async def hydrate(self, llm_args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        url = llm_args.get("url", {}).get("literalString", "")
        # Convert this WebFrameUrl into a WebFrameSrcdoc redirecting to the URL
        redirect_html = f'<script>window.location.href="{url}";</script>'
        return {
            "WebFrameSrcdoc": {
                "htmlContent": {
                    "literalString": redirect_html
                },
                "height": llm_args.get("height", 800)
            }
        }

# --- A2UI Tools Implementation ---
class BeginRenderingTool(BaseTool):
    def __init__(self):
        super().__init__(name="beginRendering", description="Signals the client to begin rendering a surface.")
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "OBJECT",
                "properties": {
                    "surfaceId": {
                        "type": "STRING",
                        "description": "The ID of the surface to create."
                    },
                    "root": {
                        "type": "STRING",
                        "description": "The ID of the root component."
                    }
                },
                "required": ["root", "surfaceId"]
            }
        )

    def _get_declaration(self) -> types.FunctionDeclaration:
        return self._declaration

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        return {"beginRendering": args}

class SurfaceUpdateTool(BaseTool):
    def __init__(
        self,
        component_schemas: dict[str, Any],
        handlers: list[BaseA2UIComponentHandler] | None = None
    ):
        super().__init__(name="surfaceUpdate", description="Updates a surface with a new set of components.")
        self._handlers = {h.get_name(): h for h in (handlers or [])}
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "OBJECT",
                "properties": {
                    "surfaceId": {"type": "STRING"},
                    "components": component_schemas
                },
                "required": ["surfaceId", "components"]
            }
        )

    def _get_declaration(self) -> types.FunctionDeclaration:
        return self._declaration

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        if "components" in args and self._handlers:
            args["components"] = await self._hydrate_components(args["components"], tool_context)
        return {"surfaceUpdate": args}

    async def _hydrate_components(self, components: list[Any], tool_context: ToolContext) -> list[Any]:
        import json
        import re

        pattern = re.compile(
            r'\\?"WebFrameUrl\\?"\s*:\s*\{\s*'
            r'\\?"url\\?"\s*:\s*\{\s*\\?"literalString\\?"\s*:\s*\\?"([^"\\]+)\\?"\s*\}'
            r'(?:\s*,\s*\\?"height\\?"\s*:\s*(\d+))?\s*\}'
        )

        def replace_match(match):
            url = match.group(1)
            height = match.group(2) or "800"
            is_escaped = match.group(0).startswith('\\"')
            
            if is_escaped:
                escaped_script = f'<script>window.location.href=\\\\\\"{url}\\\\\\";</script>'
                return f'\\"WebFrameSrcdoc\\":{{\\"htmlContent\\":{{\\"literalString\\":\\"{escaped_script}\\"}},\\"height\\":{height}}}'
            else:
                escaped_script = f'<script>window.location.href=\\"{url}\\";</script>'
                return f'"WebFrameSrcdoc":{{"htmlContent":{{"literalString":"{escaped_script}"}},"height":{height}}}'

        hydrated_components = []
        for comp_node in components:
            if isinstance(comp_node, str):
                comp_node = pattern.sub(replace_match, comp_node)
                comp_node_str = comp_node.strip()
                if comp_node_str.startswith("{") and comp_node_str.endswith("}"):
                    try:
                        comp_node = json.loads(comp_node_str)
                    except Exception:
                        pass
            if isinstance(comp_node, dict):
                component_wrapper = comp_node.get("component", {})
                if component_wrapper:
                    keys = list(component_wrapper.keys())
                    if len(keys) == 1:
                        comp_type = keys[0]
                        if comp_type in self._handlers:
                            comp_data = component_wrapper[comp_type]
                            hydrated_data = await self._handlers[comp_type].hydrate(comp_data, tool_context)
                            if isinstance(hydrated_data, dict) and len(hydrated_data) == 1 and (list(hydrated_data.keys())[0] in self._handlers or list(hydrated_data.keys())[0] == "WebFrameSrcdoc"):
                                comp_node["component"] = hydrated_data
                            else:
                                comp_node["component"][comp_type] = hydrated_data
            hydrated_components.append(comp_node)
        return hydrated_components

class DataModelUpdateTool(BaseTool):
    def __init__(self):
        super().__init__(name="dataModelUpdate", description="Updates the data model for a surface.")
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "OBJECT",
                "properties": {
                    "surfaceId": {"type": "STRING"},
                    "path": {"type": "STRING"},
                    "contents": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "key": {"type": "STRING"},
                                "valueString": {"type": "STRING"},
                                "valueNumber": {"type": "NUMBER"},
                                "valueBoolean": {"type": "BOOLEAN"}
                            },
                            "required": ["key"]
                        }
                    }
                },
                "required": ["contents", "surfaceId"]
            }
        )

    def _get_declaration(self) -> types.FunctionDeclaration:
        return self._declaration

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        return {"dataModelUpdate": args}

class DeleteSurfaceTool(BaseTool):
    def __init__(self):
        super().__init__(name="deleteSurface", description="Signals the client to delete the surface.")
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "OBJECT",
                "properties": {"surfaceId": {"type": "STRING"}},
                "required": ["surfaceId"]
            }
        )

    def _get_declaration(self) -> types.FunctionDeclaration:
        return self._declaration

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        return {"deleteSurface": args}


# --- Instantiate Root Agent & App ---

html_manager = AppHtmlManager()
web_frame_handler = WebFrameSrcdocHandler(html_manager=html_manager)

a2ui_tools = [
    BeginRenderingTool(),
    SurfaceUpdateTool(component_schemas=AGENT_A2UI_COMPONENTS, handlers=[web_frame_handler, WebFrameUrlHandler()]),
    DataModelUpdateTool(),
    DeleteSurfaceTool()
]

model_config = Gemini(
    model="gemini-flash-latest",
    retry_options=types.HttpRetryOptions(attempts=3),
)

AGENT_URL = os.getenv("APP_URL") or os.getenv("AGENT_URL") or "http://localhost:8000"

ROLE_DESCRIPTION = (
    "You are a helpful A2UI assistant. Your main task is to display documents "
    "requested by the user. You have access to a suite of A2UI tools: "
    "`beginRendering`, `surfaceUpdate`, `dataModelUpdate`, and `deleteSurface`, "
    "which you MUST use to present rich UI components to the user."
)

WORKFLOW_DESCRIPTION = (
    "- When the user asks to show, display, or view a document (e.g., matching a pattern like "
    "gs://bucket-name/path/to/document.pdf or gs://bucket-name/path/to/document.docx), you MUST generate a proxy URL and display it "
    "using an iframe.\n"
    f"- Construct the document proxy URL by taking the base agent URL '{AGENT_URL}' "
    "and appending the correct endpoint path followed by the full GCS URI. "
    "For PDF documents (*.pdf), use '/pdf?url='. "
    "For Microsoft Word documents (*.docx), use '/docx?url='.\n"
    f"For example:\n"
    f"  - If the GCS URI is gs://hcls-ge-documents/roi_2025_health.pdf, the proxy URL is "
    f"'{AGENT_URL}/pdf?url=gs://hcls-ge-documents/roi_2025_health.pdf'.\n"
    f"  - If the GCS URI is gs://ge-demo-docs/atest.docx, the proxy URL is "
    f"'{AGENT_URL}/docx?url=gs://ge-demo-docs/atest.docx'.\n"
    "- To render this iframe, use a `WebFrameUrl` component with the constructed proxy URL.\n"
    "- STRICT UI WORKFLOW: To show the document UI, you MUST call `surfaceUpdate` first "
    "to define the components. ONLY AFTER defining your components should you use `beginRendering` to trigger "
    "the actual render.\n"
    "- Always keep the surfaceId as 'main_app'.\n"
    "- Along with calling the rendering tools, you MUST also output a short, helpful text response to the user confirming which document you are rendering (e.g., 'Here is the document gs://...' or 'Rendering gs://...').\n"
)

UI_DESCRIPTION = (
    "Here is how to manage the User Interface using your tools. You MUST follow this exact order when creating a new surface:\n"
    "1. `surfaceUpdate`: Use this FIRST to send the actual UI components. The components list must contain the container "
    "and the WebFrameUrl component. The components list in surfaceUpdate must ONLY contain valid component objects. "
    "NEVER nest any tool calls or other function calls inside the components list.\n"
    "2. `beginRendering`: Use this ONLY AFTER your surfaceUpdate call is sent. This specifies the root component ID and tells the client to render the buffered surface.\n\n"
    "=== EXAMPLE OF SHOWING A PDF DOCUMENT ===\n"
    "User: show gs://hcls-ge-documents/roi_2025_health.pdf\n"
    "Agent Calls:\n"
    "1. surfaceUpdate(surfaceId='main_app', components=[{\n"
    "     'id': 'root',\n"
    "     'component': {\n"
    "       'Column': {\n"
    "         'children': {\n"
    "           'explicitList': ['iframe']\n"
    "         }\n"
    "       }\n"
    "     }\n"
    "   }, {\n"
    "     'id': 'iframe',\n"
    "     'component': {\n"
    "       'WebFrameUrl': {\n"
    "         'url': {\n"
    f"           'literalString': '{AGENT_URL}/pdf?url=gs://hcls-ge-documents/roi_2025_health.pdf'\n"
    "         },\n"
    "         'height': 800\n"
    "       }\n"
    "     }\n"
    "   }])\n"
    "2. beginRendering(surfaceId='main_app', root='root')\n\n"
    "=== EXAMPLE OF SHOWING A WORD (DOCX) DOCUMENT ===\n"
    "User: show me the document gs://ge-demo-docs/atest.docx\n"
    "Agent Calls:\n"
    "1. surfaceUpdate(surfaceId='main_app', components=[{\n"
    "     'id': 'root',\n"
    "     'component': {\n"
    "       'Column': {\n"
    "         'children': {\n"
    "           'explicitList': ['iframe']\n"
    "         }\n"
    "       }\n"
    "     }\n"
    "   }, {\n"
    "     'id': 'iframe',\n"
    "     'component': {\n"
    "       'WebFrameUrl': {\n"
    "         'url': {\n"
    f"           'literalString': '{AGENT_URL}/docx?url=gs://ge-demo-docs/atest.docx'\n"
    "         },\n"
    "         'height': 800\n"
    "       }\n"
    "     }\n"
    "   }])\n"
    "2. beginRendering(surfaceId='main_app', root='root')\n"
)

instruction = f"{ROLE_DESCRIPTION}\n\n=== WORKFLOW ===\n{WORKFLOW_DESCRIPTION}\n\n=== UI SYSTEM ===\n{UI_DESCRIPTION}"

root_agent = Agent(
    name="root_agent",
    model=model_config,
    description="An agent that renders document PDFs in an iframe.",
    instruction=instruction,
    tools=a2ui_tools,
)

app = App(
    root_agent=root_agent,
    name="app",
)
