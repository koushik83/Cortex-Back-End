# __init__.py
from . import bot
from . import processor
from . import insights
from . import store

__version__ = "0.1.0"

# Export key functions for easier imports
from .bot import process_message, add_company_knowledge
from .processor import process_document, process_webpage  # Changed from process_documents
from .insights import get_analytics
from .store import save_data, get_data