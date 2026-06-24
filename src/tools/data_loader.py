"""Data loading utilities for CSV and JSON files."""

import json
from pathlib import Path
from typing import Optional
import pandas as pd

from src.config import settings


class DataLoader:
    """Loads and caches data from local files."""
    
    _customers_df: Optional[pd.DataFrame] = None
    _orders_df: Optional[pd.DataFrame] = None
    _refund_policies: Optional[dict] = None
    _tickets_df: Optional[pd.DataFrame] = None
    
    @classmethod
    def get_customers(cls, reload: bool = False) -> pd.DataFrame:
        """Load customers data."""
        if cls._customers_df is None or reload:
            cls._customers_df = pd.read_csv(settings.customers_path)
        return cls._customers_df
    
    @classmethod
    def get_orders(cls, reload: bool = False) -> pd.DataFrame:
        """Load orders data."""
        if cls._orders_df is None or reload:
            cls._orders_df = pd.read_csv(settings.orders_path)
        return cls._orders_df
    
    @classmethod
    def get_refund_policies(cls, reload: bool = False) -> dict:
        """Load refund policies."""
        if cls._refund_policies is None or reload:
            with open(settings.refund_policies_path, "r") as f:
                cls._refund_policies = json.load(f)
        return cls._refund_policies
    
    @classmethod
    def get_tickets(cls, reload: bool = False) -> pd.DataFrame:
        """Load support tickets."""
        if cls._tickets_df is None or reload:
            cls._tickets_df = pd.read_csv(settings.tickets_path)
        return cls._tickets_df
    
    @classmethod
    def save_ticket(cls, ticket_data: dict) -> None:
        """Append a new ticket to the CSV."""
        tickets = cls.get_tickets()
        new_ticket = pd.DataFrame([ticket_data])
        tickets = pd.concat([tickets, new_ticket], ignore_index=True)
        tickets.to_csv(settings.tickets_path, index=False)
        cls._tickets_df = tickets
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached data."""
        cls._customers_df = None
        cls._orders_df = None
        cls._refund_policies = None
        cls._tickets_df = None
