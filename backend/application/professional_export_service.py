"""Compatibility entrypoint for the paused historical workflow."""
from application.local_project_export_service import LocalProjectExportService


class ProfessionalExportService(LocalProjectExportService):
    pass
