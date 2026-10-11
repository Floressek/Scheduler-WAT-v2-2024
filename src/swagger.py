from typing import Any

SWAGGER_TEMPLATE: dict[str, Any] = {
    "info": {
        "title": "WAT Scheduler API",
        "description": "API for WAT class schedule scraping and Google Calendar synchronization.",
        "version": "1.0.0",
    },
    "host": "scheduler-wat-v2-2024-production.up.railway.app",
    "basePath": "/",
    "schemes": ["https"],
    "securityDefinitions": {
        "basicAuth": {"type": "basic"},
        "bearerAuth": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "security": [{"basicAuth": []}, {"bearerAuth": []}],
    "definitions": {
        "Lesson": {
            "type": "object",
            "properties": {
                "Subject": {"type": "string", "example": "Matematyka"},
                "Start Date": {"type": "string", "example": "01/10/2024"},
                "Start Time": {"type": "string", "example": "08:00"},
                "End Date": {"type": "string", "example": "01/10/2024"},
                "End Time": {"type": "string", "example": "09:35"},
                "All Day Event": {"type": "boolean", "example": False},
                "Description": {"type": "string", "example": "Wyklad"},
                "Location": {"type": "string", "example": "academic grounds"},
                "Private": {"type": "boolean", "example": True},
            },
        },
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "example": "Internal server error"}
            },
        },
        "Message": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Token deleted successfully"}
            },
        },
    },
}
