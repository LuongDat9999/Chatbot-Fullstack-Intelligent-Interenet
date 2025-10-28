"""Custom error classes for the application"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from typing import Any


class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CsvNotLoaded(AppError):
    """CSV not loaded in session"""
    def __init__(self, session_id: str):
        super().__init__(
            f"No CSV data loaded for session {session_id}",
            status.HTTP_404_NOT_FOUND
        )


class ColumnNotFound(AppError):
    """Column not found in CSV"""
    def __init__(self, column: str):
        super().__init__(
            f"Column '{column}' not found in dataset",
            status.HTTP_404_NOT_FOUND
        )


class InvalidCsv(AppError):
    """Invalid CSV format"""
    def __init__(self, message: str = "Invalid CSV format"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class CsvTooLarge(AppError):
    """CSV file too large"""
    def __init__(self, max_size_mb: int):
        super().__init__(
            f"CSV file exceeds maximum size of {max_size_mb}MB",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )


def register_error_handlers(app: FastAPI):
    """Register error handlers for the application"""
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc)
                }
            }
        )

